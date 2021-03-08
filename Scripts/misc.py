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
        self.settings = None