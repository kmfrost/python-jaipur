import random
import numpy as np
from collections import Counter

from Player import Player


class RandomPlayer(Player):
    """This player takes random (valid) moves. Used mostly for testing. And making yourself feel good about yourself.
    """
   
    def take_action(self):
        success = False
        while not success:
            game_state = self.game_engine.get_state()
            my_goods = [x for x in game_state['my_hand'] if x != "camel"]
            market_goods = [x for x in game_state['market'] if x != "camel"]            
            # try:
            valid_moves = ["c", "g", "s", "t"]
            # do some initial checks to remove invalid moves
            if "camel" not in game_state["market"]:
                valid_moves.remove("c")
            if len(my_goods) == 7:
                valid_moves.remove("g")
            if len(my_goods) == 0:
                valid_moves.remove("s")
            if len(game_state['my_hand']) < 2:
                valid_moves.remove("t")
                
            # Cannot sell silver/gold/diamond if you have less than 2
            disallowed_sells = []
            for each in['silver', 'gold', 'diamond']:
                if my_goods.count(each) < 2:
                    disallowed_sells.append(each)
                
            my_sellable_goods = [x for x in my_goods if x not in disallowed_sells]
            if len(my_sellable_goods) == 0 and "s" in valid_moves:
                valid_moves.remove("s")
                
            
            action_type = random.choice(valid_moves)
            if action_type == "c":
                success = self.game_engine.do_action(action_type)
            elif action_type == "g":          
                grab_type = random.choice(market_goods)
                success = self.game_engine.do_action(action_type, grab_idx=game_state['market'].index(grab_type))
            elif action_type == "s":
                # Choose a non-camel card and sell all of that type
                selected_type = random.choice(my_sellable_goods)
                
                sell_idx = [i for i, x in enumerate(my_goods) if x == selected_type]
    
                success = self.game_engine.do_action(action_type, sell_idx=sell_idx)
            elif action_type == "t":
                # operate by 3 strikes and you're out
                num_strikes = 0
                
                trade_in = []
                trade_out = []
                # must trade at least 2 cards, cannot trade more cards than are in the market or your hand
                valid = False
                while not valid:
                    num_trades = random.randint(2, min(len(game_state['market']), len(game_state['my_hand'])))
                    # pick num_trades cards from your own hand
                    trade_out = random.sample(range(len(game_state['my_hand'])), num_trades)
                    trade_out_types = [game_state['my_hand'][x] for x in trade_out]
                    market_options = [x for x in game_state['market'] if x not in trade_out_types and x != "camel"]                    
                    if len(market_options) >= len(trade_out):
                        # randomly sample from the valid trades
                        trade_in_types = random.sample(market_options, num_trades)
                        trade_in = []
                        # match those types up with indices in the market
                        for each_type, num_to_trade in Counter(trade_in_types).items():
                            indices = [i for i, x in enumerate(game_state['market']) if x == each_type]
                            trade_in.extend(indices[:num_to_trade])                       
                        valid = True
                        
                    # hacky fail-safe to ensure you don't get stuck in an infinite loop!
                    else:
                        num_strikes += 1
                    if num_strikes == 3:
                        break

                success = self.game_engine.do_action(action_type, trade_in=trade_in, trade_out=trade_out)
            # except:
            #     pass
