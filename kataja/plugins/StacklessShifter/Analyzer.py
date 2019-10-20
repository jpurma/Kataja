try:
    from kataja.syntax.BaseConstituent import BaseConstituent as Constituent
    from kataja.syntax.BaseFeature import BaseFeature as Feature
    from kataja.syntax.SyntaxState import SyntaxState
    from kataja.plugins.StacklessShifter.Parser import Parser, find_mover, \
        find_checked_features, linearize

except ImportError:
    from Constituent import Constituent
    from Feature import Feature
    from Parser import Parser, find_mover, find_checked_features, linearize
import string
import time


def simple_bracket_tree_parser(sentence):
    """ Handles simple bracket trees where only leaves have text, and spaces cannot be escaped"""

    def finish_const(const):
        if const and const.label:
            c_stack[-1].parts.append(const)
            return None
        return const

    c_stack = []
    sentence = list(reversed(sentence))
    const = None
    parent = None
    in_label = False

    while sentence:
        c = sentence.pop()
        if c == '[' or c == '<':
            const = finish_const(const)
            c_stack.append(Constituent(''))
        elif c == ']' or c == '>':
            const = finish_const(const)
            if c_stack:
                parent = c_stack.pop()
                if c_stack:
                    c_stack[-1].parts.append(parent)
        elif c == ' ':
            if in_label:
                const = Constituent('')
                in_label = False
            else:
                const = finish_const(const)
        elif c == '.' and ((const and not const.label) or not const):
            const = c_stack[-1]
            in_label = True
        else:
            if not const:
                const = Constituent('')
            const.label += c
    return parent


def join_copies(tree):
    d = {}

    def _walk_tree(node):
        d[node.label] = node
        for i, part in enumerate(list(node.parts)):
            label, foo, index = part.label.partition(':')
            if index and index in d:
                node.parts[i] = d[index]
            else:
                if index:
                    d[index] = part
                    part.label = label
                _walk_tree(part)

    _walk_tree(tree)


def remove_copies(tree):
    done = set()

    def _walk_tree(node):
        if not node or node in done:
            return
        done.add(node)
        new_parts = []
        for child in node.parts:
            child = _walk_tree(child)
            if child:
                new_parts.append(child)
        if len(new_parts) == 1:
            return new_parts[0]
        node.parts = new_parts
        return node

    n = _walk_tree(tree)
    return n


def tree_to_monorail(tree):
    recipe = []

    def _tree_to_monorail(node, spine):
        if len(node.parts) == 2:
            left = _tree_to_monorail(node.left, spine)
            right = _tree_to_monorail(node.right, left)
            merged = Constituent(parts=[left, right])
            if node.label.split(':')[0] == node.left.label.split(':')[0]:
                recipe.append('<')
            else:
                recipe.append('>')
        elif spine:  # external merge
            left = Constituent(label=node.label)
            recipe.append(node.label)
            merged = Constituent(parts=[left, spine])
        else:  # first node
            merged = Constituent(label=node.label)
            recipe.append(node.label)
        return merged

    return _tree_to_monorail(tree, None), recipe


