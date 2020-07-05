import random
class GameEngine:
    def __init__(self):
        self._tokens = None
        self._bonus_tokens = None
        self._deck = None
        self._market = None
        self._player1 = None
        self._player2 = None
        self._types = ["leather", "spice", "cloth", "silver", "gold", "diamonds", "camels"]
        
        self._reset()

    def _reset(self):
        self._tokens = {
            "leather": [1, 1, 1, 1, 1, 1, 2, 3, 4],
            "spice": [1, 1, 2, 2, 3 ,3, 5],
            "cloth": [1, 1, 2, 2, 3, 3, 5],
            "silver": [5, 5, 5, 5, 5],
            "gold": [5, 5, 5, 6, 6],
            "diamonds": [5, 5, 5, 7, 7]
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
        self._player_1 = self.PlayerState([self._deck.pop() for _ in range(5)])
        self._player_2 = self.PlayerState([self._deck.pop() for _ in range(5)])

        
    def get_data(self):
        pass
        
    def get_last_action(self):
        pass
    
    def do_action(self):
        pass
    
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
