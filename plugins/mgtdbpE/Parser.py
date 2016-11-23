"""
file: mgtdbpD.py
      minimalist grammar top-down beam parser, refactored from E. Stabler's original.

   This is part of effort to make an output-equivalent mgtdbp that can be used as a Kataja plugin.
   The code aims for readability and not efficiency, so most of the parameter passings with complex
   lists are turned into objects where necessary parameters can be get by their name and not by
   their index in ad-hoc lists or tuples.

   mgtdbpA -- Turned most of the complex list parameters for functions to class instances 
   mgtdbpB -- More informative variable names and neater conversion to output trees
   mgtdbpC -- Removed heapq_mod -- now the whole thing is faster, as there is less implicit
   sorting and new parses are inserted close to their final resting place.
   mgtdbpD -- Combined DerivationTree and DerivationNode. As names tell, they were quite similar.
   Sortable indices are strings instead of lists. Easier for output and almost as fast.

   Refactoring by Jukka Purma                                      || 11/21/16 
   mgtdbp-dev Modified for py3.1 compatibility by: Erik V Arrieta. || Last modified: 9/15/12
   mgtdbp-dev by Edward P. Stabler
   
Comments welcome: jukka.purma--at--gmail.com
"""
import time
import pprint
from collections import OrderedDict

try:
    from kataja.saved.Forest import Forest
    in_kataja = True
except ImportError:
    Forest = None
    in_kataja = False

if in_kataja:
    from mgtdbpE.Constituent import Constituent as DTree
    from mgtdbpE.OutputTrees import print_results
    from mgtdbpE.KFeature import KFeature as Feature
else:
    from OutputTrees import DTree, print_results
    from Feature import Feature

class LexItem:
    """ These are more typical LIs. It takes in list of words instead of one string for
    compability with mgtdbp output. These are not used in parsing at all, they are only to print
    out the grammar. """

    def __init__(self, words, features):
        self.words = words
        self.features = features

    def __str__(self):
        return ' '.join(self.words) + '::' + ' '.join([str(f) for f in self.features])


class LexTreeNode:
    def __init__(self, feature):
        self.feature = feature
        self.subtrees = []  # LexTreeNodes
        self.terminals = []

    def subtree_with_feature(self, name):
        for subtree in self.subtrees:
            if subtree.feature and subtree.feature.name == name:
                return subtree

    def __repr__(self):
        if self.subtrees:
            return '[%s, [%s]]' % (self.feature, ', '.join([str(x) for x in self.subtrees]))
        else:
            return '[%s, %s]' % (self.feature, self.terminals)


class Prediction:
    def __init__(self, head, movers=None, head_path=None, mover_paths=None, tree=None):
        self.head = head
        self.movers = movers or {}
        self.head_path = head_path or ''
        self.mover_paths = mover_paths or {}
        self.tree = tree
        self._min_index = None
        self.update_ordering()

    def update_ordering(self):
        """ ICs can be stored in queue if they can be ordered. Original used tuples to provide
        ordering, we can have an innate property _min_index for the task. It could be calculated
        for each comparison, but for efficiency's sake do it manually before pushing to queue. """
        self._min_index = min([self.head_path] + [x for x in self.mover_paths.values()])

    def copy(self):
        return Prediction(self.head, self.movers.copy(), self.head_path[:], self.mover_paths.copy(),
                          self.tree.copy())

    def __repr__(self):
        return 'Prediction(head=%r, movers=%r, head_path=%r, mover_paths=%r, tree=%r)' % \
               (self.head, self.movers, self.head_path, self.mover_paths, self.tree)

    def __getitem__(self, key):
        return self._min_index

    def __lt__(self, other):
        return self._min_index < other._min_index

    def compact(self):
        h = str(self.head) + '; '
        if self.movers:
            m = 'm(%s); ' % str(self.movers)
        else:
            m = ''
        if self.head_path:
            hx = 'hx(%s); ' % self.head_path
        else:
            hx = ''
        if self.mover_paths:
            mx = 'mx(%s); ' % str(self.mover_paths)
        else:
            mx = ''
        self.update_ordering()
        return ''.join((self._min_index, h, m, hx, mx, self.tree.compact()))


