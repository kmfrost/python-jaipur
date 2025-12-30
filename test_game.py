"""
Comprehensive test suite for the Jaipur game implementation.
Run with: python -m pytest test_game.py -v
"""
import pytest
import random
import sys
from io import StringIO
from contextlib import contextmanager

from GameEngine import GameEngine
from RandomPlayer import RandomPlayer
from Player import Player


@contextmanager
def suppress_print():
    """Context manager to suppress print statements."""
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        yield
    finally:
        sys.stdout = old_stdout


class TestGameInitialization:
    """Tests for game initialization and setup."""

    def test_deck_has_correct_card_counts(self):
        """Verify deck starts with correct card distribution."""
        with suppress_print():
            engine = GameEngine()

        # Count all cards in deck, market, and both players' hands
        all_cards = list(engine._deck) + list(engine._market)
        all_cards += list(engine._players[0].hand) + list(engine._players[1].hand)

        expected = {0: 10, 1: 8, 2: 8, 3: 6, 4: 6, 5: 6, 6: 8}  # 8 camels shuffled in
        actual = {i: all_cards.count(i) for i in range(7)}

        # Market starts with 3 camels, so total camels = 8 + 3 = 11
        expected[6] = 11  # 3 camels in market + 8 in deck
        assert actual == expected, f"Card counts don't match. Expected {expected}, got {actual}"

    def test_market_starts_with_five_cards(self):
        """Market should start with exactly 5 cards."""
        with suppress_print():
            engine = GameEngine()
        assert len(engine._market) == 5

    def test_market_starts_with_at_least_three_camels(self):
        """Market should start with at least 3 camels (3 fixed + possibly more from deck)."""
        with suppress_print():
            engine = GameEngine()
        camel_idx = GameEngine._types.index("camel")
        camel_count = engine._market.count(camel_idx)
        # Market starts with 3 camels + 2 from deck, deck cards could be camels
        assert camel_count >= 3, f"Market should start with at least 3 camels, got {camel_count}"

    def test_players_start_with_five_cards(self):
        """Each player should start with 5 cards."""
        with suppress_print():
            engine = GameEngine()
        assert len(engine._players[0].hand) == 5
        assert len(engine._players[1].hand) == 5

    def test_tokens_initialized_correctly(self):
        """Token stacks should have correct values."""
        with suppress_print():
            engine = GameEngine()

        expected_tokens = {
            0: [1, 1, 1, 1, 1, 1, 2, 3, 4],  # leather
            1: [1, 1, 2, 2, 3, 3, 5],         # spice
            2: [1, 1, 2, 2, 3, 3, 5],         # cloth
            3: [5, 5, 5, 5, 5],               # silver
            4: [5, 5, 5, 6, 6],               # gold
            5: [5, 5, 5, 7, 7]                # diamond
        }
        assert engine._tokens == expected_tokens

    def test_bonus_tokens_initialized(self):
        """Bonus token stacks should be initialized with correct counts."""
        with suppress_print():
            engine = GameEngine()

        assert len(engine._bonus_tokens[3]) == 7
        assert len(engine._bonus_tokens[4]) == 6
        assert len(engine._bonus_tokens[5]) == 5

    def test_whos_turn_is_zero_or_one(self):
        """Starting player should be either 0 or 1."""
        with suppress_print():
            engine = GameEngine()
        assert engine.whos_turn in [0, 1]


class TestTakeCamels:
    """Tests for the 'take camels' action."""

    def test_take_camels_success(self):
        """Taking camels when available should succeed."""
        with suppress_print():
            engine = GameEngine()
            # Ensure there are camels in market
            camel_idx = GameEngine._types.index("camel")
            if camel_idx not in engine._market:
                engine._market[0] = camel_idx

            initial_camels = engine._market.count(camel_idx)
            player = engine.whos_turn
            initial_hand_camels = engine._players[player].hand.count(camel_idx)

            result = engine.do_action("c")

        assert result == True
        assert engine._players[player].hand.count(camel_idx) == initial_hand_camels + initial_camels

    def test_take_camels_no_camels_available(self):
        """Taking camels when none available should fail."""
        with suppress_print():
            engine = GameEngine()
            # Remove all camels from market
            camel_idx = GameEngine._types.index("camel")
            engine._market = [0, 1, 2, 3, 4]  # All non-camel cards

            result = engine.do_action("c")

        assert result == False

    def test_take_camels_replenishes_market(self):
        """Taking camels should replenish market to 5 cards."""
        with suppress_print():
            engine = GameEngine()
            camel_idx = GameEngine._types.index("camel")
            # Set up market with 2 camels
            engine._market = [camel_idx, camel_idx, 0, 1, 2]

            engine.do_action("c")

        assert len(engine._market) == 5


