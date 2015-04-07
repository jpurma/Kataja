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
from kataja.Movable import Movable, MovableModel
from kataja.utils import to_tuple, create_shadow_effect
import kataja.globals as g
from kataja.parser.LatexToINode import parse_field



# ctrl = Controller object, gives accessa to other modules

# alignment of edges -- in some cases it is good to draw left branches differently than right branches

NO_ALIGN = 0
LEFT = 1
RIGHT = 2


class NodeModel(MovableModel):

    """ Model for storing values of instance that will be saved """

    def __init__(self, host):
        super().__init__(host)
        self.syntactic_object = None
        self.edges_up = []
        self.edges_down = []
        self.folded_away = False
        self.folding_towards = None
        self.color = None
        self.index = None

    def touch_syntactic_object(self, attribute, value):
        """ Similar as "touch", checks if the new value would change an attribute and makes the attribute undo-ready.
            Instead of model, this goes to model of syntactic object and does the operation there.
        :param attribute:
        :param value:
        :return:
        """
        so = getattr(self, 'syntactic_object', None)
        if so:
            model = getattr(so, 'model')
            if model:
                old_value = getattr(model, attribute, None)
                if old_value != value:
                    # hmmm... cannot now think through how badly it will break things as
                    touched_name = '_' + attribute + '_touched_synobj'
                    touched = getattr(self, touched_name, False)
                    if not touched:
                        ctrl.undo_pile.add(self._host)
                        setattr(model, '_' + attribute + '_history', old_value)
                        setattr(model, touched_name, True)
                    return True
        return False


