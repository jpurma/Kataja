# coding=utf-8
""" Testing if system presented in Chomsky2004 can be described in Kataja-compatible form. """


class ComputationalSystem:
    """

    :param lexicon:
    :param pf:
    :param lf:
    """

    def __init__(self, lexicon=None, pf=None, lf=None):
        self._lexicon = lexicon
        self._pf = pf
        self._lf = lf

    def Merge(self, X, Y):
        """

        :param X:
        :param Y:
        :return:
        """
        SO = SyntacticObject(X.label.copy(), (X, Y))
        return SO

    def Select(self, label):
        """

        :param label:
        """
        pass

    def Agree(self, probe, goal):
        """

        :param probe:
        :param goal:
        """
        pass

    def derive(self, N):
        """

        :param N:
        """
        pass


class Lexicon:
    """
    Here are lexical items
    """

    def __init__(self):
        self._data = {}


class LexicalItem:
    """

    :param name:
    :param features:
    """

    def __init__(self, name, features):
        self.features = features
        self.name = name


class SyntacticObject:
    """

    :param label:
    :param SOs:
    """

    def __init__(self, label, SOs=None):
        self.label = label
        self._constituents = SOs


class Label(dict):
    """ "Label selects and can be selected", so it at least contains features that can be read and compared.
    """
    pass


class ConceptualIntentionalSystem:
    """
    Here be concepts
    """

    def __init__(self):
        self.interface = None


class PhonologicalSystem:
    """
    Here be voice production
    """

    def __init__(self):
        self.interface = None

    def linearize(self, structure):
        """

        :param structure:
        """
        pass


CI = ConceptualIntentionalSystem()
SM = PhonologicalSystem()
L = Lexicon()
C_hl = ComputationalSystem(lexicon=L, pf=SM, lf=CI)