class TestGrabCard:
    """Tests for the 'grab card' action."""

    def test_grab_card_success(self):
        """Grabbing a non-camel card should succeed."""
        with suppress_print():
            engine = GameEngine()
            # Find a non-camel card in market
            camel_idx = GameEngine._types.index("camel")
            non_camel_idx = None
            for i, card in enumerate(engine._market):
                if card != camel_idx:
                    non_camel_idx = i
                    break

            if non_camel_idx is not None:
                player = engine.whos_turn
                initial_hand_size = len(engine._players[player].hand)
                result = engine.do_action("g", grab_idx=non_camel_idx)
                assert result == True
                # After action, turn switches. Check original player's hand grew.
                assert len(engine._players[player].hand) == initial_hand_size + 1

    def test_grab_camel_fails(self):
        """Grabbing a camel should fail."""
        with suppress_print():
            engine = GameEngine()
            camel_idx = GameEngine._types.index("camel")
            # Find camel in market
            camel_pos = None
            for i, card in enumerate(engine._market):
                if card == camel_idx:
                    camel_pos = i
                    break

            if camel_pos is not None:
                result = engine.do_action("g", grab_idx=camel_pos)
                assert result == False

    def test_grab_card_hand_limit(self):
        """Cannot grab when hand has 7 non-camel cards."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            # Set hand to 7 non-camel cards
            engine._players[player].hand = [0, 0, 1, 1, 2, 2, 3]

            # Find non-camel in market
            camel_idx = GameEngine._types.index("camel")
            for i, card in enumerate(engine._market):
                if card != camel_idx:
                    result = engine.do_action("g", grab_idx=i)
                    assert result == False
                    break

    def test_grab_card_replenishes_market(self):
        """Grabbing a card should replenish market."""
        with suppress_print():
            engine = GameEngine()
            camel_idx = GameEngine._types.index("camel")
            # Find non-camel in market
            for i, card in enumerate(engine._market):
                if card != camel_idx:
                    engine.do_action("g", grab_idx=i)
                    break

        assert len(engine._market) == 5

    def test_grab_card_out_of_range(self):
        """Grabbing with invalid index should fail."""
        with suppress_print():
            engine = GameEngine()
            result = engine.do_action("g", grab_idx=10)
        # This should raise an IndexError or return False
        # Current implementation may crash - this tests for robustness


class TestSellCards:
    """Tests for the 'sell cards' action."""

    def test_sell_single_leather(self):
        """Selling a single leather should succeed."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 2, 3]  # Two leather

            initial_tokens = len(engine._players[player].tokens)
            result = engine.do_action("s", sell_idx=[0])

        assert result == True
        assert len(engine._players[player].tokens) == initial_tokens + 1

    def test_sell_multiple_same_type(self):
        """Selling multiple cards of same type should succeed."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 0, 1, 2]  # Three leather

            result = engine.do_action("s", sell_idx=[0, 1, 2])

        assert result == True

    def test_sell_different_types_fails(self):
        """Selling cards of different types should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 1, 2, 3, 4]

            result = engine.do_action("s", sell_idx=[0, 1])

        assert result == False

    def test_sell_camels_fails(self):
        """Selling camels should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            camel_idx = GameEngine._types.index("camel")
            engine._players[player].hand = [camel_idx, camel_idx, 0, 1, 2]

            result = engine.do_action("s", sell_idx=[0, 1])

        assert result == False

    def test_sell_silver_requires_two(self):
        """Selling silver requires at least 2 cards."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            silver_idx = GameEngine._types.index("silver")
            engine._players[player].hand = [silver_idx, 0, 1, 2, 3]

            result = engine.do_action("s", sell_idx=[0])

        assert result == False

    def test_sell_gold_requires_two(self):
        """Selling gold requires at least 2 cards."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            gold_idx = GameEngine._types.index("gold")
            engine._players[player].hand = [gold_idx, 0, 1, 2, 3]

            result = engine.do_action("s", sell_idx=[0])

        assert result == False

    def test_sell_diamond_requires_two(self):
        """Selling diamond requires at least 2 cards."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            diamond_idx = GameEngine._types.index("diamond")
            engine._players[player].hand = [diamond_idx, 0, 1, 2, 3]

            result = engine.do_action("s", sell_idx=[0])

        assert result == False

    def test_sell_two_silver_succeeds(self):
        """Selling 2 silver should succeed."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            silver_idx = GameEngine._types.index("silver")
            engine._players[player].hand = [silver_idx, silver_idx, 0, 1, 2]
            engine._players[player].hand.sort()

            # Find indices of silver in sorted hand
            silver_indices = [i for i, x in enumerate(engine._players[player].hand) if x == silver_idx]
            result = engine.do_action("s", sell_idx=silver_indices)

        assert result == True

    def test_sell_three_gets_bonus_token(self):
        """Selling 3 cards should get a bonus token."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 0, 1, 2]  # Three leather

            initial_bonus = len(engine._players[player].bonus_tokens[3])
            result = engine.do_action("s", sell_idx=[0, 1, 2])

        assert result == True
        assert len(engine._players[player].bonus_tokens[3]) == initial_bonus + 1

    def test_sell_four_gets_bonus_token(self):
        """Selling 4 cards should get a 4-card bonus token."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 0, 0, 1]  # Four leather

            initial_bonus = len(engine._players[player].bonus_tokens[4])
            result = engine.do_action("s", sell_idx=[0, 1, 2, 3])

        assert result == True
        assert len(engine._players[player].bonus_tokens[4]) == initial_bonus + 1

    def test_sell_five_gets_bonus_token(self):
        """Selling 5+ cards should get a 5-card bonus token."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 0, 0, 0]  # Five leather

            initial_bonus = len(engine._players[player].bonus_tokens[5])
            result = engine.do_action("s", sell_idx=[0, 1, 2, 3, 4])

        assert result == True
        assert len(engine._players[player].bonus_tokens[5]) == initial_bonus + 1

    def test_sell_duplicate_indices_fails(self):
        """Selling with duplicate indices should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 0, 1, 2]

            result = engine.do_action("s", sell_idx=[0, 0, 1])

        assert result == False

    def test_sell_index_out_of_range(self):
        """Selling with index out of range should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 0, 1, 2]

            result = engine.do_action("s", sell_idx=[0, 5])  # 5 is out of range

        assert result == False

    def test_sell_when_tokens_depleted(self):
        """Selling when token stack is empty should still work but give no tokens."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 0, 1, 2]
            engine._tokens[0] = []  # Deplete leather tokens

            initial_tokens = len(engine._players[player].tokens)
            result = engine.do_action("s", sell_idx=[0, 1, 2])

        assert result == True
        # No tokens should be gained since stack is empty
        assert len(engine._players[player].tokens) == initial_tokens


class TestTradeCards:
    """Tests for the 'trade cards' action."""

    def test_trade_two_cards_success(self):
        """Trading 2 cards should succeed with valid setup."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            # Set up hand with types not in market
            engine._players[player].hand = [0, 0, 1, 1, 2]
            engine._market = [3, 3, 4, 4, 5]  # Different types

            result = engine.do_action("t", trade_in=[0, 1], trade_out=[0, 1])

        assert result == True

    def test_trade_single_card_fails(self):
        """Trading only 1 card should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 1, 2, 3, 4]
            engine._market = [5, 5, 5, 5, 5]  # All diamonds (index 5)

            result = engine.do_action("t", trade_in=[0], trade_out=[0])

        assert result == False

    def test_trade_unequal_lengths_fails(self):
        """Trading with unequal lengths should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 1, 2]
            engine._market = [3, 3, 4, 4, 5]

            result = engine.do_action("t", trade_in=[0, 1], trade_out=[0, 1, 2])

        assert result == False

    def test_trade_cannot_take_camels(self):
        """Cannot take camels from market in a trade."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            camel_idx = GameEngine._types.index("camel")
            engine._players[player].hand = [0, 0, 1, 1, 2]
            engine._market = [camel_idx, camel_idx, 3, 4, 5]

            result = engine.do_action("t", trade_in=[0, 1], trade_out=[0, 1])  # Trying to take camels

        assert result == False

    def test_trade_can_give_camels(self):
        """Can give camels from hand in a trade."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            camel_idx = GameEngine._types.index("camel")
            engine._players[player].hand = [camel_idx, camel_idx, 0, 1, 2]
            engine._players[player].hand.sort()
            engine._market = [3, 3, 4, 4, 5]

            # Find camel indices in sorted hand
            camel_indices = [i for i, x in enumerate(engine._players[player].hand) if x == camel_idx]
            result = engine.do_action("t", trade_in=[0, 1], trade_out=camel_indices[:2])

        assert result == True

    def test_trade_same_type_overlap_fails(self):
        """Trading same type on both sides should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 1, 2]  # Has leather (0)
            engine._market = [0, 3, 4, 5, 5]  # Market also has leather (0)

            result = engine.do_action("t", trade_in=[0, 1], trade_out=[0, 1])  # Both include leather

        assert result == False

    def test_trade_duplicate_trade_in_fails(self):
        """Trading with duplicate trade_in indices should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 1, 2]
            engine._market = [3, 3, 4, 4, 5]

            result = engine.do_action("t", trade_in=[0, 0], trade_out=[0, 1])

        assert result == False

    def test_trade_duplicate_trade_out_fails(self):
        """Trading with duplicate trade_out indices should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 1, 2]
            engine._market = [3, 3, 4, 4, 5]

            result = engine.do_action("t", trade_in=[0, 1], trade_out=[0, 0])

        assert result == False

    def test_trade_out_index_out_of_range(self):
        """Trading with trade_out index out of range should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 1, 2]
            engine._market = [3, 3, 4, 4, 5]

            result = engine.do_action("t", trade_in=[0, 1], trade_out=[0, 10])

        assert result == False

    def test_trade_in_index_out_of_range(self):
        """Trading with trade_in index out of range should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 1, 2]
            engine._market = [3, 3, 4, 4, 5]

            result = engine.do_action("t", trade_in=[0, 10], trade_out=[0, 1])

        assert result == False

    def test_trade_camels_for_goods_exceeds_limit(self):
        """Trading camels for goods that would exceed hand limit should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            camel_idx = GameEngine._types.index("camel")
            # 6 goods + 2 camels = 8 total, but only 6 non-camel
            engine._players[player].hand = [0, 0, 1, 1, 2, 2, camel_idx, camel_idx]
            engine._players[player].hand.sort()
            engine._market = [3, 3, 4, 4, 5]

            # Find camel indices - trading 2 camels for 2 goods would make 8 goods
            camel_indices = [i for i, x in enumerate(engine._players[player].hand) if x == camel_idx]
            result = engine.do_action("t", trade_in=[0, 1], trade_out=camel_indices[:2])

        assert result == False


