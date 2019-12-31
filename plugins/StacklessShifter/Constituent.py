class Constituent:
    def __init__(self, label='', parts=None):
        self.label = label
        self.parts = parts or []
        self.features = []
        self.has_raised = False
        self.head = self
        self.uid = id(self)

    @property
    def left(self):
        if self.parts:
            return self.parts[0]

    @property
    def right(self):
        if self.parts:
            return self.parts[1]

    def poke(self, prop):
        pass

    def __repr__(self):
        return f"{self.label} :: {' '.join([repr(f) for f in self.features])}"

    def copy(self, done=None):
        if not done:
            done = {}
        if self.uid in done:
            return done[self.uid]
        other = Constituent(self.label)
        done[self.uid] = other
        other.parts = [x.copy(done=done) for x in self.parts]
        other.features = [f.copy() for f in self.features]
        if self.head:
            other.head = self.head.copy(done=done)
        return other
