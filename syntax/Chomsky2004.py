class ComputationalSystem:
    def __init__(self, lexicon, pf, lf):
        self._lexicon = lexicon
        self._pf = pf
        self._lf = lf

    def Merge(self, X, Y):
        SO = SyntacticObject(X.label.copy(), (X, Y))
        return SO

    def Select(self, label):
        pass

    def Agree(self, probe, goal):
        pass

    def derive(self, N):
        pass


class Lexicon:
    def __init__(self):
        self._data = {}


class LexicalItem:
    def __init__(self, name, features):
        self.features = features
        self.name = name


class SyntacticObject:
    def __init__(self, label, SOs=None):
        self.label = label
        self._constituents = SOs


class Label(dict):
    pass


class ConceptualIntentionalSystem:
    def __init__(self):
        self.interface = None


class PhonologicalSystem:
    def __init__(self):
        self.interface = None

    def linearize(self, structure):
        pass


CI = ConceptualIntentionalSystem()
SM = PhonologicalSystem()
C_hl = ComputationalSystem()
L = Lexicon()