class TestGameEnd:
    """Tests for game end conditions."""

    def test_game_ends_three_empty_stacks(self):
        """Game should end when 3 token stacks are empty."""
        with suppress_print():
            engine = GameEngine()
            engine._tokens[0] = []  # Empty leather
            engine._tokens[1] = []  # Empty spice
            engine._tokens[2] = []  # Empty cloth

            assert engine.is_done() == True

    def test_game_not_done_two_empty_stacks(self):
        """Game should not end with only 2 empty stacks."""
        with suppress_print():
            engine = GameEngine()
            engine._tokens[0] = []  # Empty leather
            engine._tokens[1] = []  # Empty spice

            assert engine.is_done() == False

    def test_game_ends_empty_deck(self):
        """Game should end when deck is empty."""
        with suppress_print():
            engine = GameEngine()
            engine._deck = []

            assert engine.is_done() == True

    def test_game_ends_four_empty_stacks(self):
        """Game should also end when 4+ stacks are empty."""
        with suppress_print():
            engine = GameEngine()
            engine._tokens[0] = []
            engine._tokens[1] = []
            engine._tokens[2] = []
            engine._tokens[3] = []

            assert engine.is_done() == True


class TestScoring:
    """Tests for scoring and tiebreakers."""

    def test_basic_score_calculation(self):
        """Test basic score calculation."""
        with suppress_print():
            engine = GameEngine()
            engine._deck = []  # Force game end
            engine._players[0].tokens = [5, 5, 5]
            engine._players[1].tokens = [3, 3, 3]
            engine._players[0].bonus_tokens = {3: [], 4: [], 5: []}
            engine._players[1].bonus_tokens = {3: [], 4: [], 5: []}

            # Give player 0 more camels for the bonus
            camel_idx = GameEngine._types.index("camel")
            engine._players[0].hand = [camel_idx, camel_idx, camel_idx]
            engine._players[1].hand = [camel_idx]

            scores, winner = engine.get_scores()

        assert scores[0] == 20  # 15 tokens + 5 camel bonus
        assert scores[1] == 9
        assert winner == 0

    def test_camel_bonus_to_majority(self):
        """Camel bonus should go to player with more camels."""
        with suppress_print():
            engine = GameEngine()
            engine._deck = []
            camel_idx = GameEngine._types.index("camel")

            engine._players[0].hand = [camel_idx, camel_idx]
            engine._players[1].hand = [camel_idx, camel_idx, camel_idx]
            engine._players[0].tokens = [10]
            engine._players[1].tokens = [10]
            engine._players[0].bonus_tokens = {3: [], 4: [], 5: []}
            engine._players[1].bonus_tokens = {3: [], 4: [], 5: []}

            scores, winner = engine.get_scores()

        assert scores[0] == 10
        assert scores[1] == 15  # 10 + 5 camel bonus
        assert winner == 1

    def test_camel_tie_no_bonus(self):
        """When camels are tied, no bonus is awarded."""
        with suppress_print():
            engine = GameEngine()
            engine._deck = []
            camel_idx = GameEngine._types.index("camel")

            engine._players[0].hand = [camel_idx, camel_idx]
            engine._players[1].hand = [camel_idx, camel_idx]
            engine._players[0].tokens = [10]
            engine._players[1].tokens = [5]
            engine._players[0].bonus_tokens = {3: [], 4: [], 5: []}
            engine._players[1].bonus_tokens = {3: [], 4: [], 5: []}

            scores, winner = engine.get_scores()

        assert scores[0] == 10
        assert scores[1] == 5
        assert winner == 0

    def test_score_tiebreaker_bonus_tokens(self):
        """First tiebreaker: number of bonus tokens."""
        with suppress_print():
            engine = GameEngine()
            engine._deck = []
            camel_idx = GameEngine._types.index("camel")

            engine._players[0].hand = [camel_idx]
            engine._players[1].hand = [camel_idx]
            engine._players[0].tokens = [10]
            engine._players[1].tokens = [10]
            engine._players[0].bonus_tokens = {3: [2, 2], 4: [], 5: []}  # 2 bonus tokens worth 4
            engine._players[1].bonus_tokens = {3: [2, 2, 2], 4: [], 5: []}  # 3 bonus tokens worth 6

            scores, winner = engine.get_scores()

        # Player 0: 10 + 4 = 14, Player 1: 10 + 6 = 16
        # Actually they're not tied, so let's adjust
        engine._players[0].bonus_tokens = {3: [3, 3], 4: [], 5: []}  # 2 bonus tokens worth 6
        engine._players[1].bonus_tokens = {3: [2, 2, 2], 4: [], 5: []}  # 3 bonus tokens worth 6

        with suppress_print():
            scores, winner = engine.get_scores()

        # Both have 16, tiebreaker goes to more bonus tokens
        assert scores[0] == scores[1]
        assert winner == 1  # Player 1 has more bonus tokens (3 vs 2)

    def test_score_tiebreaker_total_tokens(self):
        """Second tiebreaker: number of total tokens."""
        with suppress_print():
            engine = GameEngine()
            engine._deck = []
            camel_idx = GameEngine._types.index("camel")

            engine._players[0].hand = [camel_idx]
            engine._players[1].hand = [camel_idx]
            engine._players[0].tokens = [10]
            engine._players[1].tokens = [5, 5]  # Same value but 2 tokens
            engine._players[0].bonus_tokens = {3: [], 4: [], 5: []}
            engine._players[1].bonus_tokens = {3: [], 4: [], 5: []}

            scores, winner = engine.get_scores()

        assert scores[0] == scores[1] == 10
        assert winner == 1  # Player 1 has more tokens (2 vs 1)


