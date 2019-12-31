try:
    from kataja.syntax.BaseConstituent import BaseConstituent as Constituent
    from kataja.syntax.BaseFeature import BaseFeature as Feature
    from kataja.syntax.SyntaxState import SyntaxState
except ImportError:
    from Constituent import Constituent
    from Feature import Feature

    SyntaxState = None
import time


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


def find_mover(node, skip_first=False, is_leftmost=False):
    # finds the uppermost result of external merge element (this is recognized by it having flag 'has_raised')
    if not skip_first and not getattr(node, 'has_raised', None) and (node.parts or not is_leftmost):
        return node
    leftmost = True
    for part in node.parts:
        n = find_mover(part, is_leftmost=leftmost)
        if n:
            return n
        leftmost = False


def find_movers(node, movers, mover_heads, skip_first=False, is_leftmost=False):
    """ Use SURVIVE mechanism from Stroik. If there are unsatisfied positive features (sign == ''), item can be raised
    # again.
    """

    def has_unchecked_positives(node):
        for feat in node.head.features:
            if feat.sign == '' and not feat.checks:
                return True
        return False

    if not skip_first and has_unchecked_positives(node) and node.head not in mover_heads:
        movers.append(node)
        mover_heads.append(node.head)
    for part in node.parts:
        find_movers(part, movers, mover_heads)


def find_mover_old(node, movers, mover_heads, skip_first=False, is_leftmost=False):
    # Previous version sses has_raised flag
    # finds the uppermost result of external merge element (this is recognized by it having flag 'has_raised')
    if not skip_first and not getattr(node, 'has_raised', None) and (node.parts or not is_leftmost) and node.head not \
            in mover_heads:
        movers.append(node)
        mover_heads.append(node.head)
    leftmost = True
    for part in node.parts:
        find_movers(part, movers, mover_heads, is_leftmost=leftmost)
        leftmost = False


# pitää muuttaa niin että molemmat IM- ja EM-tilanteet tarkistetaan ja EM estyy jos IM-ominaisuus on sellainen joka
# täytyy tyydyttää heti kun mahdollista ja tyydytys olisi nyt mahdollista. Pitää tarkistaa järkeily sen takana,
# milloin se onkaan välttämätöntä.
# 'who did John like a picture of'
# Tuossa pitäisi saada 'did+John+like'-suhde luotua jotta 'who' olisi vapaana täydentämään 'a picture of', mutta ei saa
# päästä syntymään 'like+who'-suhdetta. Se tarvitsee tarkkuutta johon nykyinen malli ei kykene.
# Mieti myös olisiko nyt aika laittaa epävarmuutta mukaan: tilanteissa joissa sekä EM ja IM on mahdollisia,
# haarautetaan laskenta. Mieti myös mitä EM-tilanteita oikeasti tarvitaan.
def find_checked_features(pos_head, neg_head,
                          unsatisfied_neg_feature_blocks_neg_search=False,
                          unsatisfied_neg_feature_blocks_pos_search=True,
                          be_aggressive=True):
    found = _find_checked_features(pos_head, neg_head, unsatisfied_neg_feature_blocks_neg_search,
                                   unsatisfied_neg_feature_blocks_pos_search, be_aggressive)
    if found or not be_aggressive:
        return found
    return _find_checked_features(neg_head, pos_head, unsatisfied_neg_feature_blocks_neg_search,
                                  unsatisfied_neg_feature_blocks_pos_search, be_aggressive,
                                  doing_reverse=True)


def _find_checked_features(pos_head, neg_head,
                           unsatisfied_neg_feature_blocks_neg_search=False,
                           unsatisfied_neg_feature_blocks_pos_search=True,
                           be_aggressive=True, doing_reverse=False):
    if neg_head is pos_head:
        return
    for plus_feature in pos_head.features:
        if plus_feature.checks or plus_feature.checked_by:
            continue
        if plus_feature.sign == '':
            # print('finding match for ', plus_feature, ' in ', mover.head.features)
            for neg_feature in neg_head.features:
                if neg_feature.checked_by or neg_feature.checks:
                    continue
                elif neg_feature.sign == '':
                    continue
                elif neg_feature.sign == '-' and neg_feature.name == plus_feature.name:
                    return plus_feature, neg_feature, neg_head
                # elif neg_feature.sign == '~' and neg_feature.name == plus_feature.name and be_aggressive:
                #    return plus_feature, neg_feature, neg_head
                elif neg_feature.sign == '=' and neg_feature.name == plus_feature.name and not doing_reverse:
                    return plus_feature, neg_feature, pos_head
                # elif neg_feature.sign == '≈' and neg_feature.name == plus_feature.name and be_aggressive and not \
                #        doing_reverse:
                #    return plus_feature, neg_feature, pos_head
                if unsatisfied_neg_feature_blocks_neg_search:
                    # print('fail (blocking)')
                    return
        elif unsatisfied_neg_feature_blocks_pos_search:
            # print('fail')
            return


