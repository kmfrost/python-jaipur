"""
RL-based player for Jaipur GUI.
Uses a trained PPO model to select actions.
Falls back to RandomPlayer if no model exists or action is invalid.
"""

import os
import random
from collections import Counter

import numpy as np

from Player import Player
from RandomPlayer import RandomPlayer


class RLPlayer(Player):
    """Player that uses a trained RL model to select actions."""

    CARD_TYPES = ["leather", "spice", "cloth", "silver", "gold", "diamond", "camel"]
    GOOD_TYPES = ["leather", "spice", "cloth", "silver", "gold", "diamond"]

    def __init__(self, game_engine, model_path=None):
        super().__init__(game_engine)
        self.model = None
        self._fallback = RandomPlayer(game_engine)

        # Try to load model
        if model_path:
            self._load_model(model_path)
        else:
            # Look for most recent model in default location
            self._load_latest_model()

    def _load_model(self, model_path):
        """Load a trained PPO model."""
        try:
            from stable_baselines3 import PPO
            # Add .zip extension if needed
            if not model_path.endswith('.zip'):
                model_path_zip = model_path + '.zip'
            else:
                model_path_zip = model_path

            if os.path.exists(model_path_zip):
                self.model = PPO.load(model_path.replace('.zip', ''))
                print(f"Loaded RL model from {model_path}")
            elif os.path.exists(model_path):
                self.model = PPO.load(model_path)
                print(f"Loaded RL model from {model_path}")
            else:
                print(f"Model not found at {model_path}, using random player")
        except ImportError:
            print("stable_baselines3 not installed, using random player")
        except Exception as e:
            print(f"Error loading model: {e}, using random player")

    def _load_latest_model(self):
        """Look for the most recent trained model."""
        models_dirs = [
            "rl_scripts/models",
            "models",
        ]

        for models_dir in models_dirs:
            if os.path.exists(models_dir):
                models = [f for f in os.listdir(models_dir) if f.startswith("jaipur_ppo")]
                if models:
                    # Get most recent (alphabetically last due to timestamp naming)
                    latest = sorted(models)[-1]
                    model_path = os.path.join(models_dir, latest.replace('.zip', ''))
                    self._load_model(model_path)
                    return

        print("No trained model found, using random player")

    def take_action(self):
        """Take an action using the trained model or fallback to random."""
        if self.model is None:
            return self._fallback.take_action()

        state = self.game_engine.get_state()

        # Build observation vector (same format as JaipurEnv)
        obs = self._build_observation(state)

        # Get action mask
        action_mask = self._get_action_mask(state)

        # Get action from model
        action, _ = self.model.predict(obs, deterministic=True)

        # If action is masked (invalid), choose a random valid one
        if action_mask[action] == 0:
            valid_actions = np.where(action_mask == 1)[0]
            if len(valid_actions) > 0:
                action = np.random.choice(valid_actions)
            else:
                # No valid actions - this shouldn't happen, fallback
                return self._fallback.take_action()

        # Execute the action
        success = self._execute_action(action, state)

        if not success:
            # Fallback to random player if action failed
            return self._fallback.take_action()

        return success

    def _build_observation(self, state):
        """Convert game state to normalized observation vector."""
        obs = []

        # My hand card counts (7 values, max ~12 cards)
        hand_counts = Counter(state['my_hand'])
        for card_type in self.CARD_TYPES:
            obs.append(hand_counts.get(card_type, 0) / 12.0)

        # Market card counts (7 values, max 5 total)
        market_counts = Counter(state['market'])
        for card_type in self.CARD_TYPES:
            obs.append(market_counts.get(card_type, 0) / 5.0)

        # Tokens remaining per good type (6 values, max 9)
        for good_type in self.GOOD_TYPES:
            tokens = state['tokens_left'].get(good_type, [])
            obs.append(len(tokens) / 9.0)

        # Bonus tokens remaining (3 values, max 7)
        for bonus_size in [3, 4, 5]:
            obs.append(state['bonus_num_left'].get(bonus_size, 0) / 7.0)

        # My total token value (normalized by max possible ~150)
        my_token_sum = sum(state['my_tokens'])
        obs.append(my_token_sum / 150.0)

        # Enemy goods count (max 7)
        obs.append(state['enemy_num_goods'] / 7.0)

        # Enemy camel count (max 11)
        obs.append(state['enemy_num_camels'] / 11.0)

        # Enemy total token value (normalized)
        enemy_token_sum = sum(state['enemy_tokens'])
        obs.append(enemy_token_sum / 150.0)

        # Deck size (max 40)
        obs.append(state['num_deck'] / 40.0)

        return np.array(obs, dtype=np.float32)

    def _get_action_mask(self, state):
        """Return a mask of valid actions."""
        my_hand = state['my_hand']
        market = state['market']

        my_goods = [x for x in my_hand if x != "camel"]
        market_goods = [x for x in market if x != "camel"]

        mask = np.zeros(13, dtype=np.int8)

        # Action 0: Take camels
        if "camel" in market:
            mask[0] = 1

        # Actions 1-5: Grab card at position 0-4
        if len(my_goods) < 7:
            for i in range(5):
                if i < len(market) and market[i] != "camel":
                    mask[1 + i] = 1

        # Actions 6-11: Sell type 0-5
        hand_counts = Counter(my_goods)
        for i, good_type in enumerate(self.GOOD_TYPES):
            count = hand_counts.get(good_type, 0)
            if count > 0:
                # Silver, gold, diamond require at least 2
                if good_type in ["silver", "gold", "diamond"]:
                    if count >= 2:
                        mask[6 + i] = 1
                else:
                    mask[6 + i] = 1

        # Action 12: Trade
        if len(my_hand) >= 2 and len(market_goods) >= 2:
            hand_types = set(my_hand)
            tradeable_market = [x for x in market_goods if x not in hand_types]
            if len(tradeable_market) >= 2:
                mask[12] = 1

        # Ensure at least one action is valid
        if mask.sum() == 0:
            mask[0] = 1

        return mask

    def _execute_action(self, action, state):
        """Execute the given action. Returns True if successful."""
        my_hand = state['my_hand']
        market = state['market']

        if action == 0:
            # Take camels
            return self.game_engine.do_action("c")

        elif 1 <= action <= 5:
            # Grab card at position (action - 1)
            grab_idx = action - 1
            if grab_idx < len(market):
                return self.game_engine.do_action("g", grab_idx=grab_idx)
            return False

        elif 6 <= action <= 11:
            # Sell all cards of type (action - 6)
            good_type = self.GOOD_TYPES[action - 6]
            sell_idx = [i for i, x in enumerate(my_hand) if x == good_type]
            if sell_idx:
                return self.game_engine.do_action("s", sell_idx=sell_idx)
            return False

        elif action == 12:
            # Trade - find a random valid trade
            trade_in, trade_out = self._find_valid_trade(state)
            if trade_in and trade_out:
                return self.game_engine.do_action("t", trade_in=trade_in, trade_out=trade_out)
            return False

        return False

    def _find_valid_trade(self, state):
        """Find a valid trade."""
        my_hand = state['my_hand']
        market = state['market']
        market_goods = [x for x in market if x != "camel"]
        my_goods = [x for x in my_hand if x != "camel"]

        for _ in range(10):
            max_trade = min(len(market_goods), len(my_hand))
            if max_trade < 2:
                return None, None

            num_trades = random.randint(2, max_trade)
            trade_out = random.sample(range(len(my_hand)), num_trades)
            trade_out_types = [my_hand[x] for x in trade_out]

            # Check if trading camels for goods would exceed hand limit
            camels_traded_out = trade_out_types.count("camel")
            new_goods_count = len(my_goods) + camels_traded_out
            if new_goods_count > 7:
                continue

            market_options = [x for x in market if x not in trade_out_types and x != "camel"]

            if len(market_options) >= num_trades:
                trade_in_types = random.sample(market_options, num_trades)
                trade_in = []
                for each_type, num_to_trade in Counter(trade_in_types).items():
                    indices = [i for i, x in enumerate(market) if x == each_type]
                    trade_in.extend(indices[:num_to_trade])
                return trade_in, trade_out

        return None, None
