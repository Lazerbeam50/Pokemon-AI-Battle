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
        self.buttons = []
        self.currentButton = None
        self.currentMove = None
        self.group = pygame.sprite.Group()
        self.doneSetup = False
        self.frame = 0
        self.playerOptions = []
        self.rawOutput = None
        self.simEvents = []
        self.state = 0
        self.surface = pygame.Surface((1280, 720))
        self.switchLog = []
        self.text = None
        self.textMods = {}
        self.thread = None

    def update(self, values, event=None):

        if self.doneSetup and event is None:
            self.count_frames()
            self.read_output(values)
        elif self.doneSetup and event is not None:
            if event.type == pyLocals.MOUSEBUTTONUP and event.button == 1:
                pos = pygame.mouse.get_pos()
                clicked = False
                for button in self.buttons:
                    clicked = sprites.is_point_inside_rect(pos[0], pos[1], button.rect)
                    if clicked:
                        #moves
                        self.currentButton = button
                        self.handle_player_options(values)
                        break
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

            #Abilities
            elif self.state == 3:
                self.handle_ability(values)

            #Unboosts
            elif self.state == 4:
                self.handle_unboost(values)

            #Set up player options
            elif self.state == 5:
                self.set_up_player_options(values)

    def count_frames(self):
        if self.frame == 29:
            self.frame = 0
        else:
            self.frame += 1

        if self.animationFrame > 0:
            self.animationFrame -= 1

    def handle_ability(self, values):
        if not self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            if line[3] == 'Intimidate':
                self.textMods['Intimidate'] = line[2][5:]
                del self.simEvents[0]
                self.state = 1
            elif line[3] == 'Pressure\n':
                pkmn = line[2][5:]
                text = f"""{pkmn} is exerting its Pressure!"""
                self.update_text(values, text)
        elif self.animating and self.animationFrame == 0:
            del self.simEvents[0]
            self.animating = False
            self.state = 1

    def handle_player_options(self, values):
        if self.currentButton.use == 0:
            if self.currentButton.storage['pp'] > 0 and not self.currentButton.storage['disabled']:
                if self.currentButton.storage['target'] in ['normal', 'any']:
                    self.currentMove = self.currentButton.storage

                    [option.kill() for option in self.playerOptions]
                    [button.sprite.kill() for button in self.buttons]

                    self.currentButton = None
                    self.playerOptions = []
                    self.buttons = []

                    self.playerOptions.append(
                        sprites.GameSprite(
                            values.font20.render("Targets", True, (0, 0, 0)),
                            (248, 530, 0, 0),
                            2
                        )
                    )


                    self.group.add(self.playerOptions)
                    self.doneSetup = True


    def handle_sim_events(self, values):

        text = {'switch': 2, '-ability': 3, '-unboost': 4, 'turn': 5}

        #Iterate through events queue
        for line in self.simEvents[:]:
            print(line)
            #If an line is recognised, handle events accordingly
            try:
                self.state = text[line.split("|")[1]]
                if self.state == 2:
                    if line.split("|")[2] in self.switchLog:
                        self.simEvents.remove(line)
                        self.state = 1
                        continue
                    else:
                        self.switchLog.append(line.split("|")[2])
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
            text = f'{player} sent out {pkmn.upper()}!'
            self.update_text(values, text)

        elif self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            pkmnName = line[3].split(",")[0].lower()
            hpBarBox = resources.load_sprite("hp_box1.png")
            if 'p1a' in line[2]:
                x = 110
                y = 210
                hpBox_x = 630
                hpBox_y = 210
                for pkmn in values.team1.selected:
                    if pkmn.nickname == pkmnName:
                        pkmnSprite = pkmn.backSprite
                        break
            elif 'p1b' in line[2]:
                x = 410
                y = 210
                hpBox_x = 680
                hpBox_y = 310
                for pkmn in values.team1.selected:
                    if pkmn.nickname == pkmnName:
                        pkmnSprite = pkmn.backSprite
                        break
            elif 'p2a' in line[2]:
                x = 650
                y = 0
                hpBox_x = 130
                hpBox_y = 100
                for pkmn in values.team2.selected:
                    if pkmn.nickname == pkmnName:
                        pkmnSprite = pkmn.frontSprite
                        break
            elif 'p2b' in line[2]:
                x = 950
                y = 0
                hpBox_x = 180
                hpBox_y = 0
                for pkmn in values.team2.selected:
                    if pkmn.nickname == pkmnName:
                        pkmnSprite = pkmn.frontSprite
                        break

            pkmnSprite.rect.x = x
            pkmnSprite.rect.y = y
            pkmnSprite._layer = 3

            pkmn.hpBox = sprites.GameSprite(
                hpBarBox,
                (hpBox_x, hpBox_y, hpBarBox.get_width(), hpBarBox.get_height()),
                3
            )
            if pkmn.gender != "":
                gender = " (" + pkmn.gender.upper() + ")"
            else:
                gender = ""
            pkmn.nameSprite = sprites.GameSprite(
                values.font16.render(pkmnName.upper() + gender, True, (0, 0, 0)),
                (hpBox_x + 15, hpBox_y + 15, 0, 0),
                4
            )
            pkmn.hpBack = sprites.GameSprite(
                pygame.Surface((300, 20)),
                (hpBox_x + 15, hpBox_y + 30, 0, 0),
                4
            )
            pkmn.hpBack.image.fill((128, 128, 128))
            currentHP = int(line[4].split("/")[0])
            maxHP = int(line[4].split("/")[1])
            barLength = int((currentHP/maxHP) * 300)
            pkmn.hpMain = sprites.GameSprite(
                pygame.Surface((barLength, 20)),
                (hpBox_x + 15, hpBox_y + 30, 0, 0),
                5
            )
            if currentHP < maxHP/2:
                if currentHP < maxHP/5:
                    color = (255, 0, 0)
                else:
                    color = (255, 255, 0)
            else:
                color = (50, 205, 50)
            pkmn.hpMain.image.fill(color)
            pkmn.HPsprite = sprites.GameSprite(
                values.font16.render(str(currentHP) + "/" + str(maxHP), True, (0, 0, 0)),
                (hpBox_x + 320, hpBox_y + 30, 0, 0),
                4
            )
            if line[2].split(":")[0] in ('p1a', 'p1b'):
                spriteList = [pkmnSprite, pkmn.hpBox, pkmn.nameSprite, pkmn.hpBack, pkmn.hpMain,
                            pkmn.HPsprite]
            else:
                spriteList = [pkmnSprite, pkmn.hpBox, pkmn.nameSprite, pkmn.hpBack, pkmn.hpMain]
            self.group.add(spriteList)
            self.animating = False
            del self.simEvents[0]
            self.state = 1

    def handle_unboost(self, values):
        if not self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            if 'Intimidate' in self.textMods:
                pkmn = self.textMods['Intimidate']
                opponent = line[2][5:]
                text = f"""{pkmn}'s Intimidate cuts {opponent}'s attack!"""
                self.update_text(values, text)

        elif self.animating and self.animationFrame == 0:
            #Eventually add some kind of animation here
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

    def set_up_player_options(self, values):

        #Set up moves

        self.playerOptions.append(
            sprites.GameSprite(
                values.font20.render("Moves", True, (0, 0, 0)),
                (267, 530, 0, 0),
                2
            )
        )

        if self.state == 5:
            i = 0
        else:
            i = 1
        x_list = [0, 315]
        y_dict = {0:560, 1:590}
        pos = [0, 0]
        for move in values.player1.request['active'][i]['moves']:
            img = values.font16.render(move['move'], True, (0, 0, 0))
            x = sprites.centre_x(img.get_width(), 315, x_list[pos[0]])
            y = y_dict[pos[1]]
            self.buttons.append(
                sprites.Button(
                    0,
                    img,
                    (x, y, img.get_width(), img.get_height()),
                    2,
                    move,
                    self.group
                )
            )
            if pos[0] == 1:
                pos = [0, 1]
            else:
                pos[0] += 1

        #Set up switches

        self.playerOptions.append(
            sprites.GameSprite(
                values.font20.render("Switch", True, (0, 0, 0)),
                (256, 620, 0, 0),
                2
            )
        )
        x = 20
        for pkmn in values.team1.selected:
            pkmn.miniSprite.rect.x = x
            pkmn.miniSprite.rect.y = 640
            #self.playerOptions.append(pkmn.miniSprite)
            self.buttons.append(
                sprites.Button(
                    1,
                    pkmn.miniSprite.image,
                    pkmn.miniSprite.rect,
                    2,
                    pkmn,
                    self.group
                )
            )
            x += 158

        active = []
        for pkmn in values.player1.request['side']['pokemon']:
            if pkmn['active']:
                active.append(pkmn)

        text = "What will " + active[i]['details'].split(',')[0].upper() + " do?"
        self.update_text(values, text)
        self.animating = False
        self.animationFrame = 0

        self.group.add(self.playerOptions)
        self.doneSetup = True



    def update_text(self, values, text):
        textImage = values.font20.render(text, True, (0, 0, 0))
        if self.text != None:
            self.text.kill()
        self.text = sprites.GameSprite(textImage, (165, 400, textImage.get_width(), textImage.get_height()))
        self.group.add(self.text)
        self.animating = True
        self.animationFrame = values.settings.fps


def run_js_script():
    subprocess.run(["node", "pokemon-showdown/simulatorIO.js"])