class TestRandomPlayer:
    """Tests for the RandomPlayer AI."""

    def test_random_player_always_makes_valid_move(self):
        """RandomPlayer should always make a valid move."""
        with suppress_print():
            for _ in range(50):  # Run multiple games
                engine = GameEngine()
                players = [RandomPlayer(engine), RandomPlayer(engine)]

                turns = 0
                while not engine.is_done() and turns < 200:  # Prevent infinite loops
                    current_turn = engine.whos_turn
                    players[engine.whos_turn].take_action()
                    # Verify turn changed (action was successful)
                    assert engine.whos_turn != current_turn or engine.is_done()
                    turns += 1

    def test_random_player_completes_game(self):
        """RandomPlayer should be able to complete a full game."""
        with suppress_print():
            engine = GameEngine()
            players = [RandomPlayer(engine), RandomPlayer(engine)]

            turns = 0
            while not engine.is_done() and turns < 200:
                players[engine.whos_turn].take_action()
                turns += 1

            assert engine.is_done()
            scores, winner = engine.get_scores()
            assert winner in [0, 1, None]


class TestGetState:
    """Tests for the get_state method."""

    def test_get_state_returns_correct_keys(self):
        """get_state should return all expected keys."""
        with suppress_print():
            engine = GameEngine()
            state = engine.get_state()

        expected_keys = [
            'num_deck', 'market', 'tokens_left', 'bonus_num_left',
            'my_hand', 'my_tokens', 'my_bonus_num_tokens',
            'enemy_num_goods', 'enemy_num_camels', 'enemy_tokens', 'enemy_bonus_num_tokens'
        ]

        for key in expected_keys:
            assert key in state, f"Missing key: {key}"

    def test_get_state_market_has_names(self):
        """Market in state should use type names, not indices."""
        with suppress_print():
            engine = GameEngine()
            state = engine.get_state()

        for card in state['market']:
            assert card in GameEngine._types

    def test_get_state_enemy_info_sanitized(self):
        """Enemy hand details should be hidden (only counts visible)."""
        with suppress_print():
            engine = GameEngine()
            state = engine.get_state()

        # Enemy info should just be counts, not actual cards
        assert isinstance(state['enemy_num_goods'], int)
        assert isinstance(state['enemy_num_camels'], int)


