class XBar:
    """This is for storing a head, its specs and its complements in one structure. This way it is simpler for parser
    to take structures where a head has several specs and complements but in different order as one. One XBar can be
    used to represent all possible spec-head-complement combinations the parser can come up with for a specific head.
    Then it is trivial to turn XBar back into binary constituents."""

    def __init__(self, label='', features=None, movers=None,
                 risers=None, specs=None, comps=None, unjustified=None):
        self.features = features or []
        self.label = label
        self.uid = id(self)
        for feature in features:
            feature.host = self
        self.specs = specs or []
        self.comps = comps or []
        self.unjustified = unjustified or []
        self.movers = movers or set()
        self.risers = risers or set()

    def copy(self):
        """ Non-recursive copy, doesn't copy connections to other XBars. Features will be copied. Intended to be used
        for picking several instances from lexicon (e.g. when 'the' is picked second time, it will be different 'the'
        than the first one. """
        return XBar(label=self.label, features=[f.copy() for f in self.features])

    def __lt__(self, other):
        if other is None:
            return False
        return self.label < other.label

    def __repr__(self):
        return self.label
    # def __repr__(self):
    #    return f"{self.label} :: {' '.join([repr(f) for f in self.features])}"
