"""
Handles the main loop, error reporting, and the various other state managers
"""
import pygame
import pygame.locals as pyLocals

from sys import exc_info  # needed for error reporting
import traceback  # needed for error reporting

import battle
import teampreview
import misc


class Game:
    def __init__(self):
        pygame.init()

        self.values = misc.ValueHolder()
        self.values.settings = misc.GameSettings()
        self.values.teamPreviewManager = teampreview.TeamPreviewManager()
        self.values.battle = battle.Battle()

        #Set up fonts
        self.values.font20 = pygame.font.Font("Resources/Fonts/PokemonGb-RAeo.ttf", 20)
        self.values.font16 = pygame.font.Font("Resources/Fonts/PokemonGb-RAeo.ttf", 16)

        # Set up the screen
        self.screen = pygame.display.set_mode((self.values.settings.width, self.values.settings.height))
        pygame.display.set_caption("Pokemon AI Battle")

    def main_loop(self):

        while True:

            try:
                events = pygame.event.get()

                for event in events:
                    if event.type == pyLocals.QUIT:
                        self.quit_game()
                    elif self.values.state == 0:
                        self.values.teamPreviewManager.update(self.values, event)
                    elif self.values.state == 1:
                        self.values.battle.update(self.values, event)

                if self.values.state == 0:
                    self.values.teamPreviewManager.update(self.values)

                    self.values.teamPreviewManager.surface.fill(self.values.teamPreviewManager.bgColour)

                    self.values.teamPreviewManager.group.draw(self.values.teamPreviewManager.surface)

                    self.screen.blit(self.values.teamPreviewManager.surface, (0, 0))

                elif self.values.state == 1:
                    self.values.battle.update(self.values)

                    self.values.battle.surface.fill(self.values.battle.bgColour)

                    self.values.battle.group.draw(self.values.battle.surface)

                    self.screen.blit(self.values.battle.surface, (0, 0))

                pygame.display.update()

            except Exception:
                tb = exc_info()  # return error information
                print("Error found in main loop")
                print()
                print("Error type:", tb[0])
                print("Error value:", tb[1])
                l = traceback.format_tb(tb[2])
                for line in l:
                    print(line)
                self.quit_game()  # if reactor has already started, shut down the game

    def quit_game(self):
        if self.values.threadRunning:
            f = open("quit-doc.txt", "w")
            f.write("QUIT")
            f.close()
        pygame.quit()
        raise SystemExit