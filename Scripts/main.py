"""
Loads the game and runs it
"""
def main():
    import game

    g = game.Game()
    g.main_loop()

if __name__ == '__main__':
    main()