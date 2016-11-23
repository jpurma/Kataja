
class Feature:

    def __init__(self, value=None, name=None):
        self.name = name
        self.value = value

    def __repr__(self):
        if self.value == 'cat':
            return self.name
        elif self.value == 'sel':
            return '=' + self.name
        elif self.value == 'neg':
            return '-' + self.name
        elif self.value == 'pos':
            return '+' + self.name

    def __eq__(self, other):
        return self.value == other.value and self.name == other.name

    @staticmethod
    def from_string(s):
        if not s:
            return
        if s[0] == '=':
            value = 'sel'
            name = s[1:]
        elif s[0] == '-':
            value = 'neg'
            name = s[1:]
        elif s[0] == '+':
            value = 'pos'
            name = s[1:]
        else:
            value = 'cat'
            name = s
        return Feature(value, name)
