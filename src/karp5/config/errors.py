from karp5.errors import KarpException


class KarpConfigException(KarpException):
    def __init__(self, message):
        KarpException.__init__(self, message)
