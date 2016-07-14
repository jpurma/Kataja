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

import kataja.globals as g
from kataja.SavedField import SavedSynField
from kataja.singletons import ctrl, classes
from kataja.saved.movables.Node import Node


# ctrl = Controller object, gives accessa to other modules
from kataja.uniqueness_generator import next_available_type_id


class BaseConstituentNode(Node):
    """ BaseConstituentNodes are minimal graphical representations of constituents.
    ConstituentNode -class inherits this and adds more elements and features, but if you want to
     create new kind of Constituents in syntax it may be cleaner to build on BaseConstituentNode
      and not ConstituentNode. """
    __qt_type_id__ = next_available_type_id()
    width = 20
    height = 20
    is_constituent = True
    node_type = g.CONSTITUENT_NODE
    wraps = 'constituent'

    viewable = {'label': {'order': 1}}
    editable = {'label': {'order': 1}}
    addable = {}



    # ConstituentNode position points to the _center_ of the node.
    # boundingRect should be (w/-2, h/-2, w, h)

    def __init__(self, syntactic_object=None, forest=None):
        """ Most of the initiation is inherited from Node """
        Node.__init__(self, syntactic_object=syntactic_object, forest=forest)

        # ------ Bracket drawing -------
        self.left_bracket = None
        self.right_bracket = None
        # ###
        self.selectable = True

        # ### Projection -- see also preferences that govern if these are used
        self.can_project = True
        self.projecting_to = set()

        # ## use update_visibility to change these: visibility of particular elements
        # depends on many factors
        self._visibility_brackets = 0

        #self.setAcceptDrops(True)

    @staticmethod
    def create_synobj(label, forest):
        """ ConstituentNodes are wrappers for Constituents. Exact
        implementation/class of constituent is defined in ctrl.
        :return:
        """
        if not label:
            label = forest.get_first_free_constituent_name()
        c = classes.Constituent(label)
        c.after_init()
        return c

    def load_values_from_parsernode(self, parsernode):
        """ Update constituentnode with values from parsernode
        :param parsernode:
        :return:
        """

        rows = parsernode.rows
        rowcount = len(rows)
        if rowcount > 0:
            self.label = rows[0]

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
        1st wave creates the objects and calls __init__, and then iterates through and sets the
        values.
        2nd wave calls after_inits for all created objects. Now they can properly refer to each
        other and know their
        values.
        :return: None
        """
        self.update_features()
        self.update_label()
        self.update_visibility()
        self.announce_creation()
        self._visibility_brackets = self.forest.settings.bracket_style
        self.forest.store(self)

    def after_model_update(self, updated_fields, update_type):
        """ This is called after the item's model has been updated, to run the side-effects of
        various
        setters in an order that makes sense.
        :param updated_fields: list of names of elements that have been updated.
        :return: None
        """
        super().after_model_update(updated_fields, update_type)
        if 'features' in updated_fields:
            self.update_features()

    # properties implemented by syntactic node
    # set_hooks, to be run when values are set

    def if_changed_features(self, value):
        """ Synobj changed, but remind to update label here
        :param value:
        :return:
        """
        self.update_features()

    # Other properties

    def update_status_tip(self):
        """ Hovering status tip """
        if self.syntactic_object:
            if self.is_leaf(only_similar=True, only_visible=False):
                name = "Leaf constituent"
            elif self.is_top_node():
                name = "Root constituent"
            else:
                name = "Inner constituent"
            self.status_tip = "%s %s" % (name, self.label)
        else:
            self.status_tip = "Empty, but mandatory constituent position"

    def __str__(self):
        if not self.syntactic_object:
            return 'const with missing synobj'
        else:
            l = str(self.label)
            if l:
                return "constituent '%s'" % l
            else:
                return "anonymous constituent"

    def as_bracket_string(self):
        """ returns a simple bracket string representation """
        if not self.syntactic_object:
            return '0'
        inside = ' '.join((x.as_bracket_string() for x in self.get_children()))
        if inside:
            return '[ ' + inside + ' ]'
        else:
            return str(self.syntactic_object)

    def get_ordered_children(self):
        """ Return children by using the ordering method from syntax.

        fixme: A nice behavior would be to return list when children can be ordered and set when
        they cannot be.

        :return:
        """
        children = []
        if self.syntactic_object:
            if hasattr(self.syntactic_object, 'ordered_parts'):
                children += self.syntactic_object.ordered_parts()
            if hasattr(self.syntactic_object, 'ordered_features'):
                children += self.syntactic_object.ordered_features()
        nodes = []
        for child in children:
            node = ctrl.forest.get_node(child)
            if node:
                nodes.append(node)
        return nodes

    def get_attribute_nodes(self, label_key=''):
        """

        :param label_k ey:
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
        """ Compute visibility-related attributes for this constituent node and update those that
        depend on this -- meaning features etc.

        :param kw:
        """
        was_visible = self.is_visible()
        visible = not (self.folded_away or self.folding_towards)

        # Fade in / out
        fade = kw.get('fade', False)
        if fade:
            if visible and not was_visible:
                self.fade_in()
            elif (not visible) and was_visible:
                self.fade_out()
        else:
            self.setVisible(visible)
        # Label
        self.update_label_visibility()

        # ## Edges -- these have to be delayed until all constituents etc nodes know if they are
        # visible
        self.forest.order_edge_visibility_check()

        # ## FeatureNodes
        # self.forest.settings.draw_features
        feat_visible = visible and self.forest.settings.feature_nodes

        if feat_visible and not was_visible:
            for feature in self.get_features():
                feature.setVisible(True)
        elif was_visible and not feat_visible:
            for feature in self.get_features():
                feature.setVisible(False)

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
        """ Creates left and right brackets for node, depending on active bracket style.


        """

        def add_left():
            if not self.left_bracket:
                self.left_bracket = f.create_bracket(host=self, left=True)

        def add_right():
            if not self.right_bracket:
                self.right_bracket = f.create_bracket(host=self, left=False)

        def del_left():
            if self.left_bracket:
                f.bracket_manager.delete_bracket(self.left_bracket)
                self.left_bracket = None

        def del_right():
            if self.right_bracket:
                f.bracket_manager.delete_bracket(self.right_bracket)
                self.right_bracket = None

        f = self.forest
        bs = f.settings.bracket_style
        if bs == g.ALL_BRACKETS:
            if list(self.get_children()):
                add_left()
                add_right()
            else:
                del_left()
                del_right()
        elif bs == g.MAJOR_BRACKETS:
            should_have = False
            for parent in self.get_parents(only_visible=True, only_similar=True):
                if self == parent.get_ordered_children()[0]:
                    should_have = True
                    break
            if should_have:
                add_left()
                add_right()
            else:
                del_left()
                del_right()
        elif bs == g.NO_BRACKETS:
            del_left()
            del_right()

    # ### Features #########################################

    # !!!! Shouldn't be done this way. In forest, create a feature, then connect it to
    # ConstituentNode and let Forest's
    # methods to take care that syntactic parts are reflected properly. ConstituentNode shouldn't
    #  be modifying its
    # syntactic component.
    # def set_feature(self, syntactic_feature=None, key=None, value=None, string=''):
    #     """ Convenience method for assigning a new feature node related to this constituent.
    #     can take syntactic feature, which is assumed to be already assigned for the syntactic
    # constituent.
    #         Can take key, value pair to create new syntactic feature object, and then a proper
    # feature object is created from this.
    #     :param syntactic_feature:
    #     :param key:
    #     :param value:
    #     :param string:
    #     """
    #     assert self.syntactic_object
    #     if syntactic_feature:
    #         if ctrl.forest.settings.draw_features:
    #             ctrl.forest.create_feature_node(self, syntactic_feature)
    #     elif key:
    #         sf = self.syntactic_object.set_feature(key, value)
    #         self.set_feature(syntactic_feature=sf)
    #     elif string:
    #         features = ctrl.forest.parse_features(string, self)
    #         if 'gloss' in features:
    #             self.gloss = features['gloss']
    #             del features['gloss']
    #         for feature in features.values():
    #             self.set_feature(syntactic_feature=feature)
    #         self.update_features()


    def get_features(self):
        """ Returns FeatureNodes """
        return self.get_children_of_type(edge_type=g.FEATURE_EDGE)

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
        """ Empty nodes can be used as placeholders and deleted or replaced without structural
        worries """
        return (not self.label) and self.is_leaf(only_similar=True, only_visible=False)

    def get_features_as_string(self):
        """


        :return:
        """
        features = [f.syntactic_object for f in self.get_features()]
        feature_strings = [str(f) for f in features]
        return ', '.join(feature_strings)

    # ## Multidomination #############################################

    def is_multidominated(self):
        """ Check if the ConstituentNode has more than one parent. """
        return len(self.get_parents()) > 1

    def get_c_commanded(self):
        """ Returns the closest c-commanded elements of this element. All dominated by those are
        also c-commanded """
        result = []
        for parent in self.get_parents():
            for child in parent.get_children():
                if child is not self:
                    result.append(child)
        return result

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
        if edge.edge_type is not g.CONSTITUENT_EDGE:
            # We care only for constituent relations
            return
        assert edge.end is self
        s = edge.start
        if s and s.node_type == g.CONSTITUENT_NODE and s.syntactic_object:
            # Calling syntax!
            parent = s.syntactic_object
            child = self.syntactic_object
            if child not in parent.parts:
                ctrl.FL.k_connect(parent, child)
                print('making syntactic connection for constituent')

    def disconnect_in_syntax(self, edge):
        """ Implement this if disconnecting this node (using this edge) needs
        to be reflected in syntax. Remember to verify it already isn't there.
        :param edge:
        :return:
        """
        if edge.edge_type is not g.CONSTITUENT_EDGE:
            # We care only for constituent relations
            return
        assert edge.end is self
        s = edge.start
        if s and s.node_type == g.CONSTITUENT_NODE and s.syntactic_object:
            # Calling syntax!
            parent = s.syntactic_object
            child = self.syntactic_object
            if child in parent.parts:
                ctrl.FL.k_disconnect(parent, child)

    # ## Qt overrides ######################################################################

    def fpaint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        """
        painter.setPen(self.contextual_color)
        if ctrl.pressed == self:
            rect = True
        elif self._hovering:
            rect = True
        elif ctrl.is_selected(self):
            rect = True
        elif self.left_bracket:
            rect = False
        else:
            rect = False
        if rect:
            painter.drawRoundedRect(self.inner_rect, 5, 5)
            # if self.uses_scope_area:
            # self.paint_scope_rect(painter, rect)
            # Node.paint(self, painter, option, widget)

    # ### Selection ########################################################

    def update_selection_status(self, selected):
        """

        :param selected:
        """

        super().update_selection_status(selected)
        if ctrl.cm.use_glow():
            self.effect.setEnabled(selected)
            self.update()

    # ### Checks for callable actions ####

    def can_top_merge(self):
        """
        :return:
        """
        top = self.get_top_node()
        return self is not top and self not in top.get_children()

    # ### Dragging #####################################################################

    # ## Most of this is implemented in Node

    def start_dragging_tracking(self, host=False, scene_pos=None):
        """ Drag the node stack with me
        :param host:
        :param scene_pos:
        :return:
        """
        super().start_dragging_tracking(host=host, scene_pos=scene_pos)
        for node in self.children():
            if node.locked_to_node == self:
                node.start_dragging_tracking(host=False, scene_pos=scene_pos)

    def prepare_children_for_dragging(self, scene_pos):
        """ Implement this if structure is supposed to drag with the node
        :return:
        """
        children = self.forest.list_nodes_once(self)

        for tree in self.trees:
            dragged_index = tree.sorted_constituents.index(self)
            for i, node in enumerate(tree.sorted_constituents):
                if node is not self and i > dragged_index and node in children:
                    node.start_dragging_tracking(host=False, scene_pos=scene_pos)
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
        if value and not self._hovering:
            self._start_hover()
        elif self._hovering and not value:
            self._stop_hover()

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # Attributes from synobj and their setter hooks
    label = SavedSynField("label")
    features = SavedSynField("features", if_changed=if_changed_features)
