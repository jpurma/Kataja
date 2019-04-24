try:
    from MultiTree.Constituent import Constituent
    from kataja.syntax.BaseFeature import BaseFeature as Feature
    from kataja.syntax.SyntaxState import SyntaxState
except ImportError:
    from Constituent import Constituent
    from Feature import Feature
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
            if node.checks or node.checked_by:
                feature_checks.add((node.checks, node.checked_by))
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
    def _justify_external_merge(pos_head, neg_head):
        if not pos_head and neg_head:
            return
        if _final_head(neg_head) is _final_head(pos_head):
            return
        for plus_feature in pos_head.features:
            if plus_feature.sign == '':
                # print('finding match for ', plus_feature, ' in ', mover.head.features)
                for neg_feature in neg_head.features:
                    if neg_feature.sign == '':
                        continue
                    elif neg_feature.sign == '-' and neg_feature.name == plus_feature.name:
                        return plus_feature, neg_feature
                    elif neg_feature.sign == '>' and neg_feature.name == plus_feature.name:
                        return plus_feature, neg_feature
                    elif neg_feature.sign == '=' and neg_feature.name == plus_feature.name:
                        return plus_feature, neg_feature
            #elif plus_feature.sign == '>':
            #    for neg_feature in neg_head.features:
            #        if neg_feature.sign == '' and neg_feature.name == plus_feature.name:
            #            return plus_feature, neg_feature

    @staticmethod
    def _find_checked_features_for_im(pos_head, neg_head, doing_reverse=False):
        for plus_feature in pos_head.features:
            if plus_feature.sign == '':
                # print('finding match for ', plus_feature, ' in ', mover.head.features)
                for neg_feature in neg_head.features:
                    if neg_feature.name == plus_feature.name:
                        if neg_feature.sign == '':
                            continue
                        elif neg_feature.sign == '-':
                            return plus_feature, neg_feature, neg_head
                        elif neg_feature.sign == '>' and not doing_reverse:
                            return plus_feature, neg_feature, pos_head
                        elif neg_feature.sign == '=' and not doing_reverse:
                            return plus_feature, neg_feature, pos_head
            else:
                break

    def _justify_internal_merge(self, tree):
        mover = None
        if tree.movers:
            mover = tree.movers[0]
        internal_merge_is_possible = None
        if mover:
            internal_merge_is_possible = self._find_checked_features_for_im(tree, mover)
            if internal_merge_is_possible:
                return mover, internal_merge_is_possible
            internal_merge_is_possible = self._find_checked_features_for_im(mover, tree, doing_reverse=True)
        return mover, internal_merge_is_possible

    def _process_const(self, next_const, const, old_tree, remaining, branch_path):
        if not const:
            return old_tree, branch_path
        self.ticks += 1

        # External merge new constituent
        tree = Constituent(label=const.label,
                           parts=[const, old_tree],
                           movers=[old_tree] + old_tree.movers,
                           head=const,
                           features=const.features[:]) if old_tree else const

        external_merge_is_possible = self._justify_external_merge(next_const, tree)
        # Do Internal merge as many times as possible
        mover, internal_merge_is_possible = self._justify_internal_merge(tree)
        self.export_to_kataja([next_const, tree], f"External merge '{const.label}'", tree.movers, tree,
                              branch_path=branch_path)
        if internal_merge_is_possible and external_merge_is_possible:
            self.export_to_kataja([next_const, tree], "Split because EM and IM both possible, first do EM.",
                                  tree, next_const, branch_path=branch_path)
            self._split_and_continue(tree, remaining, branch_path)
            branch_path += 'i'
        elif external_merge_is_possible:
            self.export_to_kataja([next_const, tree], f"Eager EM for '{next_const.label}'", tree, next_const,
                                  branch_path=branch_path)
            return tree, branch_path
        while internal_merge_is_possible:
            self.ticks += 1
            tree_feat, mover_feat, head = internal_merge_is_possible
            movers = mover.movers + [m for m in tree.movers if m is not mover and m not in mover.movers]
            checks = mover_feat
            checked_by = tree_feat if mover_feat.sign != '>' else None
            tree = Constituent(label=head.label,
                               parts=[mover, tree],
                               movers=movers,
                               head=head,
                               features=[f for f in head.features if f is not checks and f is not checked_by],
                               checks=checks,
                               checked_by=checked_by)
            external_merge_is_possible = self._justify_external_merge(next_const, tree)
            mover, internal_merge_is_possible = self._justify_internal_merge(tree)
            self.export_to_kataja([next_const, tree], f"Internal merge '{head.label}'", tree.movers, tree,
                                  branch_path=branch_path)
            if internal_merge_is_possible and external_merge_is_possible:
                self.export_to_kataja([next_const, tree], "Split because EM and IM both possible, first do EM.",
                                      tree, next_const, branch_path=branch_path)
                self._split_and_continue(tree, remaining, branch_path)
                branch_path += 'i'
            elif external_merge_is_possible:
                self.export_to_kataja([next_const, tree], f"Eager EM for '{next_const.label}'", tree,
                                      next_const, branch_path=branch_path)
                break
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
        if self.forest and self.results and REMOVE_BAD_PARSES:
            self.remove_bad_parses()
        return self.results

    def _process_words(self, tree, const, words, branch_path):
        for i, word in enumerate(words):
            next_const = self.pick_constituent(word)
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

    def remove_bad_parses(self):
        bad_paths = []
        for path in self.stored_paths:
            found = False
            for good_path in self.good_paths:
                if good_path.startswith(path):
                    found = True
                    break
            if not found:
                bad_paths.append(path)
        self.forest.remove_iterations(bad_paths)

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
            syn_state = SyntaxState(tree_roots=trees, msg=message, marked=marked, marked2=marked2, iteration=branch_path)
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
