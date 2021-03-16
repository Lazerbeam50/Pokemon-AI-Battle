"""

"""
import pygame
import pygame.locals as pyLocals

from threading import Thread
import json
import subprocess

import resources
import sprites

class Battle:
    def __init__(self):
        self.animating = False
        self.animationFrame = 0
        self.awaitingSimOutput = True
        self.bgColour = None
        self.bgImage = None
        self.group = pygame.sprite.Group()
        self.doneSetup = False
        self.frame = 0
        self.rawOutput = None
        self.simEvents = []
        self.state = 0
        self.surface = pygame.Surface((1280, 720))
        self.text = None
        self.thread = None

    def update(self, values, event=None):

        if self.doneSetup and event == None:
            self.count_frames()
            self.read_output(values)
        elif self.doneSetup and event != None:
            pass
        else:

            self.count_frames()

            if self.state == 0:
                self.group.empty()
                self.initial_setup(values)
                self.doneSetup = True

            #Handle sim events
            elif self.state == 1:
                self.handle_sim_events(values)

            #Switch pokemon
            elif self.state == 2:
                self.handle_switch(values)


    def count_frames(self):
        if self.frame == 29:
            self.frame = 0
        else:
            self.frame += 1

        if self.animationFrame > 0:
            self.animationFrame -= 1

    def handle_sim_events(self, values):

        text = {'switch': 2}

        #Iterate through events queue
        for line in self.simEvents[:]:
            #If an line is recognised, handle events accordingly
            try:
                self.state = text[line.split("|")[1]]
                self.doneSetup = False
                break
            except KeyError:
                self.simEvents.remove(line)
            except IndexError:
                self.simEvents.remove(line)
        #If turn start is hit, wait for player input

    def handle_switch(self, values):
        if not self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            if line[2][:2] == 'p1':
                player = values.player1.name
            else:
                player = values.player2.name
            pkmn = line[3].split(',')[0]
            text = f'{player} sent out {pkmn}!'
            textImage = values.font20.render(text, True, (0, 0, 0))
            if self.text != None:
                self.text.kill()
            self.text = sprites.GameSprite(textImage, (165, 400, textImage.get_width(), textImage.get_height()))
            self.group.add(self.text)
            self.animating = True
            self.animationFrame = values.settings.fps * 4
        elif self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            pkmnName = line[3].split(",")[0].lower()
            if 'p1a' in line[2]:
                x = 110
                y = 210
                for pkmn in values.team1.selected:
                    if pkmn.nickname == pkmnName:
                        pkmnSprite = pkmn.backSprite
            elif 'p1b' in line[2]:
                x = 410
                y = 210
                for pkmn in values.team1.selected:
                    if pkmn.nickname == pkmnName:
                        pkmnSprite = pkmn.backSprite
            elif 'p2a' in line[2]:
                x = 650
                y = 0
                for pkmn in values.team2.selected:
                    if pkmn.nickname == pkmnName:
                        pkmnSprite = pkmn.frontSprite
            elif 'p2b' in line[2]:
                x = 950
                y = 0
                for pkmn in values.team2.selected:
                    if pkmn.nickname == pkmnName:
                        pkmnSprite = pkmn.frontSprite

            pkmnSprite.rect.x = x
            pkmnSprite.rect.y = y
            pkmnSprite._layer = 3
            self.group.add(pkmnSprite)

            self.animating = False
            del self.simEvents[0]
            self.state = 1

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
        self.thread = Thread(target=run_js_script)
        self.thread.start()
        values.threadRunning = True

    def read_output(self, values):
        if self.frame == 0 and self.awaitingSimOutput:
            f = open("output-doc.txt", "r")
            lines = f.readlines()
            if lines:
                self.rawOutput = lines
                f = open("output-doc.txt", "w")
                f.write("")
                f.close()
                self.awaitingSimOutput = False
                self.interpret_output(values)
                self.state = 1
                self.doneSetup = False

    def interpret_output(self, values):
        p1 = False
        p2 = False
        for line in self.rawOutput:
            if line == 'p1\n':
                p1 = True
                p2 = False
            elif line == 'p2\n':
                p1 = False
                p2 = True
            elif line[:9] == '|request|':
                if p1:
                    values.player1.request = json.loads(line.split('|request|')[1])
                elif p2:
                    values.player2.request = json.loads(line.split('|request|')[1])
                else:
                    print("Nooo")
            else:
                p1, p2 = False, False
                self.simEvents.append(line)


def run_js_script():
    subprocess.run(["node", "pokemon-showdown/simulatorIO.js"])
