"""

"""
import pygame
import pygame.locals as pyLocals

from threading import Thread
import copy
import json
import subprocess

import misc
import random
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
        self.choices = []
        self.currentButton = None
        self.currentMove = None
        self.currentPokemon = None
        self.debugging = False
        self.group = pygame.sprite.LayeredUpdates()
        self.doneSetup = False
        self.frame = 0
        self.p1Active = []
        self.p1Ready = True
        self.p1Side = []
        self.p2Active = []
        self.p2Ready = True
        self.p2Side = []
        self.playerOptions = []
        self.rawOutput = None
        self.simEvents = []
        self.state = 0
        self.surface = pygame.Surface((1280, 720))
        self.switchLog = []
        self.textGroup = pygame.sprite.LayeredUpdates()
        self.textMods = {}
        self.thread = None
        self.weather = None

    def update(self, values, event=None):

        if self.doneSetup and event is None:
            self.count_frames()
            self.read_output(values)
            self.ai_pick_moves(values)
            self.handle_ai_force_switch(values)
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

            elif event.type == pyLocals.MOUSEBUTTONUP and event.button == 3:
                if not self.p1Ready:
                    print("Cancelling!")
                    self.back_button(values)
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

            elif self.state == 5:
                self.switchLog = []
                self.update_pokemon_info(values)

            #Set up player options
            elif self.state in [6, 7]:
                self.set_up_player_options(values)

            #Player done with input
            elif self.state == 8:
                self.p1Ready = True
                if self.p1Ready and self.p2Ready:
                    p1Wait = 'wait' in values.player1.request
                    p2Wait = 'wait' in values.player2.request
                    self.write_input(values, p1Wait=p1Wait, p2Wait=p2Wait)

            elif self.state == 9:
                self.handle_boost(values)

            elif self.state == 10:
                self.handle_move(values)

            elif self.state == 11:
                self.handle_text(values)

            elif self.state == 12:
                self.handle_damage(values)

            elif self.state == 13:
                self.handle_item(values)

            elif self.state == 14:
                self.handle_faint(values)

            elif self.state == 15:
                self.handle_status(values)

            elif self.state == 99:
                print("Error")

    def ai_pick_moves(self, values):
        if not self.p2Ready and 'forceSwitch' not in values.player2.request and 'wait' not in values.player2.request:
            print("Let's take a look")
            for i in range(len(self.p2Active)):
                try:
                    availableMoves = []
                    for move in self.p2Active[i].moves['moves']:
                        if move['pp'] > 0 and not move['disabled']:
                            availableMoves.append(move)
                    choice = random.choice(availableMoves)
                    target = None
                    if 'target' in choice:
                        if choice['target'] in ['normal', 'any']:
                            target = random.choice(self.p1Active)
                        elif choice['target'] == 'adjacentAlly':
                            target = -3 - self.p2Active[i].allyLocation
                    if target is None:
                        values.player2.choices.append([self.p2Active[i].nickname,
                                                       choice['move'],
                                                       choice['id']
                                                       ])
                    elif choice['target'] == 'adjacentAlly':
                        values.player2.choices.append([self.p2Active[i].nickname,
                                                       choice['move'],
                                                       choice['id'],
                                                       target,
                                                       "Placeholder"])
                    else:
                        values.player2.choices.append([self.p2Active[i].nickname,
                                                       choice['move'],
                                                       choice['id'],
                                                       target.enemyLocation,
                                                       target.nickname])
                except KeyError:
                    if 'trapped' in values.player2.request['active'][i]:
                        choice = self.p2Active[i].moves['moves'][0]
                        values.player2.choices.append([self.p2Active[i].nickname,
                                                       choice['move'],
                                                       choice['id'],
                                                       1,
                                                       "Placeholder"
                                                       ])
                    else:
                        values.player2.choices.append(['default'])

            self.p2Ready = True


    def back_button(self, values):
        self.clear_options()
        for poke in values.team1.selected:
            poke.switchTarget = False
        if self.state == 7:
            values.player1.choices = []

        self.state = 6
        self.doneSetup = False

    def clear_options(self):
        [option.kill() for option in self.playerOptions]
        [button.sprite.kill() for button in self.buttons]
        self.playerOptions = []
        self.buttons = []

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
                text = misc.split_string(text, 80)
                self.update_text(values, text)
        elif self.animating and self.animationFrame == 0:
            del self.simEvents[0]
            self.animating = False
            self.state = 1

    def handle_ai_force_switch(self, values):

        if not self.p2Ready and 'forceSwitch' in values.player2.request:
            print("Let's look")
            #Iterate through options in request
            options = []
            for pkmn in values.player2.request['side']['pokemon']:
                # Randomly select a pokemon that is not active and still has HP
                if not pkmn['active'] and pkmn['condition'] != '0 fnt':
                    options.append(pkmn)
            #Set up choices list

            random.shuffle(options)
            fainted = int(values.player2.request['forceSwitch'][0]) + int(values.player2.request['forceSwitch'][1])
            for i in range(min(fainted, len(options))):
                values.player2.choices.append([
                    "",
                    options[i]['ident'][4:]
                ])

            self.p2Ready = True
            if self.p1Ready:
                self.state = 8
                self.doneSetup = False

    def handle_boost(self, values):
        if not self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            pkmn = line[2][5:]
            stats = {'atk': 'Attack', 'def': 'Defense', 'spa': 'Special Attack', 'spd': 'Special Defence',
                     'spe': 'Speed'}
            fall = {'1\n': '', '1': '', '2\n': ' sharply ', '2': ' sharply '}
            stat = stats[line[3]]
            rise = fall[line[4]]
            text = f"{pkmn.upper()}'s {stat}{rise} rose!"
            text = misc.split_string(text, 50)
            self.update_text(values, text)


        elif self.animating and self.animationFrame == 0:
            #Eventually add some kind of animation here
            self.animating = False
            del self.simEvents[0]
            self.state = 1

    def handle_damage(self, values):
        #Identify which pokemon was damaged
        active = self.p1Active + self.p2Active
        line = self.simEvents[0].split("|")

        if not self.animating and self.animationFrame == 0:

            for pkmn in active:
                id = line[2][:2] + line[2][3:]
                if id == pkmn.request['ident']:

                    if len(line) == 5:
                        if line[4] == '[from] item: Life Orb\n':
                            text = f"{pkmn.nickname.upper()} lost some of its HP!"
                        elif line[4] == '[from] item: Leftovers\n':
                            text = f"{pkmn.nickname.upper()} restored a little HP using its leftovers!"
                        elif line[4] == '[from] Recoil\n':
                            text = f"{pkmn.nickname.upper()} was damaged by the recoil!"
                        elif line[4] == '[from] brn\n':
                            text = f"{pkmn.nickname.upper()} was hurt by its burn!"

                        try:
                            text = misc.split_string(text, 50)
                            self.update_text(values, text)
                        except UnboundLocalError:
                            self.animating = True
                    else:
                        self.animating = True

        elif self.animating and self.animationFrame == 0:

            for pkmn in active:
                id = line[2][:2] + line[2][3:]
                if id == pkmn.request['ident']:

                    #Set its hp bar to the appropriate size (or 0 if fainted)
                    if line[3] in ['0 fnt', '0 fnt\n']:
                        pkmn.hpMain.kill()
                    else:
                        currentHP = int(line[3].split("/")[0])
                        maxHP = int(line[3].split("/")[1].split(" ")[0])
                        barLength = int((currentHP / maxHP) * 300)
                        pkmn.hpMain.image = pygame.Surface((barLength, 20))
                        if currentHP < maxHP / 2:
                            if currentHP < maxHP / 5:
                                color = (255, 0, 0)
                            else:
                                color = (255, 215, 0)
                        else:
                            color = (50, 205, 50)
                        pkmn.hpMain.image.fill(color)
                        pkmn.HPsprite.image = values.font16.render(str(currentHP) + "/" + str(maxHP), True, (0, 0, 0))
                    del self.simEvents[0]
                    self.animating = False
                    self.state = 1
                    break

    def handle_faint(self, values):
        if not self.animating and self.animationFrame == 0:
            print("A pokemon is fainting")
            line = self.simEvents[0].split("|")
            pkmn = line[2][5:]
            text = f"{pkmn.upper()} fainted!"
            text = misc.split_string(text, 50)
            self.update_text(values, text)
        elif self.animating and self.animationFrame == 0:
            active = self.p1Active + self.p2Active
            line = self.simEvents[0].split("|")

            for pkmn in active:
                id = line[2][:2] + line[2][3:]
                if id.split('\n')[0] == pkmn.request['ident']:
                    pkmn.fainted = True
                    pkmn.HPsprite.kill()
                    pkmn.backSprite.kill()
                    pkmn.frontSprite.kill()
                    pkmn.miniSprite.image = sprites.grayscale(pkmn.miniSprite.image)
                    pkmn.hpBack.kill()
                    pkmn.hpBox.kill()
                    pkmn.hpMain.kill()
                    pkmn.nameSprite.kill()
                    break
            del self.simEvents[0]
            self.animating = False
            self.state = 1

    def handle_item(self, values):
        if not self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            pkmn = line[2][5:]
            item = line[3]
            if item in ["Leftovers", "Sitrus Berry"]:
                text = f"{pkmn.upper()} restored its health using its {item}!"
                text = misc.split_string(text, 50)
                self.update_text(values, text)
            elif item in ['Liechi Berry', 'Ganlon Berry', 'Salac Berry', 'Petaya Berry', 'Apicot Berry']:
                text = f"{pkmn.upper()} ate its {item}!"
                text = misc.split_string(text, 50)
                self.update_text(values, text)
            else:
                self.animating = True
                self.animationFrame = 1
        elif self.animating and self.animationFrame == 0:
            del self.simEvents[0]
            self.animating = False
            self.state = 1

    def handle_move(self, values):
        if not self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            pkmn = line[2][5:]
            move = line[3]
            if move == 'Helping Hand':
                text = f'{pkmn.upper()} used {move}! {pkmn.upper()} is ready to help {line[4][5:].upper()}!'
            elif move == 'Synthesis':
                text = f"{pkmn.upper()} used {move}! {pkmn.upper()} regained health!"
            elif move == 'Solar Beam':
                print("This is line:", line)
                if line[1] == 'move':
                    if line[5] == '[still]\n':
                        text = f"{pkmn.upper()} absorbed light!"
                    else:
                        text = f'{pkmn.upper()} used {move}!'
                else:
                    text = f'{pkmn.upper()} used {move}!'
            else:
                text = f'{pkmn.upper()} used {move}!'
            text = misc.split_string(text, 50)
            self.update_text(values, text)
        elif self.animating and self.animationFrame == 0:
            del self.simEvents[0]
            self.animating = False
            self.state = 1

    def handle_player_options(self, values):
        if self.currentButton.use == 0:
            if self.currentButton.storage['pp'] > 0 and not self.currentButton.storage['disabled']:
                self.currentMove = self.currentButton.storage
                if self.currentButton.storage['target'] in ['normal', 'any']:

                    self.clear_options()
                    self.currentButton = None

                    self.playerOptions.append(
                        sprites.GameSprite(
                            values.font20.render("Targets", True, (0, 0, 0)),
                            (248, 530, 0, 0),
                            2
                        )
                    )


                    x = 144
                    for pkmn in reversed(self.p2Active):
                        pkmn.miniSprite.rect.x = x
                        pkmn.miniSprite.rect.y = 560
                        self.buttons.append(
                            sprites.Button(
                                2,
                                pkmn.miniSprite.image,
                                pkmn.miniSprite.rect,
                                2,
                                pkmn,
                                self.group
                            )
                        )
                        x += 200


                    x = 144
                    for pkmn in self.p1Active:
                        pkmn.miniSprite.rect.x = x
                        pkmn.miniSprite.rect.y = 650
                        self.buttons.append(
                            sprites.Button(
                                2,
                                pkmn.miniSprite.image,
                                pkmn.miniSprite.rect,
                                2,
                                pkmn,
                                self.group
                            )
                        )
                        x += 200


                    self.group.add(self.playerOptions)

                elif self.currentButton.storage['target'] == 'adjacentAlly':
                    ally = -3 - self.currentPokemon.allyLocation

                    values.player1.choices.append([self.currentPokemon.nickname,
                                                   self.currentMove['move'],
                                                   self.currentMove['id'],
                                                   ally,
                                                   "Placeholder"])

                    if len(values.player1.choices) == 1:
                        self.state = 7
                        self.doneSetup = False
                    else:
                        self.clear_options()
                        self.state = 8
                        self.doneSetup = False

                else:
                    values.player1.choices.append([self.currentPokemon.nickname,
                                         self.currentMove['move'],
                                         self.currentMove['id']
                                         ])

                    if len(values.player1.choices) < len(self.p1Active):
                        self.state = 7
                        self.doneSetup = False
                    else:
                        self.clear_options()
                        self.state = 8
                        self.doneSetup = False

        #Switch
        elif self.currentButton.use == 1:
            if (self.currentButton.storage in self.p1Side and not self.currentButton.storage.switchTarget
                    and self.currentButton.storage.request['condition'] != '0 fnt'):
                self.currentButton.storage.switchTarget = True
                values.player1.choices.append([
                    self.currentButton.storage.nickname,
                    self.currentButton.storage.slotLocation
                ])
                if len(values.player1.choices) < len(self.p1Active) and 'forceSwitch' not in values.player1.request:
                    self.state = 7
                elif 'forceSwitch' in values.player1.request:
                    #Move to switch second pokemon if only one choice has been made, the sim is asking for two
                    #pokemon, and there are two or more options
                    options = [True if not button.storage.fainted else False for button in self.buttons].count(True)
                    if (len(values.player1.choices) < options and values.player1.request['forceSwitch'][0] and
                            values.player1.request['forceSwitch'][1]):
                        self.state = 7
                    else:
                        self.clear_options()
                        self.state = 8
                else:

                    self.clear_options()
                    self.state = 8
                self.doneSetup = False

        elif self.currentButton.use == 2:
            #Make sure the player has not targeted themselves
            if self.currentPokemon is not self.currentButton.storage:
                values.player1.choices.append([self.currentPokemon.nickname,
                                     self.currentMove['move'],
                                     self.currentMove['id'],
                                     self.currentButton.storage.enemyLocation,
                                     self.currentButton.storage.nickname])

                if len(values.player1.choices) < len(self.p1Active):
                    self.state = 7
                    self.doneSetup = False
                else:
                    self.clear_options()
                    self.state = 8
                    self.doneSetup = False


    def handle_sim_events(self, values):

        text = {'error': 99, 'switch': 2, '-ability': 3, '-unboost': 4, 'turn': 5, 'move': 10, '-activate': 11,
                '-damage': 12, '-resisted': 11, '-supereffective': 11, '-enditem': 13, '-heal': 12, '-weather': 11,
                '-miss': 11, 'cant': 11, 'faint':14, '-sidestart': 11, '-status': 15, '-start': 15, '-fail': 11,
                '-notarget': 11, '-immune': 11, '-sideend': 11, '-crit': 11, '-boost': 9, '-anim': 10}

        #Iterate through events queue
        for line in self.simEvents[:]:
            print("From handler:", line)
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

        #If events list is empty, check if forceSwitch is present
        if not self.simEvents:
            if 'forceSwitch' in values.player1.request:
                self.state = 5
                self.p1Ready = False
            elif 'wait' in values.player1.request:
                self.p1Ready = True
                self.doneSetup = True
            if 'forceSwitch' in values.player2.request:
                self.p2Ready = False
            elif 'wait' in values.player2.request:
                self.p2Ready = True

    def handle_switch(self, values):
        if not self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            if line[2][:2] == 'p1':
                player = values.player1.name
            else:
                player = values.player2.name
            pkmn = line[3].split(',')[0]
            text = f'{player} sent out {pkmn.upper()}!'
            text = misc.split_string(text, 50)
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
                x = 950
                y = 0
                hpBox_x = 180
                hpBox_y = 0
                for pkmn in values.team2.selected:
                    if pkmn.nickname == pkmnName:
                        pkmnSprite = pkmn.frontSprite
                        break
            elif 'p2b' in line[2]:
                x = 650
                y = 0
                hpBox_x = 130
                hpBox_y = 100
                for pkmn in values.team2.selected:
                    if pkmn.nickname == pkmnName:
                        pkmnSprite = pkmn.frontSprite
                        break

            active = self.p1Active + self.p2Active
            #Loop through active pokes
            for pkmn2 in active:
                # See if switcher is in same position as active poke
                if pkmn2.hpBox.rect.x == hpBox_x:
                    # Delete their sprites and remove from list
                    pkmn2.HPsprite.kill()
                    pkmn2.backSprite.kill()
                    pkmn2.frontSprite.kill()
                    pkmn2.hpBack.kill()
                    pkmn2.hpBox.kill()
                    pkmn2.hpMain.kill()
                    pkmn2.nameSprite.kill()
                    self.p1Active = [pkmn if poke is pkmn2 else poke for poke in self.p1Active]
                    self.p2Active = [pkmn if poke is pkmn2 else poke for poke in self.p2Active]

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

    def handle_status(self, values):
        if not self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            pkmn = line[2][5:]
            effect = line[3]
            if effect == 'confusion\n':
                text = f"{pkmn.upper()} became confused!"
            elif effect in ['par', 'par\n']:
                text = f"{pkmn.upper()} is paralyzed! It may be unable to move!"
            elif effect == 'psn\n':
                text = f"{pkmn.upper()} was poisoned!"
            elif effect == 'brn\n':
                text = f"{pkmn.upper()} was burned!"
            elif effect == 'frz\n':
                text = f"{pkmn.upper()} was frozen solid!"
            text = misc.split_string(text, 50)
            self.update_text(values, text)

            active = self.p1Active + self.p2Active

            if effect != 'confusion\n':
                for pkmn2 in active:
                    id = line[2][:2] + line[2][3:]
                    if id == pkmn2.request['ident']:
                        if pkmn2.gender != "":
                            gender = " (" + pkmn2.gender.upper() + ") " + effect.upper()
                        else:
                            gender = "    " + effect.upper()
                        pkmn2.nameSprite.image = values.font16.render(pkmn2.nickname.upper() + gender, True, (0, 0, 0))
                        break

        elif self.animating and self.animationFrame == 0:



            del self.simEvents[0]
            self.animating = False
            self.state = 1

    #For sim events that never have animations
    def handle_text(self, values):
        if not self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            move = None
            if line[1] == '-activate':
                pkmn = line[2][5:]
                move = line[3]

            elif line[1] == '-resisted':
                text = "It's not very effective..."

            elif line[1] == '-supereffective':
                text = "It's super effective!"

            elif line[1] == '-weather':
                if line[2] == 'SunnyDay\n':
                    self.weather = 0

                    text = "The sunlight turned harsh!"
                elif line[2] == 'SunnyDay':
                    text = "The sunlight is strong."

                elif line[2] == 'none\n':
                    if self.weather == 0:
                        text = "The harsh sunlight faded."

            elif line[1] == '-miss':
                pkmn = line[3][5:]
                text = f"{pkmn.upper()} avoided the attack!"

            elif line[1] == 'cant':
                if line[3] == 'flinch\n':
                    pkmn = line[2][5:]
                    text = f"{pkmn.upper()} flinched!"
                elif line[3] == 'par\n':
                    pkmn = line[2][5:]
                    text = f"{pkmn.upper()} is paralyzed! It can't move!"
                elif line[3] == 'frz\n':
                    pkmn = line[2][5:]
                    text = f"{pkmn.upper()} is frozen solid!"

            elif line[1] == '-sidestart':
                try:
                    if line[3].split(": ")[1] == "Tailwind\n":
                        if line[2][:2] == 'p2':
                            playerName = values.player2.name
                        else:
                            playerName = values.player1.name
                        text = f"The Tailwind blew from behind {playerName.upper()}'s team!"
                except IndexError:
                    pass
                if line[3] == 'Light Screen\n':
                    if line[2][:2] == 'p2':
                        playerName = values.player2.name
                    else:
                        playerName = values.player1.name
                    text = f"Light Screen made {playerName.upper()}'s team stronger against special moves!"

                elif line[3] == 'Reflect\n':
                    if line[2][:2] == 'p2':
                        playerName = values.player2.name
                    else:
                        playerName = values.player1.name
                    text = f"Reflect made {playerName.upper()}'s team stronger against physical moves!"

            elif line[1] == '-fail':
                text = "But it failed!"

            elif line[1] == '-notarget':
                text = "But there was no target..."

            elif line[1] == '-immune':
                pkmn = line[2][5:]
                if len(line) == 4:
                    if line[3] == '[from] ability: Levitate\n':
                        text = f"{pkmn.upper()} makes ground moves miss with Levitate!"
                else:
                    text = f"It doesn't affect {pkmn.upper()}..."

            elif line[1] == '-sideend':
                if line[2][:2] == 'p2':
                    playerName = values.player2.name
                else:
                    playerName = values.player1.name
                if line[3] == 'Light Screen\n':
                    text = f"{playerName.upper()}'s Light Screen faded."

                elif line[3] == 'move: Tailwind\n':
                    text = f"{playerName.upper()}'s Tailwind peered out."

                elif line[3] == 'Reflect\n':
                    text = f"{playerName.upper()}'s Reflect faded."

            elif line[1] == '-crit':
                text = "A critical hit!"

            if move == 'Protect\n':
                text = f'{pkmn.upper()} protected itself!'

            elif move == 'confusion\n':
                text = f"{pkmn.upper()} is confused!"

            text = misc.split_string(text, 50)
            self.update_text(values, text)
        elif self.animating and self.animationFrame == 0:
            del self.simEvents[0]
            self.animating = False
            self.state = 1

    def handle_unboost(self, values):
        if not self.animating and self.animationFrame == 0:
            line = self.simEvents[0].split("|")
            if 'Intimidate' in self.textMods:
                pkmn = self.textMods['Intimidate']
                opponent = line[2][5:]
                text = f"""{pkmn.upper()}'s Intimidate cuts {opponent.upper()}'s attack!"""
            else:
                pkmn = line[2][5:]
                stats = {'atk': 'Attack', 'def': 'Defense', 'spa': 'Special Attack', 'spd': 'Special Defence',
                         'spe': 'Speed'}
                fall = {'1\n': '', '2\n': ' sharply '}
                stat = stats[line[3]]
                drop = fall[line[4]]
                text = f"{pkmn.upper()}'s {stat}{drop} fell!"
            text = misc.split_string(text, 80)
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
                                           textBoxImage.get_width(), textBoxImage.get_height()),
                                          4
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
            if self.debugging:
                print("From interpreter:", line)
            if line == 'p1\n':
                p1 = True
                p2 = False
            elif line == 'p2\n':
                p1 = False
                p2 = True
            elif line[:9] == '|request|':
                if p1:
                    print("P1 got a new request")
                    values.player1.request = json.loads(line.split('|request|')[1])
                elif p2:
                    print("P2 got a new request")
                    values.player2.request = json.loads(line.split('|request|')[1])
                else:
                    print("Nooo")
            else:
                p1, p2 = False, False
                self.simEvents.append(line)

    def read_output(self, values):
        if self.frame == 0 and self.awaitingSimOutput:
            print("Reading")
            f = open("output-doc.txt", "r")
            lines = f.readlines()
            if lines:
                print("Got lines!")
                self.rawOutput = lines
                f = open("output-doc.txt", "w")
                f.write("")
                f.close()
                self.awaitingSimOutput = False
                self.interpret_output(values)
                self.state = 1
                self.doneSetup = False

    def set_up_player_options(self, values):

        self.clear_options()

        if 'active' in values.player1.request:

            #Set up moves

            self.playerOptions.append(
                sprites.GameSprite(
                    values.font20.render("Moves", True, (0, 0, 0)),
                    (267, 530, 0, 0),
                    2
                )
            )

            if self.state == 6:
                i = 0
            else:
                i = 1
            x_list = [0, 315]
            y_dict = {0:560, 1:590}
            pos = [0, 0]
            for move in self.p1Active[i].moves['moves']:
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

        if 'active' in values.player1.request:
            self.currentPokemon = self.p1Active[i]

            text = "What will " + self.currentPokemon.nickname.upper() + " do?"
        elif 'forceSwitch' in values.player1.request and len(values.player1.choices) == 1:
            text = f"{values.player1.choices[0][0].upper()} will switch in. Select another pokemon to switch in."
        elif 'forceSwitch' in values.player1.request and not values.player1.choices:
            text = "Select a pokemon to switch in."
        text = misc.split_string(text, 50)
        self.update_text(values, text)
        self.animating = False
        self.animationFrame = 0

        self.group.add(self.playerOptions)
        self.doneSetup = True

    def update_pokemon_info(self, values):

        self.textMods = {}

        self.p1Active = []
        self.p1Side = []
        self.p2Active = []
        self.p2Side = []

        allyLocation = -1
        enemyLocation = 1
        slotLocation = 1

        if (
                ('forceSwitch' in values.player1.request)
        ):
            print("Let's see what's changed!")

        if 'active' in values.player1.request:
            activeSets = copy.copy(values.player1.request['active'])
        else:
            activeSets = []

        #Loop through player 1 selected
        for pkmn1 in values.player1.request['side']['pokemon']:
            # Match them with side pokes in the request
            for pkmn2 in values.team1.selected:
                if pkmn1['ident'].split('p1: ')[1].lower() == pkmn2.nickname:
                    pkmn2.request = pkmn1
                    pkmn2.slotLocation = slotLocation
                    pkmn2.switchTarget = False
                    slotLocation += 1
                    #Add them to appropriate list
                    if pkmn1['active'] and not pkmn2.fainted:
                        pkmn2.allyLocation = allyLocation
                        pkmn2.enemyLocation = enemyLocation
                        allyLocation -= 1
                        enemyLocation += 1

                        if activeSets:
                            pkmn2.moves = activeSets.pop(0)
                        self.p1Active.append(pkmn2)

                    elif pkmn1['active'] and pkmn2.fainted and activeSets:
                        del activeSets[0]

                    else:
                        pkmn2.allyLocation = None
                        pkmn2.enemyLocation = None
                        self.p1Side.append(pkmn2)
                    break

        allyLocation = -1
        enemyLocation = 1
        slotLocation = 1

        if 'active' in values.player2.request:
            activeSets = copy.copy(values.player2.request['active'])
        else:
            activeSets = []

        #Do the same for player 2
        for pkmn1 in values.player2.request['side']['pokemon']:
            # Match them with side pokes in the request
            for pkmn2 in values.team2.selected:
                if pkmn1['ident'].split('p2: ')[1].lower() == pkmn2.nickname:
                    pkmn2.request = pkmn1
                    pkmn2.slotLocation = slotLocation
                    pkmn2.switchTarget = False
                    slotLocation += 1
                    # Add them to appropriate list
                    if pkmn1['active'] and not pkmn2.fainted:
                        pkmn2.allyLocation = allyLocation
                        pkmn2.enemyLocation = enemyLocation
                        allyLocation -= 1
                        enemyLocation += 1

                        if activeSets:
                            pkmn2.moves = activeSets.pop(0)

                        self.p2Active.append(pkmn2)

                    elif pkmn1['active'] and pkmn2.fainted and activeSets:
                        del activeSets[0]

                    else:
                        pkmn2.allyLocation = None
                        pkmn2.enemyLocation = None
                        self.p2Side.append(pkmn2)
                    break
        try:
            del self.simEvents[0]
        except IndexError:
            pass
        self.p1Ready = False
        self.p2Ready = 'wait' in values.player2.request
        self.state = 6

    def update_text(self, values, text):
        self.textGroup.empty()
        y = 400
        for t in text:
            textImage = values.font20.render(t, True, (0, 0, 0))
            self.textGroup.add(
                sprites.GameSprite(
                    textImage, (165, y, textImage.get_width(), textImage.get_height()), 5
                )
            )
            y += 20
        self.animating = True
        self.animationFrame = values.settings.fps * 2

    def write_input(self, values, p1Wait=False, p2Wait=False):
        if p1Wait:
            string = ''
        else:
            string = '>p1 '
            for choice in values.player1.choices:
                if len(choice) == 5:
                    string += 'move ' + choice[2] + " " + str(choice[3])
                elif len(choice) == 3:
                    string += 'move ' + choice[2]
                elif len(choice) == 2:
                    string += 'switch ' + str(choice[1])
                elif len(choice) == 1:
                    string += choice[0]
                if len(values.player1.choices) == 2 and choice == values.player1.choices[0]:
                    string += ', '
                elif len(values.player1.choices) == 1 and len(self.p1Active) == 0:
                    string += ', default'
        if p2Wait:
            string += '#'
        else:
            string += '#>p2 '
            for choice in values.player2.choices:
                if len(choice) == 5:
                    string += 'move ' + choice[2] + " " + str(choice[3])
                elif len(choice) == 3:
                    string += 'move ' + choice[2]
                elif len(choice) == 2:
                    string += 'switch ' + str(choice[1])
                elif len(choice) == 1:
                    string += choice[0]
                if len(values.player2.choices) == 2 and choice == values.player2.choices[0]:
                    string += ', '
                elif len(values.player2.choices) == 1 and len(self.p2Active) == 0:
                    string += ', default'
        f = open("input-doc.txt", "w")
        f.write(string)
        f.close()

        print("Wrote output:", string)
        print(values.player2.choices)
        values.player1.choices = []
        values.player2.choices = []
        self.doneSetup = True
        self.awaitingSimOutput = True

def is_pkmn_active(pkmn):
    return pkmn['active']

def run_js_script():
    subprocess.run(["node", "pokemon-showdown/simulatorIO.js"])
