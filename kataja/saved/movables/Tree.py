# coding=utf-8
from PyQt5 import QtCore

from kataja.Saved import SavedField
from saved.Movable import Movable

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
        scx, scy = tree.current_scene_position
        self.distance_from_pointer = scx - mx, scy - my
        self.dragged_distance = None


class Tree(Movable):
    """ Container for nodes that form a single trees. It allows operations that affect
    all nodes in one trees, e.g. translation of position.
    :param top:
    """
    name = ('Tree', 'Trees')
    short_name = "Tree"

    def __init__(self, top=None):
        Movable.__init__(self)
        self.top = top
        if is_constituent(top):
            self.sorted_constituents = [top]
        else:
            self.sorted_constituents = []
        if top:
            self.sorted_nodes = [top]
        else:
            self.sorted_nodes = []
        self.current_position = 100, 100
        self.drag_data = None
        self.tree_changed = True
        self._cached_bounding_rect = None
        self.setZValue(12)

    def __repr__(self):
        return "Tree '%s' and %s nodes." % (self.top, len(self.sorted_nodes))

    def __contains__(self, item):
        return item in self.sorted_nodes

    def after_init(self):
        self.recalculate_top()
        self.update_items()

    def rebuild(self):
        self.recalculate_top()
        self.update_items()

    def recalculate_top(self):
        """ Verify that self.top is the topmost element of the trees. Doesn't handle consequences,
        e.g. it may now be that there are two identical trees at the top and doesn't update the
        constituent and node lists.
        :return: new top
        """
        passed = set()

        def walk_to_top(node):
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
            self.top = None # hopefully this trees gets deleted.
        return self.top

    def is_empty(self):
        """ Empty trees should be deleted when found
        :return:
        """
        return bool(self.top)

    def is_valid(self):
        """ If trees top has parents, the trees needs to be recalculated or it is otherwise unusable
          before fixed.
        :return:
        """
        return not self.top.get_parents(only_similar=False, only_visible=False)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65556

    def update_items(self):
        """ Check that all children of top item are included in this trees and create the sorted
        lists of items. Make sure there is a top item before calling this!
        :return:
        """
        sorted_constituents = []
        sorted_nodes = []
        used = set()

        def add_children(node):
            """ Add node to this trees.
            :param node:
            :return:
            """
            if node not in used:
                used.add(node)
                if is_constituent(node):
                    sorted_constituents.append(node)
                sorted_nodes.append(node)
                if self not in node.trees:
                    node.add_to_tree(self)
                for child in node.get_all_children():
                    if child: # undoing object creation may cause missing edge ends
                        add_children(child)

        old_nodes = set(self.sorted_nodes)

        if is_constituent(self.top):
            add_children(self.top)

        self.sorted_constituents = sorted_constituents
        self.sorted_nodes = sorted_nodes

        to_be_removed = old_nodes - set(sorted_nodes)
        for item in to_be_removed:
            item.remove_from_tree(self)

    def is_higher_in_tree(self, node_a, node_b):
        """ Compare two nodes, if node_a is higher, return True. Return False
        if not.
            Return None if nodes are not in the same trees -- cannot compare.
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

    def boundingRect(self):
        if self.tree_changed or not self._cached_bounding_rect:
            min_x, min_y = 10000, 10000
            max_x, max_y = -10000, -10000
            for node in self.sorted_nodes:
                if node.is_visible():
                    nbr = node.boundingRect()
                    x, y = node.x(), node.y()
                    x1, y1, x2, y2 = nbr.getCoords()
                    x1 += x
                    y1 += y
                    x2 += x
                    y2 += y
                    if x1 < min_x:
                        min_x = x1
                    if x2 > max_x:
                        max_x = x2
                    if y1 < min_y:
                        min_y = y1
                    if y2 > max_y:
                        max_y = y2
            self._cached_bounding_rect = QtCore.QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
            self.tree_changed = False
            return self._cached_bounding_rect
        else:
            return self._cached_bounding_rect

    def paint(self, painter, QStyleOptionGraphicsItem, QWidget_widget=None):
        pass
        #br = self.boundingRect()
        #painter.drawRect(br)
        #painter.drawText(br.topLeft() + QtCore.QPointF(2, 10), str(self))

    top = SavedField("top")