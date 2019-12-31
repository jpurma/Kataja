try:
    from kataja.SavedField import SavedField
    from kataja.syntax.BaseFeature import BaseFeature

    in_kataja = True
except ImportError:
    SavedField = object
    BaseFeature = object
    in_kataja = False


class Feature(BaseFeature):
    simple_signs = ('+', '-', '=', '_', '~', '≈', '>', '*')

    def __init__(self, name='Feature', sign='', value=None, required=False):
        if in_kataja:
            super().__init__(name=name, sign=sign, value=value)
        else:
            self.name = str(name)
            self.value = value
            self.sign = sign
        # It is useful to have a fast route from a feature to lexical element where it is used.
        self.host = None
        # checks and checked_by are computed relatively from the surroundings when creating derivations, but they can
        # be set directly here when representing a state of derivation.
        self.checks = None
        self.checked_by = None
        self.required = required

    def __eq__(self, other):
        if other and isinstance(other, Feature):
            return self.value == other.value and self.sign == other.sign and \
                   self.name == other.name
        return False

    def copy(self, done=None):
        return Feature(name=self.name, sign=self.sign, value=self.value, required=self.required)

    def __repr__(self):
        c = '✓' if self.checks or self.checked_by else ''
        val = ':' + self.value if self.value else ''
        required = '!' if self.required else ''
        return c + self.sign + self.name + val + required

    def __str__(self):
        return repr(self)

    def __hash__(self):
        return id(self)

    @classmethod
    def from_string(cls, s):
        # print('using from_string in AmbiTree for ', s)
        s = s.strip()
        if not s:
            return
        if s[0] in cls.simple_signs:
            sign = s[0]
            name = s[1:]
        else:
            sign = ''
            name = s
        if name.endswith('!'):
            required = True
            name = name[:-1]
        else:
            required = False
        name, sep, value = name.partition(':')  # 'case:acc' -> name = 'case', subtype = 'acc'
        return cls(name, sign, value, required=required)

    if in_kataja:
        # Announce Kataja that these fields should be saved (in addition to those from BaseFeature):
        required = SavedField('required')