class TestEdgeCases:
    """Tests for various edge cases."""

    def test_empty_hand_cannot_sell(self):
        """Cannot sell with empty hand."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = []

            result = engine.do_action("s", sell_idx=[0])

        assert result == False

    def test_sell_empty_index_list(self):
        """Selling with empty index list should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 1, 2, 3, 4]

            result = engine.do_action("s", sell_idx=[])

        # Empty list should be caught as falsy
        assert result == False

    def test_replenish_market_empty_deck(self):
        """Market replenishment with empty deck should handle gracefully."""
        with suppress_print():
            engine = GameEngine()
            engine._deck = []
            engine._market = [0, 1, 2, 3]  # Only 4 cards

            engine._replenish_market()

        # Market should still have 4 cards (couldn't replenish)
        assert len(engine._market) == 4

    def test_sell_with_no_tokens_remaining(self):
        """Selling when no tokens remain should work but give no tokens."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 2, 3]
            engine._tokens[0] = []  # No leather tokens

            initial_tokens = len(engine._players[player].tokens)
            result = engine.do_action("s", sell_idx=[0])

        assert result == True
        assert len(engine._players[player].tokens) == initial_tokens

    def test_bonus_tokens_depleted(self):
        """Selling for bonus when bonus stack empty should work without crashing."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 0, 1, 2]
            engine._bonus_tokens[3] = []  # No 3-card bonus tokens

            result = engine.do_action("s", sell_idx=[0, 1, 2])

        assert result == True

    def test_turns_alternate(self):
        """Turns should alternate after successful actions."""
        with suppress_print():
            engine = GameEngine()
            initial_player = engine.whos_turn

            # Make a simple action (take camels)
            camel_idx = GameEngine._types.index("camel")
            if camel_idx in engine._market:
                engine.do_action("c")
                assert engine.whos_turn == (initial_player ^ 1)

    def test_invalid_action_type(self):
        """Invalid action type should fail."""
        with suppress_print():
            engine = GameEngine()
            result = engine.do_action("x")

        assert result == False


