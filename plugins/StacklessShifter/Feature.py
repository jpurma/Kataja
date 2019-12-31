

class Feature:
    simple_signs = ('+', '-', '=', '_', '~', '≈', '>')

    def __init__(self, name='Feature', sign='', value=None):
        super().__init__()
        self.name = str(name)
        self.value = value
        self.sign = sign
        # status of being checked, checking something and being in use could be deduced online,
        # based on feature's surroundings, but it is cheaper to store them.
        self.checks = None
        self.checked_by = None
        # It is useful to have a fast route from a feature to lexical element where it is used.
        self.host = None

    def check(self, other):
        self.checks = other
        other.checked_by = self

    def __eq__(self, other):
        if other and isinstance(other, Feature):
            return self.value == other.value and self.sign == other.sign and \
                   self.name == other.name
        return False

    def copy(self):
        return Feature(name=self.name, sign=self.sign, value=self.value)

    def __repr__(self):
        c = '✓' if self.checks or self.checked_by else ''
        val = ':' + self.value if self.value else ''
        return c + self.sign + self.name + val

    @classmethod
    def from_string(cls, s):
        if not s:
            return
        if s[0] in cls.simple_signs:
            sign = s[0]
            name = s[1:]
        else:
            sign = ''
            name = s
        name, sep, value = name.partition(':')  # 'case:acc' -> name = 'case', subtype = 'acc'
        return cls(name, sign, value)
