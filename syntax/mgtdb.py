"""
file: mgtdb.py
    Modified from E. Stabler's minimalist grammar top-down beam recognizer,
      https://github.com/epstabler/mgtdb
      https://github.com/epstabler/mgtdb/blob/master/python/mgtdbp.py

    The aim of this modification is to turn recognizer into something that is
    a) Easier to read for people like me who are more accustomed to declarative languages.
    b) Compatible with Kataja's assumptions of syntax, so that Kataja can be used to replay the
    derivation

    Some computational efficiency will be lost in the process, as tuples are turned into classes.
    This code is part of Kataja, but really, see E. Stabler's original work in github and this:

    Stabler, E. P. (2013). Two models of minimalist, incremental syntactic analysis.
    Topics in Cognitive Science, 5(3), 611-633.

    jpurma
"""
import heapq
import time

"""
Example grammar, in a format fairly easy for humans
"""
mg0 = [([], [('selects', 'V'), ('category', 'C')]),
       ([], [('selects', 'V'), ('positive', 'wh'), ('category', 'C')]),
       (['the'], [('selects', 'N'), ('category', 'D')]),
       (['which'], [('selects', 'N'), ('category', 'D'), ('negative', 'wh')]),
       (['king'], [('category', 'N')]),
       (['queen'], [('category', 'N')]),
       (['wine'], [('category', 'N')]),
       (['beer'], [('category', 'N')]),
       (['drinks'], [('selects', 'D'), ('selects', 'D'), ('category', 'V')]),
       (['prefers'], [('selects', 'D'), ('selects', 'D'), ('category', 'V')]),
       (['knows'], [('selects', 'C'), ('selects', 'D'), ('category', 'V')]),
       (['says'], [('selects', 'C'), ('selects', 'D'), ('category', 'V')])]
"""
   We represent the lexicon as a tree,
   where the tree is a list, where the first element is the root,
   and the rest is the list of the subtrees.

    [[Feature("category", "C"), [Feature("selects", "V"), []],
    [Feature("positive", "wh"), [Feature("selects", "V"), []]]],
    [Feature("category", "D"), [Feature("selects", "N"), ['the']]],
    [Feature("negative", "wh"), [Feature("category", "D"), [Feature("selects", "N"), ['which']]]],
    [Feature("category", "N"), ['king'], ['queen'], ['wine'], ['beer']],
    [Feature("category", "V"), [Feature("selects", "D"), [Feature("selects", "D"), ['drinks'],
        ['prefers']],
    [Feature("selects", "C"), ['knows'], ['says']]]]]

    [[(0, 1), [(1, 0), []],
    [(3, 2), [(1, 0), []]]],
    [(0, 4), [(1, 3), ['the']]],
    [(2, 2), [(0, 4), [(1, 3), ['which']]]],
    [(0, 3), ['king'], ['queen'], ['wine'], ['beer']],
    [(0, 0), [(1, 4), [(1, 4), ['drinks'], ['prefers']],
    [(1, 1), ['knows'], ['says']]]]]


"""

ftypes = ['category', 'selects', 'negative', 'positive']

class Feature:
    def __init__(self, type, value, known_feature_values=None):
        self.type = type
        self.value = value

        # have integers to represent feature type and value for faster comparisons.
        self.int_type = ftypes.index(type) # temporarily, it is ok to raise error here.
        # We need a better way to deal with missing types anyways
        if known_feature_values is None:
            self.int_value = hash(self.value)  # this will do, but output can be brutal :)
        elif value not in known_feature_values:
            known_feature_values.append(value)
        self.int_value = known_feature_values.index(value)

    def __eq__(self, other):
        if isinstance(other, Feature):
            return self.int_type == other.int_type and self.int_value == other.int_value
        else:
            return False

    def __str__(self):
        return 'Feature(%s, %s)' % (self.type, self.value)

    def __repr__(self):
        return 'Feature("%s", "%s")' % (self.type, self.value)

    def __lt__(self, other):
        if isinstance(other, Feature):
            return (self.int_type, self.int_value) < (other.int_type, other.int_value)
        elif isinstance(other, str):  # emulate python2's behavior for tuple < str -evaluation
            return False
        else:
            return (self.int_type, self.int_value) < other

    def __gt__(self, other):
        if isinstance(other, Feature):
            return (self.int_type, self.int_value) > (other.int_type, other.int_value)
        elif isinstance(other, str):  # emulate python2's behavior for tuple > str -evaluation
            return True
        else:
            return (self.int_type, self.int_value) > other


