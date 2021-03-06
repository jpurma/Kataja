try:
    from SpreadTree.Constituent import Constituent
    from SpreadTree.Feature import Feature
    from kataja.syntax.SyntaxState import SyntaxState
    from kataja.saved.DerivationStep import DerivationStep
except ImportError:
    from Constituent import Constituent
    from Feature import Feature

    SyntaxState = object
    DerivationStep = object
import time

REMOVE_BAD_PARSES = True


def start_element():
    fstring = ''  # ''-C -T -v'
    feats = [Feature.from_string(fs) for fs in fstring.split()]
    return Constituent(label='', features=feats, set_hosts=True)


def read_lexicon(filename):
    lexicon = {}
    for line in open(filename):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        label, foo, fstring = line.partition('::')
        label = label.strip()
        feats = [Feature.from_string(fs) for fs in fstring.split()]
        const = Constituent(label=label, features=feats, set_hosts=True)
        lexicon[label] = const
    return lexicon


def linearize(tree):
    done = set()
    result = []

    def _walk_tree(node):
        if not node or node in done:
            return
        done.add(node)
        if node.parts:
            for child in node.parts:
                _walk_tree(child)
        elif node.label:
            result.append(node.label)

    _walk_tree(tree)
    return result


def _update_check_information_for_features(tree):
    feature_checks = set()
    features = set()
    done = set()

    def walk_tree(node):
        if node in done:
            return
        done.add(node)
        if node.parts:
            if node.checker or node.checked:
                feature_checks.add((node.checker, node.checked))
            for part in node.parts:
                if part is not node.riser:
                    walk_tree(part)
        else:
            for feature in node.features:
                features.add(feature)

    walk_tree(tree)
    for feature in features:
        feature.checked_by = None
        feature.checks = None
    for checks, checked_by in feature_checks:
        if checks:
            checks.checked_by = checked_by
        if checked_by:
            checked_by.checks = checks


