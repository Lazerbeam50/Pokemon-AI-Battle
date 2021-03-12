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

def is_point_inside_rect(x, y, rect):
    if (x > rect.left) and (x < rect.right) and (y > rect.top) and (y < rect.bottom):
        return True
    else:
        return False