class LexItem:
    def __init__(self, words, features):
        self.words = words
        self.features = features
        self.reversed_features = list(reversed(self.features))


class IndexedCategory:
    """ Rename those h, m, hx, mx you know what they mean. :(
    """
    def __init__(self, h, m, hx, mx):
        self.h = h
        self.m = m
        self.hx = hx
        self.mx = mx

    def __gt__(self, other):
        return (self.h, self.m, self.hx, self.mx) > other

    def __lt__(self, other):
        return (self.h, self.m, self.hx, self.mx) < other


class IQueue:
    def __init__(self, item):
        if isinstance(item, IQueue):
            self._q = item._q[:]
        elif isinstance(item, list):
            self._q = item
            heapq.heapify(self._q)
        else:
            self._q = [item]
            heapq.heapify(self._q)

    def __gt__(self, other):
        return self._q > other

    def __lt__(self, other):
        return self._q < other

    def __len__(self):
        return len(self._q)

    def heappop(self):
        return heapq.heappop(self._q)

    def heappush(self, val):
        heapq.heappush(self._q, val)

    def copy(self):
        return IQueue(self)


class DerivationQueue(IQueue):

    def copy(self):
        return DerivationQueue(self)


def member_has_feature_value(i, lst):
    for e in lst:
        if e[0].int_value == i:
            return e
    return None


def min_index(ic):
    """
    min_index should only check indices of filled mover positions.
    No mover has an empty index, so we can ignore them.
    """
    min_x = ic.hx
    for x in ic.mx:
        if x and x < min_x:
            min_x = x
    return min_x


def terminals_of(ts):
    terms = []
    nonterms = []
    for t in ts:
        if t and isinstance(t[0], Feature):
            nonterms.append(t)
        else:
            terms.append(t)
    return terms, nonterms


