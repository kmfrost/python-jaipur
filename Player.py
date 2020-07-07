from ast import literal_eval
class Player:
    def __init__(self, game_engine):
        self.game_engine = game_engine
    
    def _pretty_print_dict(self, to_print):
        if to_print is None:
            print("    None")
        else:
            for key, value in to_print.items():
                print(f"    {key}: {value}")
        print("\n")        
    
    def take_action(self):
        success = False
        while not success:
            print(f"Last action:")
            self._pretty_print_dict(self.game_engine.get_last_action())
            print(f"Game state:")
            game_state = self.game_engine.get_state()
            self._pretty_print_dict(game_state)

            try:
                action_type = None
                while action_type not in ["c", "g", "s", "t"]:
                    print("Now selecting action type and options. Enter r at any point to restart.")
                    action_type = input("What type of action? (c)amels, (g)rab, (s)ell, or (t)rade: ")
                
                if action_type == "c":
                    success = self.game_engine.do_action(action_type)
                else:
                    print(f"Your hand is: {[f'{idx}: {x}' for idx, x in enumerate(game_state['my_hand'])]}")
                    print(f"The market is: {[f'{idx}: {x}' for idx, x in enumerate(game_state['market'])]}")
                if action_type == "g":          
                    grab_idx = int(input("Which market index would you like to grab? "))
                    if grab_idx != "r":
                        success = self.game_engine.do_action(action_type, grab_idx=grab_idx)
                elif action_type == "s":
                    sell_idx = input("Which indices would you like to sell (remember to only sell items of the same type)? Input as a list: ")         
                    if sell_idx != "r":
                        success = self.game_engine.do_action(action_type, sell_idx=literal_eval(sell_idx))
                elif action_type == "t":
                    trade_out = input("Which indices from your hand would you like to trade (input as list)? ")
                    trade_in = input("Which indices from the market would you like to trade for (input as list)? ")
                    if trade_out != "r" and trade_in != "r":
                        success = self.game_engine.do_action(action_type, trade_in=literal_eval(trade_in), trade_out=literal_eval(trade_out))
            except ValueError:
                print("Bad input, try again.")
