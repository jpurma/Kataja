__author__ = 'purma'


class KatajaError(Exception):
    def __init__(self, *args):
        self.value = ':'.join([str(a) for a in args])

    def __str__(self):
        return repr(self.value)


class ForestError(Exception):
    pass


class TouchAreaError(Exception):
    pass


class UIError(Exception):
    pass