class Derivation:
    def __init__(self, p, inpt, iqs, results):
        self.probability = p
        self.input = inpt
        self.predictions = iqs
        self.results = results

    def __getitem__(self, key):
        return (self.probability, self.input, self.predictions, self.results)[key]

    def __str__(self):
        return '(%s, %s, %s, [%s])' % \
               (self.probability, ' '.join(self.input), str(self.predictions),
                ', '.join([str(x) for x in self.results]))

    def copy(self):
        return Derivation(self.probability, self.input[:], self.predictions[:], self.results[:])

    def __lt__(self, other):
        return self.probability < other.probability


class DerivationNode:
    """ DerivationNodes are constituent nodes that are represented in a queer way:
        instead of having relations to other nodes, they have 'path', a list of 1:s and 0:s that
        tells their place in a binary tree. Once there is a list of DerivationNodes, a common
        tree can be composed from it. """

    def __init__(self, path, label=None, features=None, moving_features=None, terminal=False):
        self.path = path or ''
        self.label = label or []
        self.features = features or []
        self.moving_features = moving_features or {}
        self.terminal = terminal

    def copy(self):
        return DerivationNode(self.path[:], self.label[:], self.features[:],
                              self.moving_features.copy(), self.terminal)

    def __repr__(self):
        return 'DerivationNode(path=%r, label=%r, features=%r)' % \
               (self.path, self.label, self.features)

    def __str__(self):
        if self.label or self.features:
            return '%s, (%s, %s)' % (self.path, self.label, self.features)
        else:
            return self.path

    def __lt__(self, other):
        return self.path < other.path

    def compact(self):
        if self.label:
            l = 'l(%s);' % ''.join(self.label)
        else:
            l = ''
        if self.features:
            f = 'f(%s);' % ''.join([str(x) for x in self.features])
        else:
            f = ''
        if self.moving_features:
            m = 'mf(%s);' % str(self.moving_features)
        else:
            m = ''
        return 'dn('+ ''.join((self.path, '; ', l, f, m)) + ')'


