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
                 set_hosts=False, riser=None, specs=None, comps=None):
        features = features or []
        if in_kataja:
            super().__init__(label=label, features=features, set_hosts=set_hosts)
        else:
            super().__init__()
            self.label = label
            self.features = features
            self.uid = id(self)
            if set_hosts:
                for feature in features:
                    feature.host = self
        self.specs = specs or []
        self.comps = comps or []
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
        other.specs = [x.copy(done=done) for x in self.specs]
        other.comps = [x.copy(done=done) for x in self.comps]
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

    # These methods have no syntactic functions, they are here for Kataja compatibility
    @property
    def parts(self):
        if self.riser and self.riser is not self:
            riser = [self.riser]
        else:
            riser = []
        if self.head and self.head is not self:
            head = [self.head]
        else:
            head = []
        specs = self.specs or []
        comps = self.comps or []
        # print([riser, specs, head, comps])
        return specs + head + comps
        # return riser + specs + head + comps

    @parts.setter
    def parts(self, value):
        pass

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
        if len(self.specs) != len(other.specs):
            return False
        if self.specs:
            if not self.specs[0].eq(other.specs[0]):
                return False
            elif not self.specs[1].eq(other.specs[1]):
                return False
        if len(self.comps) != len(other.comps):
            return False
        if self.comps:
            if not self.comps[0].eq(other.comps[0]):
                return False
            elif not self.comps[1].eq(other.comps[1]):
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
        specs = SavedField('specs')
        comps = SavedField('comps')
