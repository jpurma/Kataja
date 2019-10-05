# coding=utf-8

# Implementation of formalisation in
# Chris Collins and Edward Stabler (2016) A Formalization of Minimalist Syntax. Syntax 19:1 March
#  2016, 43-78
#


class UniversalGrammar:
    def __init__(self, phon_f=None, syn_f=None, sem_f=None):
        """ Definition 1: Universal Grammar is a 6-tuple: (PHON-F, SYN-F, SEM-F, Select, Merge,
        Transfer)
        """
        self.phon = phon_f or {}
        self.syn = syn_f or {}
        self.sem = sem_f or {}
        # Select, Merge and Transfer are defined as methods

    def Select(self, a, stage):
        """ Definition 12: Let S be a stage in derivation S = (LA, W). If lexical token A
        \in LA, then select(A, S) = (LA - {A}, W \cup {A})
        :return:
        """
        s = stage.copy()
        if a in s.la:
            s.la.remove(a)
            s.w.add(a)
        else:
            raise NotImplementedError

    def Merge(self, a, b):
        """ Definition 13: Given any two distinct syntactic objects A, B, Merge(A, B) = {A, B}
        :param a:
        :param b:
        :return:
        """
        if a is not b:
            return {a, b}
        else:
            return NotImplemented

    def Transfer(self):
        pass


class LI:
    def __init__(self, sem=None, syn=None, phon=None):
        """ Definition 2: A lexical item is a triple LI = (SEM, SYN, PHON) """
        self.sem = sem or {}
        self.syn = syn or {}
        self.phon = phon or {}

    def copy(self):
        copy = LI()
        for key, value in self.sem.items():
            copy.sem[key] = value.copy()
        for key, value in self.syn.items():
            copy.syn[key] = value.copy()
        for key, value in self.phon.items():
            copy.phon[key] = value.copy()
        return copy

    def __eq__(self, other):
        return self.sem == other.sem and self.syn == other.syn and self.phon == other.phon


class Lexicon:
    def __init__(self, lexicon=None):
        """ Definition 3: A lexicon is a finite set of lexical items
        :param lexicon:
        """
        self.d = lexicon or {}


class ILanguage:
    def __init__(self, lex=None, ug=None):
        """ Definition 4: An I-language is a pair (Lex, UG) where Lex is a lexicon and UG is
        Universal Grammar
        :param lex:
        :param ug:
        """
        self.lex = lex or Lexicon()
        self.ug = ug or UniversalGrammar()


class LIToken:
    def __init__(self, li=None, k=0):
        """ Definition 5: A lexical item token is a pair (LI, k) where LI is a lexical item and k
        is an integer.
        :param li:
        :param k:
        """
        self.li = li or LI()
        self.k = k

    def copy(self):
        copy = LIToken()
        copy.li = self.li.copy()
        copy.k = self.k
        return copy


class LexicalArray:
    def __init__(self, li_tokens=None):
        """ Definition 6: A lexical array (LA) is a finite set of lexical item tokens
        :param li_tokens:
        """
        self.l = li_tokens or []

    def copy(self):
        copy = LexicalArray()
        for token in self.l:
            copy.l.append(token.copy())
        return copy


def is_syntactic_object(x):
    """Definition 7: X is a syntactic object iff (i) X is a lexical item token, or (ii) X is a
    set of syntactic objects """
    return isinstance(x, LIToken) or (
            isinstance(x, set) and all([isinstance(y, LIToken) for y in x]))


def immediately_contains(a, b):
    """ Definition 8: Let A and B be syntactic objects, then B immediately contains A iff A
    \in B.
    :param a:
    :param b:
    :return:
    """
    return a is b or isinstance(b, set) and a in b


def contains(a, b):
    """ Definition 9: Let A and B be syntactic objects, then B contains A iff (i) B immediately
    contains A, or (ii) for some syntactic object C, B immediately contains C and C contains A.
    :param a:
    :param b:
    :return:
    """
    if immediately_contains(a, b):
        return True
    if isinstance(b, set):
        for c in b:
            if contains(a, c):
                return True
    return False


