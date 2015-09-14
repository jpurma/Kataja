__author__ = 'purma'

from PyQt5 import QtWidgets, QtCore

def is_constituent(item):
    return item and getattr(item, 'is_constituent', False)

# Tree includes all items that are below given constituent.


class Tree(QtWidgets.QGraphicsItem):
    def __init__(self, top):
        super().__init__()
        self.top = top
        if is_constituent(top):
            self.sorted_constituents = [top]
        else:
            self.sorted_constituents = []
        self.sorted_nodes = [top]
        self.offset = (0, 0, 0)

    def reset_top(self):
        passed = set()
        def walk_to_top(node):
            passed.add(node)
            for parent in node.get_parents(only_similar=False, only_visible=False):
                if parent not in passed:
                    return walk_to_top(parent)
            return node
        self.top = walk_to_top(self.top)

    def is_empty(self):
        return bool(self.top)

    def is_valid(self):
        return not self.top.get_parents(only_similar=False, only_visible=False)

    def update_items(self):
        """ Check that all children of top item are included in this tree
        :return:
        """
        sorted_constituents = []
        sorted_nodes = []
        used = set()
        multidominated_children = set()

        def add_children(node):
            """ Add node to this tree. Create record of multidominated nodes, because we cannot know
            during this run if they are wholly part of this tree or shared with another tree.
            :param node:
            :return:
            """
            if node not in used:
                used.add(node)
                if is_constituent(node):
                    sorted_constituents.append(node)
                sorted_nodes.append(node)
                node.add_to_tree(self)
                for child in node.get_all_children():
                    add_children(child)

        if is_constituent(self.top):
            add_children(self.top)

        self.sorted_constituents = sorted_constituents
        self.sorted_nodes = sorted_nodes

    def is_higher_in_tree(self, node_a, node_b):
        """ Compare two nodes, if node_a is higher, return True. Return False
        if not.
            Return None if nodes are not in the same tree -- cannot compare.
            (Be careful with the result,
            handle None and False differently.)
        :param node_a:
        :param node_b:
        :return:
        """
        if node_a in self.sorted_nodes and node_b in self.sorted_nodes:
            return self.sorted_nodes.index(node_a) < self.sorted_nodes.index(node_b)
        else:
            return None

