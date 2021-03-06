import pygame
import pygame.locals as pyLocals

from sys import exc_info #needed for error reporting
from threading import Thread
import traceback #needed for error reporting
import subprocess

def read_output(frame):
    if frame == 0:
        f = open("output-doc.txt", "r")
        lines = f.readlines()
        if lines:
            for line in lines:
                print(line)
            f = open("output-doc.txt", "w")
            f.write("")
            f.close()

def write_input(p1, p2):
    f = open("input-doc.txt", "w")
    f.write(p1 + "#" + p2)
    f.close()

def run_js_script():
    subprocess.run(["node", "pokemon-showdown/simulatorIO.js"])

def quit_game():
    pygame.quit()
    #myThread.join()
    f = open("quit-doc.txt", "w")
    f.write("QUIT")
    f.close()
    raise SystemExit

pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Pokemon AI Battle")

FPSclock = pygame.time.Clock()
frame = 0

myThread = Thread(target=run_js_script)
myThread.start()

while True:

    try:
        events = pygame.event.get()

        for event in events:
            if event.type == pyLocals.QUIT:
                quit_game()
            elif event.type == pyLocals.MOUSEBUTTONUP:
                write_input(">p1 move 1 1, move 1 2", ">p2 move 1 1, move 1 2")

        read_output(frame)

        pygame.display.update()

        FPSclock.tick(30)
        if frame == 29:
            frame = 0
        else:
            frame += 1

    except Exception:
        tb = exc_info()  # return error information
        print("Error found in main loop")
        print()
        print("Error type:", tb[0])
        print("Error value:", tb[1])
        l = traceback.format_tb(tb[2])
        for line in l:
            print(line)
        quit_game()

