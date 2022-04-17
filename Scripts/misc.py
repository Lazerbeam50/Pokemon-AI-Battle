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

        self.natures = {
            'hardy': [1, 1, 1, 1, 1],
            'lonely': [1.1, 0.9, 1, 1, 1],
            'brave': [1.1, 1, 1, 1, 0.9],
            'adamant': [1.1, 1, 0.9, 1, 1],
            'naughty': [1.1, 1, 1, 0.9, 1],

            'bold': [0.9, 1.1, 1, 1, 1],
            'docile': [1, 1, 1, 1, 1],
            'relaxed': [1, 1.1, 1, 1, 0.9],
            'impish': [1, 1.1, 0.9, 1, 1],
            'lax': [1, 1.1, 1, 0.9, 1],

            'timid': [0.9, 1, 1, 1, 1.1],
            'hasty': [1, 0.9, 1, 1, 1.1],
            'serious': [1, 1, 1, 1, 1],
            'jolly': [1, 1, 0.9, 1, 1.1],
            'naive': [1, 1, 1, 0.9, 1.1],

            'modest': [0.9, 1, 1.1, 1, 1],
            'mild': [1, 0.9, 1.1, 1, 1],
            'quiet': [1, 1, 1.1, 1, 0.9],
            'bashful': [1, 1, 1, 1, 1],
            'rash': [1, 1, 1.1, 0.9, 1],

            'calm': [0.9, 1, 1, 0.9, 1],
            'gentle': [1, 0.9, 1, 0.9, 1],
            'sassy': [1, 1, 1, 0.9, 0.9],
            'careful': [1, 1, 0.9, 0.9, 1],
            'quirky': [1, 1, 1, 1, 1]
        }

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

def split_string(fullString, maxLength):

    currentStrings = []
    outputStrings = []
    finalStrings = []
    currentLength = 0
    stringList = fullString.split(" ")

    for string in stringList:
        if (currentLength + len(string) + 1) > maxLength:
            outputStrings.append(currentStrings)
            currentStrings = [string]
            currentLength = len(string)
        else:
            currentStrings.append(string)
            currentLength += len(string) + 1
        if string is stringList[-1]:
            outputStrings.append(currentStrings)

    for cut in outputStrings:
        finalStrings.append(" ".join(cut))

    return finalStrings