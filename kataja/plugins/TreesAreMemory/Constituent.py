try:
    from kataja.SavedField import SavedField
    from kataja.syntax.BaseConstituent import BaseConstituent
    in_kataja = True
except ImportError:
    BaseConstituent = None
    in_kataja = False


class Constituent(BaseConstituent or object):
    """This defines the basic linguistic competence, i.e. phrase structures and operations on phrase structure """

    def __init__(self, label='', left=None, right=None, features=None, morphology=''):
        if in_kataja:
            BaseConstituent.__init__(self,
                                     label=label,
                                     parts=[left, right] if left and right else [],
                                     features=features)
        else:
            self.label = label
            self.parts = []
        # Morphology
        self.morphology = morphology

        # Relational properties
        self.left = left
        self.right = right

        # Feature set
        self.features = features or []
        for feature in self.features:
            feature.host = self

        self.inherited_features = self.features
        self.checking_features = []
        self.phase = False
        self.phase_barrier = False
        self.head = self

    def __str__(self):
        """ Readable representation of Constituent (this is what happens if you try to print Constituent or convert it
        to string) """
        if self.left and self.right:
            return f'[ {self.left} {self.right} ]'
        else:
            return self.label

    def __repr__(self):
        """ Informative representation of Constituent"""
        my_id = self.uid if in_kataja else id(self)
        if self.left and self.right:
            return f"[.{my_id} {repr(self.left)} {repr(self.right)} ]"
        elif self.morphology:
            return f"{my_id}_{self.morphology}: {self.features}"
        else:
            return f"{my_id}: {self.features}"

    @property
    def word_edge(self):
        return self.phase_barrier

    # Determines the label of a phrase structure by returning the label of the first left primitive constituent
    # i.e. HP = YP . . . H . . . ZP returns H
    def get_label(self):
        c = self
        while c.right and not c.left.is_primitive():
            c = c.right
        return c.cat()  # If we reach the bottom, then we return the label of the bottom head

    def get_head(self):
        c = self
        while c.right:
            if c.left.is_primitive():
                c = c.left
                break
            c = c.right
        return c  # If we reach the bottom, then we return the label of the bottom head

    def get_features(self):
        return self.inherited_features or self.features

    def is_primitive(self):
        return not (self.left and self.right)

    def copy(self, copy_map=None):
        """ Copy structure from this element downwards.
        If copy_map is provided (dict), a mapping from originals into new copies is built"""
        target = Constituent(label=self.label)
        if self.left:
            target.left = self.left.copy(copy_map)
        if self.right:
            target.right = self.right.copy(copy_map)

        feats = []
        for feature in self.features:
            feat = feature.copy()
            feat.host = target
            feats.append(feat)
        target.features = feats
        target.inherited_features = target.features
        if copy_map is not None:
            copy_map[self] = target
        target.phase = self.phase
        return target

    def copy_and_find(self, x):
        """ Copy tree starting from element (self), then return the copy of element x within that tree."""
        copy_map = {}
        self.copy(copy_map)
        return copy_map[x]

    # Instead of left, right, Kataja uses list of parts to store child constituents. Here we make self.left and
    # self.right to refer there.
    # These property annotations are a technique to make functions behave like instance properties.
    # We can get 'self.left' and set 'self.left = left_child', but actually they trigger these functions.

    @property
    def left(self):
        if self.parts:
            return self.parts[0]

    @left.setter
    def left(self, value):
        if self.parts:
            if in_kataja:
                # kataja tracks changes of selected fields, when mutating lists and dicts they need to be told that
                # there was a change inside, 'poke' is for that.
                self.poke('parts')
            self.parts[0] = value
            if not value and not self.parts[1]:
                self.parts = []
        else:
            self.parts = [value, None]

    @property
    def right(self):
        if self.parts:
            return self.parts[1]

    @right.setter
    def right(self, value):
        if self.parts:
            if in_kataja:
                self.poke('parts')
            self.parts[1] = value
            if not value and not self.parts[0]:
                self.parts = []
        else:
            self.parts = [None, value]

    if in_kataja:
        # Announce Kataja that these fields should be saved with the constituent:
        morphology = SavedField('morphology')
        phase = SavedField('phase')
        head = SavedField('head')
        phase_barrier = SavedField('phase_barrier')