class Parser:
    def __init__(self, lexicon, forest=None):
        self.forest = forest
        self.lexicon = lexicon or {}
        self.used_feature_names = set()
        self.results = []
        self.correct = []
        self.ticks = 0

    def pick_constituent(self, item):
        if item in self.lexicon:
            node = self.lexicon[item].copy()
        else:
            node = Constituent(item)
            self.lexicon[item] = node
        node.head = node
        return node

    @staticmethod
    def _justify_external_merge(next_const, const):
        if const and next_const:
            pos_head = next_const.head
            neg_head = const.head
        else:
            return
        if neg_head is pos_head:
            return
        for plus_feature in pos_head.features:
            if plus_feature.checks or plus_feature.checked_by:
                continue
            if plus_feature.sign == '':
                # print('finding match for ', plus_feature, ' in ', mover.head.features)
                for neg_feature in neg_head.features:
                    if neg_feature.checked_by or neg_feature.checks:
                        continue
                    elif neg_feature.sign == '':
                        continue
                    elif neg_feature.sign == '-' and neg_feature.name == plus_feature.name:
                        return plus_feature, neg_feature
                    elif neg_feature.sign == '>' and neg_feature.name == plus_feature.name:
                        return plus_feature, neg_feature
                    elif neg_feature.sign == '=' and neg_feature.name == plus_feature.name:
                        return plus_feature, neg_feature
            elif plus_feature.sign == '>':
                for neg_feature in neg_head.features:
                    if neg_feature.checked_by or neg_feature.checks:
                        continue
                    elif neg_feature.sign == '' and neg_feature.name == plus_feature.name:
                        return plus_feature, neg_feature

    @staticmethod
    def _find_checked_features_for_im(pos_head, neg_head, doing_reverse=False):
        if neg_head is pos_head:
            return
        for plus_feature in pos_head.features:
            if plus_feature.checks or plus_feature.checked_by:
                continue
            if plus_feature.sign == '':
                # print('finding match for ', plus_feature, ' in ', mover.head.features)
                for neg_feature in neg_head.features:
                    if neg_feature.checked_by or neg_feature.checks:
                        continue
                    elif neg_feature.name == plus_feature.name:
                        if neg_feature.sign == '':
                            continue
                        elif neg_feature.sign == '-':
                            return plus_feature, neg_feature, neg_head
                        # elif neg_feature.sign == '~':
                        #    return plus_feature, neg_feature, neg_head
                        elif neg_feature.sign == '>':  # and not doing_reverse:
                            return plus_feature, neg_feature, pos_head
                        elif neg_feature.sign == '=' and not doing_reverse:
                            return plus_feature, neg_feature, pos_head
                        # elif neg_feature.sign == '≈' and not doing_reverse:
                        #    return plus_feature, neg_feature, pos_head
            else:
                break

    def _justify_internal_merge(self, tree):
        movers = []
        mover_heads = [tree.head]
        find_movers(tree, movers, mover_heads, skip_first=True)
        internal_merge_is_possible = None
        if movers:
            movers = movers[:1]
            # mover = movers[0]
            for mover in movers:
                internal_merge_is_possible = self._find_checked_features_for_im(tree.head, mover.head)
                if not internal_merge_is_possible:
                    internal_merge_is_possible = self._find_checked_features_for_im(mover.head, tree.head,
                                                                                    doing_reverse=True)
                if internal_merge_is_possible:
                    break
        return movers, internal_merge_is_possible

    def sg_justify_internal_merge(self, tree):
        mover = find_mover(tree, skip_first=True)
        internal_merge_is_possible = None
        if mover:
            internal_merge_is_possible = self._find_checked_features_for_im(tree.head, mover.head)
            if not internal_merge_is_possible:
                internal_merge_is_possible = self._find_checked_features_for_im(mover.head, tree.head,
                                                                                doing_reverse=True)
        return mover, internal_merge_is_possible

    def _process_const(self, next_const, const, tree, remaining):
        # print('process const: ', const, remaining)

        # External merge new constituent
        # print('>: ', const.label)
        tree = Constituent(const.label, parts=[const, tree]) if tree else const
        tree.head = const  # Result of EM always has new constituent as head

        external_merge_is_possible = self._justify_external_merge(next_const, tree)
        # Do Internal merge as many times as possible
        movers, internal_merge_is_possible = self._justify_internal_merge(tree)
        self.export_to_kataja([next_const, tree], f'External merge {const.label}', movers, tree.head)
        if internal_merge_is_possible and external_merge_is_possible:
            tree_feat, mover_feat, head = internal_merge_is_possible
            # if mover_feat.sign == '~' or mover_feat.sign == '≈' or mover_feat.sign == '>':
            #    pass
            # else:
            em_mover_f, em_tree_f = external_merge_is_possible
            print(f'   doing split because IM is possible, {mover_feat, tree_feat, head.label} and EM is possible:'
                  f" {em_mover_f, em_tree_f, next_const.label}, at const: '{const.label}'")
            if em_mover_f.sign == '>':
                return tree
            elif em_tree_f.sign == '>':
                return tree
            else:
                self._split_and_continue(tree, remaining)
        elif external_merge_is_possible:
            self.export_to_kataja([next_const, tree], f"Eager EM for '{next_const.label}'", tree.head, next_const)
            return tree
        while internal_merge_is_possible:
            tree_feat, mover_feat, head = internal_merge_is_possible
            if mover_feat.sign == '>':
                mover_feat.checked_by = tree_feat
            else:
                tree_feat.check(mover_feat)
            # print('^: ', head.label)
            mover = movers[0]
            tree = Constituent(label=head.label, parts=[mover, tree])
            tree.head = head
            mover.has_raised = True
            external_merge_is_possible = self._justify_external_merge(next_const, tree)
            movers, internal_merge_is_possible = self._justify_internal_merge(tree)
            focus = next_const if external_merge_is_possible else movers
            self.export_to_kataja([next_const, tree], f'Internal merge {head.label}', focus, tree.head)
            if internal_merge_is_possible and external_merge_is_possible:
                mover_feat, tree_feat, head = internal_merge_is_possible
                # if mover_feat.sign == '~' or mover_feat.sign == '≈' or mover_feat.sign == '>':
                #    continue
                em_mover_f, em_tree_f = external_merge_is_possible
                print(f'   doing split because IM is possible, {mover_feat, tree_feat, head.label} and EM is possible:'
                      f" {em_mover_f, em_tree_f, next_const.label}, at const: '{const.label}'")
                if em_mover_f.sign == '>':
                    break
                elif em_tree_f.sign == '>':
                    break
                else:
                    self._split_and_continue(tree, remaining)
            elif external_merge_is_possible:
                self.export_to_kataja([next_const, tree], f"Eager EM for '{next_const.label}'", tree.head, next_const)
                # print('taking next const because it fits: ', next_const_fits)
                break
        return tree

    def parse(self, sentence):
        """ Parse that is greedy to external merge. Do external merge if there would be compatible features w. trunk"""
        # print(f'*** Parsing {sentence}')
        self.results = []
        if isinstance(sentence, str):
            words = sentence.split()
        else:
            words = list(sentence)
        self.correct = list(words)
        tree = None
        const = None
        self._process_words(tree, const, words)
        return self.results

    def _process_words(self, tree, const, words):
        for i, word in enumerate(words):
            next_const = self.pick_constituent(word)
            if const:
                tree = self._process_const(next_const, const, tree, words[i:])
            const = next_const
        tree = self._process_const(None, const, tree, [])
        linear = linearize(tree)
        if linear == self.correct:
            self.results.append(tree)
            print('  ok')
            return True
        else:
            print(f"  fail: {' '.join(linear)}")
            return False

    def _split_and_continue(self, tree, remaining):
        copy_of_tree = tree.copy()
        return self._process_words(copy_of_tree, None, remaining)

    def export_to_kataja(self, tree, message, marked=None, marked2=None):
        self.ticks += 1
        if self.forest:
            if marked and not isinstance(marked, list):
                marked = [marked]
            if marked2 and not isinstance(marked2, list):
                marked2 = [marked2]
            if tree and not isinstance(tree, list):
                tree = [tree]
            syn_state = SyntaxState(tree_roots=tree, msg=message, groups=[('', marked), ('', marked2)])
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
            for result_tree in result_trees:
                print('  ✔ ' + ' '.join(linearize(result_tree)))
        else:
            print(f'  X fail')
            fails += 1

    print('=====================')
    print(f'    {succs}/{i} ')
    print('=====================')
    print('Parsing sentences took: ', time.time() - t)
    print('ticks: ', parser.ticks)
