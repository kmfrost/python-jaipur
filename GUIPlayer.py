from Player import Player
import pygame
import pygame.locals
import os

class GUIPlayer(Player):

    base_dir = os.path.split(os.path.abspath(__file__))[0] # get location of this folder
    img_dir = os.path.join(base_dir, "game_pieces")


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._win_size = (960,540)
        self._disp = None
        self._bg = None


        pygame.init()
        self._disp = pygame.display.set_mode(self._win_size)
        pygame.display.set_caption("Jaipur GUIPlayer")
        
        self._bg = pygame.Surface(self._disp.get_size())
        self._bg = self._bg.convert()
        self._bg.fill((63,63,255))

        self._disp.blit(self._bg, (0,0))
        pygame.display.flip()

        # load sprites
        self._deck = self.BackCard(10,self._disp.get_height()/2 - self.Card.CARD_SIZE[1]/2)

        allsprites = pygame.sprite.RenderPlain(self._deck)

        self._disp.blit(self._bg, (0,0))
        allsprites.draw(self._disp)
        pygame.display.flip()

        # init to "waiting for other player"

    def render_deck(num_deck):
        pass
    def render_discard(last_discard):
        pass
    def render_market(market):
        pass
    def render_my_hand(my_hand):
        pass
    def render_enemy_hand(enemy_num_camels, enemy_num_goods):
        pass



    class Card(pygame.sprite.Sprite):
        CARD_SIZE = (102,140)
        def __init__(self, img_filename, x=0, y=0):
            pygame.sprite.Sprite.__init__(self) # call super init
            self.image = self._load_img(img_filename)
            self.rect = self.image.get_rect()
            self.rect.size = self.CARD_SIZE
            self.rect.topleft = x,y
        
        def set_position(self, x,y):
            self.rect.topleft = x,y
            
        def _load_img(self, img_filename):
            try:
                img = pygame.image.load(img_filename)
            except pygame.error:
                print(f"ERROR: Failed to load image '{img_filename}'")
                exit()
            return img

    class BackCard(Card, pygame.sprite.Sprite):
        def __init__(self, x=0, y=0):
            GUIPlayer.Card.__init__(self, os.path.join(GUIPlayer.img_dir, "cardback.png"), x, y)


