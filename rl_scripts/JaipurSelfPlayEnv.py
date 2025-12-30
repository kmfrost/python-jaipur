"""
Self-play Jaipur environment for stronger RL training.
The agent plays against a copy of itself that gets updated periodically.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from collections import Counter
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from GameEngine import GameEngine
from RandomPlayer import RandomPlayer


class JaipurSelfPlayEnv(gym.Env):
    """
    Self-play Jaipur environment.

    Key differences from JaipurEnv:
    - Opponent is a model (self-play) instead of RandomPlayer
    - Supports setting/updating opponent model
    - Mixed opponent pool for diversity
    """

    metadata = {"render_modes": ["human"]}

    CARD_TYPES = ["leather", "spice", "cloth", "silver", "gold", "diamond", "camel"]
    GOOD_TYPES = ["leather", "spice", "cloth", "silver", "gold", "diamond"]

    def __init__(self, render_mode=None, opponent_model=None, random_opponent_prob=0.2):
        super().__init__()

        self.render_mode = render_mode
        self.opponent_model = opponent_model
        self.random_opponent_prob = random_opponent_prob  # Mix in random opponent for diversity

        self.action_space = spaces.Discrete(13)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(28,),
            dtype=np.float32
        )

        self.game_engine = None
        self._use_random_opponent = False
        self._random_opponent = None
        self._suppress_prints = True

    def set_opponent_model(self, model):
        """Update the opponent model (for self-play updates)."""
        self.opponent_model = model

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        if self._suppress_prints:
            import builtins
            self._original_print = builtins.print
            builtins.print = lambda *args, **kwargs: None

        self.game_engine = GameEngine()

        # Decide whether to use random opponent this episode (for diversity)
        self._use_random_opponent = (
            self.opponent_model is None or
            random.random() < self.random_opponent_prob
        )

        if self._use_random_opponent:
            self._random_opponent = RandomPlayer(self.game_engine)

        if self._suppress_prints:
            import builtins
            builtins.print = self._original_print

        # If opponent goes first, let them play
        if self._suppress_prints:
            import builtins
            builtins.print = lambda *args, **kwargs: None

        while self.game_engine.whos_turn == 1 and not self.game_engine.is_done():
            self._opponent_take_action()

        if self._suppress_prints:
            import builtins
            builtins.print = self._original_print

        observation = self._get_observation()
        info = {"action_mask": self._get_action_mask()}

        return observation, info

    def step(self, action):
        if self._suppress_prints:
            import builtins
            builtins.print = lambda *args, **kwargs: None

        reward = 0.0
        terminated = False
        truncated = False

        # Execute agent's action
        success = self._execute_action(action)

        if not success:
            reward = -0.1

        # Check if game ended
        if self.game_engine.is_done():
            terminated = True
            reward = self._calculate_final_reward()
        else:
            # Opponent's turn(s)
            while self.game_engine.whos_turn == 1 and not self.game_engine.is_done():
                self._opponent_take_action()

            if self.game_engine.is_done():
                terminated = True
                reward = self._calculate_final_reward()

        if self._suppress_prints:
            import builtins
            builtins.print = self._original_print

        observation = self._get_observation()
        info = {"action_mask": self._get_action_mask()}

        return observation, reward, terminated, truncated, info

    def _opponent_take_action(self):
        """Have the opponent take an action."""
        if self._use_random_opponent:
            self._random_opponent.take_action()
        else:
            # Self-play: use model to select action
            # Need to get observation from opponent's perspective
            obs = self._get_observation_for_opponent()
            action_mask = self._get_action_mask_for_opponent()

            action, _ = self.opponent_model.predict(obs, deterministic=False)

            # If action is masked, choose valid one
            if action_mask[action] == 0:
                valid_actions = np.where(action_mask == 1)[0]
                if len(valid_actions) > 0:
                    action = np.random.choice(valid_actions)

            success = self._execute_action_for_opponent(action)

            # Fallback to random if action fails
            if not success:
                if self._random_opponent is None:
                    self._random_opponent = RandomPlayer(self.game_engine)
                self._random_opponent.take_action()

    def _get_observation(self):
        """Get observation from player 0's perspective."""
        state = self.game_engine.get_state()
        return self._build_observation(state)

    def _get_observation_for_opponent(self):
        """Get observation from player 1's perspective."""
        # Temporarily switch perspective
        original_turn = self.game_engine.whos_turn
        self.game_engine.whos_turn = 1
        state = self.game_engine.get_state()
        self.game_engine.whos_turn = original_turn
        return self._build_observation(state)

    def _build_observation(self, state):
        """Convert game state to normalized observation vector."""
        obs = []

        hand_counts = Counter(state['my_hand'])
        for card_type in self.CARD_TYPES:
            obs.append(hand_counts.get(card_type, 0) / 12.0)

        market_counts = Counter(state['market'])
        for card_type in self.CARD_TYPES:
            obs.append(market_counts.get(card_type, 0) / 5.0)

        for good_type in self.GOOD_TYPES:
            tokens = state['tokens_left'].get(good_type, [])
            obs.append(len(tokens) / 9.0)

        for bonus_size in [3, 4, 5]:
            obs.append(state['bonus_num_left'].get(bonus_size, 0) / 7.0)

        my_token_sum = sum(state['my_tokens'])
        obs.append(my_token_sum / 150.0)

        obs.append(state['enemy_num_goods'] / 7.0)
        obs.append(state['enemy_num_camels'] / 11.0)

        enemy_token_sum = sum(state['enemy_tokens'])
        obs.append(enemy_token_sum / 150.0)

        obs.append(state['num_deck'] / 40.0)

        return np.array(obs, dtype=np.float32)

    def _get_action_mask(self):
        """Get action mask for player 0."""
        state = self.game_engine.get_state()
        return self._build_action_mask(state)

    def _get_action_mask_for_opponent(self):
        """Get action mask for player 1."""
        original_turn = self.game_engine.whos_turn
        self.game_engine.whos_turn = 1
        state = self.game_engine.get_state()
        self.game_engine.whos_turn = original_turn
        return self._build_action_mask(state)

    def _build_action_mask(self, state):
        """Build action mask from state."""
        my_hand = state['my_hand']
        market = state['market']

        my_goods = [x for x in my_hand if x != "camel"]
        market_goods = [x for x in market if x != "camel"]

        mask = np.zeros(13, dtype=np.int8)

        if "camel" in market:
            mask[0] = 1

        if len(my_goods) < 7:
            for i in range(5):
                if i < len(market) and market[i] != "camel":
                    mask[1 + i] = 1

        hand_counts = Counter(my_goods)
        for i, good_type in enumerate(self.GOOD_TYPES):
            count = hand_counts.get(good_type, 0)
            if count > 0:
                if good_type in ["silver", "gold", "diamond"]:
                    if count >= 2:
                        mask[6 + i] = 1
                else:
                    mask[6 + i] = 1

        if len(my_hand) >= 2 and len(market_goods) >= 2:
            hand_types = set(my_hand)
            tradeable_market = [x for x in market_goods if x not in hand_types]
            if len(tradeable_market) >= 2:
                mask[12] = 1

        if mask.sum() == 0:
            mask[0] = 1

        return mask

    def _execute_action(self, action):
        """Execute action for player 0."""
        state = self.game_engine.get_state()
        return self._do_action(action, state)

    def _execute_action_for_opponent(self, action):
        """Execute action for player 1."""
        original_turn = self.game_engine.whos_turn
        self.game_engine.whos_turn = 1
        state = self.game_engine.get_state()
        self.game_engine.whos_turn = original_turn
        return self._do_action(action, state)

    def _do_action(self, action, state):
        """Execute the given action."""
        my_hand = state['my_hand']
        market = state['market']

        if action == 0:
            return self.game_engine.do_action("c")

        elif 1 <= action <= 5:
            grab_idx = action - 1
            if grab_idx < len(market):
                return self.game_engine.do_action("g", grab_idx=grab_idx)
            return False

        elif 6 <= action <= 11:
            good_type = self.GOOD_TYPES[action - 6]
            sell_idx = [i for i, x in enumerate(my_hand) if x == good_type]
            if sell_idx:
                return self.game_engine.do_action("s", sell_idx=sell_idx)
            return False

        elif action == 12:
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

    def _calculate_final_reward(self):
        """Calculate reward at end of game."""
        if self._suppress_prints:
            import builtins
            builtins.print = lambda *args, **kwargs: None

        scores, winner = self.game_engine.get_scores()

        if self._suppress_prints:
            import builtins
            builtins.print = self._original_print

        my_score = scores[0]
        opponent_score = scores[1]

        # Stronger reward signal
        if winner == 0:
            return 1.0 + (my_score - opponent_score) / 50.0  # More weight on margin
        elif winner == 1:
            return -1.0 + (my_score - opponent_score) / 50.0
        else:
            return 0.0

    def render(self):
        if self.render_mode == "human":
            state = self.game_engine.get_state()
            print("\n" + "="*50)
            print(f"Market: {state['market']}")
            print(f"My hand: {state['my_hand']}")
            print(f"My tokens: {state['my_tokens']} (sum: {sum(state['my_tokens'])})")
            print(f"Enemy goods: {state['enemy_num_goods']}, camels: {state['enemy_num_camels']}")
            print(f"Enemy tokens: {state['enemy_tokens']} (sum: {sum(state['enemy_tokens'])})")
            print(f"Deck: {state['num_deck']} cards")
            print("="*50)

    def close(self):
        pass
