import random
import numpy as np
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
            valid_moves = ["c", "g", "s", "t'"]
            # do some initial checks to remove invalid moves
            if "camel" not in game_state["market"]:
                valid_moves.remove("c")
            if len(my_goods) == 7:
                valid_moves.remove("g")
            if len(my_goods) == 0:
                valid_moves.remove("s")
                valid_moves.remove("t")
                
            # Cannot sell silver/gold/diamond if you have less than 2
            disallowed_sells = []
            for each in['silver', 'gold', 'diamond']:
                if my_goods.count(each) < 2:
                    disallowed_sells.append(each)
                
            my_sellable_goods = [x for x in my_goods if x not in disallowed_sells]
            if len(my_sellable_goods) == 0:
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
                temp_out = game_state['my_hand']
                temp_market = market_goods
                trade_in = []
                trade_out = []
                for num_trades in random.randrange(min(len(game_state['market']), len(game_state['my_hand']))):
                    try:
                        temp_trade_out = random.randrange(len(temp_out))
                        temp_trade_in = random.choice([i for i, x in enumerate(temp_market) if x != temp_out[temp_trade_out]])
                        trade_out.append(temp_out.pop(temp_trade_out))
                        trade_in.append(temp_market.pop(temp_trade_in))
                    except IndexError:
                        # if you pick something that doesn't have a valid trade, move on
                        pass
                
                success = self.game_engine.do_action(action_type, trade_in=trade_in, trade_out=trade_out)
            # except:
            #     pass
