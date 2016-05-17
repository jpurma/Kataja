# coding=utf-8
import kataja.globals as g
from kataja.singletons import qt_prefs
from kataja.saved.movables.Bracket import Bracket


class BracketManager:
    """ Bracket manager handles showing and hiding brackets. When loading and saving, it should only take care that there are no remainders of previous forests getting in the way. """

    def __init__(self, forest):
        self.forest = forest
        self.brackets = {}
        self._bracket_slots = {}

    def get_brackets(self):
        """ Get brackets as a iterable
        :return:
        """
        return self.brackets.values()

    def store(self, item):
        """ Keep track on brackets
        :param item:
        """
        self.brackets[item.key] = item

    def update_positions(self):
        """ Update all bracket positions """

        for bracket in self.brackets.values():
            bracket.update_position()

    @staticmethod
    def find_leftmost(node):
        """ Helper method for handling brackets: traverse down a trees and find the leftmost node
         of branch
        :param node: node to traverse from, only allow this kind of nodes
        :return: tuple (depth, leftmost_node)
        """
        def leftmost(depth, node):
            children = node.get_children()
            left = next(children, None)
            if left:
                depth += 1
                return leftmost(depth, left)
            else:
                return depth, node
        return leftmost(0, node)

    @staticmethod
    def find_rightmost(node):
        """ Helper method for handling brackets: traverse down a trees and find the rightmost node
         of branch
        :param node: node to traverse from, only allow this kind of nodes
        :return: tuple (depth, rightmost_node)
        """
        def rightmost(depth, node):
            children = node.get_reversed_children()
            right = next(children, None)
            if right:
                depth += 1
                return rightmost(depth, right)
            else:
                return depth, node
        return rightmost(0, node)

    def create_bracket(self, host=None, left=True):
        """

        :param host:
        :param left:
        :return:
        """
        if left:
            key = 'lb_%s' % host.uid
        else:
            key = 'rb_%s' % host.uid
        if key in self.brackets:
            # print('bracket exists already')
            return self.brackets[key]
        br = Bracket(forest=self.forest, host=host, left=left)
        assert (br.key == key)  # don't modify the key creation in Bracket...
        self.brackets[key] = br
        return br

    # ### Scope rectangles and bracket notation ###########################################

    def rebuild_brackets(self):
        """


        """
        self.brackets = {}
        for node in self.forest.nodes.values():
            if hasattr(node, 'rebuild_brackets'):
                node.rebuild_brackets()

    def update_brackets(self):
        """ Update the dict that tells how many brackets each node needs
            to put left or right to them.
            Update bracket positions and update their visibility.
            Bracket dict should be temporary reference,
            created only when using brackets and
            not saved with the trees.
        """
        # print('updating brackets')
        self._bracket_slots = {}
        f = self.forest
        self.rebuild_brackets()

        if f.settings.bracket_style != g.NO_BRACKETS:
            for tree in f:
                for node in tree.sorted_nodes:  # not sure if this should use 'once'
                    if node.left_bracket:
                        depth, left = self.find_leftmost(node)
                        k = left.uid
                        if k in self._bracket_slots:
                            left_brackets, right_brackets = self._bracket_slots[k]
                            left_brackets.append(node)
                            self._bracket_slots[k] = (left_brackets, right_brackets)
                        else:
                            self._bracket_slots[k] = ([node], [])
                        depth, right = self.find_rightmost(node)
                        k = right.uid
                        if k in self._bracket_slots:
                            left_brackets, right_brackets = self._bracket_slots[k]
                            right_brackets.append(node)
                            self._bracket_slots[k] = (left_brackets, right_brackets)
                        else:
                            self._bracket_slots[k] = ([], [node])
        # print(self._bracket_slots)
        # print(self.brackets)
        for bracket in self.brackets.values():
            bracket.update_position()

    def count_bracket_space(self, node, left=True):
        """

        :param node:
        :param left:
        :return:
        """
        if node.uid in self._bracket_slots:
            left_brackets, right_brackets = self._bracket_slots[node.uid]
            if left:
                return len(left_brackets) * (qt_prefs.font_bracket_width + 2)
            else:
                return len(right_brackets) * (qt_prefs.font_bracket_width + 2)
        else:
            return 0

    def remove_brackets(self, node):
        """

        :param node:
        """
        if hasattr(node, 'left_bracket'):
            if node.left_bracket:
                self.delete_bracket(node.left_bracket)
            if node.right_bracket:
                self.delete_bracket(node.right_bracket)

    def delete_bracket(self, bracket):
        """ remove from scene and remove references from nodes
        :param bracket:
        """
        #node = bracket.host
        #if bracket.left:
        #    node.left_bracket = None
        #else:
        #    node.right_bracket = None
        if bracket.key in self.brackets:
            del self.brackets[bracket.key]
        sc = bracket.scene()
        if sc:
            sc.removeItem(bracket)