def position(a, in_b):
    """ Definition 16: The position of SO_n in SO_1 is a path, a sequence of syntactic objects (
    SO_1, SO_2, ...., SO_n) where for all 0 < i < n, SO_i+1 \in SO_i.
    Definition 17: B occurs in A at position P iff P = (A,... ...,B).

    :param a:
    :param in_b:
    :return:
    """

    def add_path(item):
        if a == item:
            return True
        elif contains(a, item):
            path.append(item)
            if isinstance(item, set):
                for i in item:
                    if add_path(i):
                        break
        return False

    path = []
    add_path(in_b)

    # return path

    def check_path(item):
        if a == item:
            return True
        elif isinstance(item, set):
            path.append(item.copy())
            found = False
            for i in item:
                if add_path(i):
                    found = True
                if not found:
                    pass

        return False

    path = []
    check_path(in_b)


class Stage:
    def __init__(self, la=None, w=None):
        """ Definition 10: A stage is a pair S = (LA, W), where LA is a lexical array and W is a
        set of syntactic objects. We call W the workspace of S.
        :param la:
        :param w:
        """
        self.la = la or LexicalArray()
        self.w = w or {}

    def is_root(self, x):
        """ Definition 11: For any syntactic object X and any stage S = (LA, W) with workspace W,
        if X \in W, X is a root in W.
        :param x:
        :return:
        """
        return x in self.w

    def copy(self):
        copy = Stage()
        copy.la = self.la.copy()
        for item in self.w:
            copy.w.add(item.copy())
        return copy


class Derivation:
    def __init__(self, lexicon=None, stages=None, ug=None):
        self.stages = stages or []
        self.lexicon = lexicon or Lexicon()
        self.ug = ug or UniversalGrammar()

    def is_legit(self):
        """ Definition 14: A derivation from lexicon L is a finite sequence of stages (S_1,
        ... S_n), for n >= 1, where each S_i = (LA_i, W_i)
        I hope this is kind of checking is not necessary. Uncertain if I got this right.
        :return:
        """
        # (i) For all LI and k such that (LI. k) \in LA_1, LI \in L
        if not self.stages:
            return False
        stage1 = self.stages[0]
        for li_token in stage1.la:
            if li_token.li not in self.lexicon:
                return False
        # (ii) W_1 = {}
        if stage1.w:
            return False
        # (iii) for all i, such that 1 =< i < n, either
        # (derive-by-Select) for some A \in LA_i, (LA_i+1, W_i+1) = Select(A, (LA_i, W_i)), or
        prev_stage = None
        for stage in self.stages:
            if not prev_stage:
                prev_stage = stage
                continue
            derive_by_select = False
            derive_by_merge = False
            for item in prev_stage.la:
                if self.ug.Select(item, prev_stage) == stage:
                    derive_by_select = True
                    break
            if not derive_by_select:
                # (derive-by-Merge) LA_i, = LA_i+1 and the following conditions hold for some A, B:
                # (a) A \in W_i,
                # (b) either A contains B or W_i, immediately contains B, and
                # (c) W_i+1 = (W_i - {A, B}) \cup {Merge(A, B)}.
                if prev_stage.la != stage.la:
                    return False
                B = None
                for A in prev_stage.w:
                    for B in prev_stage.w:
                        if A is not B and self.ug.Merge(A, B) in stage.w:
                            # external merge -- two items in workspace got merged
                            derive_by_merge = True
                            break
                # inspect pairs created by merge at the latest stage.
                for pair in stage.w:
                    if isinstance(pair, set) and len(pair) == 2:
                        alpha, beta = pair
                        # two root nodes are merged:
                        if alpha in prev_stage.w and beta in prev_stage.w:
                            derive_by_merge = True
                            break
                        # another of merged nodes has to be a root node
                        elif alpha in prev_stage.w:
                            A = alpha
                        elif beta in prev_stage.w:
                            A = beta
                        else:
                            continue
                        # either internal merge or external merge
                        if contains(B, A) or immediately_contains(prev_stage.w, B):
                            # merged elements shouldn't exist on their own anymore
                            if A not in stage.w and B not in stage.w:
                                derive_by_merge = True
                                break
                if not (derive_by_select or derive_by_merge):
                    return False
            prev_stage = stage
        return True
