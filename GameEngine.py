import numpy as np
import random
class GameEngine:
    _types = ["leather", "spice", "cloth", "silver", "gold", "diamond", "camels"]

    def __init__(self):
        self._tokens = None
        self._bonus_tokens = None
        self._deck = None
        self._market = None
        self._players = None
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
    
    def do_action(self, top, sell_idx=None, grab_idx=None, trade_in=None, trade_out=None):
        if top == "c":
            # Selcts the "take camels" action
            success = self._do_take_camels()
        elif top == "s":
            # Selects the "sell" action
            if not sell_idx:
                # Need the sell index value to complete the sell action
                return False
            success = self._do_sell_cards(sell_idx)
        elif top == "g":
            # Selects the "grab" action
            if grab_idx is None:
                # Need the grab index value to complete the grab action
                return False
            success = self._do_grab_card(grab_idx)
        elif top == "t":
            if not trade_in or not trade_out:
                # Need the trade in indices and trade out indices to complete the trade action
                return False
            success = self._do_trade_cards(trade_in, trade_out)
        else: 
            print(f"Top-level action {top} not recognized! Please choose from: c, s, g, t.")
            return False      
        
        if success:
            # Flip whos turn it is
            self.whos_turn = self.whos_turn ^ 1
            print(f"It is now Player {self.whos_turn + 1}'s turn.")
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
            self._replenish_market()        

        # Then delete the original camels from the market
        self._market = [v for i, v in enumerate(self._market) if i not in market_camels]
                
        # Sort the player's hand
        self._players[self.whos_turn].hand.sort()
        
        # Everything went well, print the result and return true
        print(f"Player {self.whos_turn + 1} took {len(market_camels)} camels.")
        return True
    
    def _do_sell_cards(self, sell_idx):
        # Already checked for empty list / None in do_action
        # Make sure all indices are in the hand
        if max(sell_idx) > len(self._players[self.whos_turn].hand):
            print(f"Index out of range ({max(sell_idx)})! Only {len(self._players[self.whos_turn].hand)} cards in hand!")
            return False
        # Check for duplicates
        if len(sell_idx) != len(set(sell_idx)):
            print(f"Duplicate indices in sell_idx list! sell_idx = {sell_idx}")
            return False
        # Make sure every item listed is the same
        selling_type = self._players[self.whos_turn].hand[sell_idx[0]]
        for idx in sell_idx:
            if self._players[self.whos_turn].hand[idx] != selling_type:
                print("All items must be the same type!")
                return False
        # Make sure type isn't a camel
        if selling_type == self._types.index("camels"):
            print("You can't sell camels, you monster!")
            return False
        
        # Do the action
        for _ in sell_idx:
            # Remove from hand
            self._players[self.whos_turn].hand.remove(selling_type)

            # Get the goods tokens
            if self._tokens[selling_type]: # make sure it's not empty
                self._players[self.whos_turn].tokens.append(self._tokens[selling_type].pop())
            
        # Get a bonus token if applicable
        try: # try, in case it's out of bonus tokens
            if len(sell_idx) == 3:
                self._players[self.whos_turn].bonus_tokens.append(self._bonus_tokens[3].pop())
            elif len(sell_idx) == 4:
                self._players[self.whos_turn].bonus_tokens.append(self._bonus_tokens[4].pop())
            elif len(sell_idx) >= 5:
                self._players[self.whos_turn].bonus_tokens.append(self._bonus_tokens[5].pop())
        except IndexError:
            print(f"Ran out of bonus tokens for n={len(sell_idx)}. Sorry.")

        return True
    
    def _do_grab_card(self, grab_idx):
        if self._players[self.whos_turn].num_cards() == 7:
            print(f"Player {self.whos_turn + 1} already has 7 cards in their hand. Pick a different action.")
            return False
        
        card_type = self._market.pop(grab_idx)
        self._players[self.whos_turn].hand.append(card_type)
        self._replenish_market()
        
        # Sort the player's hand
        self._players[self.whos_turn].hand.sort()
        
        # Everything went well, print the result and return true
        print(f"Player {self.whos_turn + 1} grabbed card {grab_idx}, a {self._types[card_type]}.")
        return True
    
    def _do_trade_cards(self, tradeIn, tradeOut):
        pass
    
    
    def _replenish_market(self):
        try:
            self._market.append(self._deck.pop())
        except IndexError:
            print("Deck is empty and cannot replenish the market - the game is over.")



    class PlayerState():
        def __init__(self, init_hand):
            self.hand = init_hand
            self.hand.sort()

            self.tokens = []
            self.bonus_tokens = []
        
        def num_cards(self):
            # Return the number of non-camel cards (assumes the camels are the highest-index)
            return sum(i < GameEngine._types.index("camels") for i in self.hand)