class Grammar:
    def __init__(self, lex):
        self.min_p = 0.001
        self.lex_items = []
        self.known_feature_values = []
        self.expansions = []
        self.lex_array = []

        # prepare lexicon to have LexItems with Features, and while in it, collect all of the
        # values that features can take into 'known_feature_values'.
        for words, features in lex:
            feature_items = []
            for type, value in features:
                f = Feature(type, value, self.known_feature_values)
                feature_items.append(f)
            li = LexItem(words, feature_items)
            self.lex_items.append(li)

        lex_trees = []
        for lex_item in self.lex_items:
            self.add_to_lex_tree(lex_item, lex_trees)

        # We put those lexTrees in order, so that the subtree
        # with root type (i,j) appears in lA[j] and has feature type tA[j]=i.
        self.lex_array = [[]] * len(self.known_feature_values)
        for root, *rest in lex_trees:
            if isinstance(root, Feature):
                j = root.int_value
                self.lex_array[j] = rest
        # it could be more readable as a dict, see how it is used in actual derivation.

    @staticmethod
    def add_to_lex_tree(lex_item, lex_trees):
        for feature in lex_item.reversed_features:
            # find root
            found = False
            for tree in lex_trees:
                if isinstance(tree, list) and tree and tree[0] == feature:
                    lex_trees = tree
                    found = True
                    break
            if not found:
                # ...[feature, [feature, [feature...
                lex_trees.append([feature])
                lex_trees = lex_trees[-1]
        # now the tree is as deep as it can get, each feature has added one level of depth.
        # finally add the words -list as a leaf
        # ... [feature, [words]]
        lex_trees.append(lex_item.words)

    def recognize(self, start, min_p, input_string):  # initialize and begin
        """
        inpt0=['the','king','knows','which','wine','the','queen','prefers']
        recognize(mg0,'C',0.001,inpt0)

        inpt0=['the','king','knows','which','queen','prefers','the','wine']
        recognize(mg0,'C',0.001,inpt0)

        inpt0=['the','queen','says','the','king','knows','which','queen','prefers','the','wine']
        recognize(mg0,'C',0.001,inpt0)
        """
        self.min_p = min_p
        start_int = self.known_feature_values.index(start)
        h = self.lex_array[start_int]
        n = len(self.known_feature_values)
        m = [[]] * n
        mx = [[]] * n
        ic = IndexedCategory(h, m, [], mx)
        iq = IQueue(([], ic))
        self.derivations = DerivationQueue((-1.0, input_string, iq))
        t0 = time.time()
        result = self.derive()
        print(time.time() - t0, "seconds:", result)

    def derive(self):  # eliminate the recursion here?
        # p = 1.0
        while self.derivations:
            (p, input_string, iq) = self.derivations.heappop()
            print('# of parses in beam=', len(self.derivations) + 1, ', p(best parse)=', (-1 * p))
            if iq:
                prediction = iq.heappop()
                ic = prediction[1]
                self.expansions = []
                self.add_expansions(input_string, ic)
                if not self.expansions:
                    return self.derive()
                else:
                    new_p = p / float(len(self.expansions))
                    if new_p < self.min_p:
                        self.insert_new_parses(p, new_p, iq)
                    else:
                        print('improbable parses discarded')
            elif not input_string:
                return True  # success!
        return False  # failure!

    def add_expansions(self, inpt, ic):
        for tree in ic.h:
            if tree and isinstance(tree[0], Feature):
                trigger_feature, *rest = tree
                feature_value = trigger_feature.int_value
                if trigger_feature.type == 'selects':
                    terminals, nonterminals = terminals_of(rest)
                    if terminals:
                        self.merge1(inpt, terminals, feature_value, ic)
                    if nonterminals:
                        self.merge2(inpt, nonterminals, feature_value, ic)
                    if terminals:
                        self.merge3(inpt, terminals, feature_value, ic)
                    if nonterminals:
                        self.merge4(inpt, nonterminals, feature_value, ic)
                elif trigger_feature.type == 'positive':
                    self.move1(inpt, rest, feature_value, ic)
                    self.move2(inpt, rest, feature_value, ic)
                else:
                    raise RuntimeError('exps')
            else:
                self.scan(tree, inpt, ic)

    def insert_new_parses(self, p, new_p, iq):
        for exp in self.expansions:
            # scan is a special case, identifiable by empty head
            # (inpt,[(([],m),([],mx))]) <-- we check for that empty head
            inpt, ics = exp
            if not ics[0].h:
                new_parse = (p, inpt, iq)
            else:  # put indexed categories ics onto iq with new_p
                new_iq = iq.copy()
                for ic in ics:
                    new_index = min_index(ic)
                    new_iq.heappush((new_index, ic))
                new_parse = (new_p, inpt, new_iq)
            self.derivations.heappush(new_parse)

    def scan(self, w, inpt, ic):
        if not any(self.expansions):
            #  w not a prefix of input
            if w == inpt[:len(w)]:
                remainder_int = len(w)
                ic1 = IndexedCategory([], ic.m, [], ic.mx)
                exp = (inpt[remainder_int:], [ic1])
                self.expansions.append(exp)

    def merge1(self, inpt, terms, i, ic):
        #print('inpt:', inpt)
        #print('h:', ic.h)
        #print('m:', ic.m)
        #print('hx:', ic.hx)
        #print('mx:', ic.mx)
        new_head_index = ic.hx[:]
        new_head_index.append(0)
        new_comp_index = ic.hx[:]
        new_comp_index.append(1)
        empty_m = [[]] * len(ic.m)
        empty_mx = [[]] * len(ic.mx)
        ic1 = IndexedCategory(terms, empty_m, new_head_index, empty_mx)
        ic2 = IndexedCategory(self.lex_array[i], ic.m, new_comp_index, ic.mx)  # movers to complement only
        exp = (inpt, [ic1, ic2])
        self.expansions.append(exp)

    def merge2(self, inpt, nonterms, i, ic):
        new_head_index = ic.hx[:]
        new_head_index.append(1)
        new_comp_index = ic.hx[:]
        new_comp_index.append(0)
        empty_m = [[]] * len(ic.m)
        empty_mx = [[]] * len(ic.mx)
        ic1 = IndexedCategory(nonterms, ic.m, new_head_index, ic.mx)  # movers to head
        ic2 = IndexedCategory(self.lex_array[i], empty_m, new_comp_index, empty_mx)  # no spec movers
        exp = (inpt, [ic1, ic2])
        self.expansions.append(exp)

    def merge3(self, inpt, terms, i, ic):
        for nxt in range(len(ic.m)):
            matching_tree = member_has_feature_value(i, ic.m[nxt])
            if not matching_tree:
                continue
            ts = matching_tree[1:]
            tsx = ic.mx[nxt]
            empty_m = [[]] * len(ic.m)
            empty_mx = [[]] * len(ic.mx)
            n = ic.m[:]
            nx = ic.mx[:]
            n[nxt] = []  # we used the "next" licensee, so now empty
            nx[nxt] = []
            ic1 = IndexedCategory(terms, empty_m, ic.hx, empty_mx)
            ic2 = IndexedCategory(ts, n, tsx, nx)  # movers passed to complement
            exp = (inpt, [ic1, ic2])
            self.expansions.append(exp)

    def merge4(self, inpt, nonterms, i, ic):
        for nxt in range(len(ic.m)):
            matching_tree = member_has_feature_value(i, ic.m[nxt])
            if not matching_tree:
                continue
            ts = matching_tree[1:]
            tsx = ic.mx[nxt]
            empty_m = [[]] * len(ic.m)
            empty_mx = [[]] * len(ic.mx)
            n = ic.m[:]
            nx = ic.mx[:]
            n[nxt] = []  # we used the "next" licensee, so now empty
            nx[nxt] = []
            ic1 = IndexedCategory(nonterms, empty_m, ic.hx, empty_mx)
            ic2 = IndexedCategory(ts, n, tsx, nx)  # movers passed to complement
            exp = (inpt, [ic1, ic2])
            self.expansions.append(exp)

    def move1(self, inpt, ts, i, ic):
        if ic.m[i]:  # SMC
            return
        n = ic.m[:]
        nx = ic.mx[:]
        n[i] = self.lex_array[i]
        nx[i] = ic.hx[:]
        nx[i].append(0)
        new_head_index = ic.hx[:]
        new_head_index.append(1)
        ic1 = IndexedCategory(ts, n, new_head_index, nx)
        exp = (inpt, [ic1])
        self.expansions.append(exp)

    def move2(self, inpt, ts, i, ic):
        for nxt, mtree in enumerate(ic.m):
            matching_tree = member_has_feature_value(i, mtree)
            if matching_tree:
                root_f = matching_tree[0].int_value # value of rootLabel
                if root_f == nxt or not ic.m[root_f]:  # SMC
                    mts = matching_tree[1:]
                    mtsx = ic.mx[nxt]
                    new_m = ic.m[:]
                    new_m[nxt] = []  # we used the "next" licensee, so now empty
                    new_m[root_f] = mts
                    new_mx = ic.mx[:]
                    new_mx[nxt] = []
                    new_mx[root_f] = mtsx
                    ic1 = IndexedCategory(ts, new_m, ic.hx, new_mx)
                    exp = (inpt, [ic1])
                    self.expansions.append(exp)

inpt0=['the', 'king', 'knows', 'which', 'wine', 'the', 'queen', 'prefers']
g = Grammar(mg0)
g.recognize('C', 0.001, inpt0)