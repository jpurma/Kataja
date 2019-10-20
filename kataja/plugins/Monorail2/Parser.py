from itertools import chain

try:  # When this is imported in Kataja context
    from Monorail2.Constituent import Constituent
    from Monorail2.Feature import Feature
    from kataja.syntax.SyntaxState import SyntaxState
    from Monorail2.utils import simple_bracket_tree_parser
except ImportError:  # this is run as a standalone, from command line
    SyntaxState = object
    from Constituent import Constituent
    from Feature import Feature
    from utils import simple_bracket_tree_parser


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


class Parser:
    def __init__(self, lexicon, forest=None):
        if isinstance(lexicon, dict):
            self.lexicon = lexicon
        else:
            self.lexicon = load_lexicon(lexicon)
        self.forest = forest
        self.count = 0

    def new_state_ids(self):
        c = self.count
        self.count += 1
        return c or None, self.count

    def read_lexicon(self, entry_list, lexicon=None):
        self.lexicon = load_lexicon(entry_list)

    @staticmethod
    def tree_to_monorail(tree):
        """ """
        recipe = []

        def _tree_to_monorail(lnode, spine):
            if lnode.parts:
                left = _tree_to_monorail(lnode.left, spine)
                right = _tree_to_monorail(lnode.right, left)
                merged = Constituent(label='', left=left, right=right)
                recipe.append('|')
            elif spine:
                left = Constituent(label=lnode.label)
                recipe.append(lnode)
                merged = Constituent(label='', left=left, right=spine)
            else:
                merged = Constituent(label=lnode.label)
                recipe.append(lnode)
            return merged

        return _tree_to_monorail(tree, None), recipe

    def parse(self, sentence):
        sentence = sentence.strip()
        if sentence.startswith('['):
            # First derivation step shows tree as it is given by the bracket structure
            tree = simple_bracket_tree_parser(sentence, Constituent)
            self.export_to_kataja(tree, sentence, state_id='original')
            # Second step shows how the tree could be reconstructed
            tree, recipe = self.tree_to_monorail(tree)
            print('recipe: ', [str(x) for x in recipe])
            self.export_to_kataja(tree, str(recipe), state_id='rebuilt')
            print(tree)
            return tree
        return self._parse(None, self.normalize_input(sentence.split()))

    def _parse(self, tree, word_list):
        if tree:
            matching_features = self.find_matching_features(tree)
        else:
            matching_features = None

        while matching_features:
            tree = self.raise_matching_features(matching_features, tree)
            if self.forest:
                parent_id, state_id = self.new_state_ids()
                self.export_to_kataja(tree, 'Internal Merge', state_id=state_id, parent_id=parent_id)
            matching_features = self.find_matching_features(tree)

        if not word_list:
            return tree

        new_const = self.get_lexeme(word_list.pop(0))

        tree = self.merge(new_const, tree) if tree else new_const
        if self.forest:
            parent_id, state_id = self.new_state_ids()
            self.export_to_kataja(tree, f'Merge {new_const}', state_id=state_id, parent_id=parent_id)
        return self._parse(tree, word_list)

    @staticmethod
    def merge(left, right):
        merged = Constituent(label=left.label, left=left, right=right)
        merged.inherited_features = list(left.features)
        merged.head = left.head
        return merged

    def raise_matching_features(self, matching_features, tree):
        fplus, found = matching_features
        fminus, raising = found

        if fminus.sign == '-':
            head = tree
            other = raising
        else:
            head = raising
            other = tree

        if fminus.sign == '_':
            merged = Constituent(label=head.label, left=tree, right=raising)
        else:
            merged = Constituent(label=head.label, left=raising, right=tree)
        merged.inherited_features = self.inherit_features(head, other, fminus.sign)
        merged.features = head.features
        merged.head = head.head
        fplus.checks = fminus
        fminus.checked_by = fplus
        if fplus.sign == '.':
            fminus.used = False
            fplus.used = True
        elif fplus.sign == '*':
            fminus.used = True
            fplus.used = False
        else:
            fminus.used = True
            fplus.used = True
        merged.checked_features = [fminus, fplus]
        if fminus.phasemaker:
            print('setting as phase: ', raising.label)
            raising.phase = True
        return merged

    @staticmethod
    def inherit_features(head, other, sign):
        if head.phase:
            return [x for x in head.head.features if not x.used]
        if sign == '=':
            new = []
            for f in (head.inherited_features or head.features) + (other.inherited_features or other.features):
                if f not in new and not f.used:
                    new.append(f)
            return new
        elif sign == '-':
            new = []
            for f in (head.inherited_features or head.features):
                if f not in new and not f.used:
                    new.append(f)
            return new

    def find_matching_features(self, tree):
        print(tree.inherited_features)
        for fplus in tree.inherited_features:
            if fplus.used:
                continue
            elif fplus.blocks:
                if fplus.checked_by:
                    print('ok to continue, there is someone')
                    continue
                else:
                    break
            elif not fplus.positive():
                continue
            print('look match for ', fplus)
            done = {tree}
            if tree.phase:
                continue
            if tree.left and tree.label == tree.left.label:
                head = tree.left
                other = tree.right
            elif tree.right and tree.label == tree.right.label:
                head = tree.right
                other = tree.left
            else:
                return
            found = self._find_match_for(fplus, head, done, tree.head)
            if found:
                return fplus, found
            found = self._find_match_for(fplus, other, done, tree.head)
            if found:
                return fplus, found

    def _find_match_for(self, fplus, tree, done, banned_head, go_deeper=True):
        if tree in done:
            return
        done.add(tree)
        # print('looking at features: ', tree.inherited_features or tree.features)
        if tree.head is not banned_head:
            for fminus in tree.inherited_features or tree.features:
                if fminus.used:
                    continue
                elif (fminus.name == fplus.name and
                      fminus.host is not fplus.host and
                      fminus.negative()):
                    print('found match: ', fminus)
                    return fminus, tree
                elif fminus.blocks and not fminus.checked_by:
                    print('stop looking, blocked:', fminus)
                    return
        if (not go_deeper) or tree.phase:
            return
        if tree.left and tree.head is tree.left.head:
            head = tree.left
            other = tree.right
        elif tree.right and tree.head is tree.right.head:
            head = tree.right
            other = tree.left
        else:
            return
        found = self._find_match_for(fplus, head, done, banned_head)
        if found:
            return found
        return self._find_match_for(fplus, other, done, banned_head)

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

    def export_to_kataja(self, tree, message, state_id=None, parent_id=None):
        if self.forest:
            syn_state = SyntaxState(tree_roots=[tree], msg=message, state_id=state_id, parent_id=parent_id)
            self.forest.add_step(syn_state)
