from Player import Player
import pygame
import pygame.locals

class GUIPlayer(Player):
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

        # init to "waiting for other player"


