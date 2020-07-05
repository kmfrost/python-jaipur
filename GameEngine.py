import numpy as np
import random
class GameEngine:
    def __init__(self):
        self._tokens = None
        self._bonus_tokens = None
        self._deck = None
        self._market = None
        self._players = None
        self._types = ["leather", "spice", "cloth", "silver", "gold", "diamonds", "camels"]
        self.whos_turn = None
        
        self._reset()

    def _reset(self):
        self._tokens = {
            0: [1, 1, 1, 1, 1, 1, 2, 3, 4],  # leather
            1: [1, 1, 2, 2, 3 ,3, 5],  # spice
            2: [1, 1, 2, 2, 3, 3, 5],  # cloth
            3: [5, 5, 5, 5, 5],  # silver
            4: [5, 5, 5, 6, 6],  # gold
            5: [5, 5, 5, 7, 7]  # diamonds
        }
    
        self._bonus_tokens = {
            3: [1, 1, 2, 2, 2, 3, 3],
            4: [4, 4, 5, 5, 6, 6],
            5: [8, 8, 9, 10, 10]
        }
        for each in self._bonus_tokens:
            random.shuffle(self._bonus_tokens[each])

        # There are 11 camels in the deck, but only shuffle 8 into the deck
        cards_per_type = {0: 10, 1: 8, 2: 8, 3: 6, 4: 6, 5: 6, 6: 8}
        self._deck = []
        for key, value in cards_per_type.items(): 
            self._deck.extend([key] * value)
        random.shuffle(self._deck)
        
        # Create the market (cards in the middle) and deal out each player's hand
        self._market = [self._types.index("camels")]*3 + [self._deck.pop()] + [self._deck.pop()]
        self._players = [self.PlayerState([self._deck.pop() for _ in range(5)]), self.PlayerState([self._deck.pop() for _ in range(5)])]
        
        self.whos_turn = random.choice([0, 1])
        print(f"Player {self.whos_turn + 1} goes first!")

        
    def is_done(self):
        # Mark the number of empty stacks 
        empty_stacks = [1 for l in self._tokens.values() if not l]

        # The game is over if there are at least 3 empty token stacks
        return sum(empty_stacks) >= 3
        
    def get_state(self):
        pass
        
    def get_last_action(self):
        pass
    
    def do_action(self, top, sellIdx=None, grabIdx=None, tradeIn=None, tradeOut=None):
        if top == "c":
            # Selcts the "take camels" action
            success = self._do_take_camels()
        elif top == "s":
            # Selects the "sell" action
            if not sellIdx:
                # Need the sell index value to complete the sell action
                return False
            success = self._do_sell_cards(sellIdx)
        elif top == "g":
            # Selects the "grab" action
            if not grabIdx:
                # Need the grab index value to complete the grab action
                return False
            success = self._do_grab_card(grabIdx)
        elif top == "t":
            if not tradeIn or not tradeOut:
                # Need the trade in indices and trade out indices to complete the trade action
                return False
            success = self._do_trade_cards(tradeIn, tradeOut)
        else: 
            print(f"Top-level action {top} not recognized! Please choose from: c, s, g, t.")
            return False      
        
        if success:
            # Flip whos turn it is
            self.whos_turn = self.whos_turn ^ 1
        return success
    
    def _do_take_camels(self):
        camel_idx = self._types.index("camels")
        
        # Find the current market indices where there are camels
        market_camels = np.where(np.array(self._market) == camel_idx)[0]
        
        # Validate that there are camels available to take
        if len(market_camels) == 0:
            print("No camels are available to take from the market.")
            return False
        
        # Add the camels to the player's hand and replenish the market from the deck
        for _ in market_camels:
            self._players[self.whos_turn].hand.append(camel_idx)
            try:
                self._market.append(self._deck.pop())
            except IndexError:
                print("Deck is empty and cannot replenish the market - the game is over.")

        # Then delete the original camels from the market
        self._market = [v for i, v in enumerate(self._market) if i not in market_camels]
                
        # Sort the player's hand
        self._players[self.whos_turn].hand.sort()
        
        # Everything went well, print the result and return true
        print(f"Player {self.whos_turn + 1} took {len(market_camels)} camels.")
        return True
    
    def _do_sell_cards(self, sellIdx):
        pass
    
    def _do_grab_card(self, grabIdx):
        pass
    
    def _do_trade_cards(self, tradeIn, tradeOut):
        pass
    

    class PlayerState():
        def __init__(self, init_hand):
            self.hand = init_hand
            self.hand.sort()

            self.token_total = []
            self.bonus_tokens = []
