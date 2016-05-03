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
    def __init__(self, word, features):
        self.word = word
        self.features = features
        self.reversed_features = list(reversed(self.features))


class IndexedCategory:
    """ Rename those h, m, hx, mx when you know what they mean. :(
    """
    def __init__(self, head, mover, head_index, mover_index):
        self.head = head
        self.mover = mover
        self.head_index = head_index
        self.mover_index = mover_index

    def __gt__(self, other):
        return (self.head, self.mover, self.head_index, self.mover_index) > other

    def __lt__(self, other):
        return (self.head, self.mover, self.head_index, self.mover_index) < other

    def __repr__(self):
        return 'IndexedCategory(head=%r, mover=%r, head_index=%r, mover_index=%r)' % (self.head,
                                                                                      self.mover,
                                                                                      self.head_index,
                                                                                      self.mover_index)

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

    def __repr__(self):
        return 'IQueue(%r)' % self._q

    def heappop(self):
        return heapq.heappop(self._q)

    def heappush(self, val):
        heapq.heappush(self._q, val)

    def copy(self):
        return IQueue(self)


class DerivationQueue(IQueue):

    def __repr__(self):
        return 'DerivationQueue(%r)' % self._q

    def copy(self):
        return DerivationQueue(self)


def member_has_feature_value(i, lst):
    for e in lst:
        if e[0].int_value == i:
            return e
    return None


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
        self.lex_array = []
        self.input_string = []
        self.derivations = None
        self.ic = None
        self.count = 0

        # prepare lexicon to have LexItems with Features, and while in it, collect all of the
        # values that features can take into 'known_feature_values'.
        for word, features in lex:
            feature_items = []
            for type, value in features:
                f = Feature(type, value, self.known_feature_values)
                feature_items.append(f)
            li = LexItem(word, feature_items)
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
        if isinstance(lex_item.word, list):
            lex_trees.append(lex_item.word)
        else:
            lex_trees.append([lex_item.word])

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
        head = self.lex_array[start_int]
        n = len(self.known_feature_values)
        mover = [[]] * n
        mover_index = [[]] * n
        ic = IndexedCategory(head, mover, [], mover_index)
        iq = IQueue(([], ic))
        self.derivations = DerivationQueue((-1.0, input_string, iq))
        t0 = time.time()
        result = self.derive()
        print(time.time() - t0, "seconds:", result)

    def derive(self):  # eliminate the recursion here?
        # p = 1.0
        while self.derivations:
            (p, self.input_string, iq) = self.derivations.heappop()
            print('# of parses in beam=', len(self.derivations) + 1, ', p(best parse)=', (-1 * p))
            if iq:
                indices, self.ic = iq.heappop()
                expansions = self.create_expansions()
                if not expansions:
                    return self.derive()
                else:
                    new_p = p / float(len(expansions))
                    if new_p < self.min_p:
                        self.insert_new_parses(expansions, p, new_p, iq)
                    else:
                        print('improbable parses discarded')
            elif not self.input_string:
                return True  # success!
        return False  # failure!

    def create_expansions(self):
        expansions = []
        for tree in self.ic.head:
            if tree and isinstance(tree[0], Feature):
                trigger_feature, *rest = tree
                feature_value = trigger_feature.int_value
                if trigger_feature.type == 'selects':
                    terminals, nonterminals = terminals_of(rest)
                    if terminals:
                        expansions += self.merge1(terminals, feature_value)
                    if nonterminals:
                        expansions += self.merge2(nonterminals, feature_value)
                    if terminals:
                        expansions += self.merge3(terminals, feature_value)
                    if nonterminals:
                        expansions += self.merge4(nonterminals, feature_value)
                elif trigger_feature.type == 'positive':
                    expansions += self.move1(rest, feature_value)
                    expansions += self.move2(rest, feature_value)
                else:
                    raise RuntimeError('exps')
            elif not any(expansions):
                if tree:
                    expansions += self.scan(tree)
                else:
                    expansions += self.empty_scan()
        return expansions

    def insert_new_parses(self, expansions, p, new_p, iq):
        for exp in expansions:
            # scan is a special case, identifiable by empty head
            # (inpt,[(([],m),([],mx))]) <-- we check for that empty head
            inpt, ics = exp
            if not ics[0].head:
                new_parse = (p, inpt, iq)
            else:  # put indexed categories ics onto iq with new_p
                new_iq = iq.copy()
                for ic in ics:
                    # min_index should only check indices of filled mover positions.
                    # No mover has an empty index, so we can ignore them.
                    min_index = ic.head_index
                    for x in ic.mover_index:
                        if x and x < min_index:
                            min_index = x
                    new_iq.heappush((min_index, ic))
                new_parse = (new_p, inpt, new_iq)
            self.count += 1
            #print('\n\n%s adding new parse to derivations: %s' % (self.count, new_parse))
            self.derivations.heappush(new_parse)

    def scan(self, w):
        if len(w) == 1:
            if w[0] == self.input_string[0]: #  w not a prefix of input
                ic1 = IndexedCategory([], self.ic.mover, [], self.ic.mover_index)
                leaf = (self.input_string[1:], [ic1])
                return [leaf]
        else: # i'm keeping this more complex case if we need it at some point.
            # for me it seems that word list has always size 1 or 0
            if w == self.input_string[:len(w)]:
                remainder_int = len(w)
                ic1 = IndexedCategory([], self.ic.mover, [], self.ic.mover_index)
                leaf = (self.input_string[remainder_int:], [ic1])
                return [leaf]
        return []

    def empty_scan(self):
        ic1 = IndexedCategory([], self.ic.mover, [], self.ic.mover_index)
        leaf = (self.input_string.copy(), [ic1])
        return [leaf]


    def merge1(self, terms, fval):
        head_index = self.ic.head_index + [0]
        complement_index = self.ic.head_index + [1]
        empty_m = [[]] * len(self.ic.mover)
        empty_mx = [[]] * len(self.ic.mover_index)
        ic1 = IndexedCategory(terms, empty_m, head_index, empty_mx)
        ic2 = IndexedCategory(self.lex_array[fval], self.ic.mover, complement_index,
                              self.ic.mover_index)
        # movers to complement only
        merge_result = (self.input_string, [ic1, ic2])
        return [merge_result]

    def merge2(self, nonterms, fval):
        head_index = self.ic.head_index + [1]
        complement_index = self.ic.head_index + [0]
        empty_m = [[]] * len(self.ic.mover)
        empty_mx = [[]] * len(self.ic.mover_index)
        ic1 = IndexedCategory(nonterms, self.ic.mover, head_index, self.ic.mover_index)  # movers to
        #  head
        ic2 = IndexedCategory(self.lex_array[fval], empty_m, complement_index, empty_mx)
        # no spec movers
        merge_result = (self.input_string, [ic1, ic2])
        return [merge_result]

    def merge3(self, terms, fval):
        for nxt, mtree in enumerate(self.ic.mover):
            matching_tree = member_has_feature_value(fval, mtree)
            if not matching_tree:
                continue
            ts = matching_tree[1:]
            tsx = self.ic.mover_index[nxt]
            empty_m = [[]] * len(self.ic.mover)
            empty_mx = [[]] * len(self.ic.mover_index)
            complement_m = self.ic.mover.copy()
            complement_mx = self.ic.mover_index.copy()
            complement_m[nxt] = []  # we used the "next" licensee, so now empty
            complement_mx[nxt] = []
            ic1 = IndexedCategory(terms, empty_m, self.ic.head_index, empty_mx)
            ic2 = IndexedCategory(ts, complement_m, tsx, complement_mx)
            # movers passed to complement
            merge_result = (self.input_string, [ic1, ic2])
            return [merge_result]
        return []

    def merge4(self, nonterms, fval):
        for nxt, mtree in enumerate(self.ic.mover):
            matching_tree = member_has_feature_value(fval, mtree)
            if not matching_tree:
                continue
            ts = matching_tree[1:]
            tsx = self.ic.mover_index[nxt]
            empty_m = [[]] * len(self.ic.mover)
            empty_mx = [[]] * len(self.ic.mover_index)
            complement_m = self.ic.mover.copy()
            complement_m[nxt] = []  # we used the "next" licensee, so now empty
            complement_mx = self.ic.mover_index.copy()
            complement_mx[nxt] = []
            ic1 = IndexedCategory(nonterms, empty_m, self.ic.head_index, empty_mx)
            ic2 = IndexedCategory(ts, complement_m, tsx, complement_mx)  # movers passed to complement
            merge_result = (self.input_string, [ic1, ic2])
            return [merge_result]
        return []

    def move1(self, ts, fval):
        if self.ic.mover[fval]:  # SMC
            return []
        mover_m = self.ic.mover.copy()
        mover_mx = self.ic.mover_index.copy()
        mover_m[fval] = self.lex_array[fval]
        mover_mx[fval] = self.ic.head_index.copy()
        mover_mx[fval].append(0)
        new_head_index = self.ic.head_index.copy()
        new_head_index.append(1)
        ic1 = IndexedCategory(ts, mover_m, new_head_index, mover_mx)
        move_result = (self.input_string, [ic1])
        return [move_result]

    def move2(self, ts, fval):
        for nxt, mtree in enumerate(self.ic.mover):
            matching_tree = member_has_feature_value(fval, mtree)
            if matching_tree:
                root_f = matching_tree[0].int_value # value of rootLabel
                if root_f == nxt or not self.ic.mover[root_f]:  # SMC
                    mts = matching_tree[1:]
                    mtsx = self.ic.mover_index[nxt]
                    new_m = self.ic.mover.copy()
                    new_m[nxt] = []  # we used the "next" licensee, so now empty
                    new_m[root_f] = mts
                    new_mx = self.ic.mover_index.copy()
                    new_mx[nxt] = []
                    new_mx[root_f] = mtsx
                    ic1 = IndexedCategory(ts, new_m, self.ic.head_index, new_mx)
                    move_result = (self.input_string, [ic1])
                    return [move_result]
        return []

inpt0=['the', 'king', 'knows', 'which', 'wine', 'the', 'queen', 'prefers']
g = Grammar(mg0)
g.recognize('C', 0.001, inpt0)