
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
    in_label = False

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
            if part.label in d and len(part.label) > 3 and part.label[:3].isnumeric():
                node.parts[i] = d[part.label]
            else:
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


class StacklessShiftParser:
    def __init__(self, lexicon, forest=None):
        self.forest = forest

    def tree_to_monorail(self, tree):
        """ Walk to bottom left """
        recipe = []

        def _tree_to_monorail(node, spine):
            if len(node.parts) == 2:
                # Left node is built as usual, will return [node.left, spine]
                left = _tree_to_monorail(node.left, spine)
                # Right node is the tricky one, it will return [node.right, [node.left, spine]]
                right = _tree_to_monorail(node.right, left)
                # Merging left and right will create [[node.left, spine], [node.right, [node.left, spine]]]
                # If node = [X, Y], spine = Z
                # this returns [[X, Z], [Y, [X, Z]]]
                #
                #               /\        /\
                #              /\ Z  =>  /\ \
                #             X  Y      X  Z \
                #                            /\
                #                           Y /\
                #                            X  Z
                #
                # if there is no spine, it returns [X, [Y, X]] which is the basic case of merging X and Y in a manner
                # that gives them asymmetrical ordering.
                #
                #                         /\
                #              /\   =>   X /\
                #             X  Y        Y  X
                #
                merged = Constituent(parts=[left, right])
                recipe.append('|')
            elif spine:  # external merge
                # Bottom left node of the branch. If Z is bottom right node (spine) and N is bottom left (node),
                # return [X Y]
                #
                #              /\        /\
                #             N  Z  =>  N  Z
                left = Constituent(label=node.label)
                recipe.append(node.label)
                merged = Constituent(parts=[left, spine])
            else:  # first node
                # Bottom right node of the branch. Just make a simple constituent and return it.
                #
                #             X    =>    X
                merged = Constituent(label=node.label)
                recipe.append(node.label)
            return merged
        return _tree_to_monorail(tree, None), recipe

    def build_from_recipe(self, recipe):

        def _find_movable(node, skip_first=False, is_leftmost=False):
            # finds the uppermost result of external merge element (this is recognized by it having flag 'has_raised')
            if not skip_first and not getattr(node, 'has_raised', None) and (node.parts or not is_leftmost):
                return node
            leftmost = True
            for part in node.parts:
                n = _find_movable(part, is_leftmost=leftmost)
                if n:
                    return n
                leftmost = False

        tree = None
        for item in recipe:
            if not tree:
                tree = Constituent(item)
            elif item == '|':
                mover = _find_movable(tree, skip_first=True)
                if not mover:
                    mover = tree.right
                mover.has_raised = True
                tree = Constituent(parts=[mover, tree])
            else:
                node = Constituent(item)
                tree = Constituent(parts=[node, tree])
            self.export_to_kataja(tree, item)
        return tree

    def parse(self, sentence):
        sentence = sentence.strip()
        if sentence.startswith('['):
            # First derivation step shows tree as it is given by the bracket structure
            tree = simple_bracket_tree_parser(sentence)
            join_copies(tree)
            self.export_to_kataja(tree, sentence)
            # Second step shows how the tree could be reconstructed
            remove_copies(tree)
            self.export_to_kataja(tree, sentence)
            tree, recipe = self.tree_to_monorail(tree)
            print('recipe: ', [str(x) for x in recipe])
            self.export_to_kataja(tree, str(recipe))
            # Third step reconstructs the tree from bottom up
            tree = self.build_from_recipe(recipe)
            return tree
        elif '|' in sentence:
            # If tree is already provided as a 'recipe', just build it
            tree = self.build_from_recipe([x.strip() for x in sentence.split()])
            return tree

    def export_to_kataja(self, tree, message):
        if self.forest:
            syn_state = SyntaxState(tree_roots=[tree], msg=message)
            self.forest.add_step(syn_state)

# def _find_first_left(node):
#     if node.parts:
#         return _find_first_left(node.parts[0])
#     else:
#         return node

# elif item == '^':
#     mover = _find_first_left(tree)
#     mover.has_raised = True
#     tree = Constituent(parts=[mover, tree])
