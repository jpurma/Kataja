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

import math

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import Qt

import kataja.globals as g
import kataja.ui_widgets.buttons.OverlayButton as Buttons
from kataja.SavedField import SavedField
from kataja.SimpleLabel import SimpleLabel
from kataja.Triangle import Triangle
from kataja.parser.INodes import as_html
from kataja.saved.Draggable import Draggable
from kataja.saved.Movable import Movable
from kataja.settings.NodeSettings import NodeSettings
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.ui_widgets.embeds.NodeEditEmbed import NodeEditEmbed
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import equal_synobj

call_counter = [0]

#qbytes_scale = QtCore.QByteArray()
#qbytes_scale.append("scale")
qbytes_scale = QtCore.QByteArray("scale".encode())


# ctrl = Controller object, gives accessa to other modules


class Node(Draggable, Movable):
    """ Basic class for any visualization elements that can be connected to
    each other """
    __qt_type_id__ = next_available_type_id()
    width = 20
    height = 20
    node_type = g.ABSTRACT_NODE
    is_constituent = False
    is_syntactic = True
    ordered = False
    ordering_func = None
    display_name = ('Abstract node', 'Abstract nodes')
    display = False
    can_be_in_groups = True
    resizable = False
    quick_editable = False
    editable_fields = {}
    allowed_child_types = []

    default_style = {
        'color_key': 'content1',
        'font_id': g.MAIN_FONT,
        'font-size': 10,
        'card': False,
        'card_width': 0,
        'card_height': 0,
        'visible': True,
    }

    embed_edit = NodeEditEmbed
    default_edge = g.ABSTRACT_EDGE
    touch_areas_when_dragging = []
    touch_areas_when_selected = []
    buttons_when_selected = [Buttons.NodeEditorButton, Buttons.NodeUnlockButton]  # Buttons.RemoveNodeButton

    def __init__(self, forest=None):
        """ Node is an abstract class that shouldn't be used by itself, though
        it should contain all methods to make it work. Inherit and modify
        this for Constituents, Features etc. """
        self.label_object = None
        Movable.__init__(self, forest=forest)
        Draggable.__init__(self)
        self.settings = NodeSettings(self)
        self.label_object = SimpleLabel(parent=self)
        self.syntactic_object = None
        self.label = ''
        self.selected = False
        self._label_visible = True
        self.label_rect = None
        self._gravity = 0
        self.drag_data = None
        self.user_size = None
        self.invert_colors = False
        self.text_parse_mode = 1
        self._magnets = []
        self.is_syntactically_valid = False
        self.width = 0
        self.height = 0
        self.is_trace = False
        self.inner_rect = None
        self._cached_child_rect = None
        self.anim = None
        self.magnet_mapper = None
        self.halo = False
        self.halo_item = None

        self.in_scene = False

        self.edges_up = []
        self.edges_down = []
        self.triangle_stack = []  # you can always unfold only the outermost triangle, so stack
        self.color_key = None
        self.invert_colors = False

        self._editing_template = {}

        self.label_display_data = {}
        self.setFiltersChildEvents(False)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.setCacheMode(QtWidgets.QGraphicsItem.CacheMode.DeviceCoordinateCache)
        self.setFlag(QtWidgets.QGraphicsObject.GraphicsItemFlag.ItemSendsGeometryChanges)
        # self.setFlag(QtWidgets.QGraphicsObject.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsObject.GraphicsItemFlag.ItemIsSelectable)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        # self.fade_in()
        self.update_visibility()

    def set_syntactic_object(self, synobj):
        old = self.syntactic_object
        self.syntactic_object = synobj
        if self.forest:
            if synobj:
                self.forest.nodes_from_synobs[synobj.uid] = self
            elif old and not synobj:
                del self.forest.nodes_from_synobs[old.uid]

    def __lt__(self, other):
        return self.label < other.label

    def __gt__(self, other):
        return self.label > other.label

    def edge_type(self):
        """ Default edge for this kind of node, as in kataja.globals type ids."""
        return self.__class__.default_edge

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
            1st wave creates the objects and calls __init__, and then
            iterates through and sets the values.
            2nd wave calls after_inits for all created objects. Now they can
            properly refer to each other and know their
                values.
        :return: None
        """
        self.in_scene = True
        self.update_label()
        self.update_visibility()
        self.announce_creation()
        if prefs.glow_effect:
            self.toggle_halo(True)
        self.forest.store(self)

    def after_model_update(self, updated_fields, transition_type):
        """ Compute derived effects of updated values in sensible order.
        :param updated_fields: field keys of updates
        :param transition_type: 0:edit, 1:CREATED, -1:DELETED
        :return: None
        """
        if transition_type == g.CREATED:
            print('*** re-creating node in after_model_update')
            self.update_label()
            self.update_visibility()
            self.forest.store(self)
            self.forest.add_to_scene(self)
            return
        elif transition_type == g.DELETED:
            print('*** deleting node in after_model_update')
            ctrl.drawing.delete_node(self, touch_edges=False, fade=False)
            return

        if 'triangle_stack' in updated_fields:
            if self.is_triangle_host():
                Triangle.add_or_update_triangle_for(self)
        if 'locked_to_node' in updated_fields:
            print('updating locked_to_node')
            if isinstance(self.parentItem(), Node):
                if not self.locked_to_node:
                    self.release_from_locked_position()
            elif self.locked_to_node:  # parent is Tree
                self.lock_to_node(self.locked_to_node)
        self.update_position()
        self.update_label()
        self.update_visibility()

    @staticmethod
    def create_synobj(label, forest):
        """ (Abstract) Nodes do not have corresponding syntactic object, so
        return None and the Node factory knows to not try to pass syntactic
        object -argument.
        :param label: not used here
        :param forest: context where created
        :return:
        """
        return None

    @property
    def centered_scene_position(self):
        sx, sy = self.current_scene_position
        sx += self.label_object.x_offset + self.width / 2
        sy += self.label_object.y_offset + self.height / 2
        return sx, sy

    def label_as_html(self):
        """ This method builds the html to display in label. For convenience, syntactic objects
        can override this (going against the containment logic) by having their own
        'label_as_html' -method. This is so that it is easier to create custom
        implementations for constituents without requiring custom constituentnodes.

        Note that synobj's label_as_html receives the node object as parameter,
        so you can replicate the behavior below and add your own to it.
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'label_as_html'):
            return self.syntactic_object.label_as_html(self)

        return as_html(self.label)

    def label_as_editable_html(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label or synobj's label. This can be overridden in syntactic object by having
        'label_as_editable_html' -method there. The method returns a tuple,
          (field_name, setter, html).
        """
        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'label_as_editable_html'):
            return self.syntactic_object.label_as_editable_html(self)

        return 'label', as_html(self.label)

    def parse_edited_label(self, label_name, value):
        if self.syntactic_object and hasattr(self.syntactic_object, 'parse_edited_label'):
            self.syntactic_object.parse_edited_label(label_name, value)
        elif label_name == 'node label':
            self.label = value
        elif label_name == 'syntactic label':
            self.syntactic_object.label = value
        print('**** parse edited label at generic node ****')

    def is_empty(self):
        return self.label_object.is_empty()

    def is_triangle_host(self):
        return bool(self.triangle_stack and self.triangle_stack[-1] is self)

    def can_have_triangle(self):
        return (not self.triangle_stack) and not self.is_leaf()

    def if_changed_font(self, value):
        self.label_object.set_font(qt_prefs.get_font(value))

    # Non-model-based properties ########################################

    # noinspection PyMethodMayBeStatic
    def get_triangle_text(self):
        """ Label with triangled elements concatenated into it
        :return:
        """
        return ''

    def __repr__(self):
        """ This is a node and this represents this FL item """
        return '%s-%s' % (self.syntactic_object, self.uid)

    def reset(self):
        """
        Remove temporary/state information from node, eg. remove touch areas.
        """
        Movable.reset(self)
        self.update_bounding_rect()
        ctrl.ui.remove_touch_areas_for(self)

    # ### Children and parents
    # ####################################################

    def get_children(self, visible=False, of_type=None) -> list:
        """
        Get child nodes of this node
        :return: iterator of Nodes
        """
        of_type = of_type or self.node_type
        if visible:
            if of_type == g.FEATURE_NODE:
                return [edge.end for edge in self.edges_down if
                        edge.end and edge.end.node_type == of_type and edge.end.is_visible()]
            else:
                return [edge.end for edge in self.edges_down if
                        edge.end and edge.end.node_type == of_type and (not edge.origin) and edge.end.is_visible()]
        else:
            if of_type == g.FEATURE_NODE:
                return [edge.end for edge in self.edges_down if
                        edge.end and edge.end.node_type == of_type]
            else:
                return [edge.end for edge in self.edges_down if
                        edge.end and (not edge.origin) and edge.end.node_type == of_type]

    def get_all_children(self, visible=False) -> list:
        """
        Get child nodes of this node
        :return: iterator of Nodes
        """
        if visible:
            return [edge.end for edge in self.edges_down if edge.end and edge.end.is_visible()]
        else:
            return [edge.end for edge in self.edges_down if edge.end]

    def get_parents(self, visible=False, of_type=None) -> list:
        """
        :param visible: boolean, only return visible nodes
        :param of_type: int, only return parents of certain node_type
        :return: list of Nodes
        """
        if not self.edges_up:
            return []
        of_type = of_type or self.node_type
        if visible:
            return [edge.start for edge in self.edges_up if
                    edge.start and edge.start.node_type == of_type and (not edge.origin) and edge.start.is_visible()]
        else:
            return [edge.start for edge in self.edges_up if
                    edge.start and edge.start.node_type == of_type and not edge.origin]

    def get_all_parents(self, visible=False) -> list:
        """
        :param visible: boolean, only return visible nodes
        :return: list of Nodes
        """
        if not self.edges_up:
            return []
        if visible:
            return list(set(edge.start for edge in self.edges_up if
                            edge.start and edge.start.is_visible()))
        else:
            return list(set(edge.start for edge in self.edges_up if edge.start))

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

    def is_unary(self):
        for parent in self.get_parents():
            if len(parent.get_children()) == 1:
                return True
        return False

    def is_leaf(self, visible=False):
        return not self.get_children(visible=visible)

    def is_top_node(self, visible=False):
        """ Root node is the topmost node of a trees
        :param visible:
        """
        return not self.get_parents(visible=visible)

    def get_edge_to(self, other, edge_type='', origin=None) -> QtWidgets.QGraphicsItem or None:
        """ Returns edge object, not the related node. There should be only
        one instance of edge
        of certain type between two elements.
        :param other:
        :param edge_type:
        :param origin: final node of a many parted edge, projecting feature
        """
        if origin:
            if edge_type:
                for edge in self.edges_down:
                    if equal_synobj(origin, edge.origin) and edge.end is other and edge_type == edge.edge_type:
                        return edge
                for edge in self.edges_up:
                    if equal_synobj(origin, edge.origin) and edge.start is other and edge_type == edge.edge_type:
                        return edge
            else:
                for edge in self.edges_down:
                    if equal_synobj(origin, edge.origin) and edge.end is other:
                        return edge
                for edge in self.edges_up:
                    if equal_synobj(origin, edge.origin) and edge.start is other:
                        return edge
        else:
            if edge_type:
                for edge in self.edges_down:
                    if edge.end is other and edge_type == edge.edge_type:
                        return edge
                for edge in self.edges_up:
                    if edge.start is other and edge_type == edge.edge_type:
                        return edge
            else:
                for edge in self.edges_down:
                    if edge.end is other:
                        return edge
                for edge in self.edges_up:
                    if edge.start is other:
                        return edge
        return None

    def get_edges_up(self, similar=True, visible=False):
        """ Returns edges up, filtered"""

        def filter_func(edge):
            if similar and edge.start.node_type != self.node_type:
                return False
            if visible and not edge.is_visible():
                return False
            return True

        return filter(filter_func, self.edges_up)

    def list_descendants_once(self):
        """ Do left-first iteration through all nodes and return a list where
        only first instance of each node is present.
        """
        done = set()
        result = []

        def _iterate(node):
            if node not in done:
                result.append(node)
                done.add(node)
                for edge in node.edges_down:
                    if edge.end:
                        _iterate(edge.end)

        _iterate(self)
        return result[1:]

    def can_have_as_child(self, other=None):
        """ Check, usually when dragging objects, if parent -- child relationship is possible in
        current state. This can be affected by the editing mode, properties of child and parent
        and if they already have this relationship.
        """

        if other is None:
            if ctrl.dragged_focus:
                other = ctrl.dragged_focus
                other_type = other.node_type
            else:
                other_type = ctrl.dragged_text
        else:
            other_type = other.node_type
        if other_type in self.allowed_child_types:
            return other not in self.get_all_children(visible=False) if other else True
        return False

    def get_sorted_nodes(self):
        """ Recursively get children nodes, their children etc. sorted.
        :return:
        """
        sorted_nodes = []
        used = set()

        def add_children(node):
            if node not in used:
                used.add(node)
                sorted_nodes.append(node)
                for child in node.get_all_children(visible=False):
                    add_children(child)

        add_children(self)
        return sorted_nodes

    def get_highest(self):
        """ Recursively get highest grandparents/parents that can be found. Because
        multidomination, there can be more than one result, so this returns a list.
        :return:
        """
        tops = []
        used = set()

        def go_up(node):
            if node not in used:
                used.add(node)
                parents = node.get_all_parents(visible=False)
                if parents:
                    for parent in parents:
                        go_up(parent)
                else:
                    tops.append(node)

        go_up(self)
        return tops

    # ## Font
    # #####################################################################

    def get_font(self) -> QtGui.QFont:
        """ Helper to get the QFont being used here. It may be local, or set
        for forest, or come from default preferences. You don't need to know.
        :return:
        """
        return qt_prefs.get_font(self.get_font_id())

    def get_font_id(self) -> str:
        """
        :return:
        """
        return self.settings.get('font_id')

    def set_font_id(self, value):
        self.settings.set('font_id', value)

    # ### Colors and drawing settings
    # ############################################################

    @property
    def color(self) -> QtGui.QColor:
        """ Helper property to directly get the inherited/local QColor
        :return:
        """
        return ctrl.cm.get(self.get_color_key())

    def get_color_key(self):
        """
        :return:
        """
        if self.syntactic_object and self.syntactic_object.adjunct:
            return 'accent7'
        return self.settings.get('color_key')

    def set_color_key(self, value):
        self.settings.set('color_key', value)

    def palette(self):
        """
        :return:
        """
        palette = QtGui.QPalette(ctrl.cm.get_qt_palette())
        palette.setColor(QtGui.QPalette.ColorRole.WindowText, self.color)
        palette.setColor(QtGui.QPalette.ColorRole.Text, self.color)
        return palette

    def contextual_color(self):
        """ Drawing color that is sensitive to node's state
        :return: QColor
        """
        base = ctrl.cm.selection() if self.selected else ctrl.cm.get(self.get_color_key())
        if self.drag_data:
            return ctrl.cm.lighter(base)
        elif ctrl.pressed is self:
            return ctrl.cm.active(base)
        elif self.hovering:
            return ctrl.cm.hovering(base)
        else:
            return base

    def get_edge_start_symbol(self):
        return 0

    # ### Labels and identity
    # ###############################################################

    def update_label(self):
        """
        :return:
        """
        self.label_object.update_font()
        self.label_object.update_label()
        self.update_label_visibility()
        self.update_bounding_rect()
        self.update_tooltip()

    def update_label_visibility(self):
        """ Check if the label of the node has any content -- should it be
        displayed. Node itself can be visible even when its label is not.
        :return:
        """
        self._label_visible = self.label_object.keep_visible()
        self.label_object.setVisible(self._label_visible)

    def update_tooltip(self):
        """ implement properly in subclasses, let tooltip tell about the node
        :return: None
        """
        self.k_tooltip = str(self)

    def has_empty_label(self):
        """
        :return:
        """
        return not self.label_object.has_content()

    def label_edited(self):
        """ implement if label can be modified by editing it directly """
        pass

    def get_top_y(self):
        """ Implement this if the movable has content where differentiating between bottom row and
         top row can potentially make sense.
        :return:
        """
        return self.label_object.get_top_y()

    # ## Qt overrides
    # ######################################################################
    # @time_me

    # Probably overrided by node type's own paint-method
    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        xr = 5
        yr = 5
        pen = QtGui.QPen(self.contextual_color())
        pen.setWidth(1)
        rect = False
        brush = Qt.BrushStyle.NoBrush

        if self.drag_data:
            rect = True
            brush = self.drag_data.background
        elif self.hovering:
            if rect:
                brush = ctrl.cm.paper()
            rect = True
        elif ctrl.pressed is self or self.selected:
            if rect:
                brush = ctrl.cm.paper()
            if not hasattr(self, 'halo'):
                rect = True

        painter.setPen(pen)
        if rect:
            painter.setBrush(brush)
            painter.drawRoundedRect(self.inner_rect, xr, yr)

    def has_visible_label(self):
        """
        :return: bool
        """
        return self._label_visible

    def can_cascade_edges(self):
        """ Cascading edges is a visual effect for nodes that try to display many similar edges
        that go through this node. When cascaded, each edge has increasing/decreasing starting y
        compared to others. It gets ugly if some edges are strongly cascaded while others are
        flat, so node should make a decision if this should be applied at all.
        :return:
        :rtype:
        """
        return False

    def _create_magnets(self, x, y, w, h):
        w4 = (w - 2) / 4.0
        w2 = (w - 2) / 2.0
        h2 = (h - 2) / 2.0
        y_max = y + h - 4
        x_max = x + w

        #  0--1--2--3--4
        #  |           |
        #  5           6
        #  |           |
        #  7--8--9-10-11
        self._magnets = [
            (x, y),
            (x + w4, y),
            (x + w2, y),
            (x + w2 + w4, y),
            (x_max, y),
            (x, y + h2),
            (x_max, y + h2),
            (x, y_max),
            (x + w4, y_max),
            (x + w2, y_max),
            (x + w2 + w4, y_max),
            (x_max, y_max)]

    def _calculate_inner_rect(self, min_w=0, min_h=0):
        my_class = self.__class__
        label = self.label_object
        x_offset = 0
        y_offset = 0
        label_w = 0
        label_h = 0
        if self._label_visible:
            label_rect = label.boundingRect()
            label_w = label_rect.width()
            label_h = label_rect.height()
            x_offset = label.x_offset
            y_offset = label.y_offset
            self.label_rect = label_rect
        w = max((min_w, label_w, my_class.width))
        h = max((min_h, label_h, my_class.height))
        if x_offset or y_offset:
            x = x_offset
            y = y_offset
        else:
            x = w / -2
            y = h / -2
        self.width = w
        self.height = h
        self._create_magnets(x, y, w, h)
        return QtCore.QRectF(x, y, w, h)

    def update_bounding_rect(self):
        """ Do housekeeping for bounding rect and related measurements
        :return:
        """
        old_br = self.inner_rect
        self.inner_rect = self._calculate_inner_rect()

        expanding_rect = QtCore.QRectF(self.inner_rect)
        for child in self.childItems():
            if isinstance(child, Node) and child.is_visible() and not child.has_adjustment():
                expanding_rect |= child.future_children_bounding_rect().translated(
                    *child.target_position)

        self._cached_child_rect = expanding_rect

        if old_br != self.inner_rect:
            self.prepareGeometryChange()
            if ctrl.ui.selection_group and self in ctrl.ui.selection_group.selection:
                ctrl.ui.selection_group.please_update()
        return self.inner_rect

    def overlap_rect(self):
        if self._label_visible:
            return self.sceneBoundingRect().adjusted(-2, -2, 4, 4)
        else:
            return QtCore.QRectF()

    def scene_rect_coordinates(self, current=False):
        if current:
            return self.sceneBoundingRect().getCoords()
        if self.is_moving:
            scx, scy = self.target_position
        else:
            scx, scy = self.current_position
        minx, miny, maxx, maxy = self.future_children_bounding_rect().getCoords()
        minx += scx
        miny += scy
        maxx += scx
        maxy += scy
        return minx, miny, maxx, maxy

    def future_children_bounding_rect(self, limit_height=False) -> QtCore.QRectF:
        """ This combines boundingRect with children's boundingRects based on children's
        target_positions instead of their current positions. This is needed because when you are
        trying to calculate node's effective size, its childItems may still be far away and
        moving into place -- including these would make the node unreasonably large and mess up
        attempts to position it in visualisation. Using this you will get the final, intended
        size of the node.
        You'll want to use this to estimate the actual size of node + childItems when reserving
        room for node in visualisation.
        :param limit_height: return boundingRect that only expands its width to include children,
        height is the called node's boundingRect.
        :return:
        """
        if not self._cached_child_rect:
            self.update_bounding_rect()
        if limit_height:
            br = QtCore.QRectF(self._cached_child_rect)
            br.setHeight(self.boundingRect().height())
            return br
        return self._cached_child_rect

    def boundingRect(self):
        """ BoundingRects are used often and cost of this method affects
        performance.
        inner_rect is used as a get_shape_setting bounding rect and returned fast if
        there is no explicit
        update asked. """
        if not self.inner_rect:
            return self.update_bounding_rect()
        else:
            return self.inner_rect

    def node_center_position(self):
        """ Return coordinates for center of node. Nodes, especially with children
        included, are often offset in such way that we shouldn't use bounding_rect's 0,
        0 for their center point.
        :return:
        """
        px, py = self.current_position
        cp = self.future_children_bounding_rect().center()
        px += cp.x()
        py += cp.y()
        return px, py

    # #### Locking node to another node (e.g. features to constituent and in triangles)

    def release_from_locked_position(self):
        was_locked = self.locked_to_node
        if was_locked:
            self.locked_to_node = None
            scene_pos = self.scenePos()
            # following doesn't work reliably on undo:
            new_parent = self.parentItem().parentItem()
            if new_parent:
                lp = new_parent.mapFromScene(scene_pos)
            else:
                lp = scene_pos
            self.setParentItem(new_parent)
            self.current_position = lp.x(), lp.y()
            self.stop_moving()
            self.update_bounding_rect()
            if isinstance(was_locked, Node):
                was_locked.update_bounding_rect()

    def lock_to_node(self, parent, move_to=None):
        previously = self.locked_to_node
        if previously is not parent:
            self.locked_to_node = parent
            scene_pos = self.scenePos()
            self.setParentItem(parent)
            lp = parent.mapFromScene(scene_pos)
            self.current_position = lp.x(), lp.y()
            self.stop_moving()
            self.update_bounding_rect()
            if move_to:
                self.move_to(*move_to)
            parent.update_bounding_rect()
            if isinstance(previously, Node):
                previously.update_bounding_rect()
        elif move_to:
            assert (self.parentItem() == self.locked_to_node)
            self.move_to(*move_to)
            parent.update_bounding_rect()

    def get_edges_down_with_children(self, start=None, edges=None):
        """ Sometimes you need to count in also edges of locked in nodes (they are childItems). 
        :return: 
        """
        if not start:
            start = self
            edges = []
        for e in self.edges_down:
            end = e.end
            while end.locked_to_node:
                end = end.locked_to_node
            if end is not start:
                edges.append((end, e))
        for item in self.childItems():
            if isinstance(item, Node):
                item.get_edges_down_with_children(start=self, edges=edges)
        return edges

    def get_edges_up_with_children(self, end=None, edges=None):
        """ Sometimes you need to count in also edges of locked in nodes (they are childItems). 
        :return: 
        """
        if not end:
            end = self
            edges = []
        for e in self.edges_up:
            start = e.start
            while start.locked_to_node:
                start = start.locked_to_node
            if end is not start:
                edges.append((start, e))
        for item in self.childItems():
            if isinstance(item, Node):
                item.get_edges_up_with_children(end=self, edges=edges)
        return edges

    def reindex_edges(self):
        pass

    def hidden_in_triangle(self):
        """ Check if this node should be included in triangle's visible row of nodes or if it 
        should be hidden. 
        :return: 
        """
        return self.triangle_stack and self.triangle_stack[-1] is not self and not self.is_leaf()

    def in_triangle(self, exclude_top=False):
        return self.triangle_stack and (not exclude_top or self.triangle_stack[-1] is not self)

    # ## Magnets
    # ######################################################################

    def top_center_magnet(self, scene_pos=None):
        return self.magnet(2, scene_pos=scene_pos)

    def bottom_left_magnet(self, scene_pos=None):
        return self.magnet(8, scene_pos=scene_pos)

    def bottom_center_magnet(self, scene_pos=None):
        return self.magnet(9, scene_pos=scene_pos)

    def bottom_right_magnet(self, scene_pos=None):
        return self.magnet(10, scene_pos=scene_pos)

    def bottom_magnet(self, i, size, scene_pos=None):
        """ Bottom magnets that divide the bottom area to (size) points, so that each edge has a
        separate starting point. For binary branching, use the default three points.
        :param i: index in list of sibling
        :param size: size of list of siblings
        :param scene_pos: current position can be given as parameter, otherwise uses
        current_scene_position
        :return:
        """
        magnets = self.forest.settings.get('use_magnets')
        if scene_pos:
            x1, y1 = scene_pos
        else:
            x1, y1 = scene_pos = self.current_scene_position
        if not magnets:
            return scene_pos
        elif not self.has_visible_label():
            return scene_pos
        elif not self._magnets:
            self.update_bounding_rect()
        if size == 2:  # and False:
            if i == 0:
                return self.magnet(8, scene_pos)
            elif i == 1:
                return self.magnet(10, scene_pos)
        elif size == 3:  # and False:
            if i == 0:
                return self.magnet(8, scene_pos)
            elif i == 1:
                return self.magnet(9, scene_pos)
            elif i == 2:
                return self.magnet(10, scene_pos)
        x2, y2 = self._magnets[7]
        x2 += (self.width / (size + 1)) * (i + 1)
        if magnets == 2:
            x2, y2 = self._angle_to_parent(x1, y1, x2, y2)
        return int(x1 + x2), int(y1 + y2)

    def _angle_to_parent(self, x1, y1, x2, y2):
        parents = self.get_parents(visible=True)
        # We don't want to rotate multidominated or top nodes
        if len(parents) == 1:
            # Compute angle to parent
            px, py = parents[0].current_scene_position
            dx, dy = x1 - px, y1 - py
            r = -math.atan2(dy, dx) + (math.pi / 2)
            # Rotate magnet coordinates according to angle
            cos_r = math.cos(r)
            sin_r = math.sin(r)
            x = x2
            y = y2
            # if r > 0 and False:
            #    x2 = x * cos_r - y * sin_r
            #    y2 = x * sin_r + y * cos_r
            # else:
            x2 = x * cos_r + y * sin_r
            y2 = -x * sin_r + y * cos_r
        return int(x2), int(y2)

    def magnet(self, n, scene_pos=None):
        """
        :param n: index of magnets. There are five magnets in top and bottom
        and three for sides:

        0   1   2   3   4
        5               6
        7   8   9   10  11

        :param scene_pos: current position can be given as parameter, otherwise uses
        current_scene_position
        :return:
        """
        magnets = self.forest.settings.get('use_magnets')
        if scene_pos:
            x1, y1 = scene_pos
        else:
            x1, y1 = scene_pos = self.current_scene_position
        if not magnets:
            return scene_pos
        elif not self.has_visible_label():
            return scene_pos
        elif not self._magnets:
            self.update_bounding_rect()
        if self.magnet_mapper:
            n = self.magnet_mapper(n)
        x2, y2 = self._magnets[n]
        if magnets == 2:
            x2, y2 = self._angle_to_parent(x1, y1, x2, y2)
        return int(x1 + x2), int(y1 + y2)

    # ### Menus #########################################

    def update_selection_status(self, selected):
        """ This is called after item is selected or deselected to update
        appearance and related local elements.
        :param selected:
        """
        self.selected = selected
        if selected:
            self.setZValue(200)
            if ctrl.single_selection() and not ctrl.multiselection_delay:
                if self.quick_editable and prefs.single_click_editing:
                    self.label_object.set_quick_editing(True)
        else:
            self.setZValue(self.preferred_z_value())
            self.label_object.set_quick_editing(False)
        self.update()

    # ### MOUSE - kataja
    # ########################################################

    def open_embed(self):
        """ Tell ui_support to open an embedded edit, generated from
        edit template or overridden.
        :return: None
        """
        ctrl.ui.start_editing_node(self)

    def select(self, adding=False, select_area=False):
        """ Scene has decided that this node has been clicked
        :param adding: bool, we are adding to selection instead of starting a new selection
        :param select_area: bool, we are dragging a selection box, method only informs that this
        node can be included
        :returns: self if node is selectable
        """
        self.hovering = False
        # if we are selecting an area, select actions are not called here, but once for all
        # objects. In this case return only uid of this object.
        if select_area:
            return self
        if adding:
            if self.selected:
                action = ctrl.ui.get_action('remove_from_selection')
            else:
                action = ctrl.ui.get_action('add_to_selection')
            action.run_command(self.uid)
        elif self.selected:
            if len(ctrl.selected) > 1:
                action = ctrl.ui.get_action('select')
                action.run_command(self.uid)
            else:
                if self.quick_editable and not prefs.single_click_editing:
                    self.label_object.set_quick_editing(True)
        else:
            action = ctrl.ui.get_action('select')
            action.run_command(self.uid)
        return self

    def has_ordered_children(self):
        return True

    def update_visibility(self, fade_in=True, fade_out=True, skip_label=False) -> bool:
        """ see Movable.update_visibility
        This is called logical visibility and can be checked with is_visible().
        Qt's isVisible() checks for scene visibility. Items that are e.g. fading away
        have False for logical visibility but True for scene visibility and items that are part
        of graph in a forest that is not currently drawn may have True for logical visibility but
        false for scene visibility.
        """
        # Label
        if not skip_label:
            self.update_label_visibility()

        if (not self.is_syntactic) and ctrl.forest.settings.get('syntactic_mode'):
            self._visible_by_logic = False
        elif self.settings.get('visible') and not self.hidden_in_triangle():
            self._visible_by_logic = True
        else:
            self._visible_by_logic = False

        changed = super().update_visibility(fade_in=fade_in, fade_out=fade_out)
        if changed:
            # ## Edges -- these have to be delayed until all constituents etc nodes know if they are
            # visible
            self.forest.order_edge_visibility_check()
        return changed

    def update_cn_shape(self):
        pass

    def is_quick_editing(self):
        return self.label_object.is_quick_editing()

    # ###### Halo for showing some association with selected node (e.g. c-command) ######

    def start_moving(self):
        """ Hint edges that they shouldn't compute everything while these nodes are moving.
        :return:
        """
        super().start_moving()
        if prefs.move_effect:
            self.toggle_halo(True)
        for edge in self.edges_down:
            edge.start_node_started_moving()
        for edge in self.edges_up:
            edge.end_node_started_moving()

    def stop_moving(self):
        """ Experimental: remove glow effect from moving things
        :return:
        """
        super().stop_moving()
        if prefs.move_effect:
            if not self.selected:
                self.toggle_halo(False)
        for edge in self.edges_down:
            edge.start_node_stopped_moving()
        for edge in self.edges_up:
            edge.end_node_stopped_moving()

    def toggle_halo(self, value, small=False):
        if value and not self.halo_item:
            self.halo = True
            r = QtCore.QRectF(self.inner_rect)
            iw = ew = r.width()
            ih = eh = r.height()
            if iw < ih:
                eh = iw
            else:
                ew = ih
            if small:
                ew = 10
                eh = 10
            ex = ((iw - ew) / 2) - (iw / 2)
            ey = ((ih - eh) / 2) - (ih / 2)
            er = QtCore.QRectF(ex, ey, ew, eh)

            self.halo_item = QtWidgets.QGraphicsEllipseItem(er)
            self.halo_item.setParentItem(self)
            self.update_halo(color=ctrl.cm.selection())
            effect = QtWidgets.QGraphicsBlurEffect()
            if small:
                effect.setBlurRadius(2)
            else:
                effect.setBlurRadius(2)
            self.halo_item.setGraphicsEffect(effect)
            # self.halo_item.show()
        if (not value) and self.halo_item:
            if prefs.glow_effect:
                self.halo = True
                self.update_halo(color=ctrl.cm.selection())
            else:
                self.halo = False
                # self.halo_item.hide()
                # noinspection PyTypeChecker
                self.halo_item.setParentItem(None)
                scene = self.halo_item.scene()
                if scene:
                    scene.removeItem(self.halo_item)
                self.halo_item = None
        self.update()

    def update_halo(self, color):
        c = color.lighter(int(100 + (1 - ctrl.cm.background_lightness) * 120))
        c = ctrl.cm.transparent(c, opacity=128)
        self.halo_item.setZValue(2)
        self.halo_item.setPen(c)
        self.halo_item.setBrush(c)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # Saved properties
    syntactic_object = SavedField("syntactic_object")
    label = SavedField("label")
    edges_up = SavedField("edges_up")
    edges_down = SavedField("edges_down")
    triangle_stack = SavedField("triangle_stack")
