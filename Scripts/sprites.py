import pygame
import pygame.locals as pyLocals

class Button:
    def __init__(self, use, image, rect, layer=1, storage=None, group=None):
        self.use = use
        self.rect = pyLocals.Rect(rect)
        self.sprite = GameSprite(image, rect, layer)
        self.storage = storage
        if group is not None:
            group.add(self.sprite)

class GameSprite(pygame.sprite.Sprite):
    def __init__(self, image, rect, layer=1):
        pygame.sprite.DirtySprite.__init__(self)
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

def get_translucent_sprite(image):
    for row in range(image.get_height()):
        for col in range(image.get_width()):
            image.set_at((col, row), set_alphas(image.get_at((col, row))))

    return image


def set_alphas(colour):
    colour.update(colour.r, colour.g, colour.b, 128)

    return colour