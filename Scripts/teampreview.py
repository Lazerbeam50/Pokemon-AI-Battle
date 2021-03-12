"""

"""
import pygame
import pygame.locals as pyLocals

import random

import loaddata
import resources
import sprites
import trainers

class TeamPreviewManager:
    def __init__(self):
        self.bgColour = None
        self.bgImage = None
        self.boxes = []
        self.confirmSprite = None
        self.group = pygame.sprite.Group()
        self.doneSetup = False
        self.orderSprites = []
        self.state = 0
        self.surface = pygame.Surface((1280, 720))

    def update(self, values, event=None):

        if self.doneSetup and event == None:
            pass
        elif self.doneSetup and event != None:
            if event.type == pyLocals.MOUSEBUTTONUP and event.button == 1:
                clicked = False
                for pkmn in values.team1.pokemon:
                    clicked = sprites.is_point_inside_rect(pygame.mouse.get_pos()[0],
                                                           pygame.mouse.get_pos()[1],
                                                           pkmn.miniSprite.rect)
                    if clicked:
                        if pkmn in values.team1.selected:
                            values.team1.selected.remove(pkmn)
                            self.state = 1
                            self.doneSetup = False
                        else:
                            if len(values.team1.selected) < 4:
                                values.team1.selected.append(pkmn)
                                self.state = 1
                                self.doneSetup = False
                        break
                if not clicked and sprites.is_point_inside_rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1],
                                                           self.confirmSprite.rect):

                    if len(values.team1.selected) == 4:
                        self.pack_teams(values)
        else:

            if self.state == 0:
                self.group.empty()
                self.initial_setup(values)

            elif self.state == 1:
                self.setup_order_sprites(values)

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
            sprites.GameSprite(resources.load_sprite("tp_box1.png"), (80, 20, 340, 330), 0),
            sprites.GameSprite(resources.load_sprite("tp_box2.png"), (520, 20, 680, 330), 0),
            sprites.GameSprite(resources.load_sprite("tp_box3.png"), (80, 370, 1120, 330), 0)
        ]
        self.group.add(self.boxes)

        #Set up text and sprites
        player1nameImage = values.font20.render(values.player1.name, True, (0, 0, 0))
        self.group.add(sprites.GameSprite(player1nameImage,
                                          (sprites.centre_x(player1nameImage.get_width(),
                                                            self.boxes[1].rect.width,
                                                            self.boxes[1].rect.left),
                                           40, player1nameImage.get_width(), player1nameImage.get_height())
                                          )
                       )
        player2nameImage = values.font20.render(values.player2.name.upper(), True, (0, 0, 0))
        self.group.add(sprites.GameSprite(player2nameImage,
                                          (sprites.centre_x(player2nameImage.get_width(),
                                                            self.boxes[0].rect.width,
                                                            self.boxes[0].rect.left),
                                           40, player1nameImage.get_width(), player1nameImage.get_height())
                                          )
                       )
        summaryImage = values.font20.render("SUMMARY", True, (0, 0, 0))
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

        #Set up confirm button
        confirmImage = values.font20.render("CONFIRM", True, (0, 0, 0))
        x = sprites.centre_x(confirmImage.get_width(), self.boxes[1].rect.width, self.boxes[1].rect.left)
        self.confirmSprite = sprites.GameSprite(confirmImage,
                                                (x, 300, confirmImage.get_width(), confirmImage.get_height()
                                                 )
                                                )
        self.group.add(self.confirmSprite)

        #AI trainer picks its team and order
        order = [0, 1, 2, 3, 4, 5]
        random.shuffle(order)
        values.team2.selected = [values.team2.pokemon[order[0]],
                                 values.team2.pokemon[order[1]],
                                 values.team2.pokemon[order[2]],
                                 values.team2.pokemon[order[3]]
        ]

    def setup_order_sprites(self, values):
        #Remove old sprites from group
        self.group.remove(self.orderSprites)
        #Clear list
        self.orderSprites = []
        #Set up new sprites
        order = ["FIRST", "SECOND", "THIRD", "FOURTH"]
        #Loop through team 1's selected pokemon
        for pkmn in values.team1.selected:
            #Create sprite for each pokemon
            image = values.font16.render(order.pop(0), True, (0, 0, 0))
            x = sprites.centre_x(image.get_width(), pkmn.miniSprite.rect.width, pkmn.miniSprite.rect.left)
            self.orderSprites.append(sprites.GameSprite(image,
                                                        (x, 160, image.get_width(), image.get_height())
                                                        )
                                     )
        self.group.add(self.orderSprites)

    def pack_teams(self, values):
        for i in range(2):
            teamString = ""
            for pokemon in [values.team1.selected, values.team2.selected][i]:
                stringList = [pokemon.nickname]
                if pokemon.species == pokemon.nickname:
                    stringList.append("")
                else:
                    stringList.append(pokemon.species)
                stringList.append(pokemon.item)
                stringList.append(pokemon.ability)
                stringList.append(pokemon.move1 + "," + pokemon.move2 + "," + pokemon.move3 + "," + pokemon.move4)
                stringList.append(pokemon.nature)
                stringList.append(str(pokemon.hpEV) + "," + str(pokemon.atkEV) + "," + str(pokemon.defEV) + ","
                                  + str(pokemon.spaEV) + "," + str(pokemon.spdEV) + "," + str(pokemon.speEV))
                stringList.append(pokemon.gender.upper())
                stringList.append(str(pokemon.hpIV) + "," + str(pokemon.atkIV) + "," + str(pokemon.defIV) + ","
                                  + str(pokemon.spaIV) + "," + str(pokemon.spdIV) + "," + str(pokemon.speIV))
                stringList.append("")
                stringList.append("50")
                for j in range(3):
                    stringList.append("")

                #Combine
                pkmnString = "|".join(stringList)

                teamString = teamString + pkmnString + "]"

            #Write to team doc
            if i == 0:
                doc = "team1-doc.txt"
            else:
                doc = "team2-doc.txt"

            f = open(doc, "w")
            f.write(teamString[:-1])
            f.close()


