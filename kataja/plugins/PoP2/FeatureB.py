try:
    from kataja.syntax.BaseFeature import BaseFeature as MyBaseClass
    from kataja.SavedField import SavedField
    in_kataja = True
except ImportError:
    MyBaseClass = object
    in_kataja = False


def has_part(fset, *fparts):
    """ Find
    :param fparts:
    :return:
    """
    for fpart in fparts:
        found = False
        for f in fset:
            if fpart in f:
                found = True
                break
        if not found:
            return False
    return True


def get_by_part(fset, fpart):
    for f in fset:
        if fpart in f:
            return f


# It would make sense visually if unvalued features are paired with value-giving features instead
#  of just replacing them. valued_by would be this reference.

class Feature(MyBaseClass):
    role = "Feature"

    def __init__(self, namestring='', counter=0, name='', value='', unvalued=False,
                 ifeature=False, valued_by=None, inactive=False):
        if in_kataja:
            super().__init__(name=name, value=value)
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
            self.valued_by = None
            self.inactive = inactive
        else:
            self.name = name
            self.counter = counter
            self.value = value
            self.unvalued = unvalued
            self.ifeature = ifeature
            self.valued_by = None
            self.inactive = inactive

    def __str__(self):
        return repr(self)

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
        if self.valued_by:
            parts.append('(%s)' % self.valued_by)
        #return "'"+''.join(parts)+"'"
        return ''.join(parts)

    def get_parts(self):
        """ This is what Kataja uses to find if there is inner structure/links to other nodes to
        display. Use it here for valued_by -relation.

        :return:
        """
        return self.valued_by or []


    def __eq__(self, o):
        if isinstance(o, Feature):
            return self.counter == o.counter and self.name == o.name and \
                   self.value == o.value and self.unvalued == o.unvalued and \
                   self.ifeature == o.ifeature and self.valued_by == o.valued_by
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
        """ This doesn't look into linked features, you should be looking into them first
        (use expanded_features -function in Constituent to get all of them)
        :param item:
        :return:
        """
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

    def unvalued_and_alone(self):
        return self.unvalued and not self.valued_by

    def value_with(self, other):
        assert other is not self
        if self.valued_by:
            self.valued_by.append(other)
        else:
            self.valued_by = [other]

    def expand_linked_features(self):
        if self.valued_by:
            flist = []
            for f in self.valued_by:
                flist += f.expand_linked_features()
            return flist
        else:
            return [self]

    def match(self, name=None, value=None, u=None, i=None, phi=None):
        if isinstance(name, list):
            if self.name not in name:
                return None
        elif name is not None and self.name != name:
            return None
        elif value is not None and self.value != value:
            return None
        elif u is not None and self.unvalued != u:
            return None
        elif i is not None and self.ifeature != i:
            return None
        elif phi and self.name not in ("Person", "Number", "Gender"):
            return None
        return True

    def copy(self):
        return Feature(counter=self.counter, name=self.name, value=self.value,
                       unvalued=self.unvalued, ifeature=self.ifeature, valued_by=valued_by)

    if in_kataja:
        unvalued = SavedField("unvalued")
        ifeature = SavedField("ifeature")
        counter = SavedField("counter")
        valued_by = SavedField("valued_by")
        inactive = SavedField("inactive")
        # rest are same as in BaseFeature