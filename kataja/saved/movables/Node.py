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

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

import kataja.globals as g
from kataja.Label import Label
from kataja.SavedField import SavedField
from kataja.saved.Movable import Movable
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.ui_graphicsitems.ControlPoint import ControlPoint
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import to_tuple, create_shadow_effect, add_xy, time_me
from kataja.parser.INodes import as_html

call_counter = [0]

class DragData:
    """ Helper object to contain drag-related data for duration of dragging """

    def __init__(self, node:'Node', is_host, mousedown_scene_pos):
        self.is_host = is_host
        self.position_before_dragging = node.current_position
        self.adjustment_before_dragging = node.adjustment
        self.tree_top = node.tree_where_top()
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
        self.old_zvalue = node.zValue()
        parent = node.parentItem()
        if parent:
            self.parent = parent
            self.parent_old_zvalue = parent.zValue()
        else:
            self.parent = None
            self.parent_old_zvalue = 0


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

    default_style = {'color_id': 'content1', 'font_id': g.MAIN_FONT, 'font-size': 10, 'card': False,
                     'card_width': 0, 'card_height': 0}

    default_edge = g.ABSTRACT_EDGE
    touch_areas_when_dragging = {}
    touch_areas_when_selected = {}

    buttons_when_selected = {g.NODE_EDITOR_BUTTON: {'action': 'toggle_node_edit_embed'},
                             g.REMOVE_NODE: {'action': 'remove_node',
                                             'condition': 'free_drawing_mode'}}

    def __init__(self):
        """ Node is an abstract class that shouldn't be used by itself, though
        it should contain all methods to make it work. Inherit and modify
        this for
        Constituents, Features etc. """
        Movable.__init__(self)
        self.syntactic_object = None
        self.label = ''

        self._label_visible = True
        self._label_qdocument = None
        self.label_rect = None
        self._gravity = 0
        self.label_object = Label(parent=self)
        self.resizable = False
        self.drag_data = None
        self.user_size = None
        self.text_parse_mode = 1
        self._magnets = []
        self.status_tip = ""
        self.is_syntactically_valid = False
        self.width = 0
        self.height = 0
        self.is_trace = False
        self.inner_rect = None
        self.anim = None
        self.magnet_mapper = None
        self.z_value = 10
        # Visibility flags
        self._node_type_visible = True
        self._node_in_triangle = False

        self.in_scene = False

        self.edges_up = []
        self.edges_down = []
        self.triangle = None
        self.folded_away = False
        self.folding_towards = None
        self.color_id = None

        self._editing_template = {}

        self.label_display_data = {}
        self.setFiltersChildEvents(False)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.setFlag(QtWidgets.QGraphicsObject.ItemSendsGeometryChanges)
        #self.setFlag(QtWidgets.QGraphicsObject.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setZValue(self.z_value)
        self.effect = create_shadow_effect(ctrl.cm.selection())
        # self.effect = create_shadow_effect(self.color)
        self.setGraphicsEffect(self.effect)
        #self.fade_in()
        self.update_visibility()

    def set_syntactic_object(self, synobj):
        old = self.syntactic_object
        self.syntactic_object = synobj
        if ctrl.forest and synobj:
            ctrl.forest.nodes_from_synobs[synobj.uid] = self
        if ctrl.forest and old and not synobj:
            del ctrl.forest.nodes_from_synobs[old.uid]

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
        self.update_bounding_rect()
        self.update_visibility()
        self.announce_creation()
        ctrl.forest.store(self)

    def after_model_update(self, updated_fields, update_type):
        """ This is called after the item's model has been updated, to run
        the side-effects of various
        setters in an order that makes sense.
        :param updated_fields: list of names of elements that have been updated.
        :param update_type: g.DELETE or g.CREATE
        :return: None
        """
        super().after_model_update(updated_fields, update_type)

        if update_type == 1:  # CREATE
            ctrl.forest.store(self)
            ctrl.forest.add_to_scene(self)
        if update_type == 2:  # DELETE
            ctrl.forest.remove_from_scene(self, fade_out=False)
            return

        if 'folding_towards' in updated_fields:
            # do the animation and its after triggers.
            if self.folding_towards:
                self.fold_towards(self.folding_towards)
            else:
                self.folded_away = False
                self.update_position()
                #self.fade_in()
        self.update_visibility()
        self.update_label()

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

    @property
    def centered_position(self):
        px, py = self.current_position
        ox = self.offset_x
        oy = self.offset_y
        cx = px + ox + self.width / 2
        cy = py + oy + self.height / 2
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
          (field_name, html).
        :return:
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'compose_html_for_editing'):
            return self.syntactic_object.compose_html_for_editing(self)

        return 'label', as_html(self.label)

    def synobj_to_node(self):
        """ Update node's values from its synobj. Subclasses implement this.
        :return:
        """
        pass

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

    def get_editing_template(self, refresh=False):
        """ Create or fetch a dictionary template to help building an editing
        UI for Node.
        The template is based on 'editable'-class variable and combines
        templates from Node
        and its subclasses and its syntactic object's templates.
        :param refresh: force recalculation of template
        :return: dict
        """
        return self.label_object.editable

    def has_triangle(self):
        return self.triangle

    def can_have_triangle(self):
        return not self.triangle

    def if_changed_font(self, value):
        if self.label_object:
            self.label_object.set_font(qt_prefs.get_font(value))

    # Non-model-based properties ########################################

    @property
    def hovering(self):
        """ Public access to _hovering. Pretty useless.
        :return:
        """
        return self._hovering

    @hovering.setter
    def hovering(self, value):
        """ Toggle hovering effects and internal bookkeeping
        :param value: bool
        :return:
        """
        if value and not self._hovering:
            self._start_hover()
        elif self._hovering and not value:
            self._stop_hover()

    def _start_hover(self):
        """ Start all hovering effects
        :return:
        """
        self._hovering = True
        if ctrl.cm.use_glow():
            self.effect.setColor(self.contextual_color)
            self.effect.setEnabled(True)
        self.prepareGeometryChange()
        self.update()
        if self.zValue() < 150:
            self.setZValue(150)
        self.update_status_tip()
        ctrl.set_status(self.status_tip)

    def _stop_hover(self):
        """ Stop all hovering effects
        :return:
        """
        # if ctrl.cm.use_glow():
        #    self.effect.setEnabled(False)
        self._hovering = False
        self.prepareGeometryChange()
        self.setZValue(self.z_value)
        self.update()
        ctrl.remove_status(self.status_tip)

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

    def move(self, md):
        """ Add on Moveable.move the case when node is folding towards
        triangle. It has priority.

        Things that affect if and how Node moves:
        1. item folding towards position in part of animation to disappear etc.
        2. item is being dragged
        3. item is locked by user
        4. item is tightly attached to another node which is moving (then the move is handled by
        the other node, it is _not_ parent node, though.)
        5. visualisation algorithm setting it specifically
        (6) or (0) -- places where subclasses can add new movements.

        :param md: dict to collect total amount of movement.
        :return: (bool, bool) -- is the node moving, does it allow
        normalization of movement
        """

        if self.folding_towards and not self._move_counter:
            return True, False
        else:
            return super().move(md)

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


    # Tree membership ##########################################################
    #
    # Note that tree membership is bidirectional: trees keep a record of nodes that belong to
    # them and nodes keep record of which trees they belong to. This can easily lead to endless
    # loops, where removal for one calls for removal from another, or same with addition.
    # To prevent this: LET 'TREE' OBJECTS DO THE CALLING OF ADD/REMOVE METHODS IN HERE

    def pick_tallest_tree(self):
        """ A node can belong to many trees, but in some cases only one is needed. Choose taller
        trees. There is no good reason for why to choose that, but it is necessary to at least
        to have predictable behaviour for complex cases.
        :return:
        """
        ltrees = list(self.trees)
        if len(ltrees) == 0:
            return None
        elif len(ltrees) == 1:
            return ltrees[0]
        max_len = -1
        bigger = None
        for tree in ltrees:
            l = len(tree.sorted_constituents) + len(tree.sorted_nodes)
            if l > max_len:
                bigger = tree
        return bigger

    def tree_where_top(self):
        """ Returns a trees where this node is the topmost node. Cannot be topping more than one
        trees!  (They would be identical trees otherwise.)
        :return: None if not top, Tree if found
        """
        for tree in self.trees:
            if self is tree.top:
                return tree

    def shares_tree_with_node(self, other):
        """ Checks if this node has one or more same trees with other node
        :param other: node
        :return:
        """
        if other.trees is None or self.trees is None:
            return False
        return bool(self.trees & other.tree)

    def update_graphics_parent(self):
        """ Update GraphicsItem.parentItem for this node. When parent is changed, the coordinate
        system switches to that of parent (or scene, if parent is None). If this happens, compute
         new position according to new parent so that there is no visible jump.
        :return:
        """
        old_parent = self.parentItem()
        if isinstance(old_parent, Node):
            return  # This is locked to some other node and should keep it as parent
        new_parent = self.pick_tallest_tree()
        if new_parent:
            if old_parent is not new_parent:
                scene_position = self.current_scene_position
                self.setParentItem(new_parent)
                self.current_position = self.scene_position_to_tree_position(scene_position)
        elif old_parent:
            self.current_position = self.current_scene_position
            self.setParentItem(None)

    def copy_position(self, other, ax=0, ay=0):
        """ Helper method for newly created items. Takes other item and copies movement related
        attributes from it (physics settings, locks, adjustment etc). ax, ay, az can be used to
        adjust these a little to avoid complete overlap.
        :param other:
        :param ax:
        :param ay:
        :return:
        """
        shift = (ax, ay)
        if self.parentItem() is other.parentItem():
            self.current_position = add_xy(other.current_position, shift)
            self.target_position = other.target_position
        else:
            csp = other.current_scene_position
            ctp = other.tree_position_to_scene_position(other.target_position)
            self.current_position = self.scene_position_to_tree_position(add_xy(csp, shift))
            self.target_position = self.scene_position_to_tree_position(ctp)
        self.locked = other.locked
        self.use_adjustment = other.use_adjustment
        self.adjustment = other.adjustment
        self.physics_x = other.physics_x
        self.physics_y = other.physics_y

    def tree_position_to_scene_position(self, position):
        """ Return trees position converted to scene position. Works for xy -tuples.
        :param position:
        :return:
        """
        #if isinstance(position, (QtCore.QPoint, QtCore.QPointF)):
        #    position = position.x(), position.y()
        x, y = position
        tree = self.parentItem()
        if not tree:
            return x, y
        tx, ty = tree.current_position
        return x + tx, y + ty

    def scene_position_to_tree_position(self, scene_pos):
        """ Return scene position converted to coordinate system used by this node trees. Works for
         xy  -tuples.

        :param scene_pos:
        :return:
        """
        x, y = scene_pos
        tree = self.parentItem()
        if not tree:
            return x, y
        tx, ty = tree.current_position
        return x - tx, y - ty


    # ### Children and parents
    # ####################################################

    def get_children(self, visible=False, similar=False, reverse=False, of_type=None) -> list:
        """
        Get child nodes of this node
        :return: iterator of Nodes
        """
        if reverse:
            edges_down = reversed(self.edges_down) # edges_down has to be list where order makes
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
                return [edge.end for edge in edges_down if
                        edge.edge_type == et and edge.end]
            elif of_type:
                return [edge.end for edge in edges_down if
                        edge.edge_type == of_type and edge.end]
            else:
                return [edge.end for edge in edges_down if edge.end]

    def get_parents(self, similar=True, visible=False, of_type=None) ->list:
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

    def get_top_node(self, return_set=False):
        """ Getting the top node is easiest by looking from the stored trees. Don't use this if
        this is about fixing trees!
        :param return_set: Return result as a set which may contain more than 1 roots.  """
        s = set()

        for tree in ctrl.forest:
            if self in tree:
                if return_set:
                    s.add(tree.top)
                else:
                    return tree.top
        if return_set:
            return s
        else:
            return None

    def get_edge_to(self, other, edge_type='') -> QtWidgets.QGraphicsItem:
        """ Returns edge object, not the related node. There should be only
        one instance of edge
        of certain type between two elements.
        :param other:
        :param edge_type:
        """
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
        fpos = ctrl.settings.get('feature_positioning')
        shape = ctrl.settings.get('label_shape')
        children = self.get_children(visible=True, similar=False)
        if not children:
            return
        if shape == g.CARD:
            fpos = 3  # only two column arrangement looks good on cards

        if fpos == 1:  # vertical
            center_x = self.boundingRect().center().x()
            bottom_y = self.boundingRect().bottom()
            y = bottom_y
            for fnode in children:
                if fnode.locked_to_node is self:
                    fnode.move_to(center_x, y)
                    y += fnode.height
        elif fpos == 2:  # horizontal
            center_x = self.boundingRect().center().x()
            bottom_y = self.boundingRect().bottom()
            nods = []
            total_width = 0
            max_height = 0
            for fnode in children:
                if fnode.locked_to_node is self:
                    w = fnode.width / 2
                    total_width += w - 2
                    nods.append((fnode, total_width))
                    total_width += w - 2
                    if fnode.height > max_height:
                        max_height = fnode.height
            if nods:
                left_margin = (total_width / -2) #+ center_x
                #left_margin += nods[0][0].width / 2
                y = bottom_y + (max_height / 2)
                for fnode, x in nods:
                    fnode.move_to(left_margin + x, y)
        elif fpos == 3:  # card layout, two columns
            in_card = ctrl.settings.get('label_shape') == g.CARD
            cw, ch = self.label_object.card_size
            center_x = self.boundingRect().center().x()
            top_y = 22
            left_margin = center_x - (cw / 2)
            right_margin = center_x + (cw / 2)
            left_nods = []
            right_nods = []
            for fnode in children:
                if fnode.locked_to_node is self:
                    if fnode.value in ['-', '=', '✓-', '✓=']:
                        right_nods.append(fnode)
                    else:
                        left_nods.append(fnode)
            y = top_y
            if in_card:
                hspace = ch - top_y
                if left_nods:
                    node_hspace = hspace / len(left_nods)
                    half_h = node_hspace / 2
                    for fnode in left_nods:
                        fnode.move_to(left_margin + fnode.width / 2, y + half_h)
                        y += node_hspace
                if right_nods:
                    y = top_y
                    node_hspace = hspace / len(right_nods)
                    half_h = node_hspace / 2
                    for fnode in right_nods:
                        fnode.move_to(right_margin - fnode.width / 2, y + half_h)
                        y += node_hspace
            else:
                for fnode in left_nods:
                    fnode.move_to(left_margin + fnode.width / 2, y)
                    y += fnode.height - 4
                y = top_y
                for fnode in right_nods:
                    fnode.move_to(right_margin - fnode.width / 2, y)
                    y += fnode.height - 4

    def get_locked_in_nodes(self):
        return [x for x in self.get_children(visible=True, similar=False) if x.locked_to_node is
                self]

    def can_connect_with(self, other):
        """ Override this in subclasses, checks conditions when other nodes could connect to this
        node. (This node is child). Generally connection should be refuted if it already exists
        :param other:
        :return:
        """
        return other not in self.get_parents(similar=False, visible=False)

    # fixme  -- how often you call this, how is the locked relation restored to visible relation?
    def update_relations(self, parents, shape=None, position=None):
        if self.locked_to_node:
            edge = self.get_edge_to(self.locked_to_node)
            if edge:
                edge.hide()

    def reset_style(self):
        ctrl.settings.reset_node_style(node=self)
        self.update_label()

    def has_local_style_settings(self):
        return bool(self.font_id or self.color_id)

    def get_style(self):
        return {'font_id': self.get_font_id(), 'color_id': self.get_color_id()}

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
        return ctrl.cm.get(self.get_color_id())

    def get_color_id(self):
        """
        :return:
        """
        return ctrl.settings.get_node_setting('color_id', node=self)

    def set_color_id(self, value):
        ctrl.settings.set_node_setting('color_id', value, node=self)

    def palette(self):
        """
        :return:
        """
        palette = QtGui.QPalette(ctrl.cm.get_qt_palette())
        palette.setColor(QtGui.QPalette.WindowText, self.color)
        palette.setColor(QtGui.QPalette.Text, self.color)
        return palette

    @property
    def contextual_color(self):
        """ Drawing color that is sensitive to node's state
        :return: QColor
        """

        if self.drag_data:
            return ctrl.cm.lighter(ctrl.cm.selection())
        elif ctrl.pressed is self:
            return ctrl.cm.selection() # ctrl.cm.active(ctrl.cm.selection())
        elif self._hovering:
            # return ctrl.cm.hover()
            return self.color
            # return ctrl.cm.hovering(ctrl.cm.selection())
        elif ctrl.is_selected(self):
            return ctrl.cm.selection()
            # return ctrl.cm.selected(ctrl.cm.selection())
        else:
            return self.color

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
        self.update_status_tip()

    def update_label_visibility(self):
        """ Check if the label of the node has any content -- should it be
        displayed. Node itself can be visible even when its label is not.
        :return:
        """
        if not self.label_object:
            self.update_label()
        self._label_visible = self.label_object.has_content() or \
                              self.label_object.is_quick_editing()
        self.label_object.setVisible(self._label_visible)

    def label_as_html(self) -> str:
        """ Label as string """
        return as_html(self.label)

    def update_status_tip(self):
        """ implement properly in subclasses, let tooltip tell about the node
        :return: None
        """
        self.status_tip = str(self)

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

    # ## Qt overrides
    # ######################################################################

    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        ls = self.label_object.label_shape
        if ls == g.CARD:
            xr = 4
            yr = 8
        else:
            xr = 5
            yr = 5
        pen = QtGui.QPen(self.contextual_color)
        pen.setWidth(1)
        rect = False
        brush = Qt.NoBrush

        if False:
            painter.setPen(pen)
            painter.drawLine(0, 0, 0, 2)
            painter.drawRect(self.label_rect)
            painter.drawRect(self.inner_rect)
        if ls == g.SCOPEBOX or ls == g.BOX:
            pen.setWidth(0.5)
            brush = ctrl.cm.paper2()
            rect = True
        elif ls == g.CARD and self.is_leaf(only_visible=True, only_similar=True):
            brush = ctrl.cm.paper2()
            rect = True
            # make a deck of cards based on how many cards are folded into triangle
            if self.triangle and self.triangle is not self:
                leaves = [x for x in ctrl.forest.list_nodes_once(self) if
                          x.is_leaf(only_similar=True, only_visible=False)]
                painter.setBrush(brush)
                for yd in range((len(leaves) - 1) * 2, 0, -2):
                    painter.drawRoundedRect(self.inner_rect.translated(yd, yd), xr, yr)

        if self.drag_data:
            rect = True
            brush = self.drag_data.background
        elif self._hovering:
            if rect:
                brush = ctrl.cm.paper()
            rect = True
        elif ctrl.pressed is self or ctrl.is_selected(self):
            if rect:
                brush = ctrl.cm.paper()
            rect = True
        #elif self.has_empty_label() and self.node_alone():
        #    pen.setStyle(QtCore.Qt.DotLine)
        #    rect = True
        painter.setPen(pen)
        if rect:
            painter.setBrush(brush)
            painter.drawRoundedRect(self.inner_rect, xr, yr)
        if ls == g.BRACKETED and not self.is_leaf(only_similar=True, only_visible=True):
            painter.setFont(self.get_font())
            painter.drawText(self.inner_rect.right() - qt_prefs.font_bracket_width - 2, 2, ']')
        #painter.drawRect(-2, -2, 4, 4)

    def has_visible_label(self):
        """
        :return: bool
        """
        return self._label_visible

    def update_bounding_rect(self):
        """ Do housekeeping for bounding rect and related measurements
        :return:
        """
        my_class = self.__class__
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
            l = self.label_object
            lbr = l.boundingRect()
            lbw = lbr.width()
            lbh = lbr.height()
            lbx = l.x()
            lby = l.y()
            x_offset = l.x_offset
            y_offset = l.y_offset
        self.label_rect = QtCore.QRectF(lbx, lby, lbw, lbh)
        if self.label_object and self.label_object.label_shape == g.BRACKETED or \
                        self.label_object.label_shape == g.SCOPEBOX:
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
        y_max = y + self.height
        x_max = x + self.width
        self._magnets = [(x, y), (x + w4, y), (x + w2, y), (x + w2 + w4, y), (x_max, -y),
                         (x, y + h2), (x_max, y + h2),
                         (x, y_max), (x + w4, y_max), (x + w2, y_max),
                         (x + w2 + w4, y_max), (x_max, y_max)]
        if ctrl.ui.selection_group and self in ctrl.ui.selection_group.selection:
            ctrl.ui.selection_group.update_shape()
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

    def future_children_bounding_rect(self, limit_height=False):
        """ This combines boundingRect with children's boundingRects based on children's
        target_positions instead of current ones.
        You'll want to use this to estimate the actual size of node + childItems when reserving
        room for node in visualisation.
        :param limit_height: return boundingRect that only expands its width to include children,
        height is the called node's boundingRect.
        :return:
        """
        my_br = self.boundingRect()
        for child in self.childItems():
            if isinstance(child, Node):
                c_br = QtCore.QRectF(child.boundingRect())
                x, y = child.target_position
                c_br.moveCenter(QtCore.QPoint(x, y))
                my_br = my_br.united(c_br)
        if limit_height:
            my_br.setHeight(self.boundingRect().height())
        return my_br

    def boundingRect(self):
        """ BoundingRects are used often and cost of this method affects
        performance.
        inner_rect is used as a cached bounding rect and returned fast if
        there is no explicit
        update asked. """
        if not self.inner_rect:
            return self.update_bounding_rect()
        else:
            return self.inner_rect

    # ######## Triangles #########################################
    # Here we have only low level local behavior of triangles. Most of the
    # action is done in Forest
    # as triangles may involve complicated forest-level calculations.

    def fold_towards(self, node):
        """ lower level launch for actual fold movement
        :param node:
        :return:
        """
        self.folding_towards = node
        x, y = node.current_position
        self.move_to(x, y, after_move_function=self.finish_folding, can_adjust=False)
        if ctrl.is_selected(self):
            ctrl.remove_from_selection(self)
        ctrl.forest.animation_started(str(self.uid) + '_fold')

    def finish_folding(self):
        """ Hide, and remember why this is hidden """
        self.folded_away = True
        self.update_visibility()
        self.update_bounding_rect()
        # update edge visibility from triangle to its immediate children
        if self.folding_towards in self.get_parents(similar=False, visible=False):
            self.folding_towards.update_visibility()
        ctrl.forest.animation_finished(str(self.uid) + '_fold')

    def on_press(self, value):
        """ Testing if we can add some push-depth effect.
        :param value: pressed or not
        :return:
        """
        # push-animation is unwanted if we are already editing the text:
        if self.label_object and self.label_object.is_quick_editing():
            pass
        elif value:
            self.anim = QtCore.QPropertyAnimation(self, qbytes_scale)
            self.anim.setDuration(20)
            self.anim.setStartValue(self.scale())
            self.anim.setEndValue(0.95)
            self.anim.start()
        else:
            self.anim = QtCore.QPropertyAnimation(self, qbytes_scale)
            self.anim.setDuration(20)
            self.anim.setStartValue(self.scale())
            self.anim.setEndValue(1.0)
            self.anim.start()

    # ## Magnets
    # ######################################################################

    def top_center_magnet(self):
        return self.magnet(2)

    def bottom_left_magnet(self):
        return self.magnet(8)

    def bottom_center_magnet(self):
        return self.magnet(9)

    def bottom_right_magnet(self):
        return self.magnet(10)

    def bottom_magnet(self, i, size):
        """ Bottom magnets that divide the bottom area to (size) points, so that each edge has a
        separate starting point. For binary branching, use the default three points.
        :param i: index in list of sibling
        :param size: size of list of siblings
        :return:
        """
        magnets = ctrl.settings.get('use_magnets')
        if not magnets:
            return self.current_scene_position
        elif not self.has_visible_label():
            return self.current_scene_position
        elif not self._magnets:
            self.update_bounding_rect()
        if size == 2: # and False:
            if i == 0:
                return self.magnet(8)
            elif i == 1:
                return self.magnet(10)
        elif size == 3: # and False:
            if i == 0:
                return self.magnet(8)
            elif i == 1:
                return self.magnet(9)
            elif i == 2:
                return self.magnet(10)
        x1, y1 = self.current_scene_position
        x2, y2 = self._magnets[7]
        x2 += (self.width / (size + 1)) * (i + 1)
        if magnets == 2:
            x2, y2 = self._angle_to_parent(x2, y2)
        return x1 + x2, y1 + y2

    def _angle_to_parent(self, x2, y2):
        x1, y1 = self.current_scene_position
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
        return x2, y2

    def magnet(self, n):
        """
        :param n: index of magnets. There are five magnets in top and bottom
        and three for sides:

        0   1   2   3   4
        5               6
        7   8   9   10  11

        :return:
        """
        magnets = ctrl.settings.get('use_magnets')
        if not magnets:
            return self.current_scene_position
        elif not self.has_visible_label():
            return self.current_scene_position
        elif not self._magnets:
            self.update_bounding_rect()
        if self.magnet_mapper:
            n = self.magnet_mapper(n)

        x1, y1 = self.current_scene_position
        x2, y2 = self._magnets[n]
        if magnets == 2:
            x2, y2 = self._angle_to_parent(x2, y2)
        return x1 + x2, y1 + y2

    # ### Menus #########################################

    def update_selection_status(self, selected):
        """ This is called after item is selected or deselected to update
        appearance and related local elements.
        :param selected:
        """
        if not selected:
            self.setZValue(self.z_value)
            if ctrl.main.use_tooltips:
                self.setToolTip("")
            self.label_object.set_quick_editing(False)
        else:
            self.setZValue(200)
            if ctrl.main.use_tooltips:
                self.setToolTip("Edit with keyboard, click the cog to inspect the node")
            if ctrl.single_selection() and not ctrl.multiselection_delay:
                if ctrl.settings.get('single_click_editing'):
                    self.label_object.set_quick_editing(True)
        self.update()

    # ### MOUSE - kataja
    # ########################################################

    def open_embed(self):
        """ Tell ui_support to open an embedded edit, generated from
        edit template or overridden.
        :return: None
        """
        ctrl.ui.start_editing_node(self)

    def double_click(self, event=None):
        """ Scene has decided that this node has been clicked
        :param event:
        """
        # double-click is reserved for selecting words when quick-editing.
        if self.label_object and self.label_object.is_quick_editing():
            pass
        else:
            self.hovering = False
            ctrl.select(self)
            self.open_embed()

    def select(self, event=None, multi=False):
        """ Scene has decided that this node has been clicked
        :param event:
        :param multi: assume multiple selection (append, don't replace)
        """
        self.hovering = False
        if (event and event.modifiers() == Qt.ShiftModifier) or multi:
            # multiple selection
            ctrl.area_selection = True
            if ctrl.is_selected(self):
                ctrl.remove_from_selection(self)
            else:
                ctrl.add_to_selection(self)
        elif ctrl.is_selected(self):
            if len(ctrl.selected) > 1:
                ctrl.select(self)
            else:
                if not ctrl.settings.get('single_click_editing'):
                    self.label_object.set_quick_editing(True)
        else:
            ctrl.select(self)

    # Drag flow:

    # 1. start_dragging -- drag is initiated from this node. If the node was already selected,
    # then other nodes that were selected at the same time are also understood to be dragged.
    # If the node has unambiguous children, these are also dragged. If node is top node of a trees,
    # then the trees is the object of dragging, and not node.
    #
    # 2. start_dragging_tracking --
    #

    def start_dragging(self, scene_pos):
        """ Figure out which nodes belong to the dragged set of nodes.
        It may be that a whole trees is dragged. If this is the case, drag_to commands that
        target top nodes are directed to trees instead. Node doesn't change its position in trees
         if the whole trees moves.

        :param scene_pos:
        """
        def in_any_tree(item, treeset):
            for tree in treeset:
                if item in tree:
                    return True
        ctrl.dragged_focus = self
        ctrl.dragged_set = set()
        ctrl.dragged_groups = set()
        multidrag = False
        dragged_trees = set()
        # if we are working with selection, this is more complicated, as there may be many nodes
        # and trees dragged at once, with one focus for dragging.
        if ctrl.is_selected(self):
            selected_nodes = [x for x in ctrl.selected if isinstance(x, Node)]
            # find trees tops in selection
            for item in selected_nodes:
                if hasattr(item, 'tree_where_top'):
                    tree = item.tree_where_top()
                    if tree:
                        dragged_trees.add(tree)
            # include those nodes in selection and their children that are not part of wholly
            # dragged trees
            for item in selected_nodes:
                if item.drag_data:
                    continue
                if in_any_tree(item, dragged_trees):
                    continue
                elif getattr(item, 'draggable', True):
                    item.start_dragging_tracking(host=False, scene_pos=scene_pos)
                    item.prepare_children_for_dragging(scene_pos)
                    multidrag = True
        # no selection -- drag what is under the pointer
        else:
            tree = self.tree_where_top()
            if tree:
                dragged_trees.add(tree)
            else:
                self.prepare_children_for_dragging(scene_pos)
            self.start_dragging_tracking(host=True, scene_pos=scene_pos)

        moving = ctrl.dragged_set
        for tree in dragged_trees:
            moving = moving.union(tree.sorted_nodes)
        ctrl.ui.prepare_touch_areas_for_dragging(moving=moving, multidrag=multidrag)
        self.start_moving()

    def start_dragging_tracking(self, host=False, scene_pos=None):
        """ Add this node into the entourage of dragged node. These nodes will
        maintain their relative position to dragged node while dragging.
        :return: None
        """
        ctrl.dragged_set.add(self)
        ctrl.add_my_group_to_dragged_groups(self)
        self.drag_data = True
        self.drag_data = DragData(self, is_host=host, mousedown_scene_pos=scene_pos)

        tree = self.tree_where_top()
        if tree:
            tree.start_dragging_tracking(host=host, scene_pos=scene_pos)
        parent = self.parentItem()
        if parent:
            parent.setZValue(500)
        self.anim = QtCore.QPropertyAnimation(self, qbytes_scale)
        self.anim.setDuration(100)
        self.anim.setStartValue(self.scale())
        self.anim.setEndValue(1.1)
        self.anim.start()

    def prepare_children_for_dragging(self, scene_pos):
        """ Implement this if structure is supposed to drag with the node
        :return:
        """
        pass

    def drag(self, event):
        """ Drags also elements that are counted to be involved: features,
        children etc. Drag is called to only one principal drag host element. 'dragged_to' is
        called for each element.
        :param event:
        """
        crossed_out_flag = event.modifiers() == QtCore.Qt.ShiftModifier
        for edge in self.edges_up:
            edge.crossed_out_flag = crossed_out_flag
        scene_pos = to_tuple(event.scenePos())
        if not ctrl.dragged_focus:
            self.start_dragging(scene_pos)
        # change dragged positions to be based on adjustment instead of distance to main dragged.
        for node in ctrl.dragged_set:
            node.dragged_to(scene_pos)
        for group in ctrl.dragged_groups:
            group.update_shape()

    def dragged_to(self, scene_pos):
        """ Dragged focus is in scene_pos. Move there or to position relative to that
        :param scene_pos: current pos of drag pointer (tuple x,y)
        :return:
        """
        d = self.drag_data
        nx, ny = scene_pos
        if d.tree_top:
            dx, dy = d.tree_top.drag_data.distance_from_pointer
            d.tree_top.dragged_to((nx + dx, ny + dy))
            for edge in ctrl.forest.edges.values():
                edge.make_path()
                edge.update()
        else:
            dx, dy = d.distance_from_pointer
            super().dragged_to((nx + dx, ny + dy))
            for edge in itertools.chain(self.edges_up, self.edges_down):
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
            message = recipient.drop(self)
        else:
            self.lock()
            for node in ctrl.dragged_set:
                node.lock()

            if self.use_physics():
                message = 'moved node to {:.2f}, {:.2f}'.format(self.current_position[0],
                                                                self.current_position[1])
            else:
                message = 'adjusted node to {:.2f}, {:.2f}'.format(self.adjustment[0],
                                                                   self.adjustment[1])

        self.update_position()
        self.finish_dragging()
        return message

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
        if self.drag_data:
            self.setZValue(self.drag_data.old_zvalue)
            if self.drag_data.parent:
                self.drag_data.parent.setZValue(self.drag_data.parent_old_zvalue)
        self.drag_data = None
        self.anim = QtCore.QPropertyAnimation(self, qbytes_scale)
        self.anim.setDuration(100)
        self.anim.setStartValue(self.scale())
        self.anim.setEndValue(1.0)
        self.anim.start()
        self.effect.setEnabled(False)

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
            self.drag_data = None

    def is_dragging_this_type(self, dtype):
        """ Check if the currently dragged item is in principle compatible with self.
        :return:
        """
        if ctrl.dragged_focus:
            return ctrl.dragged_focus.node_type == dtype and \
                   ctrl.dragged_focus.can_connect_with(self)
        elif ctrl.dragged_text:
            return ctrl.dragged_text == dtype
        return False

    def lock(self):
        """ Display lock, unless already locked. Added functionality to
        recognize the state before
         dragging started.
        :return:
        """
        was_locked = self.locked or self.use_adjustment
        super().lock()
        # if not was_locked:
        if self.is_visible():
            ctrl.main.ui_manager.show_anchor(self)  # @UndefinedVariable

    # ### Mouse - Qt events ##################################################

    def mousePressEvent(self, event):
        ctrl.press(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # this only happens when this node is being pressed
        if ctrl.dragged_set or (event.buttonDownScenePos(
                QtCore.Qt.LeftButton) - event.scenePos()).manhattanLength() > 6:
            self.drag(event)
            ctrl.graph_scene.dragging_over(event.scenePos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """ Either we are finishing dragging or clicking the node. If clicking a node with
        editable label, the click has to be replayed to Label (QGraphicsTextItem) when it has
        toggled the edit mode on, to let its inaccessible method for positioning cursor on click
        position to do its work.
        :param event:
        :return:
        """
        replay_click = False
        if ctrl.pressed is self:
            ctrl.release(self)
            if ctrl.dragged_set:
                x, y = to_tuple(event.scenePos())
                message = self.drop_to(x, y, recipient=ctrl.drag_hovering_on, shift_down=
                                       event.modifiers() == QtCore.Qt.ShiftModifier)
                ctrl.graph_scene.kill_dragging()
                ctrl.ui.update_selections()  # drag operation may have changed visible affordances
                ctrl.main.action_finished(message)  # @UndefinedVariable
            else:  # This is a regular click on 'pressed' object
                self.select(event)
                if self.label_object.is_quick_editing():
                    replay_click = True
                self.update()
        super().mouseReleaseEvent(event)
        if replay_click:
            ctrl.graph_view.replay_mouse_press()
            self.label_object.editable_part.mouseReleaseEvent(event)
            ctrl.release(self)

    def hoverEnterEvent(self, event):
        """ Hovering has some visual effects, usually handled in paint-method
        :param event:
        """
        self.hovering = True
        QtWidgets.QGraphicsObject.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """ Object needs to be updated
        :param event:
        """
        self.hovering = False
        QtWidgets.QGraphicsObject.hoverLeaveEvent(self, event)

    def dragEnterEvent(self, event):
        """ Dragging a foreign object (could be from ui_support) over a node, entering.
        :param event:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
            self.hovering = True
        else:
            QtWidgets.QGraphicsObject.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        """ Dragging a foreign object (could be from ui_support) over a node, leaving.
        :param event:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
            self.hovering = False
        else:
            QtWidgets.QGraphicsObject.dragLeaveEvent(self, event)

    def start_moving(self):
        """ Experimental: add glow effect for moving things
        :return:
        """
        Movable.start_moving(self)
        if prefs.move_effect:
            self.effect.setColor(self.contextual_color)
            self.effect.setEnabled(True)
        for edge in self.edges_down:
            edge.start_node_started_moving()
        for edge in self.edges_up:
            edge.end_node_started_moving()

    def short_str(self):
        return as_html(self.label) or "no label"

    def stop_moving(self):
        """ Experimental: remove glow effect from moving things
        :return:
        """
        Movable.stop_moving(self)
        if prefs.move_effect:
            if not (ctrl.is_selected(self) or self._hovering):
                self.effect.setEnabled(False)
        for edge in self.edges_down:
            edge.start_node_stopped_moving()
        for edge in self.edges_up:
            edge.end_node_stopped_moving()

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsObject.ItemPositionHasChanged:
            for tree in self.trees:
                tree.tree_changed = True
            ctrl.ui.update_position_for(self)
        return QtWidgets.QGraphicsObject.itemChange(self, change, value)

    @staticmethod
    def free_drawing_mode(*args, **kwargs):
        """ Utility method for checking conditions for editing operations
        :param args: ignored
        :param kwargs: ignored
        :return:
        """
        return ctrl.free_drawing_mode

    def update_visibility(self, fade_in=True, fade_out=True) -> bool:
        """ see Movable.update_visibility
        This is called logical visibility and can be checked with is_visible().
        Qt's isVisible() checks for scene visibility. Items that are e.g. fading away
        have False for logical visibility but True for scene visibility and items that are part
        of graph in a forest that is not currently drawn may have True for logical visibility but
        false for scene visibility.
        """
        # Label
        self.update_label_visibility()

        if ctrl.settings.get('syntactic_mode'):
            self._node_type_visible = self.is_syntactic
        else:
            self._node_type_visible = True
            self._node_type_visible = True
        self._node_in_triangle = self.folded_away or self.folding_towards

        self._visible_by_logic = self._node_type_visible and not self._node_in_triangle
        changed = super().update_visibility(fade_in=fade_in, fade_out=fade_out)
        if changed:
            # ## Edges -- these have to be delayed until all constituents etc nodes know if they are
            # visible
            ctrl.forest.order_edge_visibility_check()
        return changed

    def update_label_shape(self):
        pass

    def is_quick_editing(self):
        if self.label_object:
            return self.label_object.is_quick_editing()
        return False

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
        elif isinstance(cond, dict):
            return self.check_conditions(cond.get('condition', None))
        elif isinstance(cond, list):
            return all((self.check_conditions(c) for c in cond))
        elif cond.startswith('not:'):
            return not self.check_conditions(cond[4:])
        else:
            cmethod = getattr(self, cond)
            if cmethod:
                return cmethod()
            elif self.syntactic_object:
                cmethod = getattr(self.syntactic_object, cond)
                if cmethod:
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
    triangle = SavedField("triangle")
    folded_away = SavedField("folded_away")
    folding_towards = SavedField("folding_towards")

