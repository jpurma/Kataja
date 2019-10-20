try:
    from kataja.SavedField import SavedField
    from kataja.syntax.BaseFeature import BaseFeature

    in_kataja = True
except ImportError:
    SavedField = None
    BaseFeature = None
    in_kataja = False


class Feature(BaseFeature or object):
    simple_signs = ('+', '-', '=', 'u', '_', '≤', '.', '*', '(')

    def __init__(self, name='', sign='', value='', blocks=False, phasemaker=False):
        if BaseFeature:
            super().__init__(name=name, sign=sign, value=value)
        self.name = name
        self.value = value
        self.sign = sign
        self.blocks = blocks
        self.phasemaker = phasemaker
        self.used = False
        self.checks = None
        self.checked_by = None

    def __str__(self):
        return f'{"|" if self.blocks else ""}{"(" if self.phasemaker else ""}' \
               f'{self.sign}{self.name}{":" + self.value if self.value else ""}'

    def __repr__(self):
        return str(self)

    def copy(self):
        return Feature(name=self.name, sign=self.sign, value=self.value, blocks=self.blocks, phasemaker=self.phasemaker)

    def positive(self):
        return self.sign in '.+*' or self.value

    def negative(self):
        return self.sign and self.sign in '-=_'

    @classmethod
    def from_string(cls, s):
        if not s:
            return
        blocks = False
        if s[0] == '|':
            blocks = True
            s = s[1:]
        phasemaker = False
        if s[0] == '(':
            phasemaker = True
            s = s[1:]
        if s[0] in cls.simple_signs:
            sign = s[0]
            name = s[1:]
        else:
            sign = ''
            name = s
        parts = name.split(':')  # 'case:acc' -> name = 'case', subtype = 'acc'
        name = parts[0]
        value = parts[1] if len(parts) > 1 else ''
        # family = parts[2] if len(parts) > 2 else ''
        f = cls(name, sign, value, blocks, phasemaker)
        return f

    if in_kataja:
        # Announce Kataja that these fields should be saved with the feature (in addition to those in BaseFeature):
        blocks = SavedField('blocks')
        phasemaker = SavedField('phasemaker')
