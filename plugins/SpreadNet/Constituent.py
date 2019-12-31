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

    def __init__(self, label='', parts=None, features=None, movers=None,
                 set_hosts=False, stickies=None, specs=None, comps=None, unjustified=None):
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
        self.unjustified = unjustified or []
        self.movers = movers or set()
        self.stickies = stickies or set()

    def copy(self, done=None):
        if not done:
            done = {}
        if self.uid in done:
            return done[self.uid]
        other = Constituent(self.label)
        done[self.uid] = other
        other.specs = [x.copy(done=done) for x in self.specs]
        other.comps = [x.copy(done=done) for x in self.comps]
        other.unjustified = [x.copy(done=done) for x in self.unjustified]
        other.movers = {x.copy(done=done) for x in self.movers}

        other.features = [f.copy() for f in self.features]
        for feat in other.features:
            feat.host = other
        return other

    # These methods have no syntactic functions, they are here for Kataja compatibility
    @property
    def parts(self):
        stickies = self.stickies or []
        specs = self.specs or []
        comps = self.comps or []
        return stickies + specs + comps

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
        return [(checker, checked) for checker, checked, target in self.specs] + \
               [(checker, checked) for checker, checked, target in self.comps]

    @checked_features.setter
    def checked_features(self, value):
        pass

    def poke(self, prop):
        pass

    def get_heads(self):
        return []

    def __repr__(self):
        return f"{self.label} :: {' '.join([repr(f) for f in self.features])}"

    def eq(self, other):
        if other is self:
            return True
        if other is None:
            return False
        elif self.label != other.label:
            return False
        if self.features != other.features:
            return False
        return True

    if in_kataja:
        # Announce Kataja that these fields should be saved with the constituent:
        movers = SavedField('movers')
        stickies = SavedField('stickies')
        specs = SavedField('specs')
        comps = SavedField('comps')
