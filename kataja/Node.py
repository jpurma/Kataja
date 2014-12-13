# coding=utf-8
# ############################################################################
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
# ############################################################################

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from kataja.ui.ControlPoint import ControlPoint
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.Label import Label
from kataja.Movable import Movable
from kataja.utils import to_tuple, create_shadow_effect
import kataja.globals as g


# ctrl = Controller object, gives accessa to other modules

# alignment of edges -- in some cases it is good to draw left branches differently than right branches

NO_ALIGN = 0
LEFT = 1
RIGHT = 2



class Node(Movable, QtWidgets.QGraphicsItem):
    """ Basic class for syntactic elements that have graphic representation """
    z_value = 10
    width = 20
    height = 20
    default_edge_type = g.ABSTRACT_EDGE
    node_type = g.ABSTRACT_NODE

    def __init__(self, syntactic_object=None, restoring=None):
        """ Node is an abstract class that shouldn't be used by itself, though
        it should contain all methods to make it work. Inherit and modify this for
        Constituents, Features etc. """
        QtWidgets.QGraphicsItem.__init__(self)
        Movable.__init__(self)
        # Saved attributes (can be reached through @properties without .save.)
        self.saved.syntactic_object = syntactic_object
        self.saved.edges_up = []
        self.saved.edges_down = []
        self.saved.folded_away = False
        self.saved.folding_towards = None
        self.saved.color = None
        self.saved.index = None

        self._label_complex = None
        self._label_visible = True
        self._label_font = None  # @UndefinedVariable
        self.label_rect = None

        self._index_label = None
        self._index_visible = True

        self.clickable = False
        self.selectable = True
        self.draggable = True

        self._magnets = []
        self.force = 72
        self.status_tip = ""

        self.width = 0
        self.height = 0

        self.inner_rect = None
        self.setAcceptHoverEvents(True)
        #self.setAcceptDrops(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.setZValue(10)
        self.fade_in()
        # # Remember to call update_identity in subclassed __init__s!
        self.effect = create_shadow_effect(ctrl.cm.selection())
        self._update_magnets = True
        self.setGraphicsEffect(self.effect)

    @property
    def syntactic_object(self):
        return self.saved.syntactic_object

    @syntactic_object.setter
    def syntactic_object(self, value):
        self.saved.syntactic_object = value

    @property
    def edges_up(self):
        return self.saved.edges_up

    @edges_up.setter
    def edges_up(self, value):
        if value is None:
            value = []
        self.saved.edges_up = value

    @property
    def edges_down(self):
        return self.saved.edges_down

    @edges_down.setter
    def edges_down(self, value):
        if value is None:
            value = []
        self.saved.edges_down = value

    @property
    def folded_away(self):
        return self.saved.folded_away

    @folded_away.setter
    def folded_away(self, value):
        if value is None:
            value = False
        self.saved.folded_away = value

    @property
    def folding_towards(self):
        return self.saved.folding_towards

    @folding_towards.setter
    def folding_towards(self, value):
        self.saved.folding_towards = value

    @property
    def node_color(self):
        return self.saved.color

    @node_color.setter
    def node_color(self, value):
        self.saved.node_color = value

    @property
    def index(self):
        return self.saved.index

    @index.setter
    def index(self, value):
        if value is None:
            value = ''
        self.saved.index = value


    def __repr__(self):
        """ This is a node and this represents this UG item """
        return '%s-%s' % (self.saved.syntactic_object, self.saved.save_key)


    # Let's not have nodes be able to iterate through tree --
    # it is ambiguous thing when node structures are not trees.
    # def __iter__(self):
    # return IterateOnce(self)


    def calculate_movement(self):
        """ Let a dynamic visualization algorithm work its magic """
        return ctrl.forest.visualization.calculate_movement(self)

    def reset(self):
        """
        Remove temporary/state information from node, eg. remove touch areas.
        """
        print("Resetting node ", self)
        Movable.reset(self)
        self.boundingRect(update=True)
        ctrl.ui.remove_touch_areas_for(self)


    def is_placeholder(self):
        """ Constituent structure may assume a constituent to be somewhere, before the user has intentionally created
        one there. These are shown as placeholders, which are nodes, but with limited presence.
        :return: boolean
        """
        return False

    # ### Children and parents ####################################################


    def get_children(self, only_similar=True, only_visible=False, edge_type=None):
        """
        Get child nodes of this node.
        :param only_similar: boolean, only return nodes of same type (eg. ConstituentNodes)
        :param only_visible: boolean, only return visible nodes
        :param edge_type: int, only return Edges of certain subclass.
        :return: list of Nodes
        """
        if not self.saved.edges_down:
            return []
        if only_similar or edge_type is not None:
            if edge_type is None:
                edge_type = self.__class__.default_edge_type
            if only_visible:
                return [edge.end for edge in self.saved.edges_down if edge.edge_type == edge_type and edge.end and edge.end.is_visible()]
            else:
                return [edge.end for edge in self.saved.edges_down if edge.edge_type == edge_type and edge.end]
        else:
            if only_visible:
                return [edge.end for edge in self.saved.edges_down if edge.end and edge.end.is_visible()]
            else:
                return [edge.end for edge in self.saved.edges_down if edge.end]

    def get_parents(self, only_similar=True, only_visible=False, edge_type=None):
        """
        Get parent nodes of this node.
        :param only_similar: boolean, only return nodes of same type (eg. ConstituentNodes)
        :param only_visible: boolean, only return visible nodes
        :param edge_type: int, only return Edges of certain subclass.
        :return: list of Nodes
        """
        if not self.saved.edges_up:
            return []
        if only_similar or edge_type is not None:
            if edge_type is None:
                edge_type = self.__class__.default_edge_type
            if only_visible:
                return [edge.start for edge in self.saved.edges_up if edge.edge_type == edge_type and edge.start and edge.start.is_visible()]
            else:
                return [edge.start for edge in self.saved.edges_up if edge.edge_type == edge_type and edge.start]
        else:
            if only_visible:
                return [edge.start for edge in self.saved.edges_up if edge.start and edge.start.is_visible()]
            else:
                return [edge.start for edge in self.edges_up if edge.start]

    def left(self, only_visible=True):
        """

        :param only_visible:
        :return:
        """
        for edge in self.edges_down:
            if edge.edge_type == self.__class__.default_edge_type and edge.align == g.LEFT:
                if edge.end:
                    if (only_visible and edge.end.is_visible()) or not only_visible:
                        return edge.end
                return None

    def right(self, only_visible=True):
        """

        :param only_visible:
        :return:
        """
        for edge in self.edges_down:
            if edge.edge_type == self.__class__.default_edge_type and edge.align == g.RIGHT:
                if edge.end:
                    if (only_visible and edge.end.is_visible()) or not only_visible:
                        return edge.end
                return None

    def is_leaf_node(self, only_similar=True, only_visible=True):
        """

        :param only_similar:
        :param only_visible:
        :return:
        """
        children = self.get_children(only_similar, only_visible)
        if children:
            return False
        else:
            return True

    def get_only_parent(self, only_similar=True, only_visible=True):
        """ Returns one or zero parents -- useful when not using multidomination
        :param only_similar:
        :param only_visible:
        """
        parents = self.get_parents(only_similar, only_visible)
        if parents:
            return parents[0]
        return None

    def is_root_node(self, only_similar=True, only_visible=True):
        """ Root node is the topmost node of a tree
        :param only_similar:
        :param only_visible:
        """
        if self.get_parents(only_similar, only_visible):
            return False
        else:
            return True

    def get_root_node(self, only_similar=True, only_visible=False, recursion=False, visited=None):
        """ Getting the root node is not trivial if there are derivation_steps in the tree.
        :param only_similar:
        :param only_visible:
        :param recursion:
        :param visited:
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
        """ Returns edge object, not the related node. There should be only one instance of edge of certain type between two elements.
        :param other:
        :param edge_type:
        """
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
        """ Returns edges up, filtered
        :param similar:
        :param visible:
        """
        return [rel for rel in self.edges_up if
                ((not similar) or rel.edge_type == self.__class__.default_edge_type) and (
                    (not visible) or rel.is_visible())]

    def get_edges_down(self, similar=True, visible=False):
        """ Returns edges down, filtered
        :param similar:
        :param visible:
        """
        return [rel for rel in self.edges_down if
                ((not similar) or rel.edge_type == self.__class__.default_edge_type) and (
                    (not visible) or rel.is_visible())]



    ### Font #####################################################################

    def font(self, value=None):
        if value is None:
            if self._label_font:
                return qt_prefs.font(self._label_font)
            else:
                return qt_prefs.font(ctrl.forest.settings.node_settings(self.node_type, 'font'))
        else:
            if isinstance(value, QtGui.QFont):
                self._label_font = qt_prefs.get_key_for_font(value)
            else:
                self._label_font = value

    # ### Colors and drawing settings ############################################################

    # is this necessary anymore? Does label_complex use pen color?
    def update_colors(self):
        """


        """
        pass
        # self._color = colors.drawing
        # if self._label_complex:
        # self._label_complex.setDefaultTextColor(self._color)


    def color(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self.node_color is None:
                return ctrl.cm.get(ctrl.forest.settings.node_settings(self.__class__.node_type, 'color'))
            else:
                return ctrl.cm.get(self.node_color)
        else:
            self.node_color = value
            # if self._label_complex:
            # self._label_complex.setDefaultTextColor(self._color)


    def contextual_color(self):
        """ Drawing color that is sensitive to node's state """
        if ctrl.pressed == self:
            return ctrl.cm.active(ctrl.cm.selection())
        elif self._hovering:
            return ctrl.cm.hovering(ctrl.cm.selection())
        elif ctrl.is_selected(self):
            return ctrl.cm.selection()
            #return ctrl.cm.selected(ctrl.cm.selection())
        else:
            return self.color()

    # ### Labels and identity ###############################################################

    def update_identity(self):
        """ Make sure that the node reflects its syntactic_object and that node exists in the world"""
        if not ctrl.loading:
            ctrl.forest.store(self)
        self.update_label()

    def update_label(self):
        """


        :return:
        """
        if not self._label_complex:
            self._label_complex = Label(parent=self)
            self._label_complex.set_get_method(self.get_text_for_label)
            self._label_complex.set_set_method(self.label_edited)
        a = self._label_complex.update_label()
        self.boundingRect(update=True)
        self.update_status_tip()
        return a

    def update_status_tip(self):
        """ implement properly in subclasses, let tooltip tell about the node
        :return: None
        """
        self.status_tip = str(self)


    def get_text_for_label(self):
        """ This should be overridden if there are alternative displays for label """
        return str(self.syntactic_object)

    def has_empty_label(self):
        """


        :return:
        """
        return self._label_complex.is_empty()

    def label_edited(self):
        """ Label has been modified, update this and the syntactic object """
        new_value = self._label_complex.get_plaintext()

    # ## Qt overrides ######################################################################

    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        painter.setPen(self.contextual_color())
        if ctrl.pressed == self or self._hovering or ctrl.is_selected(self):
            painter.drawRoundedRect(self.inner_rect, 5, 5)

    def boundingRect(self, update=False, pass_size_calculation=False):
        """ BoundingRects are used often and cost of this method affects performance.
        inner_rect is used as a cached bounding rect and returned fast if there is no explicit
        :param update:
        :param pass_size_calculation:
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
        self.inner_rect = QtCore.QRectF(self.width / -2, self.height / -2, self.width, self.height)
        self._update_magnets = True
        # print 'updating bounding rect ', self
        return self.inner_rect


    # ## Magnets ######################################################################


    def magnet(self, n):
        """
        :param n: index of magnets. There are five magnets in top and bottom and three for sides:

        0   1   2   3   4
        5               6
        7   8   9   10  11

        :return:
        """
        if prefs.use_magnets and self._label_visible:
            if self._update_magnets:
                self._update_magnets = False
                w4 = (self.width - 2) / 4.0
                w2 = (self.width - 2) / 2.0
                h2 = (self.height - 2) / 2.0

                self._magnets = [(-w2, -h2),
                    (-w4, -h2),
                    (0, -h2),
                    (w4, -h2),
                    (w2, -h2),
                    (-w2, 0),
                    (w2, 0),
                    (-w2, h2),
                    (-w4, h2),
                    (0, h2),
                    (w4, h2),
                    (w2, h2)]

            x1, y1, z1 = self.current_position
            x2, y2 = self._magnets[n]
            return x1 + x2, y1 + y2, z1
        else:
            return self.current_position

    # ### Menus #########################################

    def create_menu(self):
        """ Define menus for this node type """
        ctrl.add_message('Menu not implemented')
        return None

    def open_menus(self):
        """ Activates menus """
        # only one menu is open at time
        ctrl.ui.close_menus()
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
        """ Tries to remove a menu associated with this node
        :param menu:
        """
        if menu is self.ui_menu:
            ctrl.ui.remove_menu(menu)
            self.ui_menu = None

    def refresh_selection_status(self, selected):
        """ This is called

        :param selected:
        """
        if not selected:
            self.setZValue(10)
        else:
            self.setZValue(200)
        self.update()

    # ### MOUSE - kataja ########################################################

    def open_embed(self):
        """ Tell ui to open a menu relevant for this node type -- overloaded by specialized nodes
        :return: None
        """
        pass

    def double_click(self, event=None):
        """ Scene has decided that this node has been clicked
        :param event:
        """
        self.set_hovering(False)
        if ctrl.is_selected(self):
            self.open_embed()
        else:
            ctrl.select(self)

    def select(self, event=None):
        """ Scene has decided that this node has been clicked
        :param event:
        """
        self.set_hovering(False)
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
            self.open_embed()
        else:
            ctrl.select(self)
            ctrl.ui.add_completion_suggestions(self)

    # def drag(self, event):
    # """ Drags also elements that are counted to be involved: features, children etc """
    # mx, my = to_tuple(event.scenePos())
    #     if not getattr(ctrl, 'dragged', None):
    #         self.start_dragging(mx, my)
    #     for item, ox, oy in ctrl.dragged_positions:
    #         x, y, z = item.current_position
    #         item.set_adjustment(dx, dy, 0)
    #         item.update_position()

    #         [b.update() for b in item.get_children() + item.edges_up + item.edges_down]
    #     ctrl.scene.item_moved()

    def start_dragging(self, mx, my):
        """

        :param mx:
        :param my:
        """
        print('start dragging with node ', self)
        ctrl.dragged = set()

        # there if node is both above and below the dragged node, it shouldn't move
        ctrl.dragged.add(self)
        x, y, z = self.current_position
        self._position_before_dragging = x, y, z
        self._adjustment_before_dragging = self.adjustment or (0, 0, 0)
        ctrl.forest.prepare_touch_areas_for_dragging(excluded=ctrl.dragged)

    def drag(self, event):
        """

        :param event:
        """
        pos = event.scenePos()
        now_x, now_y = to_tuple(pos)
        if not getattr(ctrl, 'dragged', None):
            self.start_dragging(now_x, now_y)

        mx, my = to_tuple(event.scenePos())
        z = self.current_position[2]
        self.current_position = (mx, my, z)
        # scene.item_moved()
        px, py, pz = self._position_before_dragging
        if self.can_adjust_position:
            ax, ay, az = self._adjustment_before_dragging
            diff_x = now_x - px - ax
            diff_y = now_y - py - ay
            self.adjustment = (diff_x, diff_y, az)
        else:
            self.computed_position = (now_x, now_y, pz)

    def set_hovering(self, value):
        """ Toggle hovering effects and internal bookkeeping
        :param value: bool
        :return:
        """
        if value and not self._hovering:
            self._hovering = True
            if ctrl.cm.use_glow():
                self.effect.setColor(ctrl.cm.selection())
                self.effect.setEnabled(True)
            self.prepareGeometryChange()
            self.update()
            self.setZValue(150)
            ctrl.set_status(self.status_tip)
        elif (not value) and self._hovering:
            if ctrl.cm.use_glow():
                self.effect.setEnabled(False)
            self._hovering = False
            self.prepareGeometryChange()
            self.setZValue(self.__class__.z_value)
            self.update()
            ctrl.remove_status(self.status_tip)

    def dragged_over_by(self, dragged):
        if not self._hovering and self.accepts_drops(dragged):
            if ctrl.latest_hover and not ctrl.latest_hover is self:
                ctrl.latest_hover.set_hovering(False)
            ctrl.latest_hover = self
            self.set_hovering(True)

    def accepts_drops(self, dragged):
        if isinstance(dragged, ControlPoint):
            if dragged.role == g.START_POINT or dragged.role == g.END_POINT:
                return True
        #elif isinstance(dragged, TouchArea):
        #    return True
        return False

    #### Mouse - Qt events ##################################################

    def hoverEnterEvent(self, event):
        """ Hovering has some visual effects, usually handled in paint-method
        :param event:
        """
        self.set_hovering(True)
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """ Object needs to be updated
        :param event:
        """
        self.set_hovering(False)
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)


    #### Restoring after load / undo #########################################



