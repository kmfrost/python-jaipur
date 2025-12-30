import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from collections import Counter
import sys
import os

# Add parent directory to path to import game modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from GameEngine import GameEngine
from RandomPlayer import RandomPlayer


class JaipurEnv(gym.Env):
    """
    Jaipur environment for reinforcement learning.

    The RL agent plays as Player 0 against a RandomPlayer opponent.

    Observation Space (28 dimensions):
        - My hand card counts per type (7 values: leather, spice, cloth, silver, gold, diamond, camel)
        - Market card counts per type (7 values)
        - Tokens remaining per good type (6 values, normalized)
        - Bonus tokens remaining (3 values for 3/4/5-card bonuses)
        - My total token value (1 value, normalized)
        - Enemy goods count (1 value)
        - Enemy camel count (1 value)
        - Enemy total token value (1 value, normalized)
        - Deck size (1 value, normalized)

    Action Space (13 discrete actions):
        - 0: Take all camels from market
        - 1-5: Grab card at market position 0-4
        - 6-11: Sell all cards of type 0-5 (leather, spice, cloth, silver, gold, diamond)
        - 12: Attempt a random valid trade
    """

    metadata = {"render_modes": ["human"]}

    CARD_TYPES = ["leather", "spice", "cloth", "silver", "gold", "diamond", "camel"]
    GOOD_TYPES = ["leather", "spice", "cloth", "silver", "gold", "diamond"]

    def __init__(self, render_mode=None, verbose=False):
        super().__init__()

        self.render_mode = render_mode
        self.verbose = verbose

        # 13 discrete actions
        self.action_space = spaces.Discrete(13)

        # Observation space: 28 continuous values normalized to [0, 1]
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(28,),
            dtype=np.float32
        )

        self.game_engine = None
        self.opponent = None
        self._suppress_prints = True

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        # Suppress game engine prints during training
        if self._suppress_prints:
            self._original_print = print
            import builtins
            builtins.print = lambda *args, **kwargs: None

        self.game_engine = GameEngine()
        self.opponent = RandomPlayer(self.game_engine)

        # Restore print for potential debugging
        if self._suppress_prints:
            import builtins
            builtins.print = self._original_print

        # RL agent is always player 0
        # If player 1 starts, let opponent play first
        if self._suppress_prints:
            import builtins
            builtins.print = lambda *args, **kwargs: None

        while self.game_engine.whos_turn == 1 and not self.game_engine.is_done():
            self.opponent.take_action()

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

        # Execute the RL agent's action
        success = self._execute_action(action)

        if not success:
            # Invalid action - small penalty and skip turn
            reward = -0.1

        # Check if game ended after our move
        if self.game_engine.is_done():
            terminated = True
            reward = self._calculate_final_reward()
        else:
            # Opponent's turn(s)
            while self.game_engine.whos_turn == 1 and not self.game_engine.is_done():
                self.opponent.take_action()

            # Check if game ended after opponent's move
            if self.game_engine.is_done():
                terminated = True
                reward = self._calculate_final_reward()

        if self._suppress_prints:
            import builtins
            builtins.print = self._original_print

        observation = self._get_observation()
        info = {"action_mask": self._get_action_mask()}

        return observation, reward, terminated, truncated, info

    def _get_observation(self):
        """Convert game state to normalized observation vector."""
        state = self.game_engine.get_state()

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

    def _get_action_mask(self):
        """Return a mask of valid actions."""
        state = self.game_engine.get_state()
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

        # Ensure at least one action is valid (fallback)
        if mask.sum() == 0:
            mask[0] = 1  # Default to camels action

        return mask

    def _execute_action(self, action):
        """Execute the given action. Returns True if successful."""
        state = self.game_engine.get_state()
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
        """Find a valid trade. Same logic as RandomPlayer."""
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
                continue  # This trade would exceed hand limit, try again

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
        # Temporarily restore print to get scores
        if self._suppress_prints:
            import builtins
            builtins.print = lambda *args, **kwargs: None

        scores, winner = self.game_engine.get_scores()

        if self._suppress_prints:
            import builtins
            builtins.print = self._original_print

        my_score = scores[0]
        opponent_score = scores[1]

        # Reward based on win/loss and score difference
        if winner == 0:
            # We won
            return 1.0 + (my_score - opponent_score) / 100.0
        elif winner == 1:
            # We lost
            return -1.0 + (my_score - opponent_score) / 100.0
        else:
            # Tie
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


# Register the environment
gym.register(
    id="Jaipur-v0",
    entry_point="JaipurEnv:JaipurEnv",
)
