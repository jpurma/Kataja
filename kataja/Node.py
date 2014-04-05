#############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from PyQt5 import QtWidgets, QtGui, QtCore

from PyQt5.QtCore import Qt
from kataja.Controller import ctrl, prefs, qt_prefs, colors, palette
from kataja.Label import Label
from kataja.Movable import Movable
from kataja.TouchArea import TouchArea
from kataja.utils import to_tuple, time_me
from kataja.globals import ABSTRACT_EDGE, ABSTRACT_NODE



# ctrl = Controller object, gives accessa to other modules

# alignment of edges -- in some cases it is good to draw left branches differently than right branches
NO_ALIGN = 0
LEFT = 1
RIGHT = 2


class Node(Movable, QtWidgets.QGraphicsItem):
    """ Basic class for syntactic elements that have graphic representation """
    width = 20
    height = 20
    default_edge_type = ABSTRACT_EDGE
    saved_fields = ['level', 'syntactic_object', 'edges_up', 'edges_down', 'folded_away', 'folding_towards', 'index']
    saved_fields = list(set(Movable.saved_fields + saved_fields))
    node_type = ABSTRACT_NODE

    def __init__(self, syntactic_object=None, restoring='', forest=None):
        """ Node is an abstract class that shouldn't be used by itself, though
        it should contain all methods to make it work. Inherit and modify this for
        Constituents, Features etc. """
        QtWidgets.QGraphicsItem.__init__(self)
        # QtWidgets.QGraphicsItem.__init__(self, parent = None)
        Movable.__init__(self, forest=forest)
        self.level = 1
        self.syntactic_object = syntactic_object

        self.edges_up = []
        self.edges_down = []

        self._label_complex = None
        self._label_visible = True
        self.label_font = qt_prefs.font  # @UndefinedVariable
        self.label_rect = None

        self.folded_away = False
        self.ui_menu = None

        self.folding_towards = None
        self._color = None
        self.font = None  # @UndefinedVariable

        self._index_label = None
        self._index_visible = True
        self.index = None

        self.clickable = True
        self.selectable = True
        self.draggable = True

        self.magnets = []
        self._top_magnet = None
        self._bottom_magnet = None
        self._bottom_right_magnet = None
        self._bottom_left_magnet = None
        self.force = 72
        self.touch_areas = {}

        self.width = 0
        self.height = 0

        self.inner_rect = None
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)

        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.setZValue(10)
        self.fade_in()
        # # Remember to call update_identity in subclassed __init__s!

    def __repr__(self):
        """ This is a node and this represents this UG item """
        r = u'%s-%s-%s' % (self.__class__.__name__, self.syntactic_object, self.save_key)
        return r.encode('utf-8')


    # Let's not have nodes be able to iterate through tree --
    # it is ambiguous thing when node structures are not trees.
    # def __iter__(self):
    #    return IterateOnce(self)


    def calculate_movement(self):
        """ Let visualization algorithm work its magic """
        return self.forest.visualization.calculate_movement(self)

    def reset(self):
        Movable.reset(self)
        self.boundingRect(update=True)

        for touch_area in self.touch_areas.values():
            self.forest.remove_touch_area(touch_area)


    #### Children and parents ####################################################


    def get_children(self, only_similar=True, only_visible=False, edge_type=''):
        if only_similar or edge_type:
            edge_type = edge_type or self.__class__.default_edge_type
            if only_visible:
                return [edge.end for edge in self.edges_down if edge.edge_type == edge_type and edge.end.is_visible()]
            else:
                return [edge.end for edge in self.edges_down if edge.edge_type == edge_type]
        else:
            if only_visible:
                return [edge.end for edge in self.edges_down if edge.end.is_visible()]
            else:
                return [edge.end for edge in self.edges_down]

    def get_parents(self, only_similar=True, only_visible=False, edge_type=''):
        if only_similar or edge_type:
            edge_type = edge_type or self.__class__.default_edge_type
            if only_visible:
                return [edge.start for edge in self.edges_up if edge.edge_type == edge_type and edge.start.is_visible()]
            else:
                return [edge.start for edge in self.edges_up if edge.edge_type == edge_type]
        else:
            if only_visible:
                return [edge.start for edge in self.edges_up if edge.start.is_visible()]
            else:
                return [edge.start for edge in self.edges_up]

    def left(self, only_visible=True):
        for edge in self.edges_down:
            if edge.edge_type == self.__class__.default_edge_type and edge.align == 1:
                if (only_visible and edge.end.is_visible()) or not only_visible:
                    return edge.end

    def right(self, only_visible=True):
        for edge in self.edges_down:
            if edge.edge_type == self.__class__.default_edge_type and edge.align == 2:
                if (only_visible and edge.end.is_visible()) or not only_visible:
                    return edge.end

    def is_leaf_node(self, only_similar=True, only_visible=True):
        children = self.get_children(only_similar, only_visible)
        if children:
            return False
        else:
            return True

    def get_only_parent(self, only_similar=True, only_visible=True):
        """ Returns one or zero parents -- useful when not using multidomination """
        parents = self.get_parents(only_similar, only_visible)
        if parents:
            return parents[0]
        return None

    def is_root_node(self, only_similar=True, only_visible=True):
        """ Root node is the topmost node of a tree """
        if self.get_parents(only_similar, only_visible):
            return False
        else:
            return True

    def get_root_node(self, only_similar=True, only_visible=False, recursion=False, visited=None):
        """ Getting the root node is not trivial if there are derivation_steps in the tree.
        If a node that is already visited is visited again, this is a derivation_step that should not be followed. """
        if not recursion:
            visited = set()
        if self in visited:
            return None
        parents = self.get_parents(only_similar, only_visible)
        if not parents:
            return self
        visited.add(self)
        for parent in parents:
            root = parent.get_root_node(only_similar, only_visible, recursion=True, visited=visited)
            if root:
                return root
        return self

    def get_edge_to(self, other, edge_type=''):
        """ Returns edge object, not the related node. There should be only one instance of edge of certain type between two elements. """
        for edge in self.edges_down:
            if edge.end == other:
                if (edge_type and edge_type == edge.edge_type) or (not edge_type):
                    return edge
        for edge in self.edges_up:
            if edge.start == other:
                if (edge_type and edge_type == edge.edge_type) or (not edge_type):
                    return edge

        return None

    def get_edges_up(self, similar=True, visible=False):
        """ Returns edges up, filtered """
        return [rel for rel in self.edges_up if
                ((not similar) or rel.edge_type == self.__class__.default_edge_type) and (
                    (not visible) or rel.is_visible())]

    def get_edges_down(self, similar=True, visible=False):
        """ Returns edges down, filtered """
        return [rel for rel in self.edges_down if
                ((not similar) or rel.edge_type == self.__class__.default_edge_type) and (
                    (not visible) or rel.is_visible())]


    #### Colors and drawing settings ############################################################

    # is this necessary anymore? Does label_complex use pen color?
    def update_colors(self):
        self._color = colors.drawing
        if self._label_complex:
            self._label_complex.setDefaultTextColor(self._color)


    def color(self, value = None):
        if value is None:
            if self._color == None:
                return palette.get(self.forest.settings.node_color(self.__class__.node_type))
            else:
                return palette.get(self._color)
        else:
            self._color = value
            if self._label_complex:
                self._label_complex.setDefaultTextColor(self._color)


    def contextual_color(self):
        """ Drawing color that is sensitive to node's state """
        if ctrl.pressed == self:
            return colors.active(self.color())
        elif self._hovering:
            return colors.hovering(self.color())
        elif ctrl.is_selected(self):
            return colors.selected(self.color())
        else:
            return self.color()

    #### Labels and identity ###############################################################

    def update_identity(self):
        """ Make sure that the node reflects its syntactic_object and that node exists in the world"""
        if not ctrl.loading:
            self.forest.store(self)
        self.update_label()

    def update_label(self):
        if not self._label_complex:
            self._label_complex = Label(parent=self)
            self._label_complex.set_get_method(self.get_text_for_label)
            self._label_complex.set_set_method(self.label_edited)
        a = self._label_complex.update_label()
        self.boundingRect(update=True)
        return a

    def get_text_for_label(self):
        """ This should be overridden if there are alternative displays for label """
        return unicode(self.syntactic_object)

    def has_empty_label(self):
        return self._label_complex.is_empty()

    def label_edited(self):
        """ Label has been modified, update this and the syntactic object """
        new_value = self._label_complex.get_plaintext()

    ### Qt overrides ######################################################################

    def paint(self, painter, option, widget):
        """ Painting is sensitive to mouse/selection issues, but usually with
        nodes it is the label of the node that needs complex painting """
        painter.setPen(self.contextual_color())
        if ctrl.pressed == self or self._hovering or ctrl.is_selected():
            painter.drawRoundedRect(self.inner_rect, 5, 5)

    def boundingRect(self, update=False, pass_size_calculation=False):
        """ BoundingRects are used often and cost of this method affects performance.
        inner_rect is used as a cached bounding rect and returned fast if there is no explicit
        update asked. """
        if self.inner_rect and not update:
            return self.inner_rect
        my_class = self.__class__
        if pass_size_calculation:
            pass
        elif self._label_visible:
            if not self._label_complex:
                ctrl.quit()
            lbr = self._label_complex.boundingRect()
            self._label_complex.update_position(lbr)
            lbh = lbr.height()
            lbw = lbr.width()
            self.label_rect = QtCore.QRectF(self._label_complex.x(), self._label_complex.y(), lbw, lbh)
            self.width = max((lbw, my_class.width))
            self.height = max((lbh, my_class.height))
        else:
            self.label_rect = QtCore.QRectF(0, 0, 0, 0)
            self.width = my_class.width
            self.height = my_class.height
        w2 = self.width / 2.0
        h2 = self.height / 2.0
        self.inner_rect = QtCore.QRectF(-w2, -h2, self.width, self.height)
        self.magnets = (-h2, w2, h2, -w2)  # (top, right, bottom, left)
        self._top_magnet = (0, -h2 + 2)  # (0,-h2/2)
        self._bottom_magnet = (0, h2 - 2)  # (0,-h2/2)
        self._bottom_left_magnet = (w2 / -2, h2 - 2)
        self._bottom_right_magnet = (w2 / 2, h2 - 2)
        print 'updating bounding rect ', self
        return self.inner_rect

    ### Magnets ######################################################################

    def top_magnet(self):
        """ Adjusted coordinates to center top of the node """
        if prefs.use_magnets and self._label_visible:
            x1, y1, z1 = self.get_current_position()
            x2, y2 = self._top_magnet
            return (x1 + x2, y1 + y2, z1)
        else:
            return self.get_current_position()

    def bottom_magnet(self):
        """ Adjusted coordinates to center bottom of the node """
        if prefs.use_magnets and self._label_visible:
            x1, y1, z1 = self.get_current_position()
            x2, y2 = self._bottom_magnet
            return (x1 + x2, y1 + y2, z1)
        else:
            return self.get_current_position()

    def left_magnet(self):
        """ Adjusted coordinates to ~left bottom of the node """
        if prefs.use_magnets and self._label_visible:
            x1, y1, z1 = self.get_current_position()
            x2, y2 = self._bottom_left_magnet
            return (x1 + x2, y1 + y2, z1)
        else:
            return self.get_current_position()

    def right_magnet(self):
        """ Adjusted coordinates to ~right bottom of the node """
        if prefs.use_magnets and self._label_visible:
            x1, y1, z1 = self.get_current_position()
            x2, y2 = self._bottom_right_magnet
            return (x1 + x2, y1 + y2, z1)
        else:
            return self.get_current_position()

    #### Menus #########################################

    def create_menu(self):
        """ Define menus for this node type """
        ctrl.add_message(u'Menu not implemented')
        return None

    def open_menus(self):
        """ Activates menus """
        ui = self.forest.main.ui_manager
        # only one menu is open at time
        ui.close_menus()
        # create menus only when necessary
        if not self.ui_menu:
            self.ui_menu = self.create_menu()
        # it takes a while to open the menu, ignore open-commands if it is still opening
        if self.ui_menu and not self.ui_menu.moving():
            self.ui_menu.open()

    def close_menus(self):
        """ Close menus related to this node """
        if self.ui_menu:
            self.ui_menu.close()

    def remove_menu(self, menu):
        """ Tries to remove a menu associated with this node """
        ui = ctrl.main.ui_manager  # @UndefinedVariable
        if menu is self.ui_menu:
            ui.remove_menu(menu)
            self.ui_menu = None

    def set_selection_status(self, selected):
        if not selected:
            self.remove_merge_options()
        self.update()

    #### Merge options ########################################################

    def add_merge_options(self):
        pass

    def remove_merge_options(self):
        pass

    def get_touch_area(self, place):
        return self.touch_areas.get(place, None)

    def add_touch_area(self, touch_area):
        if touch_area.place in self.touch_areas:
            print 'Touch area exists already. Someone is confused'
            raise
        self.touch_areas[touch_area.place] = touch_area
        return touch_area

    def remove_touch_area(self, touch_area):
        del self.touch_areas[touch_area.place]

    #### MOUSE - kataja ########################################################

    def clickQt(self, event=None):
        """ temporary testing with qt menus
            it may be faster to develope prototype by relying on default menus
            """
        if not self.qt_menu:
            self.open_qt_menu()
        else:
            self.close_qt_menu()

    def double_click(self, event=None):
        """ Scene has decided that this node has been clicked """
        self._hovering = False
        if ctrl.is_selected(self):
            if (not self.ui_menu) or (not self.ui_menu.is_open()):
                self.open_menus()
            else:
                self.close_menus()
        else:
            ctrl.select(self)

    def click(self, event=None):
        """ Scene has decided that this node has been clicked """
        self._hovering = False
        if event and event.modifiers() == Qt.ShiftModifier:  # multiple selection
            for node in ctrl.get_all_selected():
                if hasattr(node, 'remove_merge_options'):
                    node.remove_merge_options()
            if ctrl.is_selected(self):
                ctrl.remove_from_selection(self)
            else:
                ctrl.add_to_selection(self)
            return
        if ctrl.is_selected(self):
            if (not self.ui_menu) or (not self.ui_menu.is_open()):
                self.open_menus()
            else:
                self.close_menus()
        else:
            ctrl.select(self)
            self.add_merge_options()

    # def drag(self, event):
    #     """ Drags also elements that are counted to be involved: features, children etc """
    #     mx, my = to_tuple(event.scenePos())
    #     if not getattr(ctrl, 'dragged', None):
    #         self.start_dragging(mx, my)
    #     for item, ox, oy in ctrl.dragged_positions:
    #         x, y, z = item.get_current_position()
    #         item.set_adjustment(dx, dy, 0)
    #         item.update_position()

    #         [b.update() for b in item.get_children() + item.edges_up + item.edges_down]
    #     ctrl.scene.item_moved()


    def start_dragging(self, mx, my):
        print 'start dragging with node ', self
        ctrl.dragged = set()

        # there if node is both above and below the dragged node, it shouldn't move
        ctrl.dragged.add(self)
        x, y, dummy_z = self.get_current_position()
        self._position_before_dragging = self.get_current_position()
        self._adjustment_before_dragging = self.get_adjustment()
        self.forest.prepare_touch_areas_for_dragging(excluded=ctrl.dragged)


    def drag(self, event):
        pos = event.scenePos()
        now_x, now_y = to_tuple(pos)
        if not getattr(ctrl, 'dragged', None):
            self.start_dragging(now_x, now_y)

        mx, my = to_tuple(event.scenePos())
        z = self.get_current_position()[2]
        self.set_current_position((mx, my, z))
        # scene.item_moved()
        px, py, pz = self._position_before_dragging
        if self.can_adjust_position:
            ax, ay, az = self._adjustment_before_dragging
            diff_x = now_x - px - ax
            diff_y = now_y - py - ay
            self.set_adjustment((diff_x, diff_y, az))
        else:
            self.set_computed_position((now_x, now_y, pz))


    #### Mouse - Qt events ##################################################

    def hoverEnterEvent(self, event):
        """ Hovering has some visual effects, usually handled in paint-method """
        if not self._hovering:
            self._hovering = True
            self.prepareGeometryChange()
            self.update()
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """ Object needs to be updated """
        if self._hovering:
            self._hovering = False
            self.prepareGeometryChange()
            self.update()
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)

    # def dragMoveEvent(self, event):
    #     """ """
    #     print 'Node dragMoveEvent!'
    #     QtGui.QGraphicsItem.dragMoveEvent(self, event)

    # def dragEnterEvent(self, event):
    #     """ """
    #     print 'Node dragEnterEvent!'
    #     QtGui.QGraphicsItem.dragEnterEvent(self, event)

    # def dragLeaveEvent(self, event):
    #     """ """
    #     print 'Node dragLeaveEvent!'
    #     QtGui.QGraphicsItem.dragLeaveEvent(self, event)

    # def dropEvent(self, event):
    #     """ """
    #     print 'Node dropEvent!'
    #     QtGui.QGraphicsItem.dropEvent(self, event)

    #### Restoring after load / undo #########################################

    def after_restore(self, changes):
        """ Fix derived attributes """
        Movable.after_restore(self, changes)


