"""

"""

import pygame

import math

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

        self.ai = None
        self.choices = []
        self.request = None

        self.side = []

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

        self.hpBox = None
        self.hpBack = None
        self.hpMain = None
        self.nameSprite = None
        self.smallName = None
        self.genderSprite = None
        self.HPsprite = None
        self.maxHPSprite = None

        self.allyLocation = None
        self.enemyLocation = None
        self.slotLocation = None
        self.switchTarget = False
        self.request = None

        self.checkedBy = []
        self.checks = []
        self.counteredBy = []
        self.counters = []
        self.fainted = False
        self.knownAbility = None
        self.moves = None
        self.moveData = []
        self.knownMoves = []
        self.potentialMoves = []
        self.statusCondition = ''
        self.speedMult = 1

        self.reset_stat_stages()

    def compute_stats(self, values, baseStats):
        self.stats = {}
        #Calculate hp
        #If Shedinja, set hp to 1
        if self.species == "shedinja":
            self.stats['hp'] = 1
        else:
            self.stats['hp'] = math.floor((2 * baseStats[0][0] + self.hpIV + math.floor(self.hpEV/4)) * 50/100) + 60

        #Itterate through the 5 other stats
        bases = [baseStats[1][0], baseStats[2][0], baseStats[3][0], baseStats[4][0], baseStats[5][0]]
        ivs = [self.atkIV, self.defIV, self.spaIV, self.spdIV, self.speIV]
        evs = [self.atkEV, self.defEV, self.spaEV, self.spdEV, self.speEV]
        nature = values.natures[self.nature]
        finalStats = []

        for i in range(5):
            finalStats.append(
                math.floor((math.floor((2 * bases[i] + ivs[i] + math.floor(evs[i]/4)) * 50/100) + 5) * nature[i])
            )
        self.stats['atk'] = finalStats[0]
        self.stats['def'] = finalStats[1]
        self.stats['spa'] = finalStats[2]
        self.stats['spd'] = finalStats[3]
        self.stats['spe'] = finalStats[4]

    def reset_stat_stages(self):

        self.statStages = {
            'atk': 0,
            'def': 0,
            'spa': 0,
            'spd': 0,
            'spe': 0
        }