class Analyzer(Parser):

    def update_lexicon(self, node):
        lex_item = self.lexicon[node.label]
        new_feats = []
        for feature in node.features:
            f = feature.copy()
            f.checked_by = None
            f.checks = None
            if f in new_feats and not f.sign:
                continue
            new_feats.append(f)
        lex_item.features = new_feats
        lex_item.poke('features')

    def updated(self, node):
        """ If lex item has changed, update this constituent with its new features """
        lex_item = self.lexicon[node.label]
        fstrings = [f.sign + f.name for f in node.features]
        for feature in lex_item.features:
            if feature.sign + feature.name not in fstrings:
                node.features.append(feature.copy())
        node.poke('features')
        return node

    def build_from_recipe_and_justify(self, recipe):
        tree = None
        # self.used_feature_names = set()
        # self.lexicon = {}
        for item in recipe:
            if not tree:
                tree = self.pick_constituent(item)
            elif item == '<' or item == '>':
                mover = find_mover(tree, skip_first=True)
                if not mover:
                    mover = tree.right
                mover.has_raised = True
                tree_head = tree.head
                mover_head = mover.head
                if item == '<':
                    head = mover_head
                else:
                    head = tree_head
                self.make_reason(self.updated(mover_head), self.updated(tree_head), head)
                tree = Constituent(parts=[mover, tree])
                tree.head = head
                tree.label = head.label
            else:
                node = self.pick_constituent(item)
                tree = Constituent(parts=[node, tree])
                tree.head = node
            self.export_to_kataja(tree, item)
        return tree

    def analyze_and_make_features(self, sentence):
        sentence = sentence.strip()
        # 1. Parse bracket tree into constituent structure
        tree = simple_bracket_tree_parser(sentence)
        self.export_to_kataja(tree, sentence)
        # 2. Make all constituents that share indices to be one constituent
        join_copies(tree)
        self.export_to_kataja(tree, sentence)
        # 3. Remove lower instances of constituents.
        remove_copies(tree)
        self.export_to_kataja(tree, sentence)
        # 4. Turn tree into monorail structure and create a recipe that can be used to reconstruct this structure
        tree, recipe = tree_to_monorail(tree)
        self.export_to_kataja(tree, str(recipe))
        # 5. Rebuild the structure from recipe, and while at it, invent features to constituent that would create
        # the same structure
        tree = self.build_from_recipe_and_justify(recipe)
        # 6. Output the structure back to linearized sentence
        linearized = linearize(tree)
        # 7. Try to rebuild the sentence without recipe, with just word order and features
        # tree = self.parse(linearized)
        # linearized = linearize(tree)
        return linearized

    def make_reason(self, mover, spine, head):
        def _insert_neg_feature(neg_feature, mover):
            put_neg_feature_before = None
            for i, neg_feature_candidate in enumerate(mover.features):
                if not neg_feature_candidate.sign:
                    continue
                elif neg_feature_candidate.checked_by or neg_feature_candidate.checks:
                    continue
                put_neg_feature_before = i
                break
            if put_neg_feature_before is not None:
                mover.features.insert(put_neg_feature_before, neg_feature)
            else:
                mover.features.append(neg_feature)
            mover.poke('features')
            neg_feature.host = mover

        def _make_neg_feature(plus_feature, head_is_mover):
            neg_feature = plus_feature.copy()
            if head_is_mover:
                neg_feature.sign = '-'
            else:
                neg_feature.sign = '='
            return neg_feature

        def _insert_plus_feature(put_plus_feature_before, plus_feature, spine):
            if put_plus_feature_before is not None:
                spine.features.insert(put_plus_feature_before, plus_feature)
            else:
                spine.features.append(plus_feature)
            spine.poke('features')
            plus_feature.host = spine

        checked_features = find_checked_features(spine.head, mover.head)
        if checked_features:
            plus_feature, neg_feature, head = checked_features
            plus_feature.check(neg_feature)
            return
        plus_feature = None
        neg_feature = None
        put_plus_feature_before = None
        # if there is positive feature available, use it as a base
        for i, plus_feature_candidate in enumerate(spine.features):
            if (plus_feature_candidate.sign == '-' or plus_feature_candidate.sign == '=') and not \
                    plus_feature_candidate.checked_by:
                put_plus_feature_before = i
                break
            if plus_feature_candidate.sign == '' and not plus_feature_candidate.checks:
                plus_feature = plus_feature_candidate
                break
        # if there is suitable negative feature available, use it as a base
        if not plus_feature:
            if head == mover:
                sign = '-'
            else:
                sign = '='
            for neg_feature_candidate in mover.features:
                if neg_feature_candidate.sign == sign and not neg_feature_candidate.checked_by:
                    neg_feature = neg_feature_candidate
                    break
        if not (plus_feature or neg_feature):
            plus_feature = self.pick_next_free_feature(spine.label)
            # print(':: create both pos and neg: ', plus_feature)
            _insert_plus_feature(put_plus_feature_before, plus_feature, spine)
            neg_feature = _make_neg_feature(plus_feature, head is mover)
            _insert_neg_feature(neg_feature, mover)
        elif not neg_feature:
            # print(':: copy from pos ', plus_feature)
            neg_feature = _make_neg_feature(plus_feature, head is mover)
            _insert_neg_feature(neg_feature, mover)
            # print('adding neg feature: ', neg_feature)
        elif not plus_feature:
            # print(':: copy from neg ', neg_feature, ' put it at :', put_plus_feature_before, ' in spine: ', spine)
            plus_feature = neg_feature.copy()
            plus_feature.sign = ''
            _insert_plus_feature(put_plus_feature_before, plus_feature, spine)
        checked_features = find_checked_features(spine.head, mover.head)
        # print('     mover: ', mover)
        # print('     spine: ', spine)
        assert checked_features
        c_plus_feature, c_neg_feature, c_head = checked_features
        c_plus_feature.check(c_neg_feature)
        assert c_plus_feature is plus_feature
        assert c_neg_feature is neg_feature
        assert c_head is spine or c_head is mover
        # plus_feature.check(neg_feature)
        self.update_lexicon(mover)
        self.update_lexicon(spine)

    def prepare_used_feature_names(self):
        for const in self.lexicon.values():
            for feat in const.features:
                self.used_feature_names.add(feat.name)

    def pick_next_free_feature(self, label):
        if not self.used_feature_names:
            self.prepare_used_feature_names()
        if len(label) <= 2 and label not in self.used_feature_names:
            self.used_feature_names.add(label)
            return Feature(label)
        for char1 in [''] + list(string.ascii_letters):
            for char2 in string.ascii_letters:
                name = char1 + char2
                if name not in self.used_feature_names:
                    self.used_feature_names.add(name)
                    return Feature(name)


if __name__ == '__main__':
    rerun = True
    t = time.time()
    parser = Analyzer({})
    sentences = []
    readfile = open('sentences_en.txt', 'r')
    for line in readfile:
        line = line.strip()
        if line and not line.startswith('#') and line.startswith('['):
            sentences.append(line)
    linearized = []
    succs = 0
    fails = 0
    i = 0
    for i, sentence in enumerate(sentences):
        linear = parser.analyze_and_make_features(sentence)
        linearized.append(linear)
        verify = linearize(parser.parse(linear))
        if linear == verify:
            print(f'{i}. ok: ', ' '.join(verify))
            succs += 1
        else:
            print(f'{i}. fail (source): ', ' '.join(linear))
            print('        (result): ', ' '.join(verify))
            fails += 1
            # raise hell
    print('=====================')
    print(f'    {succs}/{i + 1} ')
    print('=====================')
    tt = time.time() - t
    t = time.time()
    succs = 0
    fails = 0
    if rerun:
        for i, line in enumerate(linearized):
            tree = parser.parse(line)
            tree_as_line = linearize(tree)
            if line == tree_as_line:
                print(f'{i}. ok: ', ' '.join(tree_as_line))
                succs += 1
            else:
                print(f'{i}. fail (source): ', ' '.join(line))
                print('        (result): ', ' '.join(tree_as_line))
                fails += 1

    print('=====================')
    print(f'    {succs}/{i + 1} ')
    print('=====================')

    for key, value in sorted(parser.lexicon.items()):
        print(value)
    print('=====================')
    print('Deducing lexical features took: ', tt)
    print('Parsing sentences took: ', time.time() - t)
