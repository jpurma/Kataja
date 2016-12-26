
class Feature:
    """ Minimal syntactic feature implementation """

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        s = [str(self.name)]
        if self.value:
            s.append(str(self.value))
        return ":".join(s)

    def __eq__(self, other):
        if other:
            return self.value == other.value and self.name == other.name
        return False

    def copy(self):
        return self.__class__(self.name, self.value)

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
        name, foo, bar = name.partition(':')  # 'case:acc' -> name = 'case', family = 'acc'
        return Feature(name, value)
