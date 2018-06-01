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

import itertools
import math
from collections import defaultdict
import time
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

import kataja.globals as g
from kataja.Label import Label
from kataja.SavedField import SavedField
from kataja.saved.Movable import Movable
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.ui_graphicsitems.ControlPoint import ControlPoint
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import to_tuple, create_shadow_effect, add_xy, time_me, create_blur_effect
from kataja.parser.INodes import as_html
import kataja.ui_widgets.buttons.OverlayButton as Buttons

call_counter = [0]


class DragData:
    """ Helper object to contain drag-related data for duration of dragging """

    def __init__(self, node: 'Node', is_host, mousedown_scene_pos):
        self.is_host = is_host
        self.position_before_dragging = node.current_position
        self.adjustment_before_dragging = node.adjustment
        mx, my = mousedown_scene_pos
        scx, scy = node.current_scene_position
        self.distance_from_pointer = scx - mx, scy - my
        self.dragged_distance = None
        if hasattr(node, 'contextual_background'):
            self.background = node.contextual_background()
        else:
            bg = ctrl.cm.paper2().lighter(102)
            bg.setAlphaF(.65)
            self.background = bg
        parent = node.parentItem()
        if parent:
            self.parent = parent
        else:
            self.parent = None


qbytes_scale = QtCore.QByteArray()
qbytes_scale.append("scale")


# ctrl = Controller object, gives accessa to other modules


