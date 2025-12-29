import random
from collections import Counter

from Player import Player


class RandomPlayer(Player):
    """This player takes random (valid) moves. Used mostly for testing. And making yourself feel good about yourself.
    """

    def take_action(self):
        success = False
        while not success:
            game_state = self.game_engine.get_state()
            my_hand = game_state['my_hand']
            my_goods = [x for x in my_hand if x != "camel"]
            market_goods = [x for x in game_state['market'] if x != "camel"]

            valid_moves = ["c", "g", "s", "t"]

            # Check if taking camels is valid
            if "camel" not in game_state["market"]:
                valid_moves.remove("c")

            # Check if grabbing is valid (hand limit is 7 non-camel cards, and market must have non-camel goods)
            if len(my_goods) == 7 or len(market_goods) == 0:
                valid_moves.remove("g")

            # Check if selling is valid
            if len(my_goods) == 0:
                valid_moves.remove("s")
            else:
                # Cannot sell silver/gold/diamond if you have less than 2
                disallowed_sells = []
                for each in ['silver', 'gold', 'diamond']:
                    if my_goods.count(each) < 2:
                        disallowed_sells.append(each)
                my_sellable_goods = [x for x in my_goods if x not in disallowed_sells]
                if len(my_sellable_goods) == 0:
                    valid_moves.remove("s")

            # Check if trading is valid
            # Need at least 2 cards in hand AND at least 2 market goods that don't overlap with hand types
            if len(my_hand) < 2:
                valid_moves.remove("t")
            elif "t" in valid_moves:
                # Check if any valid trade is possible
                hand_types = set(my_hand)
                tradeable_market = [x for x in market_goods if x not in hand_types]
                if len(tradeable_market) < 2 or len(market_goods) < 2:
                    valid_moves.remove("t")

            action_type = random.choice(valid_moves)

            if action_type == "c":
                success = self.game_engine.do_action(action_type)

            elif action_type == "g":
                grab_type = random.choice(market_goods)
                success = self.game_engine.do_action(action_type, grab_idx=game_state['market'].index(grab_type))

            elif action_type == "s":
                # Choose a non-camel card and sell all of that type
                selected_type = random.choice(my_sellable_goods)
                # Get indices from the full hand (not just my_goods)
                sell_idx = [i for i, x in enumerate(my_hand) if x == selected_type]
                success = self.game_engine.do_action(action_type, sell_idx=sell_idx)

            elif action_type == "t":
                # Find a valid trade
                trade_in, trade_out = self._find_valid_trade(game_state)
                if trade_in and trade_out:
                    success = self.game_engine.do_action(action_type, trade_in=trade_in, trade_out=trade_out)
                # If no valid trade found, loop will retry with different action

    def _find_valid_trade(self, game_state):
        """Find a valid trade configuration. Returns (trade_in, trade_out) or (None, None) if no valid trade."""
        my_hand = game_state['my_hand']
        market = game_state['market']
        market_goods = [x for x in market if x != "camel"]

        # Try up to 10 times to find a valid trade
        for _ in range(10):
            # Determine max possible trade size
            max_trade = min(len(market_goods), len(my_hand))
            if max_trade < 2:
                return None, None

            num_trades = random.randint(2, max_trade)

            # Pick cards from hand to trade out
            trade_out = random.sample(range(len(my_hand)), num_trades)
            trade_out_types = [my_hand[x] for x in trade_out]

            # Find market cards that don't overlap with trade_out types and aren't camels
            market_options = [x for x in market if x not in trade_out_types and x != "camel"]

            if len(market_options) >= num_trades:
                # Sample the types we want from market
                trade_in_types = random.sample(market_options, num_trades)

                # Match types to market indices
                trade_in = []
                for each_type, num_to_trade in Counter(trade_in_types).items():
                    indices = [i for i, x in enumerate(market) if x == each_type]
                    trade_in.extend(indices[:num_to_trade])

                return trade_in, trade_out

        return None, None