class Parser:
    def __init__(self, lex_tuples, min_p, start=None, sentence=None, forest=None):
        print('****** Starting Parser *******')
        self.d = []
        self.min_p = min_p
        self.lex = OrderedDict()
        self.derivation_stack = []
        self.new_parses = []
        self.results = {}
        self.forest = forest # optional kataja forest where to push trees 
        # Read LIs and features from grammar.
        feature_names = set()
        base = LexTreeNode(None)
        for words, feature_tuples in lex_tuples:
            features = []
            for value, name in feature_tuples:
                feat = Feature(value, name)
                feature_names.add(name)
                features.append(feat)
            self.d.append(LexItem(words, features))
            # Build LexTrees
            node = base
            for f in reversed(features):
                found = False
                for subtree in node.subtrees:
                    if subtree.feature == f:
                        found = True
                        node = subtree
                        break
                if not found:
                    new_node = LexTreeNode(f)
                    node.subtrees.append(new_node)
                    node = new_node
            node.terminals.append(words)
        for node in base.subtrees:
            self.lex[node.feature.name] = node  # dict for quick access to starting categories

        if start and sentence:
            success, dnodes = self.parse(start, sentence)
            if success:
                self.print_results(dnodes)
            else:
                print('parse failed, what we have is:')
                print(dnodes)

    def __str__(self):
        return str(self.d)

    def parse(self, start, sentence):
        # Prepare prediction queue. We have a prediction that the derivation will finish
        # in a certain kind of category, e.g. 'C'
        final_features = [Feature('cat', start)]
        topmost_head = self.lex[start]
        prediction = Prediction(topmost_head, tree=DerivationNode('', features=final_features))

        inpt = sentence.split()
        print('inpt =' + str(inpt))

        # Prepare derivation queue. It gets expanded by derive.
        self.derivation_stack = [Derivation(-1.0, inpt, [prediction], [DerivationNode('')])]

        # The work is done by derive.
        t0 = time.time()
        success, dnodes = self.derive()
        t1 = time.time()
        if success:
            print('parse found')
        else:
            print('no parse found')
        print(str(t1 - t0) + "seconds")
        return success, dnodes

    def derive(self):
        d = None
        while self.derivation_stack:
            d = self.derivation_stack.pop()
            self.checkpoint(d)
            print('#########################################')
            print('# of parses in beam=%s, p(best parse)=%s' %
                  (len(self.derivation_stack) + 1, -1 * d.probability))
            print('')
            if not (d.predictions or d.input):
                return True, d.results  # success
            elif d.predictions:
                prediction = d.predictions.pop(0)
                self.new_parses = []
                self.create_expansions(prediction)
                if self.new_parses:
                    new_p = d.probability / len(self.new_parses)
                    if new_p < self.min_p:
                        self.insert_new_parses(d, new_p)
                    else:
                        print('improbable parses discarded')
                else:
                    self.scan_and_insert_terminals(prediction, d)
        return False, d.results  # fail

    def create_expansions(self, prediction):
        """ Expand possibilities. If we assume current {prediction}, what are the operations that
         could have lead into it? Prediction has features we know about, and those fix its place
         in LexTree. The next generation of nodes, {subtrees}, in LexTree are those that have
         these and additional features and for each we make a prediction where the subtree node
         got there because of merge or move with something else.
         All predictions get written into self.new_parses
         """

        # e.g. if current head is C, nodes are =V, -wh
        print('---prediction now: ', prediction.compact())
        for node in prediction.head.subtrees:
            if node.feature.value == 'sel':
                if node.terminals:
                    self.merge1(node, prediction)  # merge a (non-moving) complement
                    self.merge3(node, prediction)  # merge a (moving) complement
                elif node.subtrees:
                    self.merge2(node, prediction)  # merge a (non-moving) specifier
                    self.merge4(node, prediction)  # merge a (moving) specifier
            elif node.feature.value == 'pos':
                self.move1(node, prediction)
                self.move2(node, prediction)
            else:
                raise RuntimeError('exps')

    def scan_and_insert_terminals(self, prediction, derivation):
        for words in prediction.head.terminals:
            # scan -operation
            if derivation.input[:len(words)] == words:
                # print('doing scan:', terminal)
                new_pred = prediction.copy()
                new_pred.head = []
                new_pred.head_path = []
                new_parse = derivation.copy()
                new_pred.tree.label = words
                new_pred.tree.terminal = True
                new_parse.results.append(new_pred.tree)
                if new_parse.input[:len(words)] == words:
                    new_parse.input = new_parse.input[len(words):]
                print('||| scanned and found: ', words)
                self.derivation_stack.append(new_parse)
                self.derivation_stack.sort(reverse=True)
                break  # there is only one match for word+features in lexicon

    # These operations reverse familiar minimalist operations: external merges, moves and select.
    # They create predictions of possible child nodes that could have resulted in current head.
    # Predictions are packed into Expansions, and after all Expansions for this head are created,
    # the good ones are inserted to parse queue by insert_new_parses.
    # merge a (non-moving) complement
    def merge1(self, node, prediction):
        """ This reverses a situation when a new element (pr0) is external-merged to existing
        head (pr1) as a complement.
        {node} is one of the subtrees of {prediction.head}.
        {node} is terminal
        ..=X:root * X.. -> prediction
        """
        # print('doing merge1')
        # print(node)
        category = node.feature.name
        pr0 = prediction.copy()  # no movers to lexical head
        pr0.head = node  # one part of the puzzle is given, the other part is deduced from this
        pr0.head_path += '0'  # left
        pr0.movers = {}  # this is external merge, doesn't bring any movers
        pr0.mover_paths = {}
        pr0.tree.features.append(Feature('sel', category)) # =D, =N,...
        pr0.tree.path += '0'  # left
        pr0.tree.moving_features = {}

        pr1 = prediction.copy()  # movers to complement only
        pr1.head = self.lex[category]  # head can be any LI in this category
        pr1.head_path += '1'  # right
        pr1.tree.features = [Feature('cat', category)] # D, N,...
        pr1.tree.path += '1'  # right
        print('merge1, pr0:', pr0.compact())
        print('merge1, pr1:', pr1.compact())
        self.new_parses.append((pr0, pr1))

    # merge a (non-moving) specifier
    def merge2(self, node, prediction):
        """ This reverses a situation when a non-terminal element (pr0) is external-merged to
        existing head (pr1) as a specifier.
        {node} is one of the subtrees of {prediction.head}.
        {node} is non-terminal
        ..=X.. * X.. -> prediction
        """
        # print('doing merge2')
        # print(node)
        category = node.feature.name
        pr0 = prediction.copy()  # pr0 receives movers from prediction.
        pr0.head = node
        pr0.head_path += '1'  # right?
        pr0.tree.features.append(Feature('sel', category))  # =D, =N,...
        pr0.tree.path += '0'  # left?

        pr1 = prediction.copy()
        pr1.head = self.lex[category]
        pr1.movers = {}  # pr1 is non-mover and a specifier
        pr1.head_path += '0'  # left, as in specifier? Why head_path and tree path are different?
        pr1.mover_paths = {}
        pr1.tree.features = [Feature('cat', category)]  # D, N,...
        pr1.tree.path += '1'
        pr1.tree.moving_features = {}
        print('merge2, pr0:', pr0.compact())
        print('merge2, pr1:', pr1.compact())
        self.new_parses.append((pr0, pr1))

    # merge a (moving) complement
    def merge3(self, node, prediction):
        """ This reverses a situation when a terminal moving element (pr0) is merged to existing
        head (pr1) as a complement.
        {node} is one of the subtrees of {prediction.head}.
        {node} is terminal
        ..=X:root * ..X(-mover).. => prediction (with mover)
        """
        cat = node.feature.name
        for mover_cat, mover in prediction.movers.items():  # look into movers
            matching_tree = mover.subtree_with_feature(cat)  # matching tree is a child of mover
            if matching_tree:
                # print('doing merge3')
                # print(node)
                pr0 = prediction.copy()  # pr0 doesn't move anymore
                pr0.head = node  # head path is not changing. wonder why?
                pr0.movers = {}
                pr0.mover_paths = {}
                pr0.tree.features.append(Feature('sel', cat)) # =D, =N
                pr0.tree.path += '0'
                pr0.tree.moving_features = {}

                # pr1 doesn't have certain movers that higher prediction has
                pr1 = prediction.copy()  # movers passed to complement
                pr1.head = matching_tree
                del pr1.movers[mover_cat]  # we used the licensee, so now empty
                pr1.head_path = pr1.mover_paths[mover_cat]
                del pr1.mover_paths[mover_cat]
                pr1.tree.features = pr1.tree.moving_features[mover_cat][:]  # movers to complement
                pr1.tree.features.append(Feature('cat', cat))
                pr1.tree.path += '1'
                del pr1.tree.moving_features[mover_cat]
                print('merge3, pr0:', pr0.compact())
                print('merge3, pr1:', pr1.compact())
                self.new_parses.append((pr0, pr1))

    # merge a (moving) specifier
    def merge4(self, node, prediction):
        """ This reverses a situation when a non-terminal element (pr0) is merged to existing
        head (pr1) as a specifier.
        {node} is one of the subtrees of {prediction.head}.
        {node} is non-terminal
        ..=X(-mover).. * ..LexMX(mover).. => prediction (with mover)
        """
        cat = node.feature.name
        for mover_cat, mover in prediction.movers.items():
            matching_tree = mover.subtree_with_feature(cat)
            if matching_tree:
                # print('doing merge4')
                # print(node)
                pr0 = prediction.copy()  # has most of the movers that prediction has
                pr0.head = node
                del pr0.movers[mover_cat]  # we used the "next" licensee, so now empty
                del pr0.mover_paths[mover_cat]
                pr0.tree.features.append(Feature('sel', cat))
                pr0.tree.path += '0'
                del pr0.tree.moving_features[mover_cat]

                pr1 = prediction.copy()  # movers passed to complement
                pr1.head = matching_tree
                pr1.movers = {}
                pr1.head_path = pr1.mover_paths[mover_cat]
                pr1.mover_paths = {}
                pr1.tree.features = pr1.tree.moving_features[mover_cat][:]  # copy
                pr1.tree.features.append(Feature('cat', cat))
                pr1.tree.path += '1'
                pr1.tree.moving_features = {}
                print('merge4, pr0:', pr0.compact())
                print('merge4, pr1:', pr1.compact())
                self.new_parses.append((pr0, pr1))

    def move1(self, node, prediction):
        """ Making a hypothesis that the previous build step was move.
        {node} is one of the subtrees of {prediction.head}.
        {prediction.movers}

        """
        cat = node.feature.name
        if cat not in prediction.movers:  # note that it is 'not in'. We're establishing a mover.
            pr0 = prediction.copy()
            pr0.head = node  # node is remainder of head branch
            pr0.movers[cat] = self.lex[cat]
            pr0.head_path += '1'
            pr0.mover_paths[cat] = prediction.head_path
            pr0.mover_paths[cat] += '0'
            pr0.tree.features.append(Feature('pos', cat))  # trunk has '+'
            pr0.tree.path += '0'
            pr0.tree.moving_features[cat] = [Feature('neg', cat)]  # mover has '-'
            print('move1, pr0:', pr0.compact())
            self.new_parses.append((pr0, None))

    def move2(self, node, prediction):
        """ Move and keep on moving? Examples don't seem to use this. """
        cat = node.feature.name
        for mover_cat, mover in prediction.movers.items():  # <-- look into movers
            matching_tree = mover.subtree_with_feature(
                cat)  # ... for category shared with prediction
            if matching_tree:
                root_f = matching_tree.feature.name # value of rootLabel
                assert (root_f == cat)
                print(root_f, mover_cat)
                if root_f == mover_cat or root_f not in prediction.movers:  # SMC
                    print('doing move2')
                    print(node)
                    # print('doing move2')
                    mts = matching_tree  # matchingTree[1:][:]
                    pr0 = prediction.copy()
                    pr0.head = node
                    del pr0.movers[mover_cat]  # we used the "next" licensee, so now empty
                    pr0.movers[root_f] = mts
                    pr0.mover_paths[root_f] = pr0.mover_paths[mover_cat][:]
                    del pr0.mover_paths[mover_cat]
                    pr0.tree.moving_features[root_f] = pr0.tree.moving_features[mover_cat][:]
                    pr0.tree.moving_features[root_f].append(
                        Feature('neg', cat))  # extend prev features of mover with (neg cat)
                    del pr0.tree.moving_features[mover_cat]
                    pr0.tree.features.append(Feature('pos', cat))
                    pr0.tree.path += '0'
                    print('move2, pr0:', pr0.compact())
                    self.new_parses.append((pr0, None))

    def insert_new_parses(self, derivation, new_p):
        for pred0, pred1 in self.new_parses:
            new_parse = derivation.copy()
            new_parse.results.append(pred0.tree)
            pred0.update_ordering()
            new_parse.predictions.append(pred0)
            if pred1:
                new_parse.results.append(pred1.tree)
                pred1.update_ordering()
                new_parse.predictions.append(pred1)
            new_parse.predictions.sort()
            new_parse.probability = new_p
            self.derivation_stack.append(new_parse)
        self.derivation_stack.sort(reverse=True)

    def checkpoint(self, derivation):
        """ Here we can output, pause or otherwise intercept the parsing process """
        dtree = DTree.dnodes_to_dtree(derivation.results, all_features=True)
        #input()
        if in_kataja:
            self.forest.derivation_steps.save_and_create_derivation_step([dtree])
        else:
            print('******* dtree *******')
            pprint.pprint(dtree)



############################################################################################

if __name__ == '__main__':
    import mg0 as grammar

    sentences = ["the king prefers the beer",
                 "which king says which queen knows which king says which wine the queen prefers",
                 "which queen says the king knows which wine the queen prefers",
                 "which wine the queen prefers",
                 "which king says which queen knows which king says which wine the queen prefers"]
    sentences = ["which king says which queen knows which king says which wine the queen prefers"]
    sentences = ["which wine the queen prefers"]
    t = time.time()
    for s in sentences:
        pr = Parser(grammar.g, -0.0001)
        my_success, my_dnodes = pr.parse(sentence=s, start='C')
        results = print_results(my_dnodes, pr.lex)
        if True:
            for key in sorted(list(results.keys())):
                print(key)
                print(results[key])
    print(time.time() - t)
