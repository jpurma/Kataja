
class Feature:
    """ This implementation of mgtdb Features has one important difference from features as
    presented by Stabler,
    """

    def __init__(self, value='', name=''):
        self.value = value
        self.name = name

    def __repr__(self):
        if self.value == 'cat':
            return self.name
        elif self.value == 'sel':
            return '=' + self.name
        elif self.value == 'neg':
            return '-' + self.name
        elif self.value == 'pos':
            return '+' + self.name
        else:
            return self.value + self.name

    def __eq__(self, other):
        if other:
            return self.value == other.value and self.name == other.name
        else:
            return False

    @staticmethod
    def from_string(s):
        if not s:
            return
        if s[0] in '-=+':
            value = s[0]
            name = s[1:]
        else:
            value = ''
            name = s
        return Feature(value, name)