class Parser:
    def __init__(self, lexicon, forest=None):
        self.forest = forest
        self.results = []
        self.correct = []
        self.lexicon = lexicon or {}
        self.good_paths = []
        self.ticks = 0
        self.nodes = 0

    def pick_constituent(self, item):
        if item in self.lexicon:
            node = self.lexicon[item].copy()
        else:
            node = Constituent(item)
            self.lexicon[item] = node.copy()
        node.head = node
        return node

    @staticmethod
    def _justify_spec_merges(mover, tree):
        required = []
        matches = []
        for plus_feature in mover.features:
            if plus_feature.required:
                # print('skipping spec merge because required feature is present')
                return [], []
            if plus_feature.sign == '' or plus_feature.sign == '*':
                for neg_feature in tree.features:
                    if neg_feature.name == plus_feature.name and neg_feature.sign == '-':
                        if neg_feature.required:
                            required.append((plus_feature, neg_feature))
                        else:
                            matches.append((plus_feature, neg_feature))
        return required, matches

    @staticmethod
    def _justify_comp_merges(mover, tree):
        required = []
        matches = []
        for plus_feature in tree.features:
            if plus_feature.required:
                # print('skipping comp merge because required feature is present')
                return [], []
            if plus_feature.sign == '' or plus_feature.sign == '*':
                for neg_feature in mover.features:
                    if neg_feature.name == plus_feature.name and neg_feature.sign == '=':
                        if neg_feature.required:
                            required.append((plus_feature, neg_feature))
                        else:
                            matches.append((plus_feature, neg_feature))
        return required, matches

    @staticmethod
    def _justify_wh_spec_merges(riser, tree):
        if not riser:
            return [], []
        required = []
        matches = []
        for plus_feature in riser.features:
            if plus_feature.sign == '*' or plus_feature.sign == '':
                for neg_feature in tree.features:
                    if neg_feature.name == plus_feature.name and neg_feature.sign == '-':
                        if neg_feature.required:
                            required.append((plus_feature, neg_feature))
                        else:
                            matches.append((plus_feature, neg_feature))
        return required, matches

    @staticmethod
    def _justify_wh_comp_merges(riser, tree):
        if not riser:
            return [], []
        required = []
        matches = []
        for plus_feature in riser.features:
            if plus_feature.sign == '*' or plus_feature.sign == '':
                for neg_feature in tree.features:
                    if neg_feature.name == plus_feature.name and neg_feature.sign == '=':
                        if neg_feature.required:
                            required.append((plus_feature, neg_feature))
                        else:
                            matches.append((plus_feature, neg_feature))
        return required, matches

    @staticmethod
    def _find_mover(tree):
        return tree.mover

    @staticmethod
    def _find_riser(tree):
        return tree.riser

    def _find_coordinated(self, tree, skip_me, look_features=None):
        if look_features is None:
            look_features = [f.name for f in tree.features if f.sign == '']
        elif tree is skip_me:
            pass
        elif tree.checker and tree.checker.name in look_features:
            assert tree.checker.sign == '' or tree.checker.sign == '*'
            return tree  # .head?
        if tree.parts:
            found = self._find_coordinated(tree.parts[1], skip_me, look_features)
            if found:
                return found
        # else:
        #    return tree

    def _process_word(self, words, tree, path):
        if not words:
            self._do_internal_merges(words, tree, path)
            # When there are no more internal merges and no words left, this branch is done
            self.results.append((path, tree))
            return
        self.ticks += 1

        const = self.pick_constituent(words[0])

        # External merge new constituent
        self.nodes += 1
        mover = tree
        new_tree = Constituent(label=const.label,
                               comps=[tree],
                               mover=mover,
                               head=const,
                               features=const.features[:],
                               riser=tree.riser)
        if new_tree.has_riser_feature():
            new_tree.riser = new_tree

        new_path = self.add_to_parse_path(path, new_tree,
                                          f"External merge '{const.label}'")

        # Do Internal merge as many times as possible
        self._do_internal_merges(words, new_tree, new_path)

    def _do_internal_merges(self, words, tree, path):

        mover = tree.mover
        if not mover:
            return

        riser = tree.riser
        # if mover.coordinates and False:
        #     print('mover coordinates: ', mover)
        #     restored = self._find_coordinated(tree, mover)
        #     if restored:
        #         print('restoring: ', restored)
        #         self.nodes += 1
        #         new_tree = Constituent(label=restored.label,
        #                                parts=[restored, tree],
        #                                movers=[tree] + restored.movers,
        #                                head=restored,
        #                                features=restored.features,
        #                                Q=restored.Q)
        #         new_path = self.add_to_parse_path(path, new_tree,
        #                                           f"Restored '{restored.label}' to '{tree.label}'",
        #                                           new_tree, self._find_mover(new_tree))
        #         print('next movers: ', new_tree.movers)
        #         self._do_internal_merges(words, new_tree, new_path)

        required_spec_merges, available_spec_merges = self._justify_spec_merges(mover, tree)
        required_comp_merges, available_comp_merges = self._justify_comp_merges(mover, tree)
        required_wh_spec_merges, available_wh_spec_merges = self._justify_wh_spec_merges(riser, tree)
        required_wh_comp_merges, available_wh_comp_merges = self._justify_wh_comp_merges(riser, tree)

        # Try to limit possible merges
        must_do_im = required_spec_merges or required_comp_merges or required_wh_spec_merges or required_wh_comp_merges

        if must_do_im:
            available_spec_merges = required_spec_merges
            available_comp_merges = required_comp_merges
            available_wh_spec_merges = required_wh_spec_merges
            available_wh_comp_merges = required_wh_comp_merges

        if available_spec_merges or available_wh_spec_merges:
            available_comp_merges = []
            available_wh_comp_merges = []

        if available_spec_merges:
            available_wh_spec_merges = []

        if available_comp_merges:
            available_wh_comp_merges = []

        for checker, checked in available_spec_merges:
            self.nodes += 1
            if checker.sign == '*':
                riser = mover
            else:
                riser = tree.riser
            new_tree = Constituent(label=tree.label,
                                   specs=[mover],
                                   mover=mover.mover,
                                   head=tree,
                                   features=[f for f in tree.features if f is not checked],
                                   checker=checker,
                                   checked=checked,
                                   riser=riser)
            new_path = self.add_to_parse_path(path, new_tree, f"Spec merge '{mover.label}' to '{tree.label}'")
            self._do_internal_merges(words, new_tree, new_path)

        for checker, checked in available_comp_merges:
            self.nodes += 1
            if checker.sign == '*':
                riser = mover
            else:
                riser = mover.riser

            new_tree = Constituent(label=mover.label,
                                   comps=[tree],
                                   mover=mover.mover,
                                   head=mover,
                                   features=[f for f in mover.features if f is not checked and f is not checker],
                                   checker=checker,
                                   checked=checked,
                                   riser=riser)
            mover.is_riser = False
            new_path = self.add_to_parse_path(path, new_tree, f"Comp merge '{tree.label}' to '{mover.label}'")
            self._do_internal_merges(words, new_tree, new_path)

        for checker, checked in available_wh_spec_merges:
            self.nodes += 1
            new_tree = Constituent(label=tree.label,
                                   specs=[riser],
                                   mover=tree.mover,
                                   head=tree,
                                   features=[f for f in tree.features if f is not checked and f is not checker],
                                   checker=checker,
                                   checked=checked,
                                   riser=None)
            new_path = self.add_to_parse_path(path, new_tree, f"Wh-spec merge '{riser.label}' to '{tree.label}'")
            self._do_internal_merges(words, new_tree, new_path)

        for checker, checked in available_wh_comp_merges:
            self.nodes += 1
            new_tree = Constituent(label=tree.label,
                                   comps=[riser],
                                   mover=tree.mover,
                                   head=tree,
                                   features=[f for f in tree.features if f is not checked and f is not checker],
                                   checker=checker,
                                   checked=checked,
                                   riser=None)
            new_path = self.add_to_parse_path(path, new_tree, f"Wh-comp merge '{riser.label}' to '{tree.label}'")
            self._do_internal_merges(words, new_tree, new_path)

        # Instead of internal merges, it is an option to just move to next word (if there are words)
        if words:  # and not must_do_im:
            self._process_word(words[1:], tree, path)

    def parse(self, sentence):
        """ Parse that is greedy to external merge. Do external merge if there would be compatible features w. trunk"""
        # print(f'*** Parsing {sentence}')
        self.results = []
        self.good_paths = []
        self.nodes = 0
        if isinstance(sentence, str):
            words = sentence.split()
        else:
            words = list(sentence)
        self.correct = list(words)
        self._process_word(words, start_element(), [])
        succs = []
        for path, tree in self.results:
            linear = linearize(tree)
            if linear == self.correct:
                self.good_paths.append(path)
                succs.append(tree)
        print(f'  {"✔" if succs else "-"} {len(succs)} / {len(self.results)} trees, {self.nodes} nodes')
        if self.forest:
            self.export_to_kataja()
        return succs

    def add_to_parse_path(self, path, root, message):
        if self.forest:
            groups = [('mover', [root.mover] if root and root.mover else []),
                      ('tree', [root] if root else []),
                      ('riser', [root.riser] if root and root.riser else [])]
            if root:
                _update_check_information_for_features(root)
            syn_state = SyntaxState(tree_roots=[root] if root else [], msg=message, groups=groups)
            derivation_step = DerivationStep(syn_state)
            derivation_step.freeze()
            return path + [derivation_step]
        else:
            return path + [root]

    def export_to_kataja(self):
        if REMOVE_BAD_PARSES and self.good_paths:
            paths = self.good_paths
        else:
            paths = [path for path, tree in self.results]
        for i, path in enumerate(paths):
            for syn_state in path:
                self.forest.add_step(syn_state, i)


if __name__ == '__main__':
    t = time.time()
    lexicon = read_lexicon('lexicon_en.txt')
    parser = Parser(lexicon)
    sentences = []
    readfile = open('sentences_en2.txt', 'r')
    for line in readfile:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('['):
            sentences.append(line)
    successes = 0
    fails = 0
    i = 0
    for i, sentence in enumerate(sentences, 1):
        print(f'{i}. "{sentence}"')
        result_trees = parser.parse(sentence)
        if result_trees:
            successes += 1
        else:
            fails += 1

    print('=====================')
    print(f'    {successes}/{i} ')
    print('=====================')
    print('Parsing sentences took: ', time.time() - t)
    print('ticks: ', parser.ticks)
