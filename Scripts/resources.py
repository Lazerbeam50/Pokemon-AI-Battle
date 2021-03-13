#Import pygame
import pygame
import os

def load_sprite(name):
    fullname = os.path.join('Resources\Sprites', name)
    try:
        image = pygame.image.load(fullname).convert_alpha()
    except pygame.error:
        print("Cannot load image:", fullname)
        input("Press enter to exit")
        raise Exception
    return image

def load_pokemon_sprites(name):
    fullname = os.path.join('Resources\Sprites\Pokemon', name)
    try:
        image = pygame.image.load(fullname).convert_alpha()
    except pygame.error:
        print("Cannot load image:", fullname)
        input("Press enter to exit")
        raise Exception
    return image

def load_trainer_sprite(name):
    fullname = os.path.join('Resources\Sprites\Trainers', name)
    try:
        image = pygame.image.load(fullname).convert_alpha()
    except pygame.error:
        print("Cannot load image:", fullname)
        input("Press enter to exit")
        raise Exception
    return image