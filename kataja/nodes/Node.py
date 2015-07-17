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

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from kataja.ui.ControlPoint import ControlPoint
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.Label import Label
from kataja.Movable import Movable
from kataja.BaseModel import Saved, Synobj
from kataja.utils import to_tuple, create_shadow_effect, time_me
import kataja.globals as g
from kataja.parser.INodes import ITemplateNode

TRIANGLE_HEIGHT = 10


# ctrl = Controller object, gives accessa to other modules

# alignment of edges -- in some cases it is good to draw left branches
# differently than right branches

NO_ALIGN = 0
LEFT = 1
RIGHT = 2


class Node(Movable, QtWidgets.QGraphicsItem):
    """ Basic class for any visualization elements that can be connected to
    each other """
    width = 20
    height = 20
    default_edge_type = g.ABSTRACT_EDGE
    node_type = g.ABSTRACT_NODE
    ordered = False
    ordering_func = None
    name = ('Abstract node', 'Abstract nodes')
    short_name = "Node"  # shouldn't be used on its own
    display = False

    # override this if you need to turn inodes into your custom Nodes. See
    # examples in
    # ConstituentNode or FeatureNode

    default_style = {'color': 'content1', 'font': g.MAIN_FONT, 'font-size': 10,
                     'edge': g.ABSTRACT_EDGE}

    default_edge = {'id': g.ABSTRACT_EDGE, 'shape_name': 'linear',
                    'color': 'content1', 'pull': .40, 'visible': True,
                    'arrowhead_at_start': False, 'arrowhead_at_end': False,
                    'labeled': False}

    def __init__(self, syntactic_object=None):
        """ Node is an abstract class that shouldn't be used by itself, though
        it should contain all methods to make it work. Inherit and modify
        this for
        Constituents, Features etc. """
        QtWidgets.QGraphicsItem.__init__(self)
        Movable.__init__(self)
        self.syntactic_object = syntactic_object

        self._label_complex = None
        self._label_visible = True
        self._label_qdocument = None
        self.label_rect = None
        self._inode = None
        self._inode_changed = True
        self._inode_str = ''
        self._gravity = 0
        self.clickable = False
        self.selectable = True
        self.draggable = True
        self._fixed_position_before_dragging = None
        self._adjustment_before_dragging = None
        self._distance_from_dragged = (0, 0)
        self._magnets = []
        self.status_tip = ""
        self.width = 0
        self.height = 0
        self.inner_rect = None

        self.edges_up = []
        self.edges_down = []
        self.triangle = None
        self.folded_away = False
        self.folding_towards = None
        self.color_id = None

        self._editing_template = {}

        self.label_display_data = {}

        self.setAcceptHoverEvents(True)
        # self.setAcceptDrops(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
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
        a = self.as_inode
        self.update_label()
        self.update_bounding_rect()
        self.update_visibility()
        self.announce_creation()
        ctrl.forest.store(self)

    def after_model_update(self, updated_fields, update_type):
        """ This is called after the item's model has been updated, to run
        the side-effects of various
        setters in an order that makes sense.
        :param updated_fields: list of names of fields that have been updated.
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
            print('Node.CREATED. (%s)' % self.save_key)
            for edge in self.edges_up:
                print('restoring connection up: %s %s %s ' % (
                edge, edge.start, self))
                edge.connect_end_points(edge.start, self)
                edge.update_end_points()
            for edge in self.edges_down:
                print('restoring connection down: %s %s %s ' % (
                edge, self, edge.end))
                edge.connect_end_points(self, edge.end)
                edge.update_end_points()
        elif update_type == g.DELETED:
            print(
                'Node.DELETED. (%s) should I be reverting deletion or have we '
                'just been deleted?' % self.save_key)

    @staticmethod
    def create_synobj():
        """ (Abstract) Nodes do not have corresponding syntactic object, so
        return None and the Node factory knows to not try to pass syntactic
        object -argument.
        :return:
        """
        return None

    @time_me
    def prepare_schema_for_label_display(self):
        """
        :return:
        """
        if self.syntactic_object and hasattr(self.syntactic_object.__class__,
                                             'visible'):
            synvis = self.syntactic_object.__class__.visible
        else:
            synvis = {}
        myvis = getattr(self.__class__, 'visible', {})
        sortable = []
        for key, value in synvis.items():
            o = value.get('order', 50)
            sortable.append((o, 0, key, value))
        for key, value in myvis.items():
            o = value.get('order', 50)
            sortable.append((o, 1, key, value))
        sortable.sort()
        self.label_display_data = OrderedDict()
        for foo, bar, key, value in sortable:
            self.label_display_data[key] = value

    @time_me
    def get_editing_template(self, refresh=False):
        """ Create or fetch a dictionary template to help building an editing
        UI for Node.
        The template is based on 'editable'-class variable and combines
        templates from Node
        and its subclasses and its syntactic object's templates.

        The dictionary includes a special key field_order that gives the
        order of the fields.
        :param refresh: force recalculation of template
        :return: dict
        """
        if self._editing_template and not refresh:
            return self._editing_template

        self._editing_template = {}
        if self.syntactic_object and hasattr(self.syntactic_object.__class__,
                                             'editable'):
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
        """ Prepare inode (ITemplateNode) to match data structure of this
        type of node
        ITemplateNode has parsed input from latex trees to rows of text or
        ITextNodes and
        these can be mapped to match Node fields, e.g. label or index. The
        mapping is
        implemented here, and subclasses of Node should make their mapping.
        :return:
        """
        # This part should be done by all subclasses, call super(
        # ).impose_order_to_inode()
        self._inode.values = {}
        self._inode.view_order = []
        if self.syntactic_object and hasattr(self.syntactic_object.__class__,
                                             'visible'):
            synvis = self.syntactic_object.__class__.visible
        else:
            synvis = {}
        myvis = getattr(self.__class__, 'visible', {})
        sortable = []
        for key, value in synvis.items():
            o = value.get('order', 50)
            sortable.append((o, 0, key, value))
        for key, value in myvis.items():
            o = value.get('order', 50)
            sortable.append((o, 1, key, value))
        sortable.sort()
        for foo, bar, key, value in sortable:
            self._inode.values[key] = dict(value)
            if key not in self._inode.view_order:
                self._inode.view_order.append(key)

    def update_values_from_inode(self):
        """ Take values from given inode and set this object to have these
        values.
        :return:
        """
        for key, value_data in self._inode.values.items():
            if 'value' in value_data:
                v = value_data['value']
                if 'readonly' in value_data:
                    continue
                elif 'setter' in value_data:
                    getattr(self, value_data['setter'])(v)
                else:
                    setattr(self, key, v)

    def alert_inode(self, value):
        """ Setters may announce that inode needs to be updated
        :param value: don't care about that
        :return:
        """
        self._inode_changed = True

    def if_changed_triangle(self, value):
        self._inode_changed = True
        self.triangle_updated(value)

    def triangle_updated(self, value):
        """ update label positioning here so that offset doesn't need to be
        stored in save files and it
            still will be updated correctly
        :param value: bool
        :return: None
        """
        if self._label_complex:
            if value:
                self._label_complex.y_offset = TRIANGLE_HEIGHT
            else:
                self._label_complex.y_offset = 0
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
        self._set_hovering(value)

    def _set_hovering(self, value):
        """ Toggle hovering effects and internal bookkeeping
        :param value: bool
        :return:
        """
        if value and not self._hovering:
            self._hovering = True
            if ctrl.cm.use_glow():
                self.effect.setColor(self.contextual_color)
                self.effect.setEnabled(True)
            self.prepareGeometryChange()
            self.update()
            self.setZValue(150)
            ctrl.set_status(self.status_tip)
        elif (not value) and self._hovering:
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

    def is_placeholder(self):
        """ Constituent structure may assume a constituent to be somewhere,
        before the user has intentionally created
        one there. These are shown as placeholders, which are nodes, but with
        limited presence.
        :return: boolean
        """
        return False

    def update_position(self, instant=False):
        """ In addition to Movable's update_position, take account movement
        to fold nodes into triangle
        Computes new current_position and target_position.
        :param instant: don't animate (for e.g. dragging)
        :return: None
        """
        if self.folding_towards:
            tp = self._target_position
            self._target_position = self.folding_towards.current_position
            if tp == self._target_position:
                if self.current_position == self._target_position:
                    self.stop_moving()
                    # don't trigger start moving again if we are already
                    # going there
            if instant:
                self.current_position = tuple(self._target_position)
                self.stop_moving()
            else:
                if self._target_position != self.current_position:
                    self.start_moving()
                else:
                    self.stop_moving()
        else:
            super().update_position(instant=instant)

    def move(self, md):
        """ Add on Moveable.move the case when node is folding towards
        triangle. It has priority.
        :param md: dict to collect total amount of movement.
        :return: (bool, bool) -- is the node moving, does it allow
        normalization of movement
        """

        if self.folding_towards:
            if self._move_counter:
                px, py, pz = self.current_position
                tx, ty, tz = self._target_position
                if self._use_easing:
                    xvel = self._x_step * qt_prefs.easing_curve[
                        self._move_counter - 1]
                    yvel = self._y_step * qt_prefs.easing_curve[
                        self._move_counter - 1]
                    zvel = self._z_step * qt_prefs.easing_curve[
                        self._move_counter - 1]
                else:
                    xvel = (tx - px) / self._move_counter
                    yvel = (ty - py) / self._move_counter
                    zvel = (tz - pz) / self._move_counter
                self._move_counter -= 1
                if not self._move_counter:
                    self.stop_moving()
                self.current_position = (px + xvel, py + yvel, pz + zvel)
                return True, False
            else:
                return False, False
        else:
            return super().move(md)

    def adjust_opacity(self):
        """ Add to Movable.adjust_opacity fading of edges that connect to
        this node. If node fades
        away, the edges fade away. There shouldn't be situations where this
        isn't the case.
        :return: bool, is the fade in/out still going on
        """
        active = super().adjust_opacity()
        o = self.opacity()
        if active:
            for edge in self.edges_down:
                edge.setOpacity(o)
            for edge in self.edges_up:
                edge.setOpacity(o)
        return active

    # ### Children and parents
    # ####################################################

    def get_all_children(self):
        """
        Get all types of child nodes of this node.
        :return: iterator of Nodes
        """
        return (edge.end for edge in self.edges_down)

    def get_all_visible_children(self):
        """
        Get all types of child nodes of this node if they are visible.
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
        return (edge.end for edge in reversed(self.edges_down) if
                edge.edge_type == et)

    def get_visible_children(self):
        """
        Get child nodes of this node if they are of the same type as this.
        :return: iterator of Nodes
        """
        et = self.__class__.default_edge_type
        return (edge.end for edge in self.edges_down if
                edge.edge_type == et and edge.end.is_visible())

    def get_children_of_type(self, edge_type=None, node_type=None):
        """
        Get child nodes of this node if they are of the same type as this.
        :return: iterator of Nodes
        """
        if edge_type:
            return (edge.end for edge in self.edges_down if
                    edge.edge_type == edge_type)
        elif node_type:
            return (edge.end for edge in self.edges_down if
                    isinstance(edge.end, node_type))

    def get_parents(self, only_similar=True, only_visible=False,
                    edge_type=None):
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
                        edge.edge_type == edge_type and edge.start and
                        edge.start.is_visible()]
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

    def is_root_node(self, only_similar=True, only_visible=True):
        """ Root node is the topmost node of a tree
        :param only_similar:
        :param only_visible:
        """
        if self.get_parents(only_similar, only_visible):
            return False
        else:
            return True

    def get_root_node(self, only_similar=True, only_visible=False,
                      recursion=False, visited=None):
        """ Getting the root node is not trivial if there are
        derivation_steps in the tree.
        :param only_similar:
        :param only_visible:
        :param recursion:
        :param visited:
        If a node that is already visited is visited again, this is a
        derivation_step that
         should not be followed. """
        if not recursion:
            visited = set()
        if self in visited:
            return None
        parents = self.get_parents(only_similar, only_visible)
        if not parents:
            return self
        visited.add(self)
        for parent in parents:
            root = parent.get_root_node(only_similar, only_visible,
                                        recursion=True, visited=visited)
            if root:
                return root
        return self

    def get_edge_to(self, other, edge_type=''):
        """ Returns edge object, not the related node. There should be only
        one instance of edge
        of certain type between two elements.
        :param other:
        :param edge_type:
        """
        for edge in self.edges_down:
            if edge.end == other:
                if (edge_type and edge_type == edge.edge_type) or (
                not edge_type):
                    return edge
        for edge in self.edges_up:
            if edge.start == other:
                if (edge_type and edge_type == edge.edge_type) or (
                not edge_type):
                    return edge

        return None

    def get_edges_up(self, similar=True, visible=False, align=None):
        """ Returns edges up, filtered
        :param similar:
        :param visible:
        :param align:
        """

        def filter_func(rel):
            """
            :param rel:
            :return: bool """
            if similar and rel.edge_type != self.__class__.default_edge_type:
                return False
            if align and rel.align != align:
                return False
            if visible and not rel.is_visible():
                return False
            return True

        return filter(filter_func, self.edges_up)

    def get_edges_down(self, similar=True, visible=False, align=None):
        """ Returns edges down, filtered
        :param similar:
        :param visible:
        :param align:
        """

        def filter_func(rel):
            """
            :param rel:
            :return: bool """
            if similar and rel.edge_type != self.__class__.default_edge_type:
                return False
            if align and rel.align != align:
                return False
            if visible and not rel.is_visible():
                return False
            return True

        return filter(filter_func, self.edges_down)

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
        if ctrl.pressed is self:
            return ctrl.cm.active(ctrl.cm.selection())
        elif self._hovering:
            return ctrl.cm.hovering(ctrl.cm.selection())
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
        if not self._label_complex:
            self._label_complex = Label(parent=self)
        if not self.as_inode:
            return
        self._label_complex.update_label(self.font, self.as_inode)
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
        if self._inode is None:
            self._inode = ITemplateNode()
            self._inode_str = str(self._inode)
            self.impose_order_to_inode()
            self._inode_changed = True
        if self._inode_changed:
            iv = self._inode.values
            for key, value in iv.items():
                getter = value.get('getter', key)
                # use 'getter' or default to 'key', assuming that key is the
                # same as the property it is representing
                iv[key]['value'] = getattr(self, getter)
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

    # ## Qt overrides
    # ######################################################################

    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        p = QtGui.QPen(self.contextual_color)
        p.setWidth(1)
        painter.setPen(p)
        if ctrl.pressed is self or self._hovering or ctrl.is_selected(
                self) or self.has_empty_label():
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
            self.label_rect = QtCore.QRectF(self._label_complex.x(),
                                            self._label_complex.y(), lbw, lbh)
            self.width = max((lbw, my_class.width))
            self.height = max(
                (lbh + self._label_complex.y_offset, my_class.height))
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
        if ctrl.is_selected(self):
            ctrl.remove_from_selection(self)
        self.fade_out()
        self.after_move_function = self.finish_folding

    def finish_folding(self):
        """ Hide, and remember why this is hidden """
        self.folded_away = True
        self.update_visibility()
        self.update_bounding_rect()
        # update edge visibility from triangle to its immediate children
        if self.folding_towards in self.get_parents():
            self.folding_towards.update_visibility()
        ctrl.forest.draw()

    def paint_triangle(self, painter):
        """ Drawing the triangle, called from paint-method
        :param painter:
        """
        br = self.boundingRect()
        left = br.x()
        center = left + self.width / 2
        right = left + self.width
        top = br.y()
        bottom = br.y() + TRIANGLE_HEIGHT

        triangle = QtGui.QPainterPath()
        triangle.moveTo(center, top)
        triangle.lineTo(right, bottom)
        triangle.lineTo(left, bottom)
        triangle.lineTo(center, top)
        painter.drawPath(triangle)

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

                self._magnets = [(-w2, -h2), (-w4, -h2), (0, -h2), (w4, -h2),
                                 (w2, -h2), (-w2, 0), (w2, 0), (-w2, h2),
                                 (-w4, h2), (0, h2), (w4, h2), (w2, h2)]

            x1, y1, z1 = self.current_position
            x2, y2 = self._magnets[n]
            return x1 + x2, y1 + y2, z1
        else:
            return self.current_position

    # ### Menus #########################################

    def update_selection_status(self, selected):
        """ This is called

        :param selected:
        """
        if not selected:
            self.setZValue(10)
        else:
            self.setZValue(200)
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
        if ctrl.is_selected(self):
            self.open_embed()
        else:
            ctrl.select(self)

    def select(self, event=None, multi=False):
        """ Scene has decided that this node has been clicked
        :param event:
        :param multi: assume multiple selection (append, don't replace)
        """
        self.hovering = False
        if (
            event and event.modifiers() == Qt.ShiftModifier) or multi:  #
            # multiple selection
            for node in ctrl.selected:
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
            editor = ctrl.ui.get_editing_node(self)
            ctrl.select(self)
            if editor and editor.isVisible():
                self.open_embed()

    def start_dragging(self, mx, my):
        """

        :param mx:
        :param my:
        """
        ctrl.dragged_focus = self
        ctrl.dragged_set = set()
        multidrag = False
        if ctrl.is_selected(self):
            for item in ctrl.selected:
                if item is not self and getattr(item, 'draggable', True):
                    item.add_to_dragged()
                    item.prepare_children_for_dragging()
                    multidrag = True
        self.prepare_children_for_dragging()
        self._fixed_position_before_dragging = self.fixed_position
        self._adjustment_before_dragging = self.adjustment
        self._distance_from_dragged = (
        self.current_position[0], self.current_position[1])

        ctrl.ui.prepare_touch_areas_for_dragging(drag_host=self,
                                                 moving=ctrl.dragged_set,
                                                 node_type=self.node_type,
                                                 multidrag=multidrag)
        self.start_moving()

    def add_to_dragged(self):
        """ Add this node to entourage of dragged node. These nodes will
        maintain their relative
         position to dragged node while dragging.
        :return: None
        """
        ctrl.dragged_set.add(self)
        dx, dy, dummy_z = ctrl.dragged_focus.current_position
        x, y, dummy_z = self.current_position
        self._fixed_position_before_dragging = self.fixed_position
        self._adjustment_before_dragging = self.adjustment
        self._distance_from_dragged = (x - dx, y - dy)

    def prepare_children_for_dragging(self):
        """ Implement this if structure is supposed to drag with the node
        :return:
        """
        pass

    def drag(self, event):
        """ Drags also elements that are counted to be involved: features,
        children etc
        :param event:
        """
        now_x, now_y = to_tuple(event.scenePos())
        if not ctrl.dragged_focus:
            self.start_dragging(now_x, now_y)
        # change dragged positions to be based on adjustment instead of
        # distance to main dragged.
        for node in ctrl.dragged_set:
            node.dragged_to(now_x, now_y)
        self.dragged_to(now_x, now_y)

    def dragged_to(self, now_x, now_y):
        """ Dragged focus is in now_x, now_y. Move there or to position
        relative to that
        :param now_x: current drag focus x
        :param now_y: current drag focus y
        :return:
        """
        if ctrl.dragged_focus is self:
            if self.can_adjust_position:
                ax, ay, az = self.algo_position
                self.adjustment = (now_x - ax, now_y - ay, az)
            else:
                self.fixed_position = (now_x, now_y, self.z)
        else:
            dx, dy = self._distance_from_dragged
            if self.can_adjust_position:
                ax, ay, az = self.algo_position
                self.adjustment = (now_x - ax + dx, now_y - ay + dy, az)
            else:
                self.fixed_position = (now_x + dx, now_y + dy, self.z)
        self.update_position(instant=True)

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
            if self.adjustment:
                message = 'adjusted node to {:.2f}, {:.2f}'.format(
                    self.adjustment[0], self.adjustment[1])

            elif self.fixed_position:
                message = 'moved node to {:.2f}, {:.2f}'.format(
                    self.fixed_position[0], self.fixed_position[1])
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
                node.finish_dragging()
            ctrl.dragged_set = set()
            ctrl.dragged_focus = None
        self._distance_from_dragged = None
        self._fixed_position_before_dragging = None
        self._adjustment_before_dragging = None
        self.effect.setEnabled(False)

    def cancel_dragging(self):
        """ Fixme: not called by anyone
        Revert dragged items to their previous positions.
        :return: None
        """
        self.adjustment = self._adjustment_before_dragging
        self.fixed_position = self._fixed_position_before_dragging
        self.update_position()
        for node in ctrl.dragged_set:
            node.cancel_dragging()
        if self is ctrl.dragged_focus:
            self.finish_dragging()

    def lock(self):
        """ Display lock, unless already locked. Added functionality to
        recognize the state before
         dragging started.
        :return:
        """
        super().lock()
        if not (
            self._fixed_position_before_dragging or
                    self._adjustment_before_dragging):
            ctrl.main.ui_manager.show_anchor(self)  # @UndefinedVariable

    # ### Mouse - Qt events ##################################################

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
        """ Dragging a foreign object (could be from ui) over a node, entering.
        :param event:
        """
        if event.mimeData().hasFormat(
                "application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
            self.hovering = True
        else:
            QtWidgets.QGraphicsItem.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        """ Dragging a foreign object (could be from ui) over a node, leaving.
        :param event:
        """
        if event.mimeData().hasFormat(
                "application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
            self.hovering = False
        else:
            QtWidgets.QGraphicsItem.dragLeaveEvent(self, event)

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
    folding_towards = Saved("folding_towards",
                            if_changed=if_changed_folding_towards)
    color_id = Saved("color_id")
    font_id = Saved("font_id")
