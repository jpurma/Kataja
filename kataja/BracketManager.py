# coding=utf-8
from kataja.singletons import qt_prefs
from kataja.Bracket import Bracket
import kataja.globals as g

class BracketManager:
    """ Bracket manager handles showing and hiding brackets. When loading and saving, it should only take care that there are no remainders of previous forests getting in the way. """

    def __init__(self, forest):
        self.forest = forest
        self.brackets = {}
        self._bracket_slots = {}

    def get_brackets(self):
        """


        :return:
        """
        return list(self.brackets.values())

    def store(self, item):
        """

        :param item:
        """
        self.brackets[item.key] = item

    def update_positions(self):
        """


        """
        for bracket in self.brackets.values():
            bracket.update_position()

    def create_bracket(self, host=None, left=True):
        """

        :param host:
        :param left:
        :return:
        """
        print('creating bracket ...')
        if left:
            key = 'lb_%s' % host.save_key
        else:
            key = 'rb_%s' % host.save_key
        if key in self.brackets:
            # print('bracket exists already')
            return self.brackets[key]
        br = Bracket(host=host, left=left)
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
            not saved with the tree.
        """
        # print('updating brackets')
        self._bracket_slots = {}
        f = self.forest
        self.rebuild_brackets()

        if f.settings.bracket_style != g.NO_BRACKETS:
            for tree in f:
                for node in f.list_nodes_once(tree):  # not sure if this should use 'once'
                    if node.left_bracket:
                        this_left = node
                        next_left = node.left()
                        while next_left:
                            this_left = next_left
                            next_left = this_left.left()
                        key = this_left.save_key
                        if key in self._bracket_slots:
                            left_brackets, right_brackets = self._bracket_slots[key]
                            left_brackets.append(node)
                            self._bracket_slots[key] = (left_brackets, right_brackets)
                        else:
                            self._bracket_slots[key] = ([node], [])
                        this_right = node
                        next_right = node.right()
                        while next_right:
                            this_right = next_right
                            next_right = this_right.right()
                        key = this_right.save_key
                        if key in self._bracket_slots:
                            left_brackets, right_brackets = self._bracket_slots[key]
                            right_brackets.append(node)
                            self._bracket_slots[key] = (left_brackets, right_brackets)
                        else:
                            self._bracket_slots[key] = ([], [node])
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
        if node.save_key in self._bracket_slots:
            left_brackets, right_brackets = self._bracket_slots[node.save_key]
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
        print('deleting bracket ', bracket.key)
        if bracket.key in self.brackets:
            del self.brackets[bracket.key]
        sc = bracket.scene()
        if sc:
            sc.removeItem(bracket)