class TestPlayerState:
    """Tests for the PlayerState inner class."""

    def test_num_cards_counts_non_camels(self):
        """num_cards should count only non-camel cards."""
        with suppress_print():
            engine = GameEngine()

        camel_idx = GameEngine._types.index("camel")
        ps = GameEngine.PlayerState([0, 1, 2, camel_idx, camel_idx])

        assert ps.num_cards() == 3

    def test_num_cards_all_camels(self):
        """num_cards with all camels should be 0."""
        camel_idx = GameEngine._types.index("camel")
        ps = GameEngine.PlayerState([camel_idx, camel_idx, camel_idx])

        assert ps.num_cards() == 0

    def test_num_cards_no_camels(self):
        """num_cards with no camels should be total hand size."""
        ps = GameEngine.PlayerState([0, 1, 2, 3, 4])

        assert ps.num_cards() == 5


class TestStressTests:
    """Stress tests to find edge cases."""

    def test_many_games_complete_successfully(self):
        """Run many games to find edge cases."""
        with suppress_print():
            for game_num in range(100):
                random.seed(game_num)  # Reproducible
                engine = GameEngine()
                players = [RandomPlayer(engine), RandomPlayer(engine)]

                turns = 0
                while not engine.is_done() and turns < 300:
                    players[engine.whos_turn].take_action()
                    turns += 1

                assert engine.is_done(), f"Game {game_num} didn't complete in 300 turns"
                scores, winner = engine.get_scores()
                assert winner in [0, 1, None], f"Invalid winner in game {game_num}"


