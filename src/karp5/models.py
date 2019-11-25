"""Domain models use by Karp5.
"""


class User:
    """Model of a User.
    """

    def __init__(self):
        pass


class Lexicon:
    """Model of a Lexicon.
    """

    def __init__(self, name: str = None, mode=None):
        self.name = name
        self.mode = mode


class Mode:
    """Model of a Mode.
    """

    def __init__(self, name: str = None):
        self.name = name
