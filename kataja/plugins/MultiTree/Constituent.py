
try:
    from kataja.SavedField import SavedField
    from kataja.syntax.BaseConstituent import BaseConstituent
    in_kataja = True
except ImportError:
    BaseConstituent = object
    in_kataja = False


class Constituent(BaseConstituent):
    """This defines the basic linguistic competence, i.e. phrase structures and operations on phrase structure """

    def __init__(self, label='', parts=None, features=None, head=None, movers=None, checks=None, checked_by=None):
        parts = parts or []
        features = features or []
        if in_kataja:
            BaseConstituent.__init__(self, label=label, parts=parts, features=features)
        else:
            self.label = label
            self.parts = parts
            self.features = features
            self.uid = id(self)
        self.movers = movers or []
        self.head = head or self
        self.checks = checks
        self.checked_by = checked_by

    def copy(self, done=None):
        if not done:
            done = {}
        if self.uid in done:
            return done[self.uid]
        other = Constituent(self.label)
        done[self.uid] = other
        other.parts = [x.copy(done=done) for x in self.parts]
        other.features = [f.copy() for f in self.features]
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
    def left(self):
        if self.parts:
            return self.parts[0]

    @property
    def right(self):
        if self.parts:
            return self.parts[1]

    @property
    def checked_features(self):
        if self.checks and self.checked_by:
            return [(self.checks, self.checked_by)]
        else:
            return []

    @checked_features.setter
    def checked_features(self, value):
        if value:
            self.checks, self.checked_by = value[0]
        else:
            self.checks = None
            self.checked_by = None

    def poke(self, prop):
        pass

    def get_heads(self):
        return [self.head] if self.head else []

    def __repr__(self):
        return f"{self.label} :: {' '.join([repr(f) for f in self.features])}"

    if in_kataja:
        # Announce Kataja that these fields should be saved with the constituent:
        checks = SavedField('checks')
        checked_by = SavedField('checked_by')
        has_raised = SavedField('has_raised')
        head = SavedField('head')
        movers = SavedField('movers')
