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

        genderDiffs = ["venusaur", "girafarig"]

        for i in range(2):
            if i == 0:
                x = 560
                y = 100
            else:
                x = 120
                y = 100

            for pokemon in [values.team1.pokemon, values.team2.pokemon][i]:
                if pokemon.species in genderDiffs:
                    species = pokemon.species + "-" + pokemon.gender
                else:
                    species = pokemon.species

                data = loaddata.load_pokemon_sprites(species.capitalize())
                image = pygame.transform.scale(resources.load_pokemon_sprites(data[0][1]), (200, 200))
                pokemon.frontSprite = sprites.GameSprite(image, (0, 0, 200, 200))
                image = pygame.transform.scale(resources.load_pokemon_sprites(data[0][2]), (200, 200))
                pokemon.backSprite = sprites.GameSprite(image, (0, 0, 200, 200))
                image = pygame.transform.scale(resources.load_pokemon_sprites(data[0][3]), (70, 70))
                pokemon.miniSprite = sprites.GameSprite(image, (x, y, 70, 70))

                self.group.add(pokemon.miniSprite)
                if i == 0:
                    x += 100
                else:
                    if x < 290:
                        x += 90
                    else:
                        x = 120
                        y += 60

        #Set up buttons