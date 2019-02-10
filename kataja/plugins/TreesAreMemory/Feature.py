try:
    from kataja.SavedField import SavedField
    from kataja.syntax.BaseFeature import BaseFeature
    in_kataja = True
except ImportError:
    BaseFeature = None
    in_kataja = False

simple_signs = ('+', '-', '=', 'u', '_', '←', '.', '*', '!', '|', ')')


class Feature(BaseFeature or object):

    def __init__(self, name='', sign='', value=''):
        if BaseFeature:
            super().__init__(name=name, sign=sign, value=value)
        self.name = name
        self.value = value
        self.sign = sign
        self.has_initiative = None
        self.positive = True
        self.leads = True
        self.leads_other = False
        self.blocks = None
        self.goes_left = None
        self.is_phasemaker = False
        self.expires_in_use = True
        self.expires_other = True
        self.phase_barrier = False
        self.used = False
        self.checks = None
        self.checked_by = None
        self.evaluate_properties()

    def __str__(self):
        return f'{self.sign}{self.name}{":" + self.value if self.value else ""}'

    def __repr__(self):
        return str(self)

    def copy(self):
        other = Feature(name=self.name, sign=self.sign, value=self.value)
        other.evaluate_properties()
        return other

    def is_satisfied(self):
        if self.positive and self.checks and self.expires_in_use:
            return True
        elif (not self.positive) and self.checked_by and self.expires_in_use:
            return True
        return False

    def evaluate_properties(self):
        # default properties when sign is empty, e.g == ''
        self.goes_left = False
        self.leads = True
        self.leads_other = False
        self.expires_in_use = True
        self.expires_other = True
        self.has_initiative = True
        self.positive = True
        self.blocks = False
        self.phase_barrier = False
        for char in reversed(self.sign):
            if char == '-':
                self.leads = False
                self.positive = False
                self.goes_left = True
                self.has_initiative = False
            elif char == '=':
                self.goes_left = True
                self.positive = False
                self.has_initiative = False
                self.leads_other = True
            elif char == '!':
                self.has_initiative = True
            elif char == '+':
                self.expires_in_use = False
            elif char == '.':
                self.expires_other = False
            elif char == '←':
                self.goes_left = True
            elif char == '|':
                self.blocks = True
            elif char == ')':
                self.phase_barrier = True

    def get_shape(self):
        if self.positive:
            if self.checks:
                if self.checks.goes_left:
                    return 2, 1
                return 1, 2
            elif self.goes_left:
                return 1, 2
            else:
                return 2, 1
        if self.goes_left:
            return 1, -2
        else:
            return -2, 1


    @staticmethod
    def from_string(s):
        if not s:
            return
        sign = []
        for letter in s:
            if letter in simple_signs:
                sign.append(letter)
        name = s[len(sign):]
        sign = ''.join(sign)
        parts = name.split(':')  # 'case:acc' -> name = 'case', subtype = 'acc'
        name = parts[0]
        value = parts[1] if len(parts) > 1 else ''
        f = Feature(name, sign, value)
        return f

    if in_kataja:
        # Announce Kataja that these fields should be saved with the feature (in addition to those in BaseFeature):
        blocks = SavedField('blocks')
        has_initiative = SavedField('has_initiative')
        leads = SavedField('leads')
        goes_left = SavedField('goes_left')
        expires_in_use = SavedField('expires_in_use')
        positive = SavedField('positive')
