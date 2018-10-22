
from kataja.syntax.BaseConstituent import BaseConstituent as Constituent
from kataja.syntax.SyntaxState import SyntaxState


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

    while sentence:
        c = sentence.pop()
        if c == '[':
            const = finish_const(const)
            c_stack.append(Constituent(''))
        elif c == ']':
            const = finish_const(const)
            if c_stack:
                parent = c_stack.pop()
                if c_stack:
                    c_stack[-1].parts.append(parent)
        elif c == ' ':
            const = finish_const(const)
        else:
            if not const:
                const = Constituent('')
            const.label += c
    return parent


class StacklessShiftParser:
    def __init__(self, lexicon, forest=None):
        self.forest = forest

    def tree_to_monorail(self, tree):
        """ """
        recipe = []

        def _tree_to_monorail(lnode, spine):
            if lnode.parts:
                left = _tree_to_monorail(lnode.left, spine)
                right = _tree_to_monorail(lnode.right, left)
                merged = Constituent(label='', parts=[left, right])
                recipe.append('|')
            elif spine:
                left = Constituent(label=lnode.label)
                recipe.append(str(lnode))
                merged = Constituent(label='', parts=[left, spine])
            else:
                merged = Constituent(label=lnode.label)
                recipe.append(str(lnode))
            return merged
        return _tree_to_monorail(tree, None), recipe

    def fast_find_movable(self, node, excluded):
        # finds the uppermost external merged element and takes its sibling, e.g. the tree that EM
        # node was merged with.
        # probably not enough when there is a series of raises that should be done.
        if node not in excluded and not getattr(node, 'has_raised', None):
            return node
        for part in node.parts:
            n = self.fast_find_movable(part, excluded)
            if n:
                return n
        return None

    def build_from_recipe(self, recipe):
        tree = None
        for item in recipe:
            item = str(item)
            print(item)
            if not tree:
                tree = Constituent(item)
            elif item == '|':
                mover = self.fast_find_movable(tree, {tree, tree.left})
                mover.has_raised = True
                tree = Constituent(parts=[mover, tree])
            else:
                node = Constituent(item)
                tree = Constituent(parts=[node, tree])
            print(repr(tree))
        return tree

    def parse(self, sentence):
        sentence = sentence.strip()
        if sentence.startswith('['):
            # First derivation step shows tree as it is given by the bracket structure
            tree = simple_bracket_tree_parser(sentence)
            self.export_to_kataja(tree, sentence)
            # Second step shows how the tree could be reconstructed
            tree, recipe = self.tree_to_monorail(tree)
            print('recipe: ', [str(x) for x in recipe])
            self.export_to_kataja(tree, str(recipe))
            # Third step reconstructs the tree from bottom up
            tree = self.build_from_recipe(recipe)
            self.export_to_kataja(tree, str(recipe))
            return tree

    def export_to_kataja(self, tree, message):
        if self.forest:
            syn_state = SyntaxState(tree_roots=[tree], msg=message)
            self.forest.add_step(syn_state)


