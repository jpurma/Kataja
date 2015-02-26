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

from PyQt5 import QtGui

from kataja.singletons import ctrl
from kataja.Node import Node
from kataja.utils import to_tuple
import kataja.globals as g
from kataja.parser import KatajaNodeToINode

# ctrl = Controller object, gives accessa to other modules

TRIANGLE_HEIGHT = 10


class ConstituentNode(Node):
    """ ConstituentNodes are graphical representations of constituents. They are primary objects and need to support saving and loading."""
    width = 20
    height = 20
    default_edge_type = g.CONSTITUENT_EDGE
    receives_signals = []
    node_type = g.CONSTITUENT_NODE



    # ConstituentNode position points to the _center_ of the node.
    # boundingRect should be (w/-2, h/-2, w, h)

    def __init__(self, constituent=None):
        """ Most of the initiation is inherited from Node """
        Node.__init__(self, syntactic_object=constituent)
        self.saved.is_trace = False
        self.saved.triangle = False
        self.saved.merge_order = 0
        self.saved.select_order = 0
        self.saved.original_parent = None

        # ------ Bracket drawing -------
        self.has_visible_brackets = False
        self.left_bracket = None
        self.right_bracket = None
        # ###
        self.selectable = True

        # ### Projection -- see also preferences that govern if these are used
        self.can_project = True
        self.projecting_to = set()

        # ### Cycle index stores the order when node was originally merged to structure.
        # going up in tree, cycle index should go up too

        # ## use update_visibility to change these: visibility of particular elements
        # depends on many factors
        if ctrl.forest:
            self._visibility_brackets = ctrl.forest.settings.bracket_style
        else:
            self._visibility_brackets = 0

        self.setAcceptDrops(True)
        self.update_status_tip()

    def after_init(self):
        """ Call after putting values in place
        :return:
        """
        self.update_features()
        self.update_gloss()
        self.update_label()
        self.update_visibility()
        ctrl.forest.store(self)

    # properties implemented by syntactic node

    @property
    def alias(self):
        """:return:  """
        if self.syntactic_object:
            return self.syntactic_object.alias

    @alias.setter
    def alias(self, value):
        """
        :param value:  """
        if self.syntactic_object:
            self.syntactic_object.alias = value
            self._inode_changed = True

    @property
    def index(self):
        if self.syntactic_object:
            return self.syntactic_object.index

    @index.setter
    def index(self, value):
        if value is None:
            value = ""
        self.syntactic_object.index = value
        self._inode_changed = True

    @property
    def gloss(self):
        if self.syntactic_object:
            return self.syntactic_object.gloss

    @gloss.setter
    def gloss(self, value):
        if value is None:
            value = ""
        if self.syntactic_object:
            self.syntactic_object.gloss = value
        self._inode_changed = True
        self.update_gloss()

    @property
    def features(self):
        if self.syntactic_object:
            return self.syntactic_object.features

    @features.setter
    def features(self, value):
        if value is None:
            value = []
        if self.syntactic_object:
            self.syntactic_object.features = value
        self._inode_changed = True
        self.update_features()

    # Saved properties

    @property
    def is_trace(self):
        """:return:  """
        return self.saved.is_trace

    @is_trace.setter
    def is_trace(self, value):
        """
        :param value:  """
        if value is None:
            value = False
        self.saved.is_trace = value

    @property
    def original_parent(self):
        """ When switching between multidomination and traces, original parent may be needed.
        :return:
        """
        return self.saved.original_parent


    @original_parent.setter
    def original_parent(self, value):
        """
        :param value:
        :return:
        """
        self.saved.original_parent = value

    @property
    def triangle(self):
        """:return:  """
        return self.saved.triangle

    @triangle.setter
    def triangle(self, value):
        """
        :param value:  """
        if value is None:
            value = False
        self.saved.triangle = value
        # update label positioning here so that offset doesn't need to be stored in save files and it
        # still will be updated correctly
        if self._label_complex:
            if value:
                self._label_complex.y_offset = TRIANGLE_HEIGHT
            else:
                self._label_complex.y_offset = 0
            self.update_label()

    @property
    def merge_order(self):
        """:return:  """
        return self.saved.merge_order

    @merge_order.setter
    def merge_order(self, value):
        """
        :param value:  """
        if value is None:
            value = 0
        self.saved.merge_order = value

    @property
    def select_order(self):
        """:return:  """
        return self.saved.select_order

    @select_order.setter
    def select_order(self, value):
        """
        :param value:  """
        if value is None:
            value = 0
        self.saved.select_order = value

    # Other properties

    @property
    def gloss_node(self):
        """
        :return:
        """
        gl = self.get_children(edge_type=g.GLOSS_EDGE)
        if gl:
            return gl[0]

    @property
    def raw_alias(self):
        """ Get the unparsed raw version of label (str)
        :return:
        """
        return self.alias

    @property
    def as_inode(self):
        """
        :return: INodes or str or tuple of them
        """
        if self._inode_changed:
            self._inode = KatajaNodeToINode.constituentnode_to_iconstituentnode(self, children=False)
        return self._inode


    def update_status_tip(self):
        if self.syntactic_object:
            if self.alias:
                alias = '"%s" ' % self.alias
            else:
                alias = ''
            if self.is_trace:
                name = "Trace"
            if self.is_leaf_node():
                name = "Leaf constituent"
            elif self.is_root_node():
                name = "Root constituent"
            else:
                name = "Inner constituent"
            self.status_tip = "%s %s%s" % (name, alias, self.label)
        else:
            self.status_tip = "Empty, but mandatory constituent position"

    def __str__(self):
        if not self.syntactic_object:
            return 'Placeholder node'
        alias = str(self.alias)
        label = str(self.label)
        if alias and label:
            return ' '.join((alias, label))
        else:
            return alias or label


    def as_bracket_string(self):
        """ returns a simple bracket string representation """
        if not self.syntactic_object:
            return '0'
        children = self.get_children()
        if children:
            if self.alias and len(children) == 2:
                return '[.%s %s %s ]' % (self.alias, children[0].as_bracket_string(), children[1].as_bracket_string())
            elif len(children) == 2:
                return '[ %s %s ]' % (children[0].as_bracket_string(), children[1].as_bracket_string())
            else:
                return '[ %s ]' % children[0].as_bracket_string()
        else:
            return self.alias or self.syntactic_object


    def is_placeholder(self):
        """ Constituent structure may assume a constituent to be somewhere, before the user has intentionally created
        one there. These are shown as placeholders, which are nodes, but with limited presence.
        :return: boolean
        """
        return not self.syntactic_object

    def info_dump(self):
        """


        """
        print('---- %s ----' % self.save_key)
        print('| scene: %s' % self.scene())
        print('| isVisible: %s' % self.isVisible())
        print('| print: %s ' % self)
        print('| x: %s y: %s z: %s' % self.current_position)
        print('| adjustment: x: %s y: %s z: %s ' % self.adjustment)
        print('| computed x: %s y: %s z: %s' % self.computed_position)
        print('| final: x: %s y: %s z: %s ' % self.final_position)
        print('| bind x: %s y: %s z: %s' % (self.bind_x, self.bind_y, self.bind_z))
        print('| locked_to_position: %s ' % self.locked_to_position)
        print('| label rect: ', self.label_rect)
        print('| index: %s' % self.index)
        print('| edges up:', self.edges_up)
        print('| edges down:', self.edges_down)
        if self.syntactic_object:
            print('| syntactic_object:_________________')
            print(self.syntactic_object.__repr__())
        else:
            print('Empty placeholder')
        print('----------------------------------')


    def get_attribute_nodes(self, label_key=''):
        """

        :param label_key:
        :return:
        """
        atts = [x.end for x in self.edges_down if x.edge_type == g.ATTRIBUTE_EDGE]
        if label_key:
            for a in atts:
                if a.attribute_label == label_key:
                    return a
        else:
            return atts

    def update_visibility(self, **kw):
        """

        :param kw:
        """
        # print("For node %s: %s" % (self, str(kw)))
        self._visibility_brackets = kw.get('brackets', self._visibility_brackets)
        was_visible = self.visible
        visible = not self.folded_away
        self.visible = visible


        ### Fade in / out
        fade = kw.get('fade', False)
        if fade:
            if visible:
                self.fade_in()
            else:
                self.fade_out()
        else:
            self.setVisible(visible)
        ### Label

        label_mode = ctrl.forest.settings.label_style
        if label_mode == g.ALL_LABELS:
            self._label_visible = True
        elif label_mode == g.ALIASES and self.alias:
            self._label_visible = True
        elif self.triangle:
            self._label_visible = True
        elif self.label and self.is_leaf_node():
            self._label_visible = True
        else:
            self._label_visible = False
        if not self._label_complex:
            self.update_label()
        self._label_complex.setVisible(self._label_visible)

        ### Edges
        ctrl.forest.adjust_edge_visibility_for_node(self, visible)

        ### FeatureNodes
        # ctrl.forest.settings.draw_features
        feat_visible = visible and ctrl.forest.settings.draw_features

        if (feat_visible and not was_visible):
            for feature in self.get_features():
                feature.setVisible(True)
        elif (was_visible and not feat_visible):
            for feature in self.get_features():
                feature.setVisible(False)

        ### Brackets
        if self._visibility_brackets:
            if self._visibility_brackets == 2:
                self.has_visible_brackets = not self.is_leaf_node()
            elif self._visibility_brackets == 1:
                is_left = False
                for edge in self.get_edges_up():
                    if edge.align == 1:  # LEFT
                        is_left = True
                        break
                self.has_visible_brackets = is_left
        else:
            self.has_visible_brackets = False
        if self.left_bracket:
            self.left_bracket.setVisible(self.has_visible_brackets)
        if self.right_bracket:
            self.right_bracket.setVisible(self.has_visible_brackets)

    def reset(self):
        """


        """
        Node.reset(self)
        # self.uses_scope_area = False
        # self.has_visible_brackets = False
        # self.boundingRect(update = True)


    # ### Parents & Children ####################################################


    def is_projecting_to(self, other):
        """

        :param other:
        """
        pass

    def rebuild_brackets(self):
        """


        """
        if self.left():
            if not self.left_bracket:
                self.left_bracket = ctrl.forest.create_bracket(host=self, left=True)
        else:
            self.left_bracket = None
        if self.right():
            if not self.right_bracket:
                self.right_bracket = ctrl.forest.create_bracket(host=self, left=False)
        else:
            self.right_bracket = None

    # ### Features #########################################


    # !!!! Shouldn't be done this way. In forest, create a feature, then connect it to ConstituentNode and let Forest's
    # methods to take care that syntactic parts are reflected properly. ConstituentNode shouldn't be modifying its
    # syntactic component.
    def set_feature(self, syntactic_feature=None, key=None, value=None, string=''):
        """ Convenience method for assigning a new feature node related to this constituent.
        can take syntactic feature, which is assumed to be already assigned for the syntactic constituent.
            Can take key, value pair to create new syntactic feature object, and then a proper feature object is created from this.
        :param syntactic_feature:
        :param key:
        :param value:
        :param string:
        """
        assert (self.syntactic_object)
        if syntactic_feature:
            if ctrl.forest.settings.draw_features:
                ctrl.forest.create_feature_node(self, syntactic_feature)
        elif key:
            sf = self.syntactic_object.set_feature(key, value)
            self.set_feature(syntactic_feature=sf)
        elif string:
            features = ctrl.forest.parse_features(string, self)
            if 'gloss' in features:
                self.gloss = features['gloss']
                del features['gloss']
            for feature in features.values():
                self.set_feature(syntactic_feature=feature)
            self.update_features()

    def update_gloss(self):
        """


        """
        if not self.syntactic_object:
            return
        syn_gloss = self.gloss
        gloss_node = self.gloss_node
        if gloss_node and not syn_gloss:
            ctrl.forest.delete_node(gloss_node)
        elif syn_gloss and not gloss_node:
            ctrl.forest.create_gloss_node(self)
        elif syn_gloss and gloss_node:
            gloss_node.update_label()


    def get_features(self):
        """ Returns FeatureNodes """
        return self.get_children(edge_type=g.FEATURE_EDGE)

    def update_features(self):
        """


        """
        pass
        # if not self.syntactic_object:
        # return
        # current_features = set([x.syntactic_object.get() for x in self.get_features()])
        # correct_features = self.syntactic_object.features
        # print(current_features, correct_features)
        # for key, item in correct_features.items():
        # if key not in current_features:
        # self.set_feature(syntactic_feature=item, key=key)
        # else:
        # current_features.remove(key)
        # if current_features:
        # print('leftover features:', current_features)


    # ### Labels #############################################


    # things to do with traces:
    # if renamed and index is removed/changed, update chains
    # if moved, update chains
    # if copied, make sure that copy isn't in chain
    # if deleted, update chains
    # any other operations?

    def is_empty_node(self):
        """ Empty nodes can be used as placeholders and deleted or replaced without structural worries """
        return (not (self.alias or self.label or self.index)) and self.is_leaf_node()


    def get_features_as_string(self):
        """


        :return:
        """
        features = [f.syntactic_object for f in self.get_features()]
        feature_strings = [str(f) for f in features]
        return ', '.join(feature_strings)


    # ## Indexes and chains ###################################

    def is_chain_head(self):
        """


        :return:
        """
        if self.index:
            return not (self.is_leaf_node() and self.label == 't')
        return False

    # ### Folding / Triangles #################################


    def prepare_to_be_folded(self, triangle):
        """ Initialize move to triangle's position and make sure that move is not
        :param triangle:
        interrupted  """
        # print u'node %s preparing to collapse to %s at %s' % (self, triangle, triangle.target_position )
        self.folding_towards = triangle  # folding_towards should override other kinds of movements
        self.after_move_function = self.finish_folding
        tx, ty, tz = triangle.computed_position
        self.adjustment = triangle.adjustment
        self.computed_position = (tx, ty + 30, tz)  # , fast = True)
        # for feature in self.features:
        # feature.fade_out()

    def finish_folding(self):
        """ Hide, and remember why this is hidden """
        self.folded_away = True
        self.update_visibility()
        self.update_bounding_rect()


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


    # ## Multidomination #############################################


    def is_multidominated(self):
        """ Check if the ConstituentNode has more than one parent. """
        return len(self.get_parents()) > 1

    def get_c_commanded(self):
        """ Returns the closest c-commanded elements of this element. All dominated by those are also c-commanded """
        result = []
        for parent in self.get_parents():
            for child in parent.get_children():
                if child is not self:
                    result.append(child)
        return result


    # ## Qt overrides ######################################################################

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        """
        painter.setPen(self.contextual_color())
        if ctrl.pressed == self:
            rect = True
        elif self._hovering:
            rect = True
        elif ctrl.is_selected(self):
            rect = True
        elif self.has_visible_brackets:
            rect = False
        else:
            rect = False
        if self.triangle:
            self.paint_triangle(painter)
        elif rect:
            painter.drawRect(self.inner_rect)
            # if self.uses_scope_area:
            # self.paint_scope_rect(painter, rect)

    # def itemChange(self, change, value):
    # """ Whatever menus or UI objects are associated with object, they move
    # :param change:
    # :param value:
    # when node moves """
    # if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
    # #if self.ui_menu and self.ui_menu.isVisible():
    # #    self.ui_menu.update_position(drag=True)
    # if self._hovering or ctrl.focus == self:
    # pass
    # # print 'ctrl.ui problem here!'
    # # assert(False)
    # # if ctrl.ui.is_target_reticle_over(self):
    # # ctrl.ui.update_target_reticle_position()
    # return QtWidgets.QGraphicsItem.itemChange(self, change, value)



    def open_embed(self):
        """


        """
        ctrl.ui.start_constituent_editing(self)


    #### Selection ########################################################

    def refresh_selection_status(self, selected):
        """

        :param selected:
        """
        self.update()


    #### Checks for callable actions ####

    def can_root_merge(self):
        """


        :return:
        """
        root = self.get_root_node()
        return self is not root and self is not root.left(only_visible=False)


    #### Dragging #####################################################################

    # ## Some of this needs to be implemented further down in constituentnode-node-movable -inheritance

    def start_dragging(self, mx, my):
        """

        :param mx:
        :param my:
        """
        if ctrl.is_selected(self):
            drag_hosts = ctrl.get_all_selected()
        else:
            drag_hosts = [self]
        ctrl.dragged = set()

        # there if node is both above and below the dragged node, it shouldn't move
        for drag_host in drag_hosts:
            root = drag_host.get_root_node()
            nodes = ctrl.forest.list_nodes_once(root)
            drag_host_index = nodes.index(drag_host)
            dx, dy, dummy_z = drag_host.current_position
            for node in ctrl.forest.list_nodes_once(drag_host, only_visible=True):
                if nodes.index(node) >= drag_host_index:
                    ctrl.dragged.add(node)
                    x, y, dummy_z = node.current_position
                    node._position_before_dragging = node.current_position
                    node._adjustment_before_dragging = node.adjustment or (0, 0, 0)
                    node._distance_from_dragged = (x - dx, y - dy)
        if len(drag_hosts) == 1:  # don't allow merge if this is multidrag-situation
            ctrl.forest.prepare_touch_areas_for_dragging(excluded=ctrl.dragged)

    def drag(self, event):
        """ Drags also elements that are counted to be involved: features, children etc
        :param event:
        """
        pos = event.scenePos()
        now_x, now_y = to_tuple(pos)
        if not getattr(ctrl, 'dragged', None):
            self.start_dragging(now_x, now_y)

        # change dragged positions to be based on adjustment instead of distance to main dragged.
        for node in ctrl.dragged:
            dx, dy = node._distance_from_dragged
            px, py, pz = node._position_before_dragging
            if node.can_adjust_position:
                ax, ay, az = node._adjustment_before_dragging
                diff_x = now_x + dx - px - ax
                diff_y = now_y + dy - py - ay
                node.adjustment = (diff_x, diff_y, az)
            else:
                node.computed_position = (now_x + dx, now_y + dy, pz)
            # try:
            # assert (int(px - ax) == int(node._computed_position[0])) # position without adjustment
            # except AssertionError:
            # print 'Assertion error:'
            # print px - ax, py - ay, node._computed_position
            node.current_position = (now_x + dx, now_y + dy, pz)

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
        del self._distance_from_dragged
        ctrl.dragged = set()
        ctrl.dragged_positions = set()
        ctrl.main.action_finished('moved node %s' % self)
        # ctrl.scene.fit_to_window()

    def cancel_dragging(self):
        """


        """
        assert False
        sx, sy = self._before_drag_position
        z = self.current_position[2]
        self.computed_position = (sx, sy, z)
        for node, x, y in ctrl.dragged_positions:
            z = node.current_position[2]
            node.computed_position = (sx + x, sy + y, z)
        del self.before_drag_position
        ctrl.dragged = set()
        ctrl.dragged_positions = set()

    #################################

    @property
    def hovering(self):
        """


        :return:
        """
        return self._hovering

    @hovering.setter
    def hovering(self, value):
        """ Toggle hovering effects
        Overrides Node.set_hovering.
        :param value: bool
        :return:
        """
        if self.left_bracket:
            self.left_bracket.hovering = value
        if self.right_bracket:
            self.right_bracket.hovering = value
        self._set_hovering(value)

    # ### Suggestions for completing missing aspects (active for selected nodes) ######################################

    def add_completion_suggestions(self):
        """ Node has selected and if it is a placeholder or otherwise lacking, it may suggest an
         option to add a proper node here.
        """
        if self.is_placeholder():
            ctrl.ui.create_touch_area(self, g.TOUCH_ADD_CONSTITUENT)


    def dropEvent(self, event):
        """

        :param event:
        """
        print("CN dropEvent")


