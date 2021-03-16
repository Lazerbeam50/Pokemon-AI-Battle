"""
Misc classes and functions
"""

class GameSettings:
    """
    Holds setting values
    """
    def __init__(self):
        self.fps = 30
        self.height = 720
        self.width = 1280

class ValueHolder:
    """
    Used to pass variables between functions in a single object
    """
    def __init__(self):
        self.battle = None
        self.font20 = None
        self.font16 = None
        self.player1 = 0
        self.player2 = 1
        self.settings = None
        self.state = 0
        self.team1 = 1
        self.team2 = 0
        self.teamPreviewManager = None
        self.threadRunning = False

def is_blank(x, default):
    """

    :param x: Input variable to check
    :param default: Value to return if x is a blank string
    :return: Either x or default as above
    """
    if x == "":
        return default
    else:
        return x