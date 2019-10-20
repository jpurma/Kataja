try:
    from kataja.SavedField import SavedField
    from kataja.syntax.BaseConstituent import BaseConstituent

    in_kataja = True
except ImportError:
    SavedField = object
    BaseConstituent = object
    in_kataja = False


class Constituent(BaseConstituent):
    """This defines the basic linguistic competence, i.e. phrase structures and operations on phrase structure """

    def __init__(self, label='', parts=None, features=None, head=None, mover=None, checked=None, checker=None,
                 set_hosts=False, riser=None):
        features = features or []
        if in_kataja:
            super().__init__(label=label, features=features, set_hosts=set_hosts, parts=parts)
        else:
            super().__init__()
            self.label = label
            self.features = features
            self.uid = id(self)
            self.parts = parts or []
            if set_hosts:
                for feature in features:
                    feature.host = self
        self.mover = mover
        self.head = head or self
        self.checked = checked
        self.checker = checker
        self.coordinates = any(x for x in features if x.name == 'coord' or x.sign == '*')
        if riser is head:
            self.riser = self
        else:
            self.riser = riser

    def copy(self, done=None):
        if not done:
            done = {}
        if self.uid in done:
            return done[self.uid]
        other = Constituent(self.label)
        done[self.uid] = other
        other.parts = [x.copy(done=done) for x in self.parts]
        other.features = [f.copy() for f in self.features]
        other.coordinates = self.coordinates
        for feat in other.features:
            feat.host = other
        if self.head:
            if self.head is self:
                other.head = other
            else:
                other.head = self.head.copy(done=done)
        return other

    @property
    def left(self):
        if self.parts:
            return self.parts[0]

    @property
    def right(self):
        if self.parts:
            return self.parts[1]

    @property
    def checked_features(self):
        if self.checked and self.checker:
            return [(self.checked, self.checker)]
        else:
            return []

    @checked_features.setter
    def checked_features(self, value):
        if value:
            self.checked, self.checker = value[0]
        else:
            self.checked = None
            self.checker = None

    def is_riser(self):
        return self.riser

    def make_riser(self):
        self.riser = self

    def has_riser_feature(self):
        for feature in self.features:
            if feature.sign == '*':
                return feature

    def poke(self, prop):
        pass

    def get_heads(self):
        return [self.head] if self.head else []

    def __repr__(self):
        return f"{self.label} :: {' '.join([repr(f) for f in self.features])}"

    def as_tree(self):
        if self.parts:
            return f'[{self.parts[0].as_tree()} {self.parts[1].as_tree()}]'
        else:
            return self.label

    def eq(self, other):
        if other is self:
            return True
        if other is None:
            return False
        elif self.label != other.label:
            return False
        elif self.checked != other.checked:
            return False
        elif self.checker != other.checker:
            return False
        if self.head:
            if self.head is self:
                if other.head is not other:
                    return False
            elif other.head and not self.head.eq(other.head):
                return False
            elif not other.head:
                return False
        elif other.head:
            return False
        if self.features != other.features:
            return False
        return True

    if in_kataja:
        # Announce Kataja that these fields should be saved with the constituent:
        checked = SavedField('checked')
        checker = SavedField('checker')
        has_raised = SavedField('has_raised')
        head = SavedField('head')
        mover = SavedField('mover')
        coordinates = SavedField('coordinates')
        riser = SavedField('riser')
