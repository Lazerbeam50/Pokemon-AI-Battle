"""

"""
import pygame
import pygame.locals as pyLocals

import loaddata
import trainers

class TeamPreviewManager:
    def __init__(self):
        self.bgColour = None
        self.bgImage = None
        self.group = pygame.sprite.Group()
        self.doneSetup = False
        self.state = 0
        self.surface = pygame.Surface((1280, 720))

    def update(self, values, event=None):

        if self.doneSetup:
            pass
        else:
            self.group.empty()

            if self.state == 0:
                self.initial_setup(values)

            self.doneSetup = True

    def initial_setup(self, values):

        #Load players, teams and pokemon
        values.player1 = trainers.Trainer(loaddata.load_player(values.player1))
        values.player2 = trainers.Trainer(loaddata.load_player(values.player2))
        values.team1 = trainers.Team(loaddata.load_team(values.team1))
        values.team2 = trainers.Team(loaddata.load_team(values.team2))
        dummy = 4
        print("Shouldn't reach here...")
        #Set background colour
        self.bgColour = (135, 206, 250)
        #Set up boxes
        #Set up buttons