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
        self.is_highest = False
        self.complex_parts = []
        if not self.head:
            self.head = self

    if not in_kataja:
        def __str__(self):
            return self.as_string(set())

        def __repr__(self):
            return str(self)

    def __str__(self):
        return self.label
        #return f'{self.label}: {self.features}'

    def __repr__(self):
        return str(self)

    def as_string(self, done=None, with_id=False):
        if done is None:
            done = set()
        if self in done:
            return '...'
        done.add(self)
        id_part = f'({str(id(self))[-5:]})' if with_id else ''
        if self.parts:
            return f'[{self.parts[0].as_string(done, with_id)} {self.parts[1].as_string(done, with_id)}]{id_part}'
        else:
            return self.label + id_part

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

    def print_tree(self):
        # for f0, f1 in self.checked_features:
        #     assert isinstance(f0.host, Constituent)
        #     assert isinstance(f1.host, Constituent)
        # for f in self.features:
        #     assert isinstance(f.host, Constituent)
        # for f in self.inherited_features:
        #     assert isinstance(f.host, Constituent)
        if self.parts:
            return f'[{" ".join([part.print_tree() for part in self.parts])}]'
        else:
            return self.label

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
        is_highest = SavedField('is_highest')