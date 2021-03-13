"""

"""
import pygame
import pygame.locals as pyLocals

import resources
import sprites

class Battle:
    def __init__(self):
        self.bgColour = None
        self.bgImage = None
        self.group = pygame.sprite.Group()
        self.doneSetup = False
        self.state = 0
        self.surface = pygame.Surface((1280, 720))

    def update(self, values, event=None):

        if self.doneSetup and event == None:
            pass
        elif self.doneSetup and event != None:
            pass
        else:
            if self.state == 0:
                self.group.empty()
                self.initial_setup(values)

            self.doneSetup = True

    def initial_setup(self, values):

        # Set background colour
        self.bgColour = (255, 255, 255)

        # Set up boxes
        box3Image = resources.load_sprite("tp_box3.png")
        textBoxImage = pygame.transform.scale(box3Image, (1045, 130))
        choicesBox = pygame.transform.scale(box3Image, (630, 200))
        box4Image = resources.load_sprite("tp_box4.png")
        self.group.add(sprites.GameSprite(box4Image, (0, 0, box4Image.get_width(), box4Image.get_height())))
        self.group.add(sprites.GameSprite(box4Image, (1163, 0, box4Image.get_width(), box4Image.get_height())))
        self.group.add(sprites.GameSprite(textBoxImage,
                                          (118, 520 - textBoxImage.get_height(),
                                           textBoxImage.get_width(), textBoxImage.get_height())
                                          )
                       )
        self.group.add(sprites.GameSprite(choicesBox,
                                          (0, 520, choicesBox.get_width(), choicesBox.get_height())
                                          )
                       )
        self.group.add(sprites.GameSprite(choicesBox,
                                          (650, 520, choicesBox.get_width(), choicesBox.get_height())
                                          )
                       )

        #Set up pokemon and moves
        #values.team1.selected[0].backSprite.x =

        #Set up trainer sprites
        player1nameImage = values.font16.render(values.player1.name, True, (0, 0, 0))
        self.group.add(sprites.GameSprite(player1nameImage,
                                          (sprites.centre_x(player1nameImage.get_width(),
                                                            box4Image.get_width(),
                                                            0),
                                           30, player1nameImage.get_width(), player1nameImage.get_height())
                                          )
                       )
        player2nameImage = values.font16.render(values.player2.name.upper(), True, (0, 0, 0))
        self.group.add(sprites.GameSprite(player2nameImage,
                                          (sprites.centre_x(player2nameImage.get_width(),
                                                            box4Image.get_width(),
                                                            1163),
                                           30, player2nameImage.get_width(), player2nameImage.get_height())
                                          )
                       )
        values.player1.sprite.rect.x = 0
        values.player1.sprite.rect.y = 50
        values.player2.sprite.rect.x = 1163
        values.player2.sprite.rect.y = 50
        self.group.add([values.player1.sprite, values.player2.sprite])

        #Start the JS thread