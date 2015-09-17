# coding=utf-8
from Movable import Movable
from kataja.nodes import Node
from kataja.singletons import ctrl
from PyQt5 import QtWidgets

__author__ = 'purma'


def is_constituent(item):
    """ Use class attribute to decide if an item is constituent. This is quite fast way of
    evaluating it and allows user-created classes to be accepted as constituents.
    :param item:
    :return:
    """
    return item and getattr(item, 'is_constituent', False)


class TreeDragData:
    """ Helper object to contain drag-related data for duration of dragging """

    def __init__(self, tree:'Tree', is_host, mousedown_scene_pos):
        self.is_host = is_host
        self.position_before_dragging = tree.current_position
        self.adjustment_before_dragging = tree.adjustment
        mx, my = mousedown_scene_pos
        scx, scy, scz = tree.current_scene_position
        self.distance_from_pointer = scx - mx, scy - my
        self.dragged_distance = None


class Tree(Movable, QtWidgets.QGraphicsItem):
    """ Container for nodes that form a single tree. It allows operations that affect
    all nodes in one tree, e.g. translation of position.
    :param top:
    """

    def __init__(self, top: Node):
        QtWidgets.QGraphicsItem.__init__(self)
        Movable.__init__(self)
        self.top = top
        if is_constituent(top):
            self.sorted_constituents = [top]
        else:
            self.sorted_constituents = []
        self.sorted_nodes = [top]
        self.current_position = 100, 100, 0
        self.drag_data = None

    def __str__(self):
        return "I'm a tree, in pos (%s, %s) and top '%s'" % (self.current_position[0],
                                                             self.current_position[1], self.top)

    def __contains__(self, item):
        return item in self.sorted_nodes

    def recalculate_top(self):
        """ Verify that self.top is the topmost element of the tree. Doesn't handle consequences,
        e.g. it may now be that there are two identical trees at the top and doesn't update the
        constituent and node lists.
        :return: new top
        """
        passed = set()

        def walk_to_top(node: Node):
            """ Recursive walk upwards
            :param node:
            :return:
            """
            passed.add(node)
            for parent in node.get_parents(only_similar=False, only_visible=False):
                if parent not in passed:
                    return walk_to_top(parent)
            return node
        if self.top: # hopefully it is a short walk
            self.top = walk_to_top(self.top)
        elif self.sorted_nodes: # take the long way if something strange has happened to top
            self.top = walk_to_top(self.sorted_nodes[-1])
        else:
            self.top = None # hopefully this tree gets deleted.
        return self.top

    def is_empty(self):
        """ Empty trees should be deleted when found
        :return:
        """
        return bool(self.top)

    def is_valid(self):
        """ If tree top has parents, the tree needs to be recalculated or it is otherwise unusable
          before fixed.
        :return:
        """
        return not self.top.get_parents(only_similar=False, only_visible=False)

    def update_items(self):
        """ Check that all children of top item are included in this tree. Make sure there is a
        top item!
        :return:
        """
        sorted_constituents = []
        sorted_nodes = []
        used = set()

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
        if node_a in self and node_b in self:
            return self.sorted_nodes.index(node_a) < self.sorted_nodes.index(node_b)
        else:
            return None

    def start_dragging_tracking(self, host=False, scene_pos=None):
        """ Add this *Tree* to entourage of dragged nodes. These nodes will
        maintain their relative position to drag pointer while dragging.
        :return: None
        """
        self.drag_data = TreeDragData(self, is_host=host, mousedown_scene_pos=scene_pos)

