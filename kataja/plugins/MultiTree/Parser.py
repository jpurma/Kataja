try:
    from kataja.plugins.MultiTree.Constituent import Constituent
    from kataja.plugins.MultiTree.Feature import Feature
    from kataja.syntax.SyntaxState import SyntaxState
except ImportError:
    from Constituent import Constituent
    from Feature import Feature

    SyntaxState = None
import time

REMOVE_BAD_PARSES = True


def read_lexicon(filename):
    lexicon = {}
    for line in open(filename):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        label, foo, fstring = line.partition('::')
        label = label.strip()
        feats = [Feature.from_string(fs) for fs in fstring.split()]
        const = Constituent(label=label)
        const.features = feats
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
        else:
            result.append(node.label)

    _walk_tree(tree)
    return result


def inherit_features(tree, head):
    tree.features = [f for f in head.features if f is not tree.checks and f is not tree.checked_by]


def _final_head(const):
    while const.head is not const:
        const = const.head
    return const


def _update_check_information_for_features(tree):
    feature_checks = set()
    features = set()

    def walk_tree(node):
        if node.parts:
            if node.checker or node.checked:
                feature_checks.add((node.checker, node.checked))
            walk_tree(node.parts[0])
            walk_tree(node.parts[1])
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
        self.parsing_branches = 0
        self.good_paths = []
        self.stored_paths = set()
        self.ticks = 0

    def pick_constituent(self, item):
        if item in self.lexicon:
            node = self.lexicon[item].copy()
        else:
            node = Constituent(item)
            self.lexicon[item] = node.copy()
        node.head = node
        return node

    @staticmethod
    def _find_checked_features_for_im(pos_head, neg_head):
        for plus_feature in pos_head.features:
            if plus_feature.sign == '':
                for neg_feature in neg_head.features:
                    if neg_feature.name == plus_feature.name:
                        if neg_feature.sign == '-':
                            return plus_feature, neg_feature, neg_head
                        elif neg_feature.sign == '_':
                            return plus_feature, neg_feature, neg_head
                        elif neg_feature.sign == '>':
                            return plus_feature, neg_feature, pos_head
                        elif neg_feature.sign == '=':
                            return plus_feature, neg_feature, pos_head
            else:
                break

    @staticmethod
    def _find_checked_features_for_im2(pos_head, neg_head):
        for plus_feature in pos_head.features:
            if plus_feature.sign == '':
                for neg_feature in neg_head.features:
                    if neg_feature.name == plus_feature.name:
                        if neg_feature.sign == '-':
                            return plus_feature, neg_feature, neg_head
                        elif neg_feature.sign == '_':
                            return plus_feature, neg_feature, neg_head
            else:
                break

    def _justify_external_merge(self, next_const, tree):
        # return next_const and self._justify_comp_merge(tree, next_const, strict=False)
        return next_const and (self._justify_spec_merge(tree, next_const, strict=False)
                               or self._justify_comp_merge(tree, next_const, strict=False))

    @staticmethod
    def _justify_comp_merge(mover, tree, strict=True):
        for plus_feature in tree.features:
            if plus_feature.sign == '':
                for neg_feature in mover.features:
                    if neg_feature.name == plus_feature.name:
                        if neg_feature.sign == '=':
                            return plus_feature, neg_feature
            elif strict:
                break

    @staticmethod
    def _justify_spec_merge(mover, tree, strict=True):
        for plus_feature in mover.features:
            if plus_feature.sign == '':
                for neg_feature in tree.features:
                    if neg_feature.name == plus_feature.name:
                        if neg_feature.sign == '-':
                            return plus_feature, neg_feature
            elif strict:
                break

    @staticmethod
    def _q_raising_is_possible(tree, strict=True):
        mover = tree and tree.Q
        if not mover:
            return
        for plus_feature in mover.features:
            if plus_feature.sign == '':
                for neg_feature in tree.features:
                    if neg_feature.name == plus_feature.name and (neg_feature.sign == '-' or neg_feature.sign == '='):
                        return plus_feature, neg_feature
            elif strict:
                break

    @staticmethod
    def _is_q_raiser(const):
        for feature in const.features:
            if feature.sign == '*':
                return True

    @staticmethod
    def _find_mover(tree):
        for mover in tree.movers:
            return mover

    def _process_const(self, next_const, const, old_tree, remaining, branch_path):
        self.ticks += 1

        # External merge new constituent
        tree = Constituent(label=const.label,
                           parts=[const, old_tree],
                           movers=[old_tree] + old_tree.movers,
                           head=const,
                           features=const.features[:],
                           Q=old_tree.Q) if old_tree else const
        if self._is_q_raiser(const):
            tree.Q = const

        self.export_to_kataja([next_const, tree], f"External merge '{const.label}'", tree.movers, tree,
                              branch_path=branch_path)

        # Do Internal merge as many times as possible
        while True:
            mover = self._find_mover(tree)
            if not mover:
                break
            # Priorities:

            print('movers for tree: ', tree.label, tree.movers)
            print('movers for mover:', mover.label, mover.movers)
            spec_merge_is_possible = self._justify_spec_merge(mover, tree)
            self.export_to_kataja([next_const, tree], f"Evaluating spec merge '{tree.label}'", tree, mover,
                                  branch_path=branch_path)
            print(mover.features, tree.features)
            if next_const:
                external_merge_is_possible = self._justify_external_merge(next_const, tree)
            else:
                external_merge_is_possible = False
            if external_merge_is_possible:
                self.export_to_kataja([next_const, tree], f"Eager to EM next const '{next_const.label}'", tree,
                                      next_const, branch_path=branch_path)
                break
            if spec_merge_is_possible:
                checker, checked = spec_merge_is_possible
                print('doing spec merge, movers before: ', mover.movers, tree.movers)
                movers = mover.movers + [m for m in tree.movers if m is not mover and m not in mover.movers]
                print('doing spec merge, movers after: ', movers)
                tree = Constituent(label=tree.label,
                                   parts=[mover, tree],
                                   movers=movers,
                                   head=tree,
                                   features=[f for f in tree.features if f is not checked],
                                   checker=checker,
                                   checked=checked,
                                   Q=tree.Q or mover.Q)
                print('features after: ', tree.features)
                self.export_to_kataja([next_const, tree], f"Spec merge '{tree.label}'",
                                      branch_path=branch_path)
                continue

            comp_merge_is_possible = self._justify_comp_merge(mover, tree)
            self.export_to_kataja([next_const, tree], f"Evaluating comp merge '{tree.label}'", mover, tree,
                                  branch_path=branch_path)
            if comp_merge_is_possible:
                checker, checked = comp_merge_is_possible
                print('checker: ', checker, 'checked: ', checked)
                print('doing comp merge, movers before: ', mover.movers, tree.movers)
                movers = mover.movers + [m for m in tree.movers if m is not mover and m not in mover.movers]
                print('doing comp merge, movers after: ', movers)

                tree = Constituent(label=mover.label,
                                   parts=[mover, tree],
                                   movers=movers,
                                   head=mover,
                                   features=[f for f in mover.features if f is not checked],
                                   checker=checker,
                                   checked=checked,
                                   Q=mover.Q or tree.Q)
                print('features after: ', tree.features)
                self.export_to_kataja([next_const, tree], f"Comp merge '{tree.label}'", mover, tree,
                                      branch_path=branch_path)
                continue

            q_raising_is_possible = self._q_raising_is_possible(tree)
            if q_raising_is_possible:
                checker, checked = q_raising_is_possible
                tree = Constituent(label=tree.label,
                                   parts=[tree.Q, tree],
                                   movers=tree.movers,  # not sure...
                                   head=tree,
                                   features=[f for f in tree.features if f is not checked],
                                   checker=checker,
                                   checked=checked)
                self.export_to_kataja([next_const, tree], f"Q raising to spec '{tree.label}'",
                                      branch_path=branch_path)
                continue
            else:
                break
            # mover, internal_merge_is_possible = self._justify_internal_merge(tree)
            # external_merge_is_possible = self._justify_external_merge(next_const, tree)
            # if not internal_merge_is_possible:
            #     break
            # self.ticks += 1
            # if external_merge_is_possible:
            #     self.export_to_kataja([next_const, tree], "Split because EM and IM both possible, first do EM.",
            #                           tree, next_const, branch_path=branch_path)
            #     self._split_and_continue(tree, remaining, branch_path)
            #     branch_path += 'i'
        return tree, branch_path

    def _split_and_continue(self, tree, remaining, branch_path):
        self.parsing_branches += 1
        return self._process_words(tree, None, remaining, branch_path + 'e')

    def parse(self, sentence):
        """ Parse that is greedy to external merge. Do external merge if there would be compatible features w. trunk"""
        # print(f'*** Parsing {sentence}')
        self.results = []
        self.stored_paths = set()
        self.parsing_branches = 1
        self.ticks = 0
        if isinstance(sentence, str):
            words = sentence.split()
        else:
            words = list(sentence)
        self.correct = list(words)
        tree = None
        const = None
        self._process_words(tree, const, words, '')
        return self.results

    def _process_words(self, tree, const, words, branch_path):
        for i, word in enumerate(words):
            next_const = self.pick_constituent(word)
            if const:
                tree, branch_path = self._process_const(next_const, const, tree, words[i:], branch_path)
            const = next_const
        tree, branch_path = self._process_const(None, const, tree, [], branch_path)
        linear = linearize(tree)
        if linear == self.correct:
            self.export_to_kataja([tree], ' '.join(linear), branch_path=branch_path)
            self.good_paths.append(branch_path)
            print('  ✔ ' + ' '.join(linear))
            self.results.append(tree)
            return True
        else:
            self.export_to_kataja([tree], 'Crash', branch_path=branch_path)
            print(f"  fail: {' '.join(linear)}")
            return False

    def export_to_kataja(self, trees, message, marked=None, marked2=None, branch_path=''):
        if self.forest:
            if marked and not isinstance(marked, list):
                marked = [marked]
            if marked2 and not isinstance(marked2, list):
                marked2 = [marked2]
            if trees and not isinstance(trees, list):
                trees = [trees]
            for tree in trees:
                if tree:
                    _update_check_information_for_features(tree)
            self.stored_paths.add(branch_path)
            print(message)
            syn_state = SyntaxState(tree_roots=trees, msg=message, groups=[('', marked), ('', marked2)],
                                    state_id=branch_path)
            self.forest.add_step(syn_state)


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
    succs = 0
    fails = 0
    i = 0
    for i, sentence in enumerate(sentences, 1):
        print(f'{i}. "{sentence}"')
        result_trees = parser.parse(sentence)
        if result_trees:
            succs += 1
        else:
            fails += 1

    print('=====================')
    print(f'    {succs}/{i} ')
    print('=====================')
    print('Parsing sentences took: ', time.time() - t)
    print('ticks: ', parser.ticks)
