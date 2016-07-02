try:
    from BaseFeature import BaseFeature as MyBaseClass
    in_kataja = True
except ImportError:
    MyBaseClass = object
    in_kataja = False


class FeatureSet(set):

    def contains(self, other):
        """ Alternative for hash-based containment """
        for item in self:
            if other == item:
                return True

    def has_part(self, *fparts):
        """ Find
        :param fparts:
        :return:
        """
        for fpart in fparts:
            found = False
            for f in self:
                if fpart in f:
                    found = True
                    break
            if not found:
                return False
        return True

    def get_by_part(self, fpart):
        for f in self:
            if fpart in f:
                return f

    def copy(self):
        return FeatureSet(set.copy(self))

    def __repr__(self):
        #return 'FS'+repr(sorted(self))
        return repr(sorted(self))


class Feature(MyBaseClass):
    replaces = "BaseFeature"

    def __init__(self, namestring='', counter=0, name='', value='', unvalued=False,
                 ifeature=False):
        if in_kataja:
            super().__init__(name=name, value=value, assigned=not unvalued)
        if namestring:
            if namestring.startswith('u'):
                namestring = namestring[1:]
                self.unvalued = True
                self.ifeature = False
            elif namestring.startswith('i'):
                namestring = namestring[1:]
                self.unvalued = False
                self.ifeature = True
            else:
                self.unvalued = False
                self.ifeature = False
            digits = ''
            digit_count = 0
            for char in reversed(namestring):
                if char.isdigit():
                    digits = char + digits
                    digit_count += 1
                else:
                    break
            if digit_count:
                self.counter = int(digits)
                namestring = namestring[:-digit_count]
            else:
                self.counter = 0
            self.name, part, self.value = namestring.partition(':')
        else:
            self.name = name
            self.counter = counter
            self.value = value
            self.unvalued = unvalued
            self.ifeature = ifeature

    def __repr__(self):
        parts = []
        if self.ifeature:
            parts.append('i')
        elif self.unvalued:
            parts.append('u')
        parts.append(self.name)
        if self.value:
            parts.append(':' + self.value)
        if self.counter:
            parts.append(str(self.counter))
        #return "'"+''.join(parts)+"'"
        return ''.join(parts)

    def __eq__(self, o):
        if isinstance(o, Feature):
            return self.counter == o.counter and self.name == o.name and \
                   self.value == o.value and self.unvalued == o.unvalued and \
                   self.ifeature == o.ifeature
        elif isinstance(o, str):
            return str(self) == o
        else:
            return False

    def __lt__(self, other):
        return repr(self) < repr(other)

    def __gt__(self, other):
        return repr(self) > repr(other)

    def __hash__(self):
        return hash(str(self))

    def __contains__(self, item):
        if isinstance(item, Feature):
            if item.name != self.name:
                return False
            if item.ifeature and not self.ifeature:
                return False
            if item.value and self.value != item.value:
                return False
            if item.unvalued and not self.unvalued:
                return False
            return True
        else:
            return item in str(self)

    def copy(self):
        return Feature(counter=self.counter, name=self.name, value=self.value,
                       unvalued=self.unvalued, ifeature=self.ifeature)