from itertools import chain

try:  # When this is imported in Kataja context
    from plugins.TreesAreMemory.Constituent import Constituent
    from plugins.TreesAreMemory.Feature import Feature
    from kataja.syntax.SyntaxState import SyntaxState
    from plugins.TreesAreMemory.utils import simple_bracket_tree_parser
except ImportError:  # this is run as a standalone, from command line
    from Constituent import Constituent
    from Feature import Feature
    from utils import simple_bracket_tree_parser

    SyntaxState = None


def load_lexicon(lines):
    d = {}
    for line in lines:
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        key, definition = line.split('::')
        key = key.strip()
        definitions = definition.split()
        features = [Feature.from_string(df.strip()) for df in definitions]
        d[key] = Constituent(label=key, features=features, morphology=key)
    return d


class TreesAreMemoryParser:
    def __init__(self, lexicon, forest=None):
        if isinstance(lexicon, dict):
            self.lexicon = lexicon
        else:
            self.lexicon = load_lexicon(lexicon)
        self.forest = forest

    def read_lexicon(self, entry_list, lexicon=None):
        self.lexicon = load_lexicon(entry_list)

    def parse(self, sentence):
        word_list = self.normalize_input(sentence.strip().split())
        if not word_list:
            return None
        next_const = self.get_lexeme(word_list.pop(0))
        return self._parse(next_const, None, word_list)

    def _parse(self, next_const, tree, word_list):

        # Check if new node has immediate justification for merging with tree.
        if tree:
            next_will_match = self.find_matching_features_for(next_const, tree, deep=False)
        else:
            next_will_match = False
        if next_will_match:
            # ...if match is found a pile of nodes in wrong order is put at the top of the tree
            msg = f'Merge because "{next_const}" fits into ongoing phrase. "{tree.label}", {next_will_match[0]}' \
                  f' & {next_will_match[2]}'
            tree = self.merge(next_const, tree)
            self.export_to_kataja(tree, msg)
        else:
            # otherwise we attempt to fix the structure before merging a new node into it.
            # fixing is done by raising nodes as long as we can.
            msg = f'Next constituent "{next_const}" doesn´t fit into ongoing phrase. "{tree and tree.label}".\n'
            match = self.find_matching_features_for(tree, tree)
            if match:  # match is a tuple that has match_feat, match_node, feat
                msg += f'Internal Merge {match[1].label} to repair {tree.label}'
                tree = self.raise_matching_features(match, tree)
                self.export_to_kataja(tree, msg)
                return self._parse(next_const, tree, word_list)
            elif next_const:
                if tree:
                    msg = f'Merge after raising "{next_const}" to "{tree.label}"'
                    tree = self.merge(next_const, tree)
                else:
                    msg = f'Starting new tree from "{next_const}"'
                    tree = next_const
                self.export_to_kataja(tree, msg)
        if not (word_list or next_const):
            print('stop parsing because no words left and nothing to do')
            return tree
        next_const = self.get_lexeme(word_list.pop(0)) if word_list else None
        return self._parse(next_const, tree, word_list)

    @staticmethod
    def merge(left, right):
        merged = Constituent(label=left.label, left=left, right=right)
        merged.inherited_features = list(left.features)
        merged.head = left.head
        # print('made a naive merge: ', merged, merged.inherited_features)
        return merged

    @staticmethod
    def raise_matching_features(matching_features, tree):
        """ Feature match that is justifying this merge is also used to configure the merge. """
        match_feat, const, feat = matching_features
        # print('matching features: ', match_feat, match_feat.leads, feat, feat.leads)

        # Label
        label = '-'
        if match_feat.leads and not feat.leads_other:
            inherited_from_const = const.inherited_features
            label = const.label
        else:
            inherited_from_const = [match_feat]
        if feat.leads and not match_feat.leads_other:
            inherited_from_tree = tree.inherited_features
            label = tree.label
        else:
            inherited_from_tree = [feat]
        if match_feat.leads and feat.leads:
            label = f'{const.label}+{tree.label}'

        # Checking
        if match_feat.positive:
            checked_features = [feat, match_feat]
            match_feat.checks = feat
            feat.checked_by = match_feat
        else:
            checked_features = [match_feat, feat]
            feat.checks = match_feat
            match_feat.checked_by = feat

        # Features are satisfied or not
        if match_feat.expires_in_use and feat.expires_other:
            match_feat.used = True
        if feat.expires_in_use and match_feat.expires_other:
            feat.used = True

        # Directionality, e.g. which goes left
        if match_feat.goes_left and feat.goes_left:
            const_is_left = not feat.positive
        elif not (match_feat.goes_left or feat.goes_left):
            const_is_left = not match_feat.positive
        else:
            const_is_left = match_feat.goes_left
        if const_is_left:
            left = const
            right = tree
            inherited_features = inherited_from_const + inherited_from_tree
        else:
            left = tree
            right = const
            inherited_features = inherited_from_tree + inherited_from_const

        merged = Constituent(label=label, left=left, right=right)

        # Is this phase? - should we stop search here
        if match_feat.phase_barrier or feat.phase_barrier:
            merged.phase_barrier = True
            # print('set up phase barrier at ', merged)
            # print(merged.word_edge)
        if match_feat.leads:
            merged.head = const.head
        else:
            merged.head = tree.head
        merged.checked_features = checked_features
        merged.inherited_features = inherited_features
        return merged

    def find_matching_features_for(self, const, tree, deep=True):
        if not (const and tree and tree.parts):
            return
        for feat in const.inherited_features:
            # print(f'looking for match w. {feat} (has_initiative: {feat.has_initiative})')
            if not feat.has_initiative:
                if feat.blocks and not feat.is_satisfied():
                    break
                continue
            if feat.is_satisfied():
                continue
            passed = {const}
            match = self.find_match_for(feat, tree, passed, deep)
            if match:
                return match
            if feat.blocks and not feat.is_satisfied():
                break

    def find_match_for(self, feat, const, passed, deep=True):
        passed.add(const)
        # print('at ', const.label, ' looking for match for ', feat)
        # print('inherited features here:  ', const.inherited_features)
        for match_feat in const.inherited_features:
            if (match_feat.name == feat.name and
                    not match_feat.is_satisfied() and
                    feat.host is not match_feat.host and
                    match_feat.positive != feat.positive):
                return match_feat, const, feat

            if match_feat.blocks and feat.host is not match_feat.host and not match_feat.is_satisfied():
                print('breaking feature search because block: ', match_feat)
                return

        if deep and not const.phase_barrier:
            if const.left and const.left not in passed:
                match = self.find_match_for(feat, const.left, passed)
                if match:
                    return match
            if const.right and const.right not in passed:
                return self.find_match_for(feat, const.right, passed)
        elif deep and const.phase_barrier:
            if const.left and const.left not in passed and const.left.right and const.left.right not in passed:
                return self.find_match_for(feat, const.left.right, passed, deep=False)

    def normalize_input(self, lst):
        return list(chain.from_iterable([reversed(self.get_morphology(w).split("#")) for w in lst]))

    def get_lexeme(self, key):
        if key in self.lexicon:
            return self.lexicon[key].copy()
        return Constituent(label=key)

    def get_morphology(self, key):
        return self.lexicon[key].morphology if key in self.lexicon else key

    @staticmethod
    def spellout(tree):
        def _spellout(tree, used):
            if tree in used:  # don't visit any branch twice
                return []
            used.add(tree)
            if tree.left:
                return _spellout(tree.left, used) + _spellout(tree.right, used)
            else:
                return [str(tree)]

        used = set()
        res = _spellout(tree, used)
        return ' '.join(res)

    def export_to_kataja(self, tree, message):
        if self.forest:
            print(message)
            syn_state = SyntaxState(tree_roots=[tree], msg=message)
            self.forest.add_step(syn_state)