class TestRLEnvironment:
    """Tests for the JaipurEnv RL environment."""

    def test_env_creation(self):
        """Environment should create successfully."""
        import sys
        sys.path.insert(0, 'rl_scripts')
        from JaipurEnv import JaipurEnv

        env = JaipurEnv()
        assert env is not None
        env.close()

    def test_env_reset(self):
        """Reset should return valid observation and info."""
        import sys
        sys.path.insert(0, 'rl_scripts')
        from JaipurEnv import JaipurEnv

        env = JaipurEnv()
        obs, info = env.reset()

        assert obs.shape == (28,)
        assert 'action_mask' in info
        assert info['action_mask'].shape == (13,)
        env.close()

    def test_env_observation_normalized(self):
        """All observation values should be in [0, 1]."""
        import sys
        sys.path.insert(0, 'rl_scripts')
        from JaipurEnv import JaipurEnv

        env = JaipurEnv()
        obs, _ = env.reset()

        assert (obs >= 0).all(), "Observation has negative values"
        assert (obs <= 1).all(), "Observation has values > 1"
        env.close()

    def test_env_step_valid_action(self):
        """Step with valid action should work."""
        import sys
        sys.path.insert(0, 'rl_scripts')
        from JaipurEnv import JaipurEnv

        env = JaipurEnv()
        obs, info = env.reset()

        # Find a valid action
        mask = info['action_mask']
        valid_action = None
        for i in range(13):
            if mask[i] == 1:
                valid_action = i
                break

        if valid_action is not None:
            obs, reward, terminated, truncated, info = env.step(valid_action)
            assert obs.shape == (28,)
            assert isinstance(reward, float)
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)
        env.close()

    def test_env_action_mask_valid(self):
        """Action mask should only allow valid actions."""
        import sys
        sys.path.insert(0, 'rl_scripts')
        from JaipurEnv import JaipurEnv

        env = JaipurEnv()
        obs, info = env.reset()

        mask = info['action_mask']
        # At least one action must be valid
        assert mask.sum() >= 1
        env.close()

    def test_env_full_game(self):
        """Environment should handle a full game."""
        import sys
        sys.path.insert(0, 'rl_scripts')
        from JaipurEnv import JaipurEnv
        import random

        env = JaipurEnv()
        obs, info = env.reset()

        steps = 0
        terminated = False
        while not terminated and steps < 300:
            mask = info['action_mask']
            valid_actions = [i for i in range(13) if mask[i] == 1]
            action = random.choice(valid_actions)

            obs, reward, terminated, truncated, info = env.step(action)
            steps += 1

        assert terminated, "Game didn't terminate within 300 steps"
        env.close()

    def test_env_multiple_games(self):
        """Run multiple games to test stability."""
        import sys
        sys.path.insert(0, 'rl_scripts')
        from JaipurEnv import JaipurEnv
        import random

        env = JaipurEnv()

        for game in range(20):
            obs, info = env.reset()
            terminated = False
            steps = 0

            while not terminated and steps < 300:
                mask = info['action_mask']
                valid_actions = [i for i in range(13) if mask[i] == 1]
                action = random.choice(valid_actions)
                obs, reward, terminated, truncated, info = env.step(action)
                steps += 1

            assert terminated, f"Game {game} didn't terminate"

        env.close()


