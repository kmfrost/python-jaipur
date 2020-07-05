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
        return None
        
    def get_state(self):
        pass
        
    def get_last_action(self):
        pass
    
    def do_action(self):
        
        # Flip whos turn it is
        self.whos_turn = self.whos_turn ^ 1
    
    def _do_take_camels(self):
        pass
    
    def _do_sell_cards(self):
        pass
    
    def _do_grab_card(self):
        pass
    
    def _do_trade_cards(self):
        pass
    

    class PlayerState():
        def __init__(self, init_hand):
            self.hand = init_hand
        
            self.token_total = []
            self.bonus_tokens = []
