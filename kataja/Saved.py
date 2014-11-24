import sys

__author__ = 'purma'


class Savable:
    """ Make the object to have internal .saved -object where saved data should go.
    Also makes it neater to check if item is Savable.
    """

    def __init__(self, unique=False):
        if unique:
            key = self.__class__.__name__
        else:
            key = str(id(self)) + self.__class__.__name__
        self.saved = Saved()
        self.saved.key = key
        sys.intern(self.saved.key)

    @property
    def save_key(self):
        return self.saved.key

    @save_key.setter
    def save_key(self, value):
        self.saved.key = value


class Saved:
    """ Everything about object that needs to be saved should be put inside instance of Saved, inside the object.
    eg. for Node instance:  self.saved.syntactic_object = ...

    This class takes care of translating the data to storage format and back.
    """

    def __init__(self):
        pass



