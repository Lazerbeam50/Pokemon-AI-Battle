import pygame
import pygame.locals as pyLocals

class GameSprite(pygame.sprite.Sprite):
    def __init__(self, image, rect, layer=1):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = pyLocals.Rect(rect)
        self._layer = layer

def centre_x(objectWidth, fitWidth, fitLeft):
    x = int((fitWidth - objectWidth) / 2 + fitLeft)

    return x