class Node(Movable):
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
    editable = {}
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

    default_edge = g.ABSTRACT_EDGE
    touch_areas_when_dragging = []
    touch_areas_when_selected = []
    buttons_when_selected = [Buttons.NodeEditorButton, Buttons.RemoveNodeButton,
                             Buttons.NodeUnlockButton]

    def __init__(self):
        """ Node is an abstract class that shouldn't be used by itself, though
        it should contain all methods to make it work. Inherit and modify
        this for
        Constituents, Features etc. """
        self.label_object = None
        Movable.__init__(self)
        self.syntactic_object = None
        self.label = ''
        self.node_type_settings_chain = None
        self.selected = False
        self._label_visible = True
        self._label_qdocument = None
        self.label_rect = None
        self._gravity = 0
        self.label_object = Label(parent=self)
        self.resizable = False
        self.drag_data = None
        self.user_size = None
        self.inverse_colors = False
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
        self.cached_edge_ordering = {}
        self.color_key = None

        self._editing_template = {}

        self.label_display_data = {}
        self.setFiltersChildEvents(False)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
        self.setFlag(QtWidgets.QGraphicsObject.ItemSendsGeometryChanges)
        # self.setFlag(QtWidgets.QGraphicsObject.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        # self.fade_in()
        self.update_visibility()

    def set_syntactic_object(self, synobj):
        old = self.syntactic_object
        self.syntactic_object = synobj
        if ctrl.forest:
            if synobj:
                ctrl.forest.nodes_from_synobs[synobj.uid] = self
            elif old and not synobj:
                del ctrl.forest.nodes_from_synobs[old.uid]
        self.update_label()

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
        self.node_type_settings_chain = ctrl.settings.node_type_chains[self.node_type].new_child()
        self.update_label()
        self.update_visibility()
        self.announce_creation()
        if prefs.glow_effect:
            self.toggle_halo(True)
        ctrl.forest.store(self)

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
            ctrl.forest.store(self)
            ctrl.forest.add_to_scene(self)
            return
        elif transition_type == g.DELETED:
            print('*** deleting node in after_model_update')
            ctrl.free_drawing.delete_node(self, touch_edges=False, fade=False)
            return

        if 'triangle_stack' in updated_fields:
            print('updating triangle_stack')
            if self.is_triangle_host():
                print('rebuilding triangle headed by ', self)
                ctrl.free_drawing.add_or_update_triangle_for(self)
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
    def offset_x(self):
        if self.label_object:
            return self.label_object.x_offset
        else:
            return self.width / -2

    @property
    def offset_y(self):
        if self.label_object:
            return self.label_object.y_offset
        else:
            return self.height / -2

    @property
    def centered_scene_position(self):
        sx, sy = self.current_scene_position
        ox = self.offset_x
        oy = self.offset_y
        cx = sx + ox + self.width / 2
        cy = sy + oy + self.height / 2
        return cx, cy


    def compose_html_for_viewing(self, peek_into_synobj=True):
        """ This method builds the html to display in label. For convenience, syntactic objects
        can override this (going against the containment logic) by having their own
        'compose_html_for_viewing' -method. This is so that it is easier to create custom
        implementations for constituents without requiring custom constituentnodes.

        Note that synobj's compose_html_for_viewing receives the node object as parameter,
        so you can replicate the behavior below and add your own to it.

        :param peek_into_synobj: allow syntactic object to override this method. If synobj in turn
        needs the result from this implementation (e.g. to append something to it), you have to
        turn this off to avoid infinite loop. See example plugins.
        :return:
        """

        # Allow custom syntactic objects to override this
        if peek_into_synobj and hasattr(self.syntactic_object, 'compose_html_for_viewing'):
            return self.syntactic_object.compose_html_for_viewing(self)

        return as_html(self.label), ''

    def compose_html_for_editing(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label or synobj's label. This can be overridden in syntactic object by having
        'compose_html_for_editing' -method there. The method returns a tuple,
          (field_name, setter, html).
        :return:
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'compose_html_for_editing'):
            return self.syntactic_object.compose_html_for_editing(self)

        return 'label', as_html(self.label)

    def parse_edited_label(self, label_name, value):
        success = False
        if self.syntactic_object and hasattr(self.syntactic_object, 'parse_edited_label'):
            success = self.syntactic_object.parse_edited_label(label_name, value)
        if not success:
            if label_name == 'node label':
                self.label = value
                return True
            elif label_name == 'syntactic label':
                self.syntactic_object.label = value
                return True
        return False

    def is_empty(self):
        if self.label_object:
            return self.label_object.is_empty()
        return True

    def cut(self, others):
        """
        :param others: other items targeted for cutting, to help decide which relations to maintain
        :return:
        """
        for parent in self.get_parents(similar=False, visible=False):
            if parent not in others:
                ctrl.free_drawing.disconnect_node(parent, self)
        for child in self.get_children(similar=False, visible=False):
            if child not in others:
                ctrl.free_drawing.disconnect_node(self, child)
        ctrl.forest.remove_from_scene(self)
        return self

    # def copy(self, **kwargs):
    #     if self.syntactic_object:
    #         synobj = self.syntactic_object.copy()
    #     else:
    #         synobj = None

    def get_editing_template(self):
        """ Create or fetch a dictionary template to help building an editing
        UI for Node.
        The template is based on 'editable'-class variable and combines
        templates from Node
        and its subclasses and its syntactic object's templates.
        :return: dict
        """
        return self.label_object.editable

    def is_triangle_host(self):
        return bool(self.triangle_stack and self.triangle_stack[-1] is self)

    def can_have_triangle(self):
        return not self.triangle_stack

    def if_changed_font(self, value):
        if self.label_object:
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

    # def fade_out(self, s=300):
    #     for edge in itertools.chain(self.edges_down, self.edges_up):
    #         edge.fade_out(s=s)
    #     super().fade_out(s=s)
    #
    # def fade_in(self, s=300):
    #     for edge in self.edges_up:
    #         if (edge.start and edge.start.is_visible()) or not edge.start:
    #             edge.fade_in(s=s)
    #     for edge in self.edges_down:
    #         if edge.end and edge.end.is_visible():
    #             edge.fade_in(s=s)
    #
    #     super().fade_in(s=s)

    def copy_position(self, other):
        """ Helper method for newly created items. Takes other item and copies movement related
        attributes from it (physics settings, locks, adjustment etc).
        :param other:
        :return:
        """
        parent = self.parentItem()
        if parent is other.parentItem():
            self.current_position = other.current_position[0], other.current_position[1]
            self.target_position = other.target_position
        else:
            csp = other.current_scene_position
            nsp = QtCore.QPointF(csp[0], csp[1])
            if parent:
                nsp = parent.mapFromScene(nsp)
            else:
                nsp = self.mapFromScene(nsp)
            self.current_position = nsp.x(), nsp.y()
            self.target_position = nsp.x(), nsp.y()
        if self.current_scene_position != other.current_scene_position:
            print('copy position led to different positions: ', self.current_scene_position,
                  other.current_scene_position)
        self.locked = other.locked
        self.use_adjustment = other.use_adjustment
        self.adjustment = other.adjustment
        self.physics_x = other.physics_x
        self.physics_y = other.physics_y

    # ### Children and parents
    # ####################################################

    def get_children(self, visible=False, similar=False, reverse=False, of_type=None) -> list:
        """
        Get child nodes of this node
        :return: iterator of Nodes
        """
        if reverse:
            edges_down = reversed(self.edges_down)  # edges_down has to be list where order makes
            # some syntactic sense.
        else:
            edges_down = self.edges_down
        if visible:
            if similar:
                et = self.edge_type()
                return [edge.end for edge in edges_down if
                        edge.edge_type == et and edge.end and edge.end.is_visible()]
            elif of_type:
                return [edge.end for edge in edges_down if
                        edge.edge_type == of_type and edge.end and edge.end.is_visible()]
            else:
                return [edge.end for edge in edges_down if edge.end and edge.end.is_visible()]
        else:
            if similar:
                et = self.edge_type()
                return [edge.end for edge in edges_down if edge.edge_type == et and edge.end]
            elif of_type:
                return [edge.end for edge in edges_down if edge.edge_type == of_type and edge.end]
            else:
                return [edge.end for edge in edges_down if edge.end]

    def get_parents(self, similar=True, visible=False, of_type=None) -> list:
        """
        Get parent nodes of this node.
        :param similar: boolean, only return nodes of same type (eg.
        ConstituentNodes)
        :param visible: boolean, only return visible nodes
        :param of_type: int, only return Edges of certain subclass.
        :return: list of Nodes
        """
        if not self.edges_up:
            return []
        if similar or of_type is not None:
            if of_type is None:
                of_type = self.edge_type()
            if visible:
                return [edge.start for edge in self.edges_up if
                        edge.edge_type == of_type and edge.start and edge.start.is_visible()]
            else:
                return [edge.start for edge in self.edges_up if
                        edge.edge_type == of_type and edge.start]
        else:
            if visible:
                return [edge.start for edge in self.edges_up if
                        edge.start and edge.start.is_visible()]
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

    def is_unary(self):
        for parent in self.get_parents(similar=True, visible=False):
            if len(parent.get_children(visible=False, similar=True)) == 1:
                return True
        return False

    def is_leaf(self, only_similar=True, only_visible=False):
        """

        :param only_similar:
        :param only_visible:
        :return:
        """
        return not self.get_children(visible=only_visible, similar=only_similar)

    def get_only_parent(self, only_similar=True, only_visible=True):
        """ Returns one or zero parents -- useful when not using multidomination
        :param only_similar:
        :param only_visible:
        """
        parents = self.get_parents(similar=only_similar, visible=only_visible)
        if parents:
            return parents[0]
        return None

    def is_top_node(self, only_similar=True, only_visible=False):
        """ Root node is the topmost node of a trees
        :param only_similar:
        :param only_visible:
        """
        return not self.get_parents(similar=only_similar, visible=only_visible)

    def get_edge_to(self, other, edge_type='', alpha=None) -> QtWidgets.QGraphicsItem or None:
        """ Returns edge object, not the related node. There should be only
        one instance of edge
        of certain type between two elements.
        :param other:
        :param edge_type:
        :param alpha: extra identifier stored with edge, to distinguish between otherwise
        similar edges. Usually points to the origin of many-parted edge
        """
        if alpha:
            if edge_type:
                for edge in self.edges_down:
                    if alpha is edge.alpha and edge.end is other and edge_type == edge.edge_type:
                        return edge
                for edge in self.edges_up:
                    if alpha is edge.alpha and edge.start is other and edge_type == edge.edge_type:
                        return edge
            else:
                for edge in self.edges_down:
                    if alpha is edge.alpha and edge.end is other:
                        return edge
                for edge in self.edges_up:
                    if alpha is edge.alpha and edge.start is other:
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
        """ Returns edges up, filtered
        :param similar:
        :param visible:
        """

        def filter_func(rel):
            """
            :param rel:
            :return: bool """
            if similar and rel.edge_type != self.edge_type():
                return False
            if visible and not rel.is_visible():
                return False
            return True

        return filter(filter_func, self.edges_up)

    def get_edges_down(self, similar=True, visible=False):
        """ Returns edges down, filtered
        :param similar:
        :param visible:
        """

        def filter_func(edge):
            """
            :param edge:
            :return: bool """
            if similar and edge.edge_type != self.edge_type():
                return False
            if visible and not edge.is_visible():
                return False
            return True

        return filter(filter_func, self.edges_down)

    def node_alone(self):
        return not (self.edges_down or self.edges_up)

    def gather_children(self):
        """ If there are other Nodes that are childItems for this node, arrange them to their 
        proper positions. Behavior depends a lot on node type, so default implementation does 
        nothing.
        :return: 
        """
        pass

    def get_locked_in_nodes(self):
        return [x for x in self.get_children(visible=True, similar=False) if
                x.locked_to_node is self]

    def can_have_as_child(self, other=None):
        """ Check, usually when dragging objects, if parent -- child relationship is possible in
        current state. This can be affected by the editing mode, properties of child and parent
        and if they already have this relationship.
        :param other:
        :return:
        """

        if other is None:
            if ctrl.dragged_focus:
                other = ctrl.dragged_focus
                other_type = other.node_type
            else:
                other_type = ctrl.dragged_text
        else:
            other_type = other.node_type
        if (not ctrl.free_drawing_mode) and (
                        other_type == g.CONSTITUENT_NODE or other_type == g.FEATURE_NODE):
            return False
        elif other_type in self.allowed_child_types:
            if other:
                return other not in self.get_children(similar=False, visible=False)
            return True
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
                for child in node.get_children(similar=False, visible=False):
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
                parents = node.get_parents(similar=False, visible=False)
                if parents:
                    for parent in parents:
                        go_up(parent)
                else:
                    tops.append(node)

        go_up(self)
        return tops

    # fixme  -- how often you call this, how is the locked relation restored to visible relation?
    def update_relations(self, parents, shape=None, position=None, checking_mode=None):
        pass

    def get_style(self):
        return {
            'font_id': self.get_font_id(),
            'color_key': self.get_color_key()
        }

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
        return ctrl.settings.get_node_setting('font_id', node=self)

    def set_font_id(self, value):
        ctrl.settings.set_node_setting('font_id', value, node=self)

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
        return ctrl.settings.get_node_setting('color_key', node=self)

    def set_color_key(self, value):
        ctrl.settings.set_node_setting('color_key', value, node=self)

    def palette(self):
        """
        :return:
        """
        palette = QtGui.QPalette(ctrl.cm.get_qt_palette())
        palette.setColor(QtGui.QPalette.WindowText, self.color)
        palette.setColor(QtGui.QPalette.Text, self.color)
        return palette

    def contextual_color(self):
        """ Drawing color that is sensitive to node's state
        :return: QColor
        """

        if self.drag_data:
            return ctrl.cm.lighter(ctrl.cm.selection())
        elif ctrl.pressed is self:
            return ctrl.cm.selection()  # ctrl.cm.active(ctrl.cm.selection())
        elif self.hovering:
            # return ctrl.cm.hover()
            return self.color
            # return ctrl.cm.hovering(ctrl.cm.selection())
        elif self.selected:
            return ctrl.cm.selection()
            # return ctrl.cm.selected(ctrl.cm.selection())
        else:
            return self.color

    def get_edge_start_symbol(self):
        return 0

    # ### Labels and identity
    # ###############################################################

    def update_label(self):
        """
        :return:
        """
        if not self.label_object:
            self.label_object = Label(parent=self)
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
        if not self.label_object:
            self.update_label()
        self._label_visible = self.label_object.has_content() or \
            self.label_object.is_quick_editing() or \
            self.label_object.is_card()
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

    def get_lower_part_y(self):
        """ This should return the relative (within node) y-coordinate to bottom part of label.
        If the label is only one row, bottom and top part are the same.
        Lower and top parts can each have multiple lines in them, the idea is that
        triangle goes between them.
        :return:
        """
        if self.label_object:
            return self.label_object.get_lower_part_y()
        else:
            return 0

    def get_top_y(self):
        """ Implement this if the movable has content where differentiating between bottom row and
         top row can potentially make sense.
        :return:
        """
        if self.label_object:
            return self.label_object.get_top_y()
        else:
            return 0

    def get_node_shape(self):
        """ Node shapes are based on settings-stack, but also get_shape_setting in label.
        Return this get_shape_setting value.
        :return:
        """
        if self.label_object:
            return self.label_object.node_shape
        else:
            return g.NORMAL

    # ## Qt overrides
    # ######################################################################
    # @time_me
    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        ls = self.label_object.node_shape
        if ls == g.CARD:
            xr = 4
            yr = 8
        else:
            xr = 5
            yr = 5
        pen = QtGui.QPen(self.contextual_color())
        pen.setWidth(1)
        rect = False
        brush = Qt.NoBrush

        # if not self.edges_up:
        #     painter.setPen(pen)
        #     painter.drawLine(0, 0, 0, 2)
        #     painter.drawRect(self.label_rect)
        #     painter.drawRect(self.inner_rect)
        if ls == g.SCOPEBOX or (ls == g.BOX and not self.is_empty()):
            pen.setWidthF(0.5)
            brush = ctrl.cm.paper2()
            rect = True
        elif self.label_object.is_card():
            brush = ctrl.cm.paper2()
            rect = True
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

        # elif self.has_empty_label() and self.node_alone():
        #    pen.setStyle(QtCore.Qt.DotLine)
        #    rect = True
        painter.setPen(pen)
        if rect:
            painter.setBrush(brush)
            painter.drawRoundedRect(self.inner_rect, xr, yr)
        if ls == g.BRACKETED and not self.is_leaf(only_similar=True, only_visible=True):
            painter.setFont(self.get_font())
            painter.drawText(self.inner_rect.right() - qt_prefs.font_bracket_width - 2, 2, ']')
        # painter.drawRect(-2, -2, 4, 4)
        # if False:  # False and not self.static:
        #     painter.setBrush(ctrl.cm.get('accent4tr'))
        #     #b = QtCore.QRectF(self.future_children_bounding_rect())
        #     # if b.width() < b.height():
        #     #    b.setWidth(b.height())
        #     # elif b.height() < b.width():
        #     #    b.setHeight(b.width())
        #     #painter.drawEllipse(b)
        #
        #     #painter.drawRect(self.future_children_bounding_rect())
        #     painter.drawRect(self.boundingRect())

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

    def update_bounding_rect(self):
        """ Do housekeeping for bounding rect and related measurements
        :return:
        """
        my_class = self.__class__
        obr = self.inner_rect
        if self.user_size is None:
            user_width, user_height = 0, 0
        else:
            user_width, user_height = self.user_size

        lbw = 0
        lbh = 0
        lbx = 0
        lby = 0
        x_offset = 0
        y_offset = 0
        box_width = 0

        if self._label_visible and self.label_object:
            label = self.label_object
            lbr = label.boundingRect()
            lbw = lbr.width()
            lbh = lbr.height()
            lbx = label.x()
            lby = label.y()
            x_offset = label.x_offset
            y_offset = label.y_offset
        self.label_rect = QtCore.QRectF(lbx, lby, lbw, lbh)
        if self.label_object and self.label_object.node_shape == g.BRACKETED \
                or self.label_object.node_shape == g.SCOPEBOX:
            box_width = ctrl.forest.width_map.get(self.uid, 0)
        self.width = max((lbw, my_class.width, user_width, box_width))
        self.height = max((lbh, my_class.height, user_height))
        if x_offset or y_offset:
            x = x_offset
            y = y_offset
        else:
            x = self.width / -2
            y = self.height / -2
        self.inner_rect = QtCore.QRectF(x, y, self.width, self.height)
        w4 = (self.width - 2) / 4.0
        w2 = (self.width - 2) / 2.0
        h2 = (self.height - 2) / 2.0
        y_max = y + self.height - 4
        x_max = x + self.width

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

        expanding_rect = QtCore.QRectF(self.inner_rect)
        for child in self.childItems():
            if isinstance(child, Node):
                #cbr = child.future_children_bounding_rect()
                #cbr_new = child.future_children_bounding_rect(update=True)
                #if cbr != cbr_new:
                #    print(cbr, cbr_new)
                expanding_rect |= child.future_children_bounding_rect().translated(
                    *child.target_position)
        self._cached_child_rect = expanding_rect

        if ctrl.ui.selection_group and self in ctrl.ui.selection_group.selection:
            ctrl.ui.selection_group.update_shape()
        if obr != self.inner_rect:
            self.prepareGeometryChange()
        return self.inner_rect

    def overlap_rect(self):
        if self._label_visible:
            return self.sceneBoundingRect().adjusted(-2, -2, 4, 4)
        else:
            return QtCore.QRectF()

    def set_user_size(self, width, height):
        self.user_size = (width, height)
        if self.label_object:
            self.label_object.resize_label()

    def scene_rect_coordinates(self, current=False):
        if current:
            return self.sceneBoundingRect().getCoords()
        if self._is_moving:
            scx, scy = self.target_position
        else:
            scx, scy = self.current_position
        minx, miny, maxx, maxy = self.future_children_bounding_rect().getCoords()
        minx += scx
        miny += scy
        maxx += scx
        maxy += scy
        return minx, miny, maxx, maxy

    def future_scene_bounding_rect(self):
        r = self.future_children_bounding_rect()
        p = self.parentItem()
        if p:
            return p.mapToScene(r)
        else:
            return self.mapToScene(r)

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
            assert(self.parentItem() == self.locked_to_node)
            self.move_to(*move_to)
            parent.update_bounding_rect()

    def get_edges_down_with_children(self):
        """ Sometimes you need to count in also edges of locked in nodes (they are childItems). 
        :return: 
        """
        edges = self.edges_down[:]
        for item in self.childItems():
            if isinstance(item, Node):
                edges += item.get_edges_down_with_children()
        return edges

    def get_edges_up_with_children(self):
        """ Sometimes you need to count in also edges of locked in nodes (they are childItems). 
        :return: 
        """
        edges = self.edges_up[:]
        for item in self.childItems():
            if isinstance(item, Node):
                edges += item.get_edges_up_with_children()
        return edges

    def reindex_edges(self):
        down = defaultdict(list)
        up = defaultdict(list)
        # for edge in self.edges_down:
        #     down[edge.edge_type].append(edge)
        # for edge in self.edges_up:
        #     up[edge.edge_type].append(edge)
        # for edges in down.values():
        #     down_size = len(down)
        #     for i, edge in enumerate(edges):
        #         edge.cached_edge_start_index = (i, down_size)
        #         if edge.path:
        #             edge.path.cached_shift_for_start = None
        # for edges in up.values():
        #     up_size = len(up)
        #     for i, edge in enumerate(edges):
        #         edge.cached_edge_end_index = (i, up_size)
        #         if edge.path:
        #             edge.path.cached_shift_for_start = None

    # ######## Triangles #########################################
    # Here we have only low level local behavior of triangles. Most of the
    # action is done in Forest
    # as triangles may involve complicated forest-level calculations.

    def is_cosmetic_triangle(self):
        """ Triangle that doesn't have any other nodes folded into it """
        return self in self.triangle_stack and self.is_leaf(only_similar=True, only_visible=False)

    def should_draw_triangle(self):
        """ When in syntactic mode or using automatic labels, don't draw cosmetic triangles        
        :return: 
        """

    def hidden_in_triangle(self):
        """ Check if this node should be included in triangle's visible row of nodes or if it 
        should be hidden. 
        :return: 
        """
        return self.triangle_stack and self.triangle_stack[-1] is not self and not self.is_leaf(
            only_similar=True, only_visible=False)

    def fold_into_me(self, nodes):
        to_do = []
        x = 0
        for node in nodes:
            node.lock_to_node(self)
            br = node.boundingRect()
            to_do.append((node, x, br.left()))
            if not node.hidden_in_triangle():
                x += br.width()
        xt = x / 2
        self.label_object.triangle_width = x
        self.update_label()
        y = self.boundingRect().bottom()
        for node, my_x, my_l in to_do:
            node.move_to(my_x - my_l - xt, y, can_adjust=False, valign=g.TOP)
            node.update_label()
            node.update_visibility()

    # def on_press(self, value):
    #     """ Testing if we can add some push-depth effect.
    #     :param value: pressed or not
    #     :return:
    #     """
    #     print('on_press')
    #     # push-animation is unwanted if we are already editing the text:
    #     if self.label_object and self.label_object.is_quick_editing():
    #         pass
    #     elif value:
    #         self.anim = QtCore.QPropertyAnimation(self, qbytes_scale)
    #         self.anim.setDuration(20)
    #         self.anim.setStartValue(self.scale())
    #         self.anim.setEndValue(0.90)
    #         self.anim.start()
    #     else:
    #         self.anim = QtCore.QPropertyAnimation(self, qbytes_scale)
    #         self.anim.setDuration(20)
    #         self.anim.setStartValue(self.scale())
    #         self.anim.setEndValue(1.0)
    #         self.anim.start()

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
        magnets = ctrl.settings.get('use_magnets')
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
        parents = self.get_parents(similar=True, visible=True)
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
        magnets = ctrl.settings.get('use_magnets')
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
                if ctrl.settings.get('single_click_editing'):
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
            action.run_command(self.uid, has_params=True)
        elif self.selected:
            if len(ctrl.selected) > 1:
                action = ctrl.ui.get_action('select')
                action.run_command(self.uid, has_params=True)
            else:
                if not ctrl.settings.get('single_click_editing'):
                    self.label_object.set_quick_editing(True)
        else:
            action = ctrl.ui.get_action('select')
            action.run_command(self.uid, has_params=True)
        return self

    # Drag flow:

    # 0.
    #

    # 1. drag -- compute drag's current situation, where is mouse cursor, should we start
    # dragging or just announce new position for 'dragged_to'.
    #
    #   2. start_dragging -- drag is initiated from this node. If the node was already selected,
    #   then other nodes that were selected at the same time are also understood to be dragged.
    #   If the node has unambiguous children, these are also dragged. If node is top node of a tree,
    #   then the tree is the object of dragging, and not node.
    #
    #   2b. prepare_children_for_dragging -- compute what should be included in drag for this
    #   type of node.
    #
    #   3. prepare_dragging_participiant -- this is called for each node that is included into drag.
    #   Prepares drag data and sets up animations.
    #
    #   4. dragged_to -- this is called for each node in drag set. Node moves to position
    #   relative to drag given scene position (given position is the position of drag pointer
    #   and main dragged element.
    #
    # 5. drop_to -- with dragged node, activate whatever happens in this position if something is
    # dropped there. Call finish_dragging.
    #
    #   6. finish_dragging -- if called with dragged node, calls finish_dragging also for other
    #   nodes in drag set. Clears temporary data and restores node to normal. Should always be
    #   called, even when dragging is cancelled or interrupted.

    def start_dragging(self, scene_pos):
        """ Figure out which nodes belong to the dragged set of nodes.
        :param scene_pos:
        """
        ctrl.dragged_focus = self
        ctrl.dragged_set = set()
        ctrl.dragged_groups = set()
        multidrag = False
        # if we are working with selection, this is more complicated, as there may be many nodes
        # and trees dragged at once, with one focus for dragging.
        if self.selected:
            selected_nodes = [x for x in ctrl.selected if isinstance(x, Node)]
            # include those nodes in selection and their children that are not part of wholly
            # dragged trees
            for item in selected_nodes:
                if item.drag_data:
                    continue
                elif getattr(item, 'draggable', True):
                    item.prepare_dragging_participiant(host=False, scene_pos=scene_pos)
                    item.prepare_children_for_dragging(scene_pos)
                    multidrag = True
        # no selection -- drag what is under the pointer
        else:
            self.prepare_children_for_dragging(scene_pos)
            self.prepare_dragging_participiant(host=True, scene_pos=scene_pos)

        moving = ctrl.dragged_set
        ctrl.ui.prepare_touch_areas_for_dragging(moving=moving, multidrag=multidrag)
        ctrl.ui.create_drag_info(self)
        self.start_moving()

    def prepare_children_for_dragging(self, scene_pos):
        """ Implement this if structure is supposed to drag with the node
        :return:
        """
        pass

    def prepare_dragging_participiant(self, host=False, scene_pos=None):
        """ Add this node into the entourage of dragged node. These nodes will
        maintain their relative position to dragged node while dragging.
        This can and should be called also for the host of the dragging operation. In this case
        host=True.
        :return: None
        :param host: is this the main dragged node or one of its children
        :param scene_pos: mouse position when dragging started -- dragging participiant will keep
        its distance from pointer fixed during dragging
        """
        ctrl.dragged_set.add(self)
        ctrl.add_my_group_to_dragged_groups(self)
        self.drag_data = True
        self.drag_data = DragData(self, is_host=host, mousedown_scene_pos=scene_pos)

        parent = self.parentItem()
        if parent:
            parent.setZValue(500)
            # self.anim = QtCore.QPropertyAnimation(self, qbytes_scale)
            # self.anim.setEasingCurve(QtCore.QEasingCurve.Linear)
            # self.anim.setDuration(600)
            # self.anim.setStartValue(self.scale())
            # self.anim.setEndValue(1.5)
            # self.anim.start()

    def drag(self, event):
        """ Drag also elements that are counted to be involved: features,
        children etc. Drag is called to only one principal drag host element. 'dragged_to' is
        called for each element.
        :param event:
        """
        crossed_out_flag = event.modifiers() == QtCore.Qt.ShiftModifier
        for edge in self.edges_up:
            edge.crossed_out_flag = crossed_out_flag
        scene_pos = to_tuple(event.scenePos())
        nx, ny = scene_pos

        # Call dragged_to -method for all nodes that are dragged with the drag focus
        # Their positions are relative to this focus, compute how much.
        for node in ctrl.dragged_set:
            d = node.drag_data
            dx, dy = d.distance_from_pointer
            node.dragged_to((int(nx + dx), int(ny + dy)))
        ctrl.ui.show_drag_adjustment()
        for group in ctrl.dragged_groups:
            group.update_shape()

    def dragged_to(self, scene_pos):
        """ Dragged focus is in scene_pos. Move there or to position relative to that
        :param scene_pos: current pos of drag pointer (tuple x,y)
        :return:
        """
        super().dragged_to(scene_pos)
        edge_list = [self.edges_up, self.edges_down]
        for item in self.childItems():
            if isinstance(item, Node):
                edge_list.append(item.edges_up)
                edge_list.append(item.edges_down)
        for edge in itertools.chain.from_iterable(edge_list):
            edge.make_path()
            edge.update()

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

    def drop_to(self, x, y, recipient=None, shift_down=False):
        """

        :param recipient:
        :param x:
        :param y:
        :param shift_down:
        :return: action finished -message (str)
        """
        self.stop_moving()
        self.update()
        for edge in self.edges_up:
            edge.crossed_out_flag = False
            if shift_down:
                ctrl.free_drawing.disconnect_node(edge=edge)
        if recipient and recipient.accepts_drops(self):
            self.release()
            recipient.drop(self)
        else:
            if self.use_physics():
                drop_action = ctrl.ui.get_action('move_node')
                drop_action.run_command(self.uid, x, y, has_params=True)
            else:
                adj_x, adj_y = self.adjustment
                drop_action = ctrl.ui.get_action('adjust_node')
                drop_action.run_command(self.uid, adj_x, adj_y, has_params=True)
        self.update_position()
        self.finish_dragging()

    def finish_dragging(self):
        """ Flush dragging-related temporary variables. Called always when
        dragging is finished for any
         reason.
        :return:
        """
        if self is ctrl.dragged_focus:
            for node in ctrl.dragged_set:
                if node is not self:
                    node.finish_dragging()
            ctrl.dragged_set = set()
            ctrl.dragged_focus = None
            ctrl.dragged_groups = set()
            ctrl.dragged_text = None
        self.setZValue(self.preferred_z_value())
        self.drag_data = None
        ctrl.ui.remove_drag_info()
        # self.anim = QtCore.QPropertyAnimation(self, qbytes_scale)
        # self.anim.setDuration(100)
        # self.anim.setStartValue(self.scale())
        # self.anim.setEndValue(1.0)
        # self.anim.start()

    def cancel_dragging(self):
        """ Fixme: not called by anyone
        Revert dragged items to their previous positions.
        :return: None
        """
        d = self.drag_data
        if d:
            self.adjustment = d.adjustment_before_dragging
            self.current_position = d.position_before_dragging
            self.update_position()
            if d.is_host:
                for node in ctrl.dragged_set:
                    node.cancel_dragging()
            self.setZValue(self.preferred_z_value())
            self.drag_data = None

    def lock(self):
        """ Display lock, unless already locked. Added functionality to
        recognize the state before
         dragging started.
        :return:
        """
        # was_locked = self.locked or self.use_adjustment
        super().lock()
        # if not was_locked:
        print('locking node to position')
        if self.is_visible():
            ctrl.main.ui_manager.show_anchor(self)  # @UndefinedVariable

    # ### Mouse - Qt events ##################################################

    def mousePressEvent(self, event):
        ctrl.press(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, e):
        # mouseMoveEvents only happen between mousePressEvents and mouseReleaseEvents
        scene_pos_pf = e.scenePos()
        if ctrl.dragged_focus is self:
            self.drag(e)
            ctrl.graph_scene.dragging_over(scene_pos_pf)
        elif (e.buttonDownScenePos(QtCore.Qt.LeftButton) - scene_pos_pf).manhattanLength() > 6:
            scene_pos = to_tuple(scene_pos_pf)
            self.start_dragging(scene_pos)
            self.drag(e)
            ctrl.graph_scene.dragging_over(scene_pos_pf)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, event):
        """ Either we are finishing dragging or clicking the node. If clicking a node with
        editable label, the click has to be replayed to Label (QGraphicsTextItem) when it has
        toggled the edit mode on, to let its inaccessible method for positioning cursor on click
        position to do its work.
        :param event:
        :return:
        """
        replay_click = False
        shift = event.modifiers() == QtCore.Qt.ShiftModifier

        if ctrl.pressed is self:
            ctrl.release(self)
            if ctrl.dragged_set:
                x, y = to_tuple(event.scenePos())
                self.drop_to(int(x), int(y), recipient=ctrl.drag_hovering_on, shift_down=shift)
                ctrl.graph_scene.kill_dragging()
                ctrl.ui.update_selections()  # drag operation may have changed visible affordances
            else:  # This is a regular click on 'pressed' object
                self.select(adding=shift, select_area=False)
                if self.label_object.is_quick_editing():
                    replay_click = True
                self.update()
        super().mouseReleaseEvent(event)
        if replay_click and False:
            ctrl.graph_view.replay_mouse_press()
            self.label_object.editable_part.mouseReleaseEvent(event)
            ctrl.release(self)

    def dragEnterEvent(self, event):
        """ Dragging a foreign object (could be from ui_support) over a node, entering.
        :param event:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist") \
                or event.mimeData().hasFormat("text/plain"):
            self.label_object.dragEnterEvent(event)
            self.hovering = True
        else:
            QtWidgets.QGraphicsObject.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        """ Dragging a foreign object (could be from ui_support) over a node, leaving.
        :param event:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist") \
                or event.mimeData().hasFormat("text/plain"):
            event.acceptProposedAction()
            self.hovering = False
        else:
            QtWidgets.QGraphicsObject.dragLeaveEvent(self, event)

    def dropEvent(self, event: 'QGraphicsSceneDragDropEvent'):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist") \
                or event.mimeData().hasFormat("text/plain"):
            self.label_object.dropEvent(event)

    def start_moving(self):
        """ Hint edges that they shouldn't compute everything while these nodes are moving.
        :return:
        """
        Movable.start_moving(self)
        if prefs.move_effect:
            self.toggle_halo(True)
        for edge in self.edges_down:
            edge.start_node_started_moving()
        for edge in self.edges_up:
            edge.end_node_started_moving()

    def short_str(self):
        return as_html(self.label) or "no label"

    def has_ordered_children(self):
        return True

    def stop_moving(self):
        """ Experimental: remove glow effect from moving things
        :return:
        """
        Movable.stop_moving(self)
        if prefs.move_effect:
            if not self.selected:
                self.toggle_halo(False)
        for edge in self.edges_down:
            edge.start_node_stopped_moving()
        for edge in self.edges_up:
            edge.end_node_stopped_moving()

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

        if (not self.is_syntactic) and ctrl.settings.get('syntactic_mode'):
            self._visible_by_logic = False
        elif ctrl.settings.get_node_setting('visible', node=self) and not self.hidden_in_triangle():
            self._visible_by_logic = True
        else:
            self._visible_by_logic = False

        changed = super().update_visibility(fade_in=fade_in, fade_out=fade_out)
        if changed:
            # ## Edges -- these have to be delayed until all constituents etc nodes know if they are
            # visible
            ctrl.forest.order_edge_visibility_check()
        return changed

    def update_node_shape(self):
        pass

    def is_quick_editing(self):
        if self.label_object:
            return self.label_object.is_quick_editing()
        return False

    # ###### Halo for showing some association with selected node (e.g. c-command) ######

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
        c = color.lighter(100 + (1 - ctrl.cm.background_lightness) * 120)
        c = ctrl.cm.transparent(c, opacity=128)
        self.halo_item.setZValue(2)
        self.halo_item.setPen(c)
        self.halo_item.setBrush(c)

    # noinspection PyTypeChecker
    def check_conditions(self, cond):
        """ Various templates may need to check that all conditions apply before doing things.
        Conditions are methods in this node or in syntactic object of this node.
        this method takes
        1) str with method name
        2) list of method names or
        3) dict where there is a key 'condition' that has (1, 2) as value.
        It returns True if the method/s return True or if the methods are missing.
        (understand this as 'no filters' instead of 'no pass')
        It also accepts 'not:methodname' in string to negate the result.
        :param cond: None, string, list or dict
        :return:
        """
        if not cond:
            return True
        elif isinstance(cond, list):
            for c in cond:
                if not self.check_conditions(c):
                    return False
            return True
        elif isinstance(cond, str):
            not_flag = False
            if cond.startswith('not:'):
                cond = cond[4:]
                not_flag = True
            cmethod = getattr(self, cond)
            if (not cmethod) and self.syntactic_object:
                cmethod = getattr(self.syntactic_object, cond)
            if cmethod:
                if not_flag:
                    return not cmethod()
                else:
                    return cmethod()
            raise NotImplementedError(cond)

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
    user_size = SavedField("user_size")
    triangle_stack = SavedField("triangle_stack")
