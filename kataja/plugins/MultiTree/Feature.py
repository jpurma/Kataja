simple_signs = ('+', '-', '=', '_', '~', '≈', '>', '*')


class Feature:

    def __init__(self, name='Feature', sign='', value=None):
        super().__init__()
        self.name = str(name)
        self.value = value
        self.sign = sign
        # It is useful to have a fast route from a feature to lexical element where it is used.
        self.host = None
        # checks and checked_by are computed relatively from the surroundings when creating derivations, but they can
        # be set directly here when representing a state of derivation.
        self.checks = None
        self.checked_by = None

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

    @staticmethod
    def from_string(s):
        if not s:
            return
        if s[0] in simple_signs:
            sign = s[0]
            name = s[1:]
        else:
            sign = ''
            name = s
        name, sep, value = name.partition(':')  # 'case:acc' -> name = 'case', subtype = 'acc'
        return Feature(name, sign, value)
