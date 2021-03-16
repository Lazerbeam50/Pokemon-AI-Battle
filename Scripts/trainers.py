"""

"""

import pygame

import misc
import resources
import sprites

class Trainer:
    def __init__(self, data):
        self.charID = data[0][0]
        self.name = data[0][1]
        trainerImage = pygame.transform.scale(resources.load_trainer_sprite(data[0][2]), (118, 267))
        #trainerImage = sprites.get_translucent_sprite(trainerImage)
        self.sprite = sprites.GameSprite(trainerImage, (0, 0, trainerImage.get_width(), trainerImage.get_height()), 2)

        self.request = None


class Team:
    def __init__(self, data):
        self.teamID = data[0][3]
        self.pokemon = [
            Pokemon(data[0]),
            Pokemon(data[1]),
            Pokemon(data[2]),
            Pokemon(data[3]),
            Pokemon(data[4]),
            Pokemon(data[5])
        ]
        self.selected = []

class Pokemon:
    def __init__(self, data):
        """

        :param data:
        """
        self.nickname = misc.is_blank(data[4], data[5])
        self.species = data[5]
        self.gender = data[6]
        self.item = data[7]
        self.ability = data[8]
        self.hpEV = misc.is_blank(data[9], 0)
        self.atkEV = misc.is_blank(data[10], 0)
        self.defEV = misc.is_blank(data[11], 0)
        self.spaEV = misc.is_blank(data[12], 0)
        self.spdEV = misc.is_blank(data[13], 0)
        self.speEV = misc.is_blank(data[14], 0)
        self.hpIV = misc.is_blank(data[15], 31)
        self.atkIV = misc.is_blank(data[16], 31)
        self.defIV = misc.is_blank(data[17], 31)
        self.spaIV = misc.is_blank(data[18], 31)
        self.spdIV = misc.is_blank(data[19], 31)
        self.speIV = misc.is_blank(data[20], 31)
        self.nature = data[21]
        self.move1 = data[22]
        self.move2 = data[23]
        self.move3 = data[24]
        self.move4 = data[25]

        self.frontSprite = None
        self.backSprite = None
        self.miniSprite = None

        