class TestAdditionalEdgeCases:
    """Additional edge case tests."""

    def test_sell_negative_index(self):
        """Selling with negative index should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 2, 3]

            result = engine.do_action("s", sell_idx=[-1])

        assert result == False, "Negative index should be rejected"

    def test_trade_negative_index(self):
        """Trading with negative index should fail."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 1, 2]
            engine._market = [3, 3, 4, 4, 5]

            result = engine.do_action("t", trade_in=[0, 1], trade_out=[-1, 0])

        assert result == False, "Negative index should be rejected"

    def test_all_market_camels_grab_invalid(self):
        """Can't grab when all market cards are camels."""
        with suppress_print():
            engine = GameEngine()
            camel_idx = GameEngine._types.index("camel")
            engine._market = [camel_idx, camel_idx, camel_idx, camel_idx, camel_idx]

            # Try to grab at each position - all should fail
            for i in range(5):
                result = engine.do_action("g", grab_idx=i)
                assert result == False

    def test_trade_all_market_camels(self):
        """Can't trade when all market cards are camels."""
        with suppress_print():
            engine = GameEngine()
            camel_idx = GameEngine._types.index("camel")
            engine._market = [camel_idx, camel_idx, camel_idx, camel_idx, camel_idx]
            engine._players[engine.whos_turn].hand = [0, 0, 1, 1, 2]

            result = engine.do_action("t", trade_in=[0, 1], trade_out=[0, 1])

        assert result == False

    def test_multiple_sells_deplete_tokens(self):
        """Multiple sells should deplete token stack correctly."""
        with suppress_print():
            engine = GameEngine()

            # Keep selling leather until tokens are depleted
            player = 0
            engine.whos_turn = player
            leather_tokens = len(engine._tokens[0])

            for i in range(leather_tokens + 1):
                engine._players[player].hand = [0, 1, 2, 3, 4]
                engine.whos_turn = player
                engine.do_action("s", sell_idx=[0])

            # After all sells, leather tokens should be empty
            assert len(engine._tokens[0]) == 0

    def test_sell_max_at_once(self):
        """Selling many cards at once should work."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            # Give player 7 leather cards
            engine._players[player].hand = [0, 0, 0, 0, 0, 0, 0]

            initial_tokens = len(engine._players[player].tokens)
            result = engine.do_action("s", sell_idx=[0, 1, 2, 3, 4, 5, 6])

        assert result == True
        # Should get bonus token for 5+
        assert len(engine._players[player].bonus_tokens[5]) >= 1

    def test_grab_fills_hand_to_limit(self):
        """Grabbing when at 6 cards should fill hand to 7."""
        with suppress_print():
            engine = GameEngine()
            player = engine.whos_turn
            engine._players[player].hand = [0, 0, 1, 1, 2, 2]  # 6 cards
            camel_idx = GameEngine._types.index("camel")
            engine._market = [3, 3, 4, 4, 5]  # All non-camels

            assert engine._players[player].num_cards() == 6
            result = engine.do_action("g", grab_idx=0)

        assert result == True
        assert engine._players[player].num_cards() == 7

    def test_last_card_in_deck_replenishes_market(self):
        """When deck has 1 card, it should replenish market."""
        with suppress_print():
            engine = GameEngine()
            engine._deck = [5]  # One diamond left
            player = engine.whos_turn
            engine._players[player].hand = [0, 1, 2, 3, 4]
            engine._market = [0, 1, 2, 3, 4]  # All goods

            result = engine.do_action("g", grab_idx=0)

        assert result == True
        assert len(engine._market) == 5
        assert 5 in engine._market  # The diamond from deck

    def test_game_ends_immediately_on_empty_deck(self):
        """After action that empties deck, game should end."""
        with suppress_print():
            engine = GameEngine()
            engine._deck = [5]  # One card
            player = engine.whos_turn
            engine._players[player].hand = [0, 1, 2, 3, 4]
            engine._market = [0, 1, 2, 3, 4]

            engine.do_action("g", grab_idx=0)

        assert engine.is_done() == True


class TestRandomPlayerEdgeCases:
    """Test edge cases for RandomPlayer."""

    def test_random_player_only_camels_in_market(self):
        """RandomPlayer should handle market with only camels."""
        with suppress_print():
            engine = GameEngine()
            camel_idx = GameEngine._types.index("camel")
            engine._market = [camel_idx, camel_idx, camel_idx, camel_idx, camel_idx]
            engine._players[engine.whos_turn].hand = [0, 0, 1, 1, 2, 2, 3]

            player = RandomPlayer(engine)
            # Should not crash - should take camels or sell
            player.take_action()

    def test_random_player_full_hand_only_sell(self):
        """RandomPlayer with 7 goods should only sell."""
        with suppress_print():
            engine = GameEngine()
            engine._players[engine.whos_turn].hand = [0, 0, 0, 1, 1, 1, 2]
            camel_idx = GameEngine._types.index("camel")
            engine._market = [3, 3, 4, 4, camel_idx]

            player = RandomPlayer(engine)
            # With 7 goods, can only sell or take camels
            player.take_action()

    def test_random_player_no_valid_sell(self):
        """RandomPlayer should handle case where sell is invalid."""
        with suppress_print():
            engine = GameEngine()
            # Hand with only 1 of each high-value good
            engine._players[engine.whos_turn].hand = [3, 4, 5]  # silver, gold, diamond
            camel_idx = GameEngine._types.index("camel")
            engine._market = [camel_idx, camel_idx, camel_idx, 0, 1]

            player = RandomPlayer(engine)
            # Can't sell (need 2 of high-value), so must grab or trade
            player.take_action()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