class Node(Movable, QtWidgets.QGraphicsItem):
    """ Basic class for syntactic elements that have graphic representation """
    width = 20
    height = 20
    default_edge_type = g.ABSTRACT_EDGE
    node_type = g.ABSTRACT_NODE

    def __init__(self, syntactic_object=None):
        """ Node is an abstract class that shouldn't be used by itself, though
        it should contain all methods to make it work. Inherit and modify this for
        Constituents, Features etc. """
        if not hasattr(self, 'model'):
            self.model = NodeModel(self)
        QtWidgets.QGraphicsItem.__init__(self)
        Movable.__init__(self)
        self.syntactic_object = syntactic_object

        self._label_complex = None
        self._label_visible = True
        self._label_font = None  # @UndefinedVariable
        self._label_qdocument = None
        self.label_rect = None
        self._inode = None
        self._inode_changed = True

        self._index_label = None
        self._index_visible = True

        self._gravity = 0

        self.clickable = False
        self.selectable = True
        self.draggable = True

        self._magnets = []
        self.status_tip = ""

        self.width = 0
        self.height = 0

        self.inner_rect = None
        self.setAcceptHoverEvents(True)
        # self.setAcceptDrops(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.setZValue(10)
        self.fade_in()
        self.effect = create_shadow_effect(ctrl.cm.selection())
        self._update_magnets = True
        self.setGraphicsEffect(self.effect)

    @property
    def syntactic_object(self):
        """ Each Node _can_ be a vehicle for a syntactic object (or a representation of).
        The syntactic object may have its own model, so getting values from there may take few @properties
        :return:
        """
        return self.model.syntactic_object

    @syntactic_object.setter
    def syntactic_object(self, value):
        """ Each Node _can_ be a vehicle for a syntactic object (or a representation of).
        The syntactic object may have its own model, so getting values from there may take few @properties
        :return:
        """
        if self.model.touch('syntactic_object', value):
            self.model.syntactic_object = value

    @property
    def label(self):
        """ Label refers to syntactic object's label. If there is no syntactic object there is no label.
        Labels are important for syntactic manipulation.
        :return: str or ITextNode
        """
        if self.syntactic_object:
            return self.syntactic_object.label

    @label.setter
    def label(self, value):
        """ Label refers to syntactic object's label. If there is no syntactic object there is no label.
        Labels are important for syntactic manipulation.
        :param value: str or ITextNode
        """
        if self.model.touch_syntactic_object('label', value):
            self.syntactic_object.label = value
            self._inode_changed = True

    @property
    def edges_up(self):
        """ Edges up is a list of those edges that lead INTO this node, eg. these can be followed to get the parent
        nodes.
        :return: list (or set?) of Edge instances or None
        """
        return self.model.edges_up

    @edges_up.setter
    def edges_up(self, value):
        """ Edges up is a list of those edges that lead INTO this node, eg. these can be followed to get the parent
        nodes.
        :param value: list of Edge instances or None
        """
        if value is None:
            value = []
        if self.model.touch('edges_up', value):
            self.model.edges_up = value

    @property
    def edges_down(self):
        """ Edges down is a list of those edges that leave FROM this node, eg. these can be followed to get the child
        nodes.
        :return: list of Edge instances or None
        """
        return self.model.edges_down

    @edges_down.setter
    def edges_down(self, value):
        """ Edges down is a list of those edges that leave FROM this node, eg. these can be followed to get the child
        nodes.
        :param value: list (or set?) of Edge instances or None
        """
        if value is None:
            value = []
        if self.model.touch('edges_down', value):
            self.model.edges_down = value

    @property
    def folded_away(self):
        """ Flag to announce that node exists, but it is currently folded away
        :return:
        """
        return self.model.folded_away

    @folded_away.setter
    def folded_away(self, value):
        if value is None:
            value = False
        if self.model.touch('folded_away', value):
            self.model.folded_away = value

    @property
    def folding_towards(self):
        return self.model.folding_towards

    @folding_towards.setter
    def folding_towards(self, value):
        if self.model.touch('folding_towards', value):
            self.model.folding_towards = value

    @property
    def node_color(self):
        return self.model.color

    @node_color.setter
    def node_color(self, value):
        if self.model.touch('node_color', value):
            self.model.node_color = value


    # fixme: Ok why is this doubling constituentnode's index? do other nodes need index too?
    @property
    def index(self):
        return self.model.index

    @index.setter
    def index(self, value):
        if value is None:
            value = ''
        if self.model.touch('index', value):
            self.model.index = value
            self._inode_changed = True


    @property
    def hovering(self):
        return self._hovering

    @hovering.setter
    def hovering(self, value):
        """ Toggle hovering effects and internal bookkeeping
        :param value: bool
        :return:
        """
        self._set_hovering(value)

    def _set_hovering(self, value):
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
            self.setZValue(10)
            self.update()
            ctrl.remove_status(self.status_tip)


    def __repr__(self):
        """ This is a node and this represents this UG item """
        return '%s-%s' % (self.model.syntactic_object, self.model.save_key)


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
        self.update_bounding_rect()
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
        if not self.model.edges_down:
            return []
        if only_similar or edge_type is not None:
            if edge_type is None:
                edge_type = self.__class__.default_edge_type
            if only_visible:
                return [edge.end for edge in self.model.edges_down if
                        edge.edge_type == edge_type and edge.end and edge.end.is_visible()]
            else:
                return [edge.end for edge in self.model.edges_down if edge.edge_type == edge_type and edge.end]
        else:
            if only_visible:
                return [edge.end for edge in self.model.edges_down if edge.end and edge.end.is_visible()]
            else:
                return [edge.end for edge in self.model.edges_down if edge.end]

    def get_parents(self, only_similar=True, only_visible=False, edge_type=None):
        """
        Get parent nodes of this node.
        :param only_similar: boolean, only return nodes of same type (eg. ConstituentNodes)
        :param only_visible: boolean, only return visible nodes
        :param edge_type: int, only return Edges of certain subclass.
        :return: list of Nodes
        """
        if not self.model.edges_up:
            return []
        if only_similar or edge_type is not None:
            if edge_type is None:
                edge_type = self.__class__.default_edge_type
            if only_visible:
                return [edge.start for edge in self.model.edges_up if
                        edge.edge_type == edge_type and edge.start and edge.start.is_visible()]
            else:
                return [edge.start for edge in self.model.edges_up if edge.edge_type == edge_type and edge.start]
        else:
            if only_visible:
                return [edge.start for edge in self.model.edges_up if edge.start and edge.start.is_visible()]
            else:
                return [edge.start for edge in self.edges_up if edge.start]


    def is_connected_to(self, other):
        """ Generic check for having direct connection to some other node
        :param other:
        :return:
        """
        for edge in self.edges_up:
            if edge.start == other:
                return True
        for edge in self.edges_down:
            if edge.end == other:
                return True
        return False


    def left(self, only_visible=True):
        """

        :param only_visible:
        :return:
        """
        for edge in self.edges_down:
            if edge.edge_type == self.__class__.default_edge_type and edge.alignment == g.LEFT:
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
            if edge.edge_type == self.__class__.default_edge_type and edge.alignment == g.RIGHT:
                if edge.end:
                    if (only_visible and edge.end.is_visible()) or not only_visible:
                        return edge.end
                return None

    def is_sibling(self, other):
        """ Nodes are siblings if they share a parent.
        :param other: node to compared with
        :return:
        """
        parents = self.get_parents()
        other_parents = other.get_parents()
        for parent in parents:
            if parent in other_parents:
                return True
        return False

    def get_siblings(self):
        """ Return those nodes that are other children of node's parents
        :return:
        """
        sibs = []
        for parent in self.get_parents():
            for child in parent.get_children():
                if child is not self:
                    sibs.append(child)
        return sibs

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

    @property
    def font(self):
        """


        :return:
        """
        if self._label_font:
            return qt_prefs.font(self._label_font)
        else:
            return qt_prefs.font(ctrl.forest.settings.node_settings(self.node_type, 'font'))

    @font.setter
    def font(self, value):
        """

        :param value:
        """
        if isinstance(value, QtGui.QFont):
            self._label_font = qt_prefs.get_key_for_font(value)
        else:
            self._label_font = value

    # ### Colors and drawing settings ############################################################

    @property
    def color(self):
        """


        :return:
        """
        if self.node_color is None:
            return ctrl.cm.get(ctrl.forest.settings.node_settings(self.__class__.node_type, 'color'))
        else:
            return ctrl.cm.get(self.node_color)

    @color.setter
    def color(self, value=None):
        """

        :param value:
        :return:
        """
        self.node_color = value
        # if self._label_complex:
        # self._label_complex.setDefaultTextColor(self._color)

    def palette(self):
        """


        :return:
        """
        palette = QtGui.QPalette(ctrl.cm.get_qt_palette())
        palette.setColor(QtGui.QPalette.WindowText, self.color)
        palette.setColor(QtGui.QPalette.Text, self.color)
        return palette


    def contextual_color(self):
        """ Drawing color that is sensitive to node's state """
        if ctrl.pressed == self:
            return ctrl.cm.active(ctrl.cm.selection())
        elif self._hovering:
            return ctrl.cm.hovering(ctrl.cm.selection())
        elif ctrl.is_selected(self):
            return ctrl.cm.selection()
            # return ctrl.cm.selected(ctrl.cm.selection())
        else:
            return self.color

    # ### Labels and identity ###############################################################

    def update_label(self):
        """

        :return:
        """
        if not self._label_complex:
            self._label_complex = Label(parent=self)
        self._label_complex.update_label()
        self.update_bounding_rect()
        self.update_status_tip()

    @property
    def raw_label(self):
        """ Get the unparsed raw version of label (str)
        :return:
        """
        return self.label

    @property
    def as_inode(self):
        """
        :return: INodes or str or tuple of them
        """
        if self._inode_changed:
            self._inode = parse_field(self.label)
            self._inode_changed = False
        return self._inode

    def update_status_tip(self):
        """ implement properly in subclasses, let tooltip tell about the node
        :return: None
        """
        self.status_tip = str(self)


    def get_html_for_label(self):
        """ This should be overridden if there are alternative displays for label """
        return self.label

    def has_empty_label(self):
        """


        :return:
        """
        print('has_empty_label: ', self._label_complex.is_empty())
        return self._label_complex.is_empty()

    def label_edited(self):
        """ implement if label can be modified by editing it directly """
        pass


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

        # x,y,z = self.current_position
        # w2 = self.width/2.0
        # painter.setPen(self.contextual_color())
        # painter.drawEllipse(-w2, -w2, w2 + w2, w2 + w2)


    def update_bounding_rect(self):
        """


        :return:
        """
        my_class = self.__class__
        if self._label_visible and self._label_complex:
            lbr = self._label_complex.boundingRect()
            lbh = lbr.height()
            lbw = lbr.width()
            self.label_rect = QtCore.QRectF(self._label_complex.x(), self._label_complex.y(), lbw, lbh)
            self.width = max((lbw, my_class.width))
            self.height = max((lbh + self._label_complex.y_offset, my_class.height))
            y = self.height / -2
            x = self.width / -2
        else:
            self.label_rect = QtCore.QRectF(0, 0, 0, 0)
            self.width = my_class.width
            self.height = my_class.height
            y = self.height / -2
            x = self.width / -2
        self.inner_rect = QtCore.QRectF(x, y, self.width, self.height)
        self._update_magnets = True
        return self.inner_rect

    def boundingRect(self):
        """ BoundingRects are used often and cost of this method affects performance.
        inner_rect is used as a cached bounding rect and returned fast if there is no explicit
        update asked. """
        if self.inner_rect:
            return self.inner_rect
        else:
            return self.update_bounding_rect()


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
        self.hovering = False
        if ctrl.is_selected(self):
            self.open_embed()
        else:
            ctrl.select(self)

    def select(self, event=None):
        """ Scene has decided that this node has been clicked
        :param event:
        """
        self.hovering = False
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
            editor = ctrl.ui.get_constituent_edit_embed()
            ctrl.select(self)
            ctrl.ui.add_completion_suggestions(self)
            if editor and editor.isVisible():
                self.open_embed()

    # def drag(self, event):
    # """ Drags also elements that are counted to be involved: features, children etc """
    # mx, my = to_tuple(event.scenePos())
    # if not getattr(ctrl, 'dragged', None):
    # self.start_dragging(mx, my)
    # for item, ox, oy in ctrl.dragged_positions:
    # x, y, z = item.current_position
    # item.set_adjustment(dx, dy, 0)
    # item.update_position()

    # [b.update() for b in item.get_children() + item.edges_up + item.edges_down]
    # ctrl.scene.item_moved()

    def start_dragging(self, mx, my):
        """

        :param mx:
        :param my:
        """
        print("start dragging for ", self)
        ctrl.dragged = set()

        # there if node is both above and below the dragged node, it shouldn't move
        ctrl.dragged.add(self)
        x, y, z = self.current_position
        self._position_before_dragging = x, y, z
        self._adjustment_before_dragging = self.adjustment or (0, 0, 0)
        ctrl.ui.prepare_touch_areas_for_dragging(drag_host=self, moving=ctrl.dragged, node_type=self.node_type)

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


    def dragged_over_by(self, dragged):
        """

        :param dragged:
        """
        if not self._hovering and self.accepts_drops(dragged):
            if ctrl.latest_hover and not ctrl.latest_hover is self:
                ctrl.latest_hover.hovering = False
            ctrl.latest_hover = self
            self.hovering = True

    def accepts_drops(self, dragged):
        """

        :param dragged:
        :return:
        """
        if isinstance(dragged, ControlPoint):
            if dragged.role == g.START_POINT or dragged.role == g.END_POINT:
                return True
        # elif isinstance(dragged, TouchArea):
        # return True
        return False

    def drop_to(self, x, y, recipient=None):
        """


        :param recipient:
        :param x:
        :param y:
        """
        self.release()
        self.update()
        if recipient and recipient.accepts_drops(self):
            self.adjustment = (0, 0, 0)
            recipient.drop(self)
        else:
            for node in ctrl.dragged:
                node.lock()
                ctrl.main.ui_manager.show_anchor(node)  # @UndefinedVariable
        del self._position_before_dragging
        del self._adjustment_before_dragging
        ctrl.dragged = set()
        ctrl.dragged_positions = set()
        ctrl.main.action_finished('moved node %s' % self)
        # ctrl.scene.fit_to_window()


    #### Mouse - Qt events ##################################################

    def hoverEnterEvent(self, event):
        """ Hovering has some visual effects, usually handled in paint-method
        :param event:
        """
        self.hovering = True
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """ Object needs to be updated
        :param event:
        """
        self.hovering = False
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)


    def dragEnterEvent(self, event):
        """

        :param event:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
            self.hovering = True
        else:
            QtWidgets.QGraphicsItem.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        """

        :param event:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
            self.hovering = False
        else:
            QtWidgets.QGraphicsItem.dragLeaveEvent(self, event)

            # def dragMoveEvent(self, event):
            # if
            # pass
            # print("Drag move event for Movable")


            #### Restoring after load / undo #########################################

