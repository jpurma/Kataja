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
from collections import OrderedDict

import itertools

import math
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

import kataja.shapes
from kataja.ui.ControlPoint import ControlPoint
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.Label import Label
from kataja.Movable import Movable
from kataja.BaseModel import Saved
from kataja.utils import to_tuple, create_shadow_effect, multiply_xy, div_xy, sub_xy, add_xy, \
    time_me, add_xy
import kataja.globals as g
from kataja.parser.INodes import ITemplateNode

TRIANGLE_HEIGHT = 10


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
        self.background = ctrl.cm.paper2().lighter(102)
        self.old_zvalue = node.zValue()


qbytes_scale = QtCore.QByteArray()
qbytes_scale.append("scale")

# ctrl = Controller object, gives accessa to other modules


class Node(Movable):
    """ Basic class for any visualization elements that can be connected to
    each other """
    width = 20
    height = 20
    default_edge_type = g.ABSTRACT_EDGE
    node_type = g.ABSTRACT_NODE
    is_constituent = False
    ordered = False
    ordering_func = None
    name = ('Abstract node', 'Abstract nodes')
    short_name = "Node"  # shouldn't be used on its own
    display = False
    can_be_in_groups = True

    # override this if you need to turn inodes into your custom Nodes. See
    # examples in
    # ConstituentNode or FeatureNode

    default_style = {'color': 'content1', 'font': g.MAIN_FONT, 'font-size': 10,
                     'edge': g.ABSTRACT_EDGE}

    default_edge = {'id': g.ABSTRACT_EDGE, 'shape_name': 'linear', 'color': 'content1', 'pull': .40,
                    'visible': True, 'arrowhead_at_start': False, 'arrowhead_at_end': False,
                    'labeled': False}
    touch_areas_when_dragging = {}
    touch_areas_when_selected = {}
    buttons_when_selected = {}

    def __init__(self, syntactic_object=None):
        """ Node is an abstract class that shouldn't be used by itself, though
        it should contain all methods to make it work. Inherit and modify
        this for
        Constituents, Features etc. """
        Movable.__init__(self)
        self.syntactic_object = syntactic_object

        self.label_object = None
        self._label_visible = True
        self._label_qdocument = None
        self.label_rect = None
        self._inode = None
        self._inode_changed = True
        self._inode_str = ''
        self._gravity = 0
        self.label_object = Label(parent=self)
        self.clickable = False
        self.selectable = True
        self.draggable = True
        self.drag_data = None
        self._magnets = []
        self.status_tip = ""
        self.width = 0
        self.height = 0
        self.inner_rect = None
        self.anim = None

        self.edges_up = []
        self.edges_down = []
        self.triangle = None
        self.folded_away = False
        self.folding_towards = None
        self.color_id = None

        self._editing_template = {}

        self.label_display_data = {}
        self.setFiltersChildEvents(True)
        self.setAcceptHoverEvents(True)
        # self.setAcceptDrops(True)
        self.setFlag(QtWidgets.QGraphicsObject.ItemSendsGeometryChanges)
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setZValue(10)
        self.fade_in()
        self.effect = create_shadow_effect(ctrl.cm.selection())
        # self.effect = create_shadow_effect(self.color)
        self._update_magnets = True
        self.setGraphicsEffect(self.effect)

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
            1st wave creates the objects and calls __init__, and then
            iterates through and sets the values.
            2nd wave calls after_inits for all created objects. Now they can
            properly refer to each other and know their
                values.
        :return: None
        """
        self._inode_changed = True
        a = self.as_inode()
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
        if 'label' in updated_fields:
            self._inode_changed = True
            self.update_label()
        if 'triangle' in updated_fields:
            self.triangle_updated(self.triangle)
        if 'folding_towards' in updated_fields:
            # do the animation and its after triggers.
            if self.folding_towards:
                self.fold_towards(self.folding_towards)
            else:
                self.folded_away = False
                self.update_position()
                self.fade_in()
            self.update_visibility()
        if update_type == g.CREATED:
            for edge in self.edges_up:
                edge.connect_end_points(edge.start, self)
                edge.update_end_points()
            for edge in self.edges_down:
                edge.connect_end_points(self, edge.end)
                edge.update_end_points()
        elif update_type == g.DELETED:
            print('Node.DELETED. (%s) should I be reverting deletion or have we '
                  'just been deleted?' % self.save_key)

    @staticmethod
    def create_synobj(label=None):
        """ (Abstract) Nodes do not have corresponding syntactic object, so
        return None and the Node factory knows to not try to pass syntactic
        object -argument.
        :param label: not used here
        :return:
        """
        return None

    # This seems to be not used
    def prepare_schema_for_label_display(self):
        """
        :return:
        """
        if self.syntactic_object and hasattr(self.syntactic_object.__class__, 'viewable'):
            synvis = self.syntactic_object.__class__.viewable
        else:
            synvis = {}
        myvis = getattr(self.__class__, 'viewable', {})
        sortable = []
        label_line_length = 0
        for key, value in synvis.items():
            o = value.get('order', 50)
            sortable.append((o, 0, key, value))
        for key, value in myvis.items():
            o = value.get('order', 50)
            sortable.append((o, 1, key, value))
        sortable.sort()
        self.label_display_data = OrderedDict()
        for foo, bar, key, value in sortable:
            if key not in self.label_display_data:
                self.label_display_data[key] = dict(value)
            else:
                old = self._inode.fields[key]
                new = dict(value)
                new.update(old)
                self.label_display_data[key] = new
            if 'resizable' in value:
                label_resizable = True
            if 'line_length' in value:
                ll = value['line_length']
                if ll > label_line_length:
                    label_line_length = ll


    def get_editing_template(self, refresh=False):
        """ Create or fetch a dictionary template to help building an editing
        UI for Node.
        The template is based on 'editable'-class variable and combines
        templates from Node
        and its subclasses and its syntactic object's templates.

        The dictionary includes a special key field_order that gives the
        order of the elements.
        :param refresh: force recalculation of template
        :return: dict
        """
        if self._editing_template and not refresh:
            return self._editing_template

        self._editing_template = {}
        if self.syntactic_object and hasattr(self.syntactic_object.__class__, 'editable'):
            synedit = self.syntactic_object.__class__.editable
        else:
            synedit = {}
        myedit = getattr(self.__class__, 'editable', {})
        sortable = []
        for key, value in myedit.items():
            o = value.get('order', 200)
            sortable.append((o, 1, key, value))
        for key, value in synedit.items():
            o = value.get('order', 200)
            sortable.append((o, 0, key, value))
        sortable.sort()
        order = []
        for foo, syntactic, key, value in sortable:
            if key not in self._editing_template:
                self._editing_template[key] = value
            if syntactic == 0:
                self._editing_template[key]['syntactic'] = True
            if key not in order:
                order.append(key)
        self._editing_template['field_order'] = order
        return self._editing_template

    def impose_order_to_inode(self):
        """ Prepare inode (ITemplateNode) to match data structure of this type of node
        ITemplateNode has parsed input from latex trees to rows of text or ITextNodes and
        these can be mapped to match Node elements, e.g. label or index. The mapping is
        implemented here, and subclasses of Node should make their mapping.
        :return:
        """
        # This part should be done by all subclasses, call super(
        # ).impose_order_to_inode()
        assert self.label_object

        self._inode.fields = {}
        self._inode.view_order = []

        if self.syntactic_object and hasattr(self.syntactic_object.__class__, 'viewable'):
            syn_obj_viewable_fields = self.syntactic_object.__class__.viewable
        else:
            syn_obj_viewable_fields = {}
        my_viewable_fields = getattr(self.__class__, 'viewable', {})
        label_line_length = 0
        sortable = []
        for key, value in syn_obj_viewable_fields.items():
            o = value.get('order', 50)
            sortable.append((o, 0, key, value))
        for key, value in my_viewable_fields.items():
            o = value.get('order', 50)
            sortable.append((o, 1, key, value))
        sortable.sort()
        fields = self._inode.fields
        view_order = self._inode.view_order
        for foo, bar, field_name, value in sortable:
            if field_name not in fields:
                fields[field_name] = dict(value)
            else:
                old = fields[field_name]
                new = dict(value)
                new.update(old)
                fields[field_name] = new
            if field_name not in view_order:
                view_order.append(field_name)
            if 'resizable' in value:
                self.label_object.resizable = True
            if 'line_length' in value:
                ll = value['line_length']
                if ll > self.label_object.line_length:
                    self.label_object.line_length = ll
            if 'text_align' in value:
                self.label_object.text_align = value['text_align']


    def update_values_from_inode(self):
        """ Take values from given inode and set this object to have these values.
        :return:
        """
        for field_name, value_data in self._inode.fields.items():
            if 'value' in value_data:
                v = value_data['value']
                if 'readonly' in value_data:
                    continue
                elif 'setter' in value_data:
                    getattr(self, value_data['setter'])(v)
                else:
                    setattr(self, field_name, v)

    def alert_inode(self, value=None):
        """ Setters may announce that inode needs to be updated
        :param value: don't care about that
        :return:
        """
        self._inode_changed = True

    def if_changed_triangle(self, value):
        self._inode_changed = True
        self.triangle_updated(value)

    def has_triangle(self):
        return self.triangle

    def can_have_triangle(self):
        return not self.triangle

    def triangle_updated(self, value):
        """ update label positioning here so that offset doesn't need to be
        stored in save files and it
            still will be updated correctly
        :param value: bool
        :return: None
        """
        if self.label_object:
            if value:
                self.label_object.y_offset = TRIANGLE_HEIGHT
            else:
                self.label_object.y_offset = 0
            if self.label_object.has_been_initialized:
                self.update_label()

    def if_changed_folding_towards(self, value):
        self.update_position()

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
        self.setZValue(10)
        self.update()
        ctrl.remove_status(self.status_tip)

    def __repr__(self):
        """ This is a node and this represents this FL item """
        return '%s-%s' % (self.syntactic_object, self.save_key)

    def reset(self):
        """
        Remove temporary/state information from node, eg. remove touch areas.
        """
        Movable.reset(self)
        self.update_bounding_rect()
        ctrl.ui.remove_touch_areas_for(self)

    def node_info(self):
        so = self.syntactic_object
        if so:
            so = so._saved
        print('''-----------Node saved data-----------
saved: %s
syntactic_object: %s
-----------------------''' % (self._saved, so))

    def is_placeholder(self):
        """ Constituent structure may assume a constituent to be somewhere,
        before the user has intentionally created
        one there. These are shown as placeholders, which are nodes, but with
        limited presence.
        :return: boolean
        """
        return False

    def move(self, md):
        """ Add on Moveable.move the case when node is folding towards
        triangle. It has priority.
        :param md: dict to collect total amount of movement.
        :return: (bool, bool) -- is the node moving, does it allow
        normalization of movement
        """

        if self.folding_towards and not self._move_counter:
            #self.fold_towards(self.folding_towards)
            return True, False
        else:
            return super().move(md)

    def fade_out(self, s=300):
        for edge in itertools.chain(self.edges_down, self.edges_up):
            edge.fade_out(s=s)
        super().fade_out(s=s)

    def fade_in(self, s=300):
        for edge in self.edges_up:
            if (edge.start and edge.start.is_visible()) or not edge.start:
                edge.fade_in(s=s)
        for edge in self.edges_down:
            if edge.end and edge.end.is_visible():
                edge.fade_in(s=s)

        super().fade_in(s=s)


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
        new_parent = self.pick_tallest_tree()
        if new_parent:
            if old_parent is not new_parent:
                scene_position = self.current_scene_position
                self.setParentItem(new_parent)
                self.current_position = self.scene_position_to_tree_position(scene_position)
        elif old_parent:
            self.current_position = self.current_scene_position
            self.setParentItem(None)

    def add_to_tree(self, tree):
        """ Add this node to given trees and possibly set it as parent for this graphicsitem.
        :param tree: Tree
        :return:
        """
        self.trees.add(tree)
        self.update_graphics_parent()

    def remove_from_tree(self, tree, recursive_down=False):
        """ Remove node from trees and remove the (graphicsitem) parenthood-relation.
        :param tree: Tree
        :param recursive_down: bool -- do recursively remove child nodes from tree too
        :return:
        """
        if tree in self.trees:
            self.trees.remove(tree)
            self.update_graphics_parent()
        if recursive_down:
            for child in self.get_children():
                legit = False
                for parent in child.get_parents():
                    if tree in parent.trees:
                        legit = True
                if not legit:
                    child.remove_from_tree(tree, recursive_down=True)

    def copy_position(self, other, ax=0, ay=0):
        """ Helper method for newly created items. Takes other item and copies movement related
        attributes from it (physics settings, locks, adjustment etc). ax, ay, az can be used to
        adjust these a little to avoid complete overlap.
        :param other:
        :param ax:
        :param ay:
        :param az:
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
        """ Return scene position converted to coordinate system used by this node trees. Works for xy  -tuples.

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

    def get_all_children(self):
        """ Get all types of child nodes of this node.
        :return: iterator of Nodes
        """
        return (edge.end for edge in self.edges_down)

    def get_all_visible_children(self):
        """ Get all types of child nodes of this node if they are visible.
        :return: iterator of Nodes
        """
        return (edge.end for edge in self.edges_down if edge.end.is_visible())

    def get_children(self):
        """
        Get child nodes of this node if they are of the same type as this.
        :return: iterator of Nodes
        """
        et = self.__class__.default_edge_type
        return (edge.end for edge in self.edges_down if edge.edge_type == et)

    def get_reversed_children(self):
        """
        Get child nodes of this node if they are of the same type as this.
        :return: iterator of Nodes
        """
        et = self.__class__.default_edge_type
        return (edge.end for edge in reversed(self.edges_down) if edge.edge_type == et)

    def get_visible_children(self):
        """
        Get child nodes of this node if they are of the same type as this.
        :return: iterator of Nodes
        """
        et = self.__class__.default_edge_type
        return (edge.end for edge in self.edges_down if
                edge.edge_type == et and edge.end and edge.end.is_visible())

    def get_children_of_type(self, edge_type=None, node_type=None):
        """
        Get child nodes of this node if they are of the same type as this.
        :return: iterator of Nodes
        """
        if edge_type:
            return (edge.end for edge in self.edges_down if edge.edge_type == edge_type)
        elif node_type:
            return (edge.end for edge in self.edges_down if isinstance(edge.end, node_type))

    def get_parents(self, only_similar=True, only_visible=False, edge_type=None)->list:
        """
        Get parent nodes of this node.
        :param only_similar: boolean, only return nodes of same type (eg.
        ConstituentNodes)
        :param only_visible: boolean, only return visible nodes
        :param edge_type: int, only return Edges of certain subclass.
        :return: list of Nodes
        """
        if not self.edges_up:
            return []
        if only_similar or edge_type is not None:
            if edge_type is None:
                edge_type = self.__class__.default_edge_type
            if only_visible:
                return [edge.start for edge in self.edges_up if
                        edge.edge_type == edge_type and edge.start and edge.start.is_visible()]
            else:
                return [edge.start for edge in self.edges_up if
                        edge.edge_type == edge_type and edge.start]
        else:
            if only_visible:
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

    def is_unary(self):
        for parent in self.get_parents(only_similar=True):
            if len(list(parent.get_children())) == 1:
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

    def is_leaf(self, only_similar=True, only_visible=False):
        """

        :param only_similar:
        :param only_visible:
        :return:
        """
        if only_similar and only_visible:
            gen = self.get_visible_children()
        elif only_similar:
            gen = self.get_children()
        elif only_visible:
            gen = self.get_all_visible_children()
        else:
            gen = self.get_all_children()
        return not next(gen, False)

    def get_only_parent(self, only_similar=True, only_visible=True):
        """ Returns one or zero parents -- useful when not using multidomination
        :param only_similar:
        :param only_visible:
        """
        parents = self.get_parents(only_similar, only_visible)
        if parents:
            return parents[0]
        return None

    def is_top_node(self, only_similar=True, only_visible=False):
        """ Root node is the topmost node of a trees
        :param only_similar:
        :param only_visible:
        """
        if self.get_parents(only_similar, only_visible):
            return False
        else:
            return True

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

    def get_edge_to(self, other, edge_type=''):
        """ Returns edge object, not the related node. There should be only
        one instance of edge
        of certain type between two elements.
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

    def get_edges_up(self, similar=True, visible=False, alignment=None):
        """ Returns edges up, filtered
        :param similar:
        :param visible:
        :param alignment:
        """

        def filter_func(rel):
            """
            :param rel:
            :return: bool """
            if similar and rel.edge_type != self.__class__.default_edge_type:
                return False
            if alignment and rel.alignment != alignment:
                return False
            if visible and not rel.is_visible():
                return False
            return True

        return filter(filter_func, self.edges_up)

    def get_edges_down(self, similar=True, visible=False, alignment=None):
        """ Returns edges down, filtered
        :param similar:
        :param visible:
        :param alignment:
        """

        def filter_func(edge):
            """
            :param rel:
            :return: bool """
            if similar and edge.edge_type != self.__class__.default_edge_type:
                return False
            if alignment and edge.alignment != alignment:
                return False
            if visible and not edge.is_visible():
                return False
            return True

        return filter(filter_func, self.edges_down)

    def node_alone(self):
        return not (self.edges_down or self.edges_up)

    def can_connect_with(self, other):
        """ Override this in subclasses, checks conditions when other nodes could connect to this
        node. (This node is child). Generally connection should be refuted if it already exists
        :param other:
        :return:
        """
        return other not in self.get_parents(only_similar=False, only_visible=False)

    # Reflecting structural changes in syntax
    # Nodes are connected and disconnected to each other by user, through UI,
    # and these connections may have different syntactical meaning.
    # Each node type can define how connect or disconnect affects syntactic
    # elements.
    #
    # These are called in all forest's connect and disconnect -activities,
    # so they get called also when the connection was initiated from syntax.
    # In these cases methods should be smart enough to notice that the
    # connection is already there and not duplicate it.
    # ########################################

    def connect_in_syntax(self, edge):
        """ Implement this if connecting this node (using this edge) needs to be
         reflected in syntax. Remember to verify it already isn't there.
        :param edge:
        :return:
        """
        pass

    def disconnect_in_syntax(self, edge):
        """ Implement this if disconnecting this node (using this edge) needs
        to be reflected in syntax. Remember to verify it already isn't there.
        :param edge:
        :return:
        """
        pass

    # ## Font
    # #####################################################################

    @property
    def font(self) -> QtGui.QFont:
        """ Helper to get the QFont being used here. It may be local, or set
        for forest, or come from default preferences. You don't need to know.
        :return:
        """
        return qt_prefs.font(self.get_font_id())

    def get_font_id(self):
        """
        :return:
        """
        if self.font_id:
            return self.font_id
        else:
            return ctrl.fs.node_info(self.node_type, 'font')

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
        if self.color_id is None:
            c = ctrl.fs.node_info(self.__class__.node_type, 'color')
            return c
        else:
            return self.color_id

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
            return ctrl.cm.active(ctrl.cm.selection())
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

    def update_label(self, force_update=False):
        """

        :param force_update: Force inode recomposition and visibility checks
        :return:
        """
        if not self.label_object:
            self.label_object = Label(parent=self)
        if force_update:
            self._inode_changed = True
        self.label_object.update_label(self.font, self.as_inode())
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
        self._label_visible = not self.as_inode().is_empty_for_view()
        self.label_object.setVisible(self._label_visible)

    @property
    def raw_label(self):
        """ Get the unparsed raw version of label (str)
        :return:
        """
        return self.label

    def as_inode(self):
        """
        :return: INodes or str or tuple of them
        """
        if self._inode is None:
            self._inode = ITemplateNode()
            self._inode_str = str(self._inode)
            self.impose_order_to_inode()
            self._inode_changed = True
        if self._inode_changed:
            iv = self._inode.fields
            for key, value in iv.items():
                getter = value.get('getter', key)
                # use 'getter' or default to 'key', assuming that key is the
                # same as the property it is representing
                value['value'] = getattr(self, getter)
            self._inode_str = str(self._inode)
            self._inode_changed = False
        return self._inode

    def update_status_tip(self):
        """ implement properly in subclasses, let tooltip tell about the node
        :return: None
        """
        self.status_tip = str(self)

    def get_html_for_label(self):
        """ This should be overridden if there are alternative displays for
        label """
        return self.label

    def has_empty_label(self):
        """


        :return:
        """
        return not self._inode_str

    def label_edited(self):
        """ implement if label can be modified by editing it directly """
        pass


    def get_bottom_row_y(self):
        """ Label should answer to this.
        :return:
        """
        if self.label_object:
            return self.label_object.get_bottom_row_y()
        else:
            return 0

    def get_top_row_y(self):
        """ Implement this if the movable has content where differentiating between bottom row and top row can potentially make sense.
        :return:
        """
        if self.label_object:
            return self.label_object.get_top_row_y()
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
        if self.triangle:
            p = QtGui.QPen(self.contextual_color)
            p.setWidth(1)
            painter.setPen(p)
            self.paint_triangle(painter)
        if self.drag_data:
            p = QtGui.QPen(self.contextual_color)
            #b = QtGui.QBrush(ctrl.cm.paper())
            #p.setColor(ctrl.cm.hover())
            p.setWidth(1)
            painter.setPen(p)
            painter.setBrush(self.drag_data.background)
            painter.drawRoundedRect(self.inner_rect, 5, 5)
            painter.setBrush(Qt.NoBrush)


        elif self._hovering:
            p = QtGui.QPen(self.contextual_color)
            #p.setColor(ctrl.cm.hover())
            p.setWidth(1)
            painter.setPen(p)
            painter.drawRoundedRect(self.inner_rect, 5, 5)
        elif ctrl.pressed is self or ctrl.is_selected(self):
            p = QtGui.QPen(self.contextual_color)
            p.setWidth(1)
            painter.setPen(p)
            painter.drawRoundedRect(self.inner_rect, 5, 5)
        elif self.has_empty_label() and self.node_alone():
            p = QtGui.QPen(self.contextual_color)
            p.setStyle(QtCore.Qt.DotLine)
            p.setWidth(1)
            painter.setPen(p)
            painter.drawRoundedRect(self.inner_rect, 5, 5)
            # x,y,z = self.current_position
            # w2 = self.width/2.0
            # painter.setPen(self.contextual_color())
            # painter.drawEllipse(-w2, -w2, w2 + w2, w2 + w2)
        #x = 0
        #p = QtGui.QPen(self.contextual_color)
        #p.setWidth(1)
        #painter.setPen(p)
        #for trees in self.trees:
        #    painter.drawEllipse(x, 10, 6, 6)
        #    x += 10

    def has_visible_label(self):
        """
        :return: bool
        """
        return self._label_visible

    def update_bounding_rect(self):
        """


        :return:
        """
        my_class = self.__class__
        if self._label_visible and self.label_object:
            lbr = self.label_object.boundingRect()
            lbh = lbr.height()
            lbw = lbr.width()
            self.label_rect = QtCore.QRectF(self.label_object.x(), self.label_object.y(), lbw,
                                            lbh)
            self.width = max((lbw, my_class.width))
            self.height = max((lbh, my_class.height))
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
        """ BoundingRects are used often and cost of this method affects
        performance.
        inner_rect is used as a cached bounding rect and returned fast if
        there is no explicit
        update asked. """
        if self.inner_rect:
            return self.inner_rect
        else:
            return self.update_bounding_rect()

    ######### Triangles #########################################

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
        ctrl.forest.animation_started(self.save_key+'_fold')
        self.fade_out()

    def finish_folding(self):
        """ Hide, and remember why this is hidden """
        self.folded_away = True
        self.update_visibility()
        self.update_bounding_rect()
        # update edge visibility from triangle to its immediate children
        if self.folding_towards in self.get_parents():
            self.folding_towards.update_visibility()
        ctrl.forest.animation_finished(self.save_key+'_fold')

    def paint_triangle(self, painter):
        """ Drawing the triangle, called from paint-method
        :param painter:
        """
        br = self.boundingRect()
        left = br.x()
        center = left + self.width / 2
        right = left + self.width
        top = self.label_object.triangle_y
        bottom = top + self.label_object.triangle_height
        simple = False
        if simple:
            triangle = QtGui.QPainterPath()
            triangle.moveTo(center, top)
            triangle.lineTo(right, bottom)
            triangle.lineTo(left, bottom)
            triangle.lineTo(center, top)
            painter.drawPath(triangle)
        else:
            c = self.contextual_color
            edge_type = self.__class__.default_edge_type
            shape_name = ctrl.fs.edge_info(edge_type, 'shape_name')
            presets = kataja.shapes.SHAPE_PRESETS[shape_name]
            method = presets['method']
            path, lpath, foo = method(start_point=(center, top),
                                      end_point=(right, bottom),
                                      alignment=g.RIGHT, **presets)
            if presets['fill']:
                painter.fillPath(path, c)
            else:
                painter.drawPath(path)
            painter.drawLine(left, bottom, right, bottom)
            path, lpath, foo = method(start_point=(center, top),
                                      end_point=(left, bottom),
                                      alignment=g.LEFT, **presets)
            if presets['fill']:
                painter.fillPath(path, c)
            else:
                painter.drawPath(path)

    def on_press(self, value):
        """ Testing if we can add some push-depth effect.
        :param value: pressed or not
        :return:
        """
        if value:
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

    def magnet(self, n):
        """
        :param n: index of magnets. There are five magnets in top and bottom
        and three for sides:

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

                self._magnets = [(-w2, -h2), (-w4, -h2), (0, -h2), (w4, -h2), (w2, -h2), (-w2, 0),
                                 (w2, 0), (-w2, h2), (-w4, h2), (0, h2), (w4, h2), (w2, h2)]

            x1, y1 = self.current_scene_position
            x2, y2 = self._magnets[n]
            if prefs.use_magnets == 2:
                parents = list(self.get_parents())
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
                    #if r > 0 and False:
                    #    x2 = x * cos_r - y * sin_r
                    #    y2 = x * sin_r + y * cos_r
                    #else:
                    x2 = x * cos_r + y * sin_r
                    y2 = -x * sin_r + y * cos_r
            return x1 + x2, y1 + y2
        else:
            return self.current_scene_position

    # ### Menus #########################################

    def update_selection_status(self, selected):
        """ This is called after item is selected or deselected to update
        appearance and related local elements.
        :param selected:
        """
        if not selected:
            self.setZValue(10)
            if ctrl.main.use_tooltips:
                self.setToolTip("")
            self.label_object.set_quick_editing(False)
        else:
            self.setZValue(200)
            if ctrl.main.use_tooltips:
                self.setToolTip("Edit with keyboard, double click to inspect node")
            self.label_object.set_quick_editing(True)

            # self.node_info()
        self.update()

    # ### MOUSE - kataja
    # ########################################################

    def open_embed(self):
        """ Tell ui to open an embedded edit, generated from
        edit template or overridden.
        :return: None
        """
        ctrl.ui.start_editing_node(self)

    def double_click(self, event=None):
        """ Scene has decided that this node has been clicked
        :param event:
        """
        self.hovering = False
        ctrl.select(self)
        self.open_embed()

        #if ctrl.is_selected(self):
        #else:

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
            return
        if ctrl.is_selected(self):
            pass
        else:
            editor = ctrl.ui.get_editing_embed_for_node(self)
            ctrl.select(self)
            if editor and editor.isVisible():
                self.open_embed()

    # Drag flow:

    # 1. start_dragging -- drag is initiated from this node. If the node was already selected,
    # then other nodes that were selected at the same time are also understood to be dragged.
    # If the node has unambiguous children, these are also dragged. If node is top node of a trees,
    # then the trees is the object of dragging, and not node.
    #
    # 2. start_dragging_tracking --
    #
    #
    #
    #

    def start_dragging(self, scene_pos):
        """ Figure out which nodes belong to the dragged set of nodes.
        It may be that a whole trees is dragged. If this is the case, drag_to commands to nodes that are tops of trees are directed to trees instead. Node doesn't change its position in trees if the whole trees moves.

        :param scene_pos:
        """
        def in_any_tree(node, treeset):
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
            # find trees tops in selection
            for item in ctrl.selected:
                tree = item.tree_where_top()
                if tree:
                    dragged_trees.add(tree)
            # include those nodes in selection and their children that are not part of wholly
            # dragged trees
            for item in ctrl.selected:
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
        ctrl.ui.prepare_touch_areas_for_dragging(drag_host=self, moving=moving,
                                                 dragged_type=self.node_type, multidrag=multidrag)

        self.start_moving()

    def start_dragging_tracking(self, host=False, scene_pos=None):
        """ Add this node into the entourage of dragged node. These nodes will
        maintain their relative position to dragged node while dragging.
        :return: None
        """
        ctrl.dragged_set.add(self)
        ctrl.add_my_group_to_dragged_groups(self)
        self.drag_data = DragData(self, is_host=host, mousedown_scene_pos=scene_pos)
        tree = self.tree_where_top()
        if tree:
            tree.start_dragging_tracking(host=host, scene_pos=scene_pos)
        self.anim = QtCore.QPropertyAnimation(self, qbytes_scale)
        self.anim.setDuration(100)
        self.anim.setStartValue(self.scale())
        self.anim.setEndValue(1.1)
        self.anim.start()
        self.setZValue(500)

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
        scene_pos = to_tuple(event.scenePos())
        if not ctrl.dragged_focus:
            self.start_dragging(scene_pos)
        # change dragged positions to be based on adjustment instead of
        # distance to main dragged.
        for node in ctrl.dragged_set:
            node.dragged_to(scene_pos)
        for group in ctrl.dragged_groups:
            group.update_shape()

    def dragged_to(self, scene_pos):
        """ Dragged focus is in scene_pos. Move there or to position
        relative to that
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
            p = self.parentItem()
            if p:
                px, py = p.current_position
                super().dragged_to((nx + dx - px, ny + dy - py))
            else:
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

    def drop_to(self, x, y, recipient=None):
        """

        :param recipient:
        :param x:
        :param y:
        :return: action finished -message (str)
        """
        self.stop_moving()
        self.update()
        message = ''
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
        if self.drag_data:
            self.setZValue(self.drag_data.old_zvalue)
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

    def lock(self):
        """ Display lock, unless already locked. Added functionality to
        recognize the state before
         dragging started.
        :return:
        """
        was_locked = self.locked or self.use_adjustment
        super().lock()
        #if not was_locked:
        if self.is_visible():
            ctrl.main.ui_manager.show_anchor(self)  # @UndefinedVariable

    # ### Mouse - Qt events ##################################################

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
        """ Dragging a foreign object (could be from ui) over a node, entering.
        :param event:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
            self.hovering = True
        else:
            QtWidgets.QGraphicsObject.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        """ Dragging a foreign object (could be from ui) over a node, leaving.
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
        return self.label or "no label"

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

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # Saved properties
    syntactic_object = Saved("syntactic_object")
    label = Saved("label", if_changed=alert_inode)
    edges_up = Saved("edges_up")
    edges_down = Saved("edges_down")
    triangle = Saved("triangle", if_changed=if_changed_triangle)
    folded_away = Saved("folded_away")
    folding_towards = Saved("folding_towards", if_changed=if_changed_folding_towards)
    color_id = Saved("color_id")
    font_id = Saved("font_id")
