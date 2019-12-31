from kataja.syntax.BaseFeature import BaseFeature


class Feature(BaseFeature):
    simple_signs = ('-', '!')

    def get_shape(self):
        if not self.value:
            return 2, 2
        elif self.sign == '-':
            return 1, 1
        elif self.name == 'COMP':
            return 1, -2
        elif self.name == 'SPEC':
            return -2, 1
        else:
            return 1, 1

    def get_color_key(self):
        if not self.value:
            return 'accent1'
        elif self.sign == '-':
            return 'accent5'
        elif self.sign == '!':
            return 'accent3'
        elif self.name == 'COMP':
            return 'accent2'
        elif self.name == 'SPEC':
            return 'accent2'
        else:
            return 'accent8'
