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
                 set_hosts=False, result_of_em=False, sticky=None, banned=None):
        parts = parts or []
        features = features or []
        if in_kataja:
            super().__init__(label=label, parts=parts, features=features, set_hosts=set_hosts)
        else:
            super().__init__()
            self.label = label
            self.parts = parts
            self.features = features
            self.uid = id(self)
            if set_hosts:
                for feature in features:
                    feature.host = self
        self.mover = mover
        self.head = head or self
        self.checked = checked
        self.checker = checker
        self.result_of_em = result_of_em
        self.coordinates = any(x for x in features if x.name == 'coord' or x.sign == '*')
        if sticky is head:
            self.sticky = self
        else:
            self.sticky = sticky
        self.banned = banned or []

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

    def is_sticky(self):
        return self.sticky

    def make_sticky(self):
        self.sticky = self

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
        if len(self.parts) != len(other.parts):
            return False
        if self.parts:
            if not self.parts[0].eq(other.parts[0]):
                return False
            elif not self.parts[1].eq(other.parts[1]):
                return False
        return True

    def d__eq__(self, other):
        if other is None:
            return False
        if other is self:
            return True
        sd = getattr(other, '_saved', None)
        if not sd:
            return False
        return (self.label == sd.get('label') and
                self.checker == sd.get('checker') and
                self.checked == sd.get('checked') and
                self.head == sd.get('head') and
                self.features == sd.get('features') and
                self.parts == sd.get('parts')
                )

    if in_kataja:
        # Announce Kataja that these fields should be saved with the constituent:
        checked = SavedField('checked')
        checker = SavedField('checker')
        has_raised = SavedField('has_raised')
        head = SavedField('head')
        mover = SavedField('mover')
        coordinates = SavedField('coordinates')
        sticky = SavedField('sticky')
        result_of_em = SavedField('result_of_em')
        banned = SavedField('banned')
