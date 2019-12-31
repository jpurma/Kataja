try:
    from kataja.syntax.BaseConstituent import BaseConstituent
    from kataja.SavedField import SavedField

    in_kataja = True
except ImportError:
    SavedField = None
    BaseConstituent = None
    in_kataja = False


class Constituent(BaseConstituent or object):
    nodecount = 0

    def __init__(self, label='', features=None, parts=None, argument=None, head=None, lexical_heads=None,
                 set_hosts=False, checked_features=None):
        if BaseConstituent:
            super().__init__(label, parts=parts, features=features, head=head, lexical_heads=lexical_heads,
                             checked_features=checked_features or ())
        else:
            self.label = label
            self.features = list(features) if features else []
            self.checked_features = checked_features or ()
            self.parts = parts or []
            self.inherited_features = self.features
            self.head = head
            if set_hosts and features:
                for feature in features:
                    feature.host = self
        self.argument = argument

    if not in_kataja:
        def __str__(self):
            return self.as_string(done=set())

        def as_string(self, done):
            if self in done:
                return '...'
            done.add(self)
            if self.parts:
                return f'[{self.parts[0].as_string(done)} {self.parts[1].as_string(done)}]'
            else:
                return repr(self.label)

        def __repr__(self):
            return str(self)

    @property
    def left(self):
        if self.parts:
            return self.parts[0]

    @property
    def right(self):
        if self.parts:
            return self.parts[1]

    def get_heads(self):
        if isinstance(self.head, Constituent):
            return [self.head]
        elif self.head:
            return self.head
        return []

    def get_features(self):
        if self.features:
            return self.features
        else:
            return self.inherited_features

    def first_label(self):
        if self.parts:
            return self.parts[0].first_label()
        else:
            return self.label

    def is_wh(self):
        return self.wh

    def copy(self, done=None):
        """ Does not copy parts, this is intended only for picking words from lexicon"""
        other = Constituent(self.label)
        other.features = [f.copy() for f in self.features]
        for feature in other.features:
            feature.host = other
        other.head = other
        return other

    if in_kataja:
        argument = SavedField('argument')
        wh = SavedField('wh')
