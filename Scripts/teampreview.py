"""

"""
import pygame
import pygame.locals as pyLocals

import loaddata
import resources
import sprites
import trainers

class TeamPreviewManager:
    def __init__(self):
        self.bgColour = None
        self.bgImage = None
        self.boxes = []
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

        #Set background colour
        self.bgColour = (135, 206, 250)

        #Set up boxes
        self.boxes = [
            sprites.GameSprite(resources.load_sprite("tp_box1.png"), (80, 20, 340, 330)),
            sprites.GameSprite(resources.load_sprite("tp_box2.png"), (520, 20, 680, 330)),
            sprites.GameSprite(resources.load_sprite("tp_box3.png"), (80, 370, 1120, 330))
        ]
        self.group.add(self.boxes)

        #Set up text and sprites
        player1nameImage = values.font.render(values.player1.name, True, (0, 0, 0))
        self.group.add(sprites.GameSprite(player1nameImage,
                                          (sprites.centre_x(player1nameImage.get_width(),
                                                            self.boxes[1].rect.width,
                                                            self.boxes[1].rect.left),
                                           40, player1nameImage.get_width(), player1nameImage.get_height())
                                          )
                       )
        player2nameImage = values.font.render(values.player2.name.upper(), True, (0, 0, 0))
        self.group.add(sprites.GameSprite(player2nameImage,
                                          (sprites.centre_x(player2nameImage.get_width(),
                                                            self.boxes[0].rect.width,
                                                            self.boxes[0].rect.left),
                                           40, player1nameImage.get_width(), player1nameImage.get_height())
                                          )
                       )
        summaryImage = values.font.render("SUMMARY", True, (0, 0, 0))
        self.group.add(sprites.GameSprite(summaryImage,
                                          (sprites.centre_x(summaryImage.get_width(),
                                                            self.boxes[2].rect.width,
                                                            self.boxes[2].rect.left),
                                           390, player1nameImage.get_width(), player1nameImage.get_height())
                                          )
                       )
        #Set up buttons