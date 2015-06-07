# -*- coding: UTF-8 -*-
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


import string
import collections

from kataja.errors import ForestError
import kataja.ForestSyntax as ForestSyntax
from kataja.debug import forest
from kataja.ForestSettings import ForestSettings, ForestRules
from kataja.Bracket import Bracket
from kataja.BracketManager import BracketManager
from kataja.ConstituentNode import ConstituentNode
from kataja.AttributeNode import AttributeNode
from kataja.CommentNode import CommentNode
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.ChainManager import ChainManager
from kataja.DerivationStep import DerivationStepManager
from kataja.GlossNode import GlossNode
from kataja.Node import Node
from kataja.parser.INodeToKatajaConstituent import INodeToKatajaConstituent
from kataja.Presentation import TextArea, Image
from kataja.Edge import Edge
from kataja.UndoManager import UndoManager
from kataja.utils import to_tuple, caller
from kataja.FeatureNode import FeatureNode
from kataja.BaseModel import BaseModel, Saved
import kataja.globals as g

ONLY_LEAF_LABELS = 0
ALL_LABELS = 1
ALIASES = 2


class Forest(BaseModel):
    """ Forest is a group of trees that together form one view.
    Often there needs to be more than one tree visible at same time,
     so that they can be compared or to show states of construction
      where some edges are not yet linked to the main root.
      Forest is the container for these.
      Forest also takes care of the operations manipulating, creating and
      removing trees. """

    short_name = "Fore"

    def __init__(self, buildstring='', definitions=None, gloss_text='', comments=None):
        """ Create an empty forest """
        super().__init__()
        self.nodes_from_synobs = {}
        self.main = ctrl.main
        self.main.forest = self  # assign self to be the active forest while creating the managers.
        self.in_display = False
        self.visualization = None
        self.gloss = None
        self.bracket_manager = BracketManager(self)
        self.parser = INodeToKatajaConstituent(self)
        self.undo_manager = UndoManager(self)
        self.chain_manager = ChainManager(self)
        self.settings = ForestSettings()
        self.rules = ForestRules()
        self.derivation_steps = DerivationStepManager()
        self.roots = []  # the current line of trees
        self.nodes = {}
        self.edges = {}
        self.others = {}
        self.vis_data = {}
        self.merge_counter = 0
        self.select_counter = 0
        self.comments = []
        self.gloss_text = ''

        if buildstring:
            self.create_tree_from_string(buildstring)
        if definitions:
            self.read_definitions(definitions)
        if gloss_text:
            self.gloss_text = gloss_text
        if comments:
            self.comments = comments

        # Update request flags
        self._do_edge_visibility_check = False

    def after_model_update(self, updated_fields, update_type):
        """ This is called after the item's model has been updated (e.g. by undo),
        to run the side-effects of various setters in an order that makes sense.
        :param update_type:
        :param updated_fields: list of names of fields that have been updated.
        :return: None
        """
        if 'nodes' in updated_fields:
            # rebuild from-syntactic_object-to-node -dict
            self.nodes_from_synobs = {}
            for node in self.nodes.values():
                if node.syntactic_object:
                    self.nodes_from_synobs[node.syntactic_object.save_key] = node


    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
            1st wave creates the objects and calls __init__, and then iterates through and sets the values.
            2nd wave calls after_inits for all created objects. Now they can properly refer to each other and know their
                values.
        :return: None
        """
        #print('created a forest %s , its traces should be visible: %s ' % (self, self.traces_are_visible()))
        pass
        # self.bracket_manager.rebuild_brackets()
        # for node in self.nodes.values():
        # if node.syntactic_object:
        # self.nodes_by_uid[node.syntactic_object.save_key] = node


    @property
    def scene(self):
        """ Return the graphics scene where objects are stored and drawn.
        :return: GraphScene instance
        """
        return self.main.graph_scene

    def prepare_for_drawing(self):
        """ Prepares the forest instance to be displayed in graph scene --
         called when switching forests
        :return: None
        """
        self.in_display = True
        ctrl.undo_disabled = True
        self.update_colors()
        self.add_all_to_scene()
        self.update_visualization()
        self.scene.manual_zoom = False
        ctrl.ui.update_all_fields()
        self.draw()  # do draw once to avoid having the first draw in undo stack.
        ctrl.undo_disabled = False

    def retire_from_drawing(self):
        """ Announce that this forest should not try to work with scene anymore --
         some other forest is occupying the scene now.
        :return:
        """
        scene = self.scene
        for item in self.get_all_objects():
            if item.scene() is scene:
                scene.removeItem(item)
        self.in_display = False

    def traces_are_visible(self):
        """ Helper method for checking if we need to deal with chains
        :return:
        """
        return not self.settings.uses_multidomination

    # @time_me
    def list_nodes(self, first):
        """
        Do left-first iteration through all nodes. Can become quite large if there is lots of multidomination.
        :param first: Node, can be started from a certain point in structure
        :return: list of nodes
        """
        res = []
        assert(first.save_key in self.nodes)

        def _iterate(node):
            res.append(node)
            l = node.left()
            if l:
                _iterate(l)
            r = node.right()
            if r:
                _iterate(r)

        _iterate(first)
        return res

    # @time_me
    def list_nodes_once(self, first, only_visible=True):
        """
        Do left-first iteration through all nodes and return a list where only first instance of each node is present.
        :param first: Node, can be started from a certain point in structure
        :param only_visible:
        :return: list of nodes
        """
        res = []
        assert(first.save_key in self.nodes)

        def _iterate(node):
            if node not in res:
                res.append(node)
                l = node.left(only_visible=only_visible)
                if l:
                    _iterate(l)
                r = node.right(only_visible=only_visible)
                if r:
                    _iterate(r)

        _iterate(first)
        return res

    def info_dump(self):
        """
        Show debug info about forest in console
        """
        if hasattr(self, 'save_key'):
            print('----- Forest %s ------' % self.save_key)
            print('| Nodes: %s' % len(self.nodes))
            print('| Edges: %s' % len(self.edges))
            print('| Others: %s' % len(self.others))
            print('| Visualization: ', self.visualization)
            print('| Color scheme: ', self.settings.hsv)
        else:
            print('odd forest, not initialized.')

    def visible_nodes(self):
        """ Any node that is visible. Ignore the type.
        :return:
        """
        return [x for x in self.nodes.values() if x.is_visible]

    def update_forest_gloss(self):
        """ Draw the gloss text on screen, if it exists. """
        if self.gloss_text:
            if prefs.show_gloss_text:
                if not self.gloss:
                    self.gloss = self.create_gloss_node(label=self.gloss_text)
            elif self.gloss:
                self.scene.removeItem(self.gloss)
                self.gloss = None
        elif self.gloss:
            self.scene.removeItem(self.gloss)
            self.gloss = None

    @caller
    def change_visualization(self, name):
        """ Switches the active visualization to visualization with given key
        :param key: string
        """
        print('changing visualization to ', name)
        if self.visualization and self.visualization.say_my_name() == name:
            self.visualization.reselect()
        else:
            vs = self.main.visualizations
            self.visualization = vs.get(name, vs.get(prefs.default_visualization, None))
            self.vis_data = {'name': self.visualization.say_my_name()}

            self.visualization.prepare(self)
        self.main.graph_scene.manual_zoom = False

    def update_visualization(self):
        """ Verify that the active visualization is the same as defined in the vis_data (saved visualization state)
        :return: None
        """
        name = self.vis_data.get('name', None)
        if (not self.visualization) or name != self.visualization.say_my_name():
            self.change_visualization(name)

    # ### Maintenance and support methods ################################################

    def __iter__(self):
        return self.roots.__iter__()

    def textual_form(self, root=None):
        """ return (unicode) version of linearizations of all trees with traces removed --
            as close to original sentences as possible. If root is given, return linearization of only that.
        :param root:
        """

        def _tree_as_text(root_node, gap):
            """ Cheapo linearization algorithm for Node structures."""
            l = []
            for node in self.list_nodes_once(root_node):
                l.append(str(node.syntactic_object))
            return gap.join(l)

        if root:
            return _tree_as_text(root, ' ')
        else:
            roots = []
            for root in self.roots:
                roots.append(_tree_as_text(root, ' '))
            return '/ '.join(roots)

    def syntax_trees_as_string(self):
        """


        :return:
        """
        s = []
        for root in self.roots:
            s.append(root.syntactic_object.print_tree())
        return '\n'.join(s)

    def store(self, item):
        """ Confirm that item is stored in some dictionary or other storage in forest
        :param item:
        """
        # if isinstance(item, ConstituentNode):
        # self.nodes[item.key] = item
        # elif isinstance(item, FeatureNode):
        # self.features[item.key] = item

        if isinstance(item, Node):
            self.poke('nodes')
            self.nodes[item.save_key] = item
            if item.syntactic_object:
                # remember to rebuild nodes_by_uid in undo/redo, as it is not stored in model
                self.nodes_from_synobs[item.syntactic_object.save_key] = item
        elif isinstance(item, Edge):
            self.poke('edges')
            self.edges[item.save_key] = item
        elif isinstance(item, TextArea):
            self.poke('others')
            self.others[item.save_key] = item
        elif isinstance(item, Bracket):
            self.bracket_manager.store(item)

        else:
            key = getattr(item, 'save_key', '') or getattr(item, 'key', '')
            if key and key not in self.others:
                self.poke('others')
                self.others[key] = item
            else:
                print('F trying to store broken type:', item.__class__.__name__)

    def get_all_objects(self):
        """ Just return all objects governed by Forest -- not all scene objects 
        :return: list of objects
        """
        return list(self.nodes.values()) + list(self.edges.values()) + list(
            self.others.values()) + self.bracket_manager.get_brackets()

    def draw(self):
        """ Update all trees in the forest according to current visualization """
        if not self.in_display:
            print("Why are we drawing a forest which shouldn't be in scene")
        sc = ctrl.graph_scene
        sc.stop_animations()
        for root in self.roots:
            root.update_visibility()
        self.bracket_manager.update_brackets()
        self.update_forest_gloss()
        self.visualization.draw()
        if not sc.manual_zoom:
            sc.fit_to_window()
        sc.start_animations()
        ctrl.graph_view.repaint()

    def add_all_to_scene(self):
        """ Put items belonging to this forest to scene """
        if self.in_display:
            for item in self.get_all_objects():
                self.scene.addItem(item)

    def add_to_scene(self, item):
        """ Put items belonging to this forest to scene
        :param item:
        """
        if self.in_display:
            if item.scene() != self.scene:
                self.scene.addItem(item)

    def update_colors(self):
        """ Update colors to those specified for this Forest."""
        cm = ctrl.cm
        old_gradient_base = cm.paper()
        self.main.color_manager.update_colors(prefs, self.settings)
        self.main.app.setPalette(cm.get_qt_palette())
        if old_gradient_base != cm.paper() and cm.gradient:
            self.main.graph_scene.fade_background_gradient(old_gradient_base, cm.paper())
        else:
            self.main.graph_scene.setBackgroundBrush(qt_prefs.no_brush)
        for other in self.others.values():
            other.update_colors()
        self.main.ui_manager.update_colors()

    def get_node(self, constituent):
        """
        Returns a node corresponding to a constituent
        :rtype : kataja.ConstituentNode
        :param constituent: syntax.BaseConstituent
        :return: kataja.ConstituentNode
        """
        return self.nodes_from_synobs.get(constituent.save_key, None)

    def get_constituent_edges(self):
        """ Return list of constituent edges
        :return: list
        """
        return [x for x in self.edges.values() if x.edge_type == g.CONSTITUENT_EDGE and x.is_visible()]

    def get_constituent_nodes(self):
        """ Return list of constituent nodes
        :return: list
        """
        return [x for x in self.nodes.values() if isinstance(x, ConstituentNode) and x.isVisible()]

    def get_feature_nodes(self):
        """ Return list of feature nodes
        :return: list
        """
        return [x for x in self.nodes.values() if isinstance(x, FeatureNode)]

    def get_attribute_nodes(self):
        """ Return list of attribute nodes
        :return: list
        """
        return [x for x in self.nodes.values() if isinstance(x, AttributeNode)]

    def add_comment(self, comment):
        """ Add comment item to forest
        :param comment: comment item
        """
        self.comments.append(comment)

    def remove_comment(self, comment):
        """ Remove comment item from forest
        :param comment: comment item
        :return:
        """
        if comment in self.comments:
            self.comments.remove(comment)

    def remove_intertree_relations(self):
        """ After disconnections there may be multidominated nodes whose parents are in different trees.
        In most of syntaxes these shouldn't happen: there is no disconnection activity to create such things.

        When user disconnects a node, it is to work with branches separately: a multidominated node should get its own
        copy.

        However there is a remote possibility for creating them by merging non-root node from another tree to
        construction, so the option should be there.

        :return:
        """
        pass

    def update_root_status(self, node):
        """ Check if a node should be listed as root nodes. Tries to maintain the order of trees:
        new roots are appended to right. This is called by operations that may change the root status, but
        there is no global way for updating all of the roots, as then the order of root list is lost.
        :param node: root to check. Only ConstituentNodes can be roots
        :return:
        """
        if (not isinstance(node, ConstituentNode)) or node.is_placeholder():
            return
        has_parents = bool([x for x in node.edges_up if x.edge_type is g.CONSTITUENT_EDGE])
        if node in self.roots:
            if has_parents:
                self.poke('roots')
                self.roots.remove(node)
        elif not has_parents:
            self.poke('roots')
            self.roots.append(node)

    # not used
    def is_higher_in_tree(self, node_a, node_b):
        """ Compare two nodes, if node_a is higher, return True. Return False if not.
            Return None if nodes are not in the same tree -- cannot compare. (Be careful with the result,
            handle None and False differently.)
        :param node_a:
        :param node_b:
        :return:
        """
        for root in self.roots:
            nodes = self.list_nodes_once(root)
            if node_a in nodes and node_b in nodes:
                return nodes.index(node_a) < nodes.index(node_b)
        return None

    # not used
    def index_in_tree(self, node):
        """ Find the index of first usage in tree.
        :param node: node to look for
        :return: index
        """
        for root in self.roots:
            nodes = self.list_nodes_once(root)
            if node in nodes:
                return nodes.index(node)
        return None

    def get_first_free_constituent_name(self):
        """ Generate a name for constituent, ABCDEF... and then abcdef..., then AA, AB, AC...
         until a free (not used in this forest) is found.
        :return: String
        """
        names = [node.syntactic_object.label for node in self.nodes.values() if
                 isinstance(node, ConstituentNode) and node.syntactic_object]
        # I'm not trying to be efficient here.
        for letter in string.ascii_uppercase:
            if letter not in names:
                return letter
        for letter in string.ascii_lowercase:
            if letter not in names:
                return letter
        for letter in string.ascii_uppercase:
            for letter2 in string.ascii_uppercase:
                if letter + letter2 not in names:
                    return letter + letter2

    # ### Primitive creation of forest objects ###################################

    def create_node_from_constituent(self, constituent, pos=None, result_of_merge=False, result_of_select=False,
                                     replacing_merge=0, replacing_select=0, silent=False, inherits_from=None):
        """ All of the node creation should go through this!
        :param constituent:
        :param pos:
        :param result_of_merge:
        :param result_of_select:
        :param replacing_merge:
        :param replacing_select:
        :param silent:
        :param inherits_from:
        """
        node = self.get_node(constituent)
        if not node:
            node = ConstituentNode(constituent=constituent)
            node.after_init()
        else:
            assert False
        if pos:
            node.set_original_position(pos)
        elif ctrl.focus_point:
            node.set_original_position(ctrl.focus_point)
        self.add_to_scene(node)
        if inherits_from:
            alias = inherits_from.alias
            if alias:
                node.alias = alias

        if result_of_merge:
            self.add_merge_counter(node)
        elif replacing_merge:
            self.add_merge_counter(node, replace=replacing_merge)
        elif result_of_select:
            self.add_select_counter(node)
        elif replacing_select:
            self.add_select_counter(node, replace=replacing_select)
        elif silent:
            pass
        else:
            print("ConstituentNode doesn't announce its origin")
            raise KeyError

        # for key, feature in constituent.get_features().items():
        # self.create_feature_node(node, feature)
        if self.visualization:
            self.visualization.reset_node(node)
        self.update_root_status(node)
        return node

    def create_placeholder_node(self, pos):
        """

        :param pos:
        :return:
        """
        node = ConstituentNode(constituent=None)
        node.set_original_position(pos)
        node.after_init()
        self.add_to_scene(node)
        # for key, feature in C.get_features().items():
        # self.create_feature_node(node, feature)
        if self.visualization:
            self.visualization.reset_node(node)
        return node

    def create_feature_node(self, host, syntactic_feature):
        """

        :param host:
        :param syntactic_feature:
        :return:
        """
        FN = FeatureNode(syntactic_feature)
        FN.after_init()
        if host:
            FN.compute_start_position(host)
            self.connect_node(host, child=FN)
        self.add_to_scene(FN)
        FN.update_visibility()
        return FN

    def create_attribute_node(self, host, attribute_id, attribute_label, show_label=False):
        """

        :param host:
        :param attribute_id:
        :param attribute_label:
        :param show_label:
        :return:
        """
        AN = AttributeNode(host, attribute_id, attribute_label, show_label=show_label)
        self.connect_node(host, child=AN)
        self.add_to_scene(AN)
        AN.update_visibility()
        return AN

    def create_edge(self, start=None, end=None, edge_type='', direction=''):
        # print 'creating edge ', start, end, edge_type
        """

        :param start:
        :param end:
        :param edge_type:
        :param direction:
        :return:
        """
        rel = Edge(start=start, end=end, edge_type=edge_type, direction=direction)
        rel.after_init()
        self.store(rel)
        self.add_to_scene(rel)
        return rel

    def create_bracket(self, host=None, left=True):
        """

        :param host:
        :param left:
        :return:
        """
        br = self.bracket_manager.create_bracket(host, left)
        self.add_to_scene(br)
        return br

    def create_gloss_node(self, host_node=None, label=None):
        """ Creates the gloss node for existing constituent node and necessary connection
        :param label:
        :param host_node: if the gloss is created for some specific constituentnode. Can be None
        :return: gloss node
        """
        if host_node:
            gn = GlossNode(text=host_node.gloss)
            self.connect_node(child=gn, parent=host_node)
        elif label:
            gn = GlossNode(text=label)
        else:
            gn = GlossNode(text="gloss")
        gn.after_init()
        self.add_to_scene(gn)

        # Cosmetic improvemet, if gloss is created by editing the gloss text field. (not present anymore)
        # ee = ctrl.ui.get_constituent_edit_embed()
        # if ee and ee.isVisible():
        #     pos = ee.master_edit.pos()
        #     scene_pos = ctrl.graph_view.mapToScene(ee.mapToParent(pos))
        #     gn.set_original_position(scene_pos)
        return gn

    def create_comment_node(self, comment):
        """

        :param comment:
        :return:
        """
        cn = CommentNode(comment)
        cn.after_init()
        self.add_to_scene(cn)
        return cn

    # not used
    def create_image(self, image_path):
        """

        :param image_path:
        :return:
        """
        im = Image(image_path)
        self.others[im.save_key] = im
        self.add_to_scene(im)
        return im

    def create_node_from_string(self, text='', pos=None):
        """

        :param text:
        :param pos:
        """
        node = self.parser.parse_into_forest(text)
        return node
        # self.add_to_scene(root_node)
        # self.update_root_status(root_node)

    # @time_me
    def create_tree_from_string(self, text, replace=False):
        """ This will probably end up resulting one tree, but during parsing there may be multiple roots/trees
        :param text:
        :param replace:
        """
        if replace:
            self.roots = []
        text = text.strip()
        nodes = self.parser.parse_into_forest(text)
        self.settings.uses_multidomination = False
        self.traces_to_multidomination()

    def read_definitions(self, definitions):
        """
        :param definitions: Try to set features and glosses according to definition strings for nodes in tree.
        :return:
        """
        # todo: can we write feature/gloss definitions into node text fields?
        # print('we have following keys:', self.nodes_by_uid.keys())
        pass

    def create_trace_for(self, node):
        """

        :param node:
        :return:
        """
        print('Creating a trace for ', node)
        index = node.index
        if not index:
            index = self.chain_manager.next_free_index()
            node.index = index
        assert index
        constituent = ForestSyntax.new_constituent('t', source='t_' + index)
        ForestSyntax.set_constituent_index(constituent, index)
        trace = self.create_node_from_constituent(constituent, silent=True)
        trace.is_trace = True
        # if new_chain:
        # self.chain_manager.rebuild_chains()
        # if self.settings.uses_multidomination:
        # trace.hide()
        return trace

    def create_empty_node(self, pos, give_label=True, node_type='c'):
        """


        :param node_type:
        :param pos:
        :param give_label:
        :return:
        """
        node = None
        if node_type == g.CONSTITUENT_NODE:
            if give_label:
                label = self.get_first_free_constituent_name()
            else:
                label = ''
            const = ForestSyntax.new_constituent(label)
            node = self.create_node_from_constituent(const, pos, result_of_select=True)
        elif node_type == g.FEATURE_NODE:
            label = 'feature'
            feat = ForestSyntax.new_feature(label)
            node = self.create_feature_node(None, feat)
            node.set_original_position(pos)
        elif node_type == g.GLOSS_NODE:
            label = 'gloss'
            node = self.create_gloss_node(None, label=label)
            node.set_original_position(pos)
        elif node_type == g.COMMENT_NODE:
            label = 'comment'
            node = self.create_comment_node(label)
            node.set_original_position(pos)
        print('created a new node: ', node)
        return node

    def create_arrow(self, p1, p2, text=None):
        """ Create an arrow (Edge) using the default arrow style

        :param p1: start point
        :param p2: end point
        :param text: explanatory text associated with the arrow
        :return:
        """
        edge = self.create_edge(start=None, end=None, edge_type=g.ARROW)
        edge.set_start_point(p1)
        edge.set_end_point(p2)
        if text:
            edge.label_text = text
        edge.show()
        ctrl.select(edge)
        return edge

    ############# Deleting items ######################################################
    # item classes don't have to know how they relate to each others.
    # here when something is removed from scene, it is made sure that it is also removed
    # from items that reference to it.

    def delete_node(self, node, ignore_consequences=False):
        """ Delete given node and its children and fix the tree accordingly
        :param node:
        :param ignore_consequences: don't try to fix things like connections, just delete.
        Note: This and other complicated revisions assume that the target tree is 'normalized' by
        replacing multidomination with traces. Each node can have only one parent.
        This makes calculation easier, just remember to call multidomination_to_traces
        and traces_to_multidomination after deletions.
        """
        # -- connections to other nodes --
        print('deleting node: ', node)
        if not ignore_consequences:
            for edge in list(node.edges_down):
                if edge.end:
                    self.delete_node(edge.end)  # this will also disconnect node
                else:
                    self.disconnect_node(edge=edge)
            for edge in list(node.edges_up):
                self.disconnect_node(edge=edge)

        # -- ui elements --
        self.main.ui_manager.delete_ui_elements_for(node)
        # -- brackets --
        self.bracket_manager.remove_brackets(node)
        # -- dictionaries --
        if node.save_key in self.nodes:
            self.poke('nodes')
            del self.nodes[node.save_key]
        if node.syntactic_object and node.syntactic_object.save_key in self.nodes_from_synobs:
            del self.nodes_from_synobs[node.syntactic_object.save_key]
        if node in self.roots:
            self.poke('roots')
            self.roots.remove(node)
        # -- scene --
        sc = node.scene()
        if sc:
            sc.removeItem(node)
        # -- undo stack --
        node.announce_deletion()

    def delete_edge(self, edge, ignore_consequences=False):
        """ remove from scene and remove references from nodes
        :param edge:
        :param ignore_consequences: don't try to fix things like connections, just delete.
        """
        # -- connections to host nodes --
        start_node = edge.start
        end_node = edge.end
        # -- selections --
        ctrl.remove_from_selection(edge)
        if not ignore_consequences:
            if start_node:
                if edge in start_node.edges_down:
                    start_node.poke('edges_down')
                    start_node.edges_down.remove(edge)
                if edge in start_node.edges_up:  # shouldn't happen
                    start_node.poke('edges_up')
                    start_node.edges_up.remove(edge)
                    self.update_root_status(start_node)
            if end_node:
                if edge in end_node.edges_down:  # shouldn't happen
                    end_node.poke('edges_down')
                    end_node.edges_down.remove(edge)
                if edge in end_node.edges_up:
                    end_node.poke('edges_up')
                    end_node.edges_up.remove(edge)
                    self.update_root_status(end_node)
        # -- ui elements --
        self.main.ui_manager.delete_ui_elements_for(edge)
        # -- dictionaries --
        if edge.save_key in self.edges:
            self.poke('edges')
            del self.edges[edge.save_key]
        # -- scene --
        sc = edge.scene()
        if sc:
            sc.removeItem(edge)
        # -- undo stack --
        edge.announce_deletion()

    def delete_item(self, item, ignore_consequences=False):
        """ User-triggered deletion (e.g backspace on selection)
        :param item: item from selection. can be anything that can be selected
        :param ignore_consequences: don't try to fix remainders (because deletion is part of
            some major rewrite of values, e.g. in undo process.
        """
        if isinstance(item, Edge):
            start = item.start
            self.delete_edge(item, ignore_consequences=ignore_consequences)
            if (not ignore_consequences) and start:
                self.fix_stubs_for(item.start)
        elif isinstance(item, Node):
            self.delete_node(item, ignore_consequences=ignore_consequences)

    # ## Free edges ###############################

    # there are edges that are initially not connected anywhere and which need to be able to connect and disconnect
    # start and end points separately

    def set_edge_start(self, edge, new_start):
        """

        :param edge:
        :param new_start:
        """
        assert new_start.save_key in self.nodes
        if edge.start:
            ForestSyntax.disconnect_edge(edge)
            edge.start.poke('edges_down')
            edge.start.edges_down.remove(edge)
        edge.connect_end_points(new_start, edge.end)
        ForestSyntax.connect_according_to_edge(edge)
        new_start.poke('edges_down')
        new_start.edges_down.append(edge)

    def set_edge_end(self, edge, new_end):
        """

        :param edge:
        :param new_end:
        """
        assert new_end.save_key in self.nodes
        if edge.end:
            ForestSyntax.disconnect_edge(edge)
            edge.end.poke('edges_up')
            edge.end.edges_up.remove(edge)
            self.update_root_status(edge.end)
        edge.connect_end_points(edge.start, new_end)
        ForestSyntax.connect_according_to_edge(edge)
        new_end.poke('edges_up')
        new_end.edges_up.append(edge)
        self.update_root_status(new_end)
        self.update_root_status(edge.start)

    def set_edge_ends(self, edge, new_start, new_end):
        """

        :param edge:
        :param new_start:
        :param new_end:
        """
        assert new_start.save_key in self.nodes
        assert new_end.save_key in self.nodes
        if edge.start:
            ForestSyntax.disconnect_edge(edge)
            edge.start.poke('edges_down')
            edge.start.edges_down.remove(edge)
        if edge.end:
            ForestSyntax.disconnect_edge(edge)
            edge.end.poke('edges_up')
            edge.end.edges_up.remove(edge)
            self.update_root_status(edge.end)
        edge.connect_end_points(new_start, new_end)
        ForestSyntax.connect_according_to_edge(edge)
        new_end.poke('edges_up')
        new_end.edges_up.append(edge)
        new_start.poke('edges_down')
        new_start.edges_down.append(edge)
        self.update_root_status(new_start)
        self.update_root_status(new_end)

    def disconnect_edge_start(self, edge):
        """ This shouldn't be done for ConstituentEdges. It leaves a problematic stub going up (nice rhyme)
        :param edge:
        :return:
        """
        if edge.start:
            ForestSyntax.disconnect_edge(edge)
            edge.poke('edges_down')
            edge.start.edges_down.remove(edge)
        edge.start = None
        edge.make_relative_vector()
        ctrl.ui.reset_control_points(self)
        edge.update_shape()

    def disconnect_edge_end(self, edge):
        """

        :param edge:
        """
        if edge.end:
            ForestSyntax.disconnect_edge(edge)
            edge.poke('edges_up')
            edge.end.edges_up.remove(edge)
            self.update_root_status(edge.end)
        edge.end = None
        edge.make_relative_vector()
        ctrl.ui.reset_control_points(self)
        edge.update_shape()

    def fix_stubs_for(self, node):
        """ Make sure that node (ConstituentNode) has binary children. Creates stubs if needed, and removes stubs if
        node has two empty stubs.
        :param node: node to be fixed (ignore anything but constituent nodes)
        :return: None
        """
        if not isinstance(node, ConstituentNode):
            return
        left = node.left()
        right = node.right()
        print("Fixing stubs for ", node, left, right)

        if not (left or right):
            # nothing to do, doesn't have children
            return
        elif not left:
            if right.is_placeholder():
                right_edge = node.get_edge_to(right)
                self.delete_edge(right_edge)
                self.delete_node(right)
            else:
                # we are missing the stub to left here
                print("Creating placeholder to LEFT")
                placeholder = self.create_placeholder_node(node.current_position)
                self.connect_node(node, placeholder, direction=g.LEFT)
        elif not right:
            if left.is_placeholder():
                left_edge = node.get_edge_to(left)
                self.delete_edge(left_edge)
                self.delete_node(left)
            else:
                # we are missing the stub to right here
                print("Creating placeholder to RIGHT")
                placeholder = self.create_placeholder_node(node.current_position)
                self.connect_node(node, placeholder, direction=g.RIGHT)
        elif left.is_placeholder() and right.is_placeholder():
            # both are placeholders, so this node doesn't need to have children at all. remove stubs.
            left_edge = node.get_edge_to(left)
            self.delete_edge(left_edge)
            self.delete_node(left)
            right_edge = node.get_edge_to(right)
            self.delete_edge(right_edge)
            self.delete_node(right)

    def add_placeholder_to_edge_start(self, edge):
        """

        :param edge:
        """
        assert (not edge.start)
        pos = edge.start_point
        placeholder = self.create_placeholder_node(pos)
        self.set_edge_start(edge, placeholder)

    def add_placeholder_to_edge_end(self, edge):
        """

        :param edge:
        """
        assert (not edge.end)
        pos = edge.end_point
        placeholder = self.create_placeholder_node(pos)
        self.set_edge_end(edge, placeholder)

    def order_edge_visibility_check(self):
        """ Make sure that all edges are checked to update their visibility. This can be called multiple
        times, but the visibility check is done only once.
        """
        self._do_edge_visibility_check = True

    def edge_visibility_check(self):
        """ Perform check for each edge: hide them if their start/end is hidden, show them if necessary.
        """
        if self._do_edge_visibility_check:
            sc = self.settings.shows_constituent_edges
            for edge in self.edges.values():
                if edge.edge_type == g.CONSTITUENT_EDGE:
                    if not sc:
                        edge.visible = False
                        continue
                    start = edge.start
                    sv = False
                    ev = True
                    if start:
                        sv = start.is_visible
                        if not sv:
                            ev = False
                        else:
                            ev = self.visualization.show_edges_for(start)
                    edge.visible = ev and ((edge.end and edge.end.visible) or ((not edge.end) and sv))
                else:
                    if edge.start:
                        edge.visible = edge.start.is_visible
                    else:
                        edge.visible = True
            self._do_edge_visibility_check = False

    def adjust_edge_visibility_for_node(self, node, visible):
        """

        :param node:
        :param visible:
        """
        if isinstance(node, ConstituentNode):
            if not visible:
                edges_visible = False
            elif self.visualization:
                edges_visible = self.visualization.show_edges_for(node) and self.settings.shows_constituent_edges
            else:
                edges_visible = False
            for edge in node.edges_down:
                v = edge.visible
                if edge.edge_type == g.CONSTITUENT_EDGE:
                    edge.visible = edges_visible and ((edge.end and edge.end.visible) or not edge.end)
                else:
                    edge.visible = visible
                if v and not edge.visible:
                    ctrl.ui.remove_touch_areas_for(edge)

    def add_feature_to_node(self, feature, node):
        """

        :param feature:
        :param node:
        """
        C = node.syntactic_object
        F = feature.syntactic_object
        C.set_feature(F.key, F)
        self.connect_node(parent=node, child=feature)

    def add_comment_to_node(self, comment, node):
        """

        :param comment:
        :param node:
        """
        self.connect_node(parent=node, child=comment)

    def add_gloss_to_node(self, gloss, node):
        """

        :param gloss:
        :param node:
        """
        self.connect_node(parent=node, child=gloss)
        node.gloss = gloss.label

    # ## order markers are special nodes added to nodes to signal the order when the node was merged/added to forest
    #######################################################################

    def add_order_features(self, key='M'):
        """

        :param key:
        """
        help_text = ''
        if key == 'M':
            attr_id = 'merge_order'
            show_label = True
        elif key == 'S':
            attr_id = 'select_order'
            show_label = False
        for node in self.get_attribute_nodes():
            assert (node.attribute_label != key)
        for node in self.get_constituent_nodes():
            val = getattr(node, attr_id)
            if isinstance(val, collections.Callable):
                val = val()
            if val:
                attr_node = self.create_attribute_node(node, attr_id, attribute_label=key, show_label=show_label)

    def remove_order_features(self, key='M'):
        """

        :param key:
        """
        for node in self.get_attribute_nodes():
            if node.attribute_label == key:
                self.delete_node(node)

    def update_order_features(self, node):
        """

        :param node:
        """
        M = node.get_attribute_nodes('M')
        S = node.get_attribute_nodes('S')
        if M and not self.settings.shows_merge_order:
            self.delete_node(M)
        elif self.settings.shows_merge_order and (not M) and node.merge_order:
            self.create_attribute_node(node, 'merge_order', attribute_label='M', show_label=True)
        if S and not self.settings.show_select_order:
            self.delete_node(S)
        elif self.settings.shows_select_order and (not S) and node.select_order:
            self.create_attribute_node(node, 'select_order', attribute_label='S', show_label=False)

    def add_select_counter(self, node, replace=0):
        """

        :param node:
        :param replace:
        """
        if replace:
            node.select_order = replace
        else:
            self.select_counter += 1
            node.select_order = self.select_counter
        self.update_order_features(node)

    def add_merge_counter(self, node, replace=0):
        """

        :param node:
        :param replace:
        """
        if replace:
            node.select_order = replace
        else:
            self.merge_counter += 1
            node.merge_order = self.merge_counter
        self.update_order_features(node)

    # ### Minor updates for forest elements #######################################################################

    def reform_constituent_node_from_string(self, text, node):
        """

        :param text:
        :param node:
        """
        new_nodes = self.parser.parse_into_forest(text)
        if new_nodes:
            self.replace_node(node, new_nodes[0])

    # not used
    def edit_node_alias(self, node, text):
        # this just changes the node without modifying its identity
        """

        :param node:
        :param text:
        """
        assert False
        node.alias = text

    # ### Switching between multidomination and traces ######################################

    def group_traces_to_chain_head(self):
        """


        """
        #print('group_traces_to_chain_head called in ', self)
        self.chain_manager.group_traces_to_chain_head()

    def traces_to_multidomination(self):
        """


        """
        #print('traces_to_multidomination called in ', self)
        self.chain_manager.traces_to_multidomination()
        for node in self.nodes.values():
            if hasattr(node, 'is_trace') and node.is_trace:
                print('We still have a visible trace after traces_to_multidomination')
                # else:
                #    print('no is_trace -property')

    def multidomination_to_traces(self):
        """


        """
        #print('multidomination_to_traces called in ', self)
        self.chain_manager.multidomination_to_traces()


        # # if using traces, merge original and leave trace, or merge trace and leave original. depending on which way the structure is built.
        # print '-------------------'
        # print 'dropping for merge'

        # print 'f.settings.use_multidomination:', f.settings.use_multidomination
        # if not f.settings.use_multidomination:
        # new_trace = f.create_trace_for(dropped_node)
        # new_trace.set_original_position(dropped_node.current_position)
        # chain = f.get_chain(dropped_node.get_index())
        # traces_first = f.traces_go_first()
        # if traces_first:
        # if f.is_higher_in_tree(self.host, dropped_node):
        # new_node = new_trace
        # else:
        # new_node = dropped_node
        # dropped_node.replace_node(new_trace)
        # else:
        # if f.is_higher_in_tree(self.host, dropped_node):
        # new_node = dropped_node
        # dropped_node.replace_node(new_trace)
        # else:
        # new_node = new_trace
        # else:
        # new_node = dropped_node
        # top_node, left_node, right_node = self.merge_to_host(new_node)
        # ctrl.on_cancel_delete = []
        # left_node._hovering = False
        # right_node._hovering = False
        # return True

    #### Undoable commands ###############################################################

    def disconnect_node_from_tree(self, node):
        """ Delete node from tree and make a new tree out of it
        :param node:
        """
        self.main.add_message("Disconnecting node %s" % node)
        # if self.settings.uses_multidomination():
        #     self.multidomination_to_traces()
        #     if node.index:
        #         chain = self.chain_manager.chains.get(node.index, None)
        #         for l in chain:
        #             self.delete_node(l)
        #     else:
        #         self.delete_node(node)
        #     self.chain_manager.rebuild_chains()
        #     # self._fix_chains()
        #     self.traces_to_multidomination()
        self.delete_node(node)
        if self.traces_are_visible():
            self.chain_manager.rebuild_chains()
        self.undo_manager.record("Disconnected node %s" % node)
        return None

    def command_delete(self, node):
        """ Undoable UI interface for deletion
        :param node:
        """
        self.main.add_message("Deleting node %s" % node)
        # if self.settings.uses_multidomination():
        #     self.multidomination_to_traces()
        #     if node.index:
        #         chain = self.chain_manager.chains[node.index]
        #         for l in chain:
        #             self.delete_node(l)
        #     else:
        #         self.delete_node(node)
        #     self.chain_manager.rebuild_chains()
        #     # self._fix_chains()
        #     self.traces_to_multidomination()
        self.delete_node(node)
        if self.traces_are_visible():
            self.chain_manager.rebuild_chains()
        self.undo_manager.record("Delete node %s" % node)
        return None


    def get_direction(self, parent, child):
        """ Returns the direction/alignment parameter of edge between nodes, can be useful for deciding
        how to show them or what exactly needs replacing.
        :param parent: Node
        :param child: Node
        :return: int (from globals, see g.LEFT, g.RIGHT, g.NO_ALIGN )
        """
        edge = parent.get_edge_to(child)
        return edge.alignment

    # ### Connecting and disconnecting items ##########################
    #
    # Since the "trees" are not necessarily trees, but can have circular
    # edges, recursive or composite methods are not very reliable for
    # making or removing connections between nodes. It is better to do it
    # here on forest level.
    #
    # These manipulations should be low level operations only called from
    # by forest's higher level methods.
    #

    def connect_node(self, parent=None, child=None, direction='', revert=False):
        """ This is for connecting nodes with a certain edge. Calling this once will create the necessary links for both partners.
        Sanity checks:
        - Immediate circular links (child becomes immediate parent of its immediate parent) are not allowed.
        - If items are already linked with this edge type, error is raised.
        - Cannot link to itself.
        This needs to be robust.

        connections are revertable: if reverted-flag is true, connect_node returns a tuple, where
        the other part is a dict of original arguments.
        :param parent: Node
        :param child: Node
        :param direction:
        :param revert: If revert flag is on, instead of making a connection, an existing connection of this description
         is destroyed

        """
        forest('connect_node %s %s %s %s' % (parent, child, direction, revert))

        # Check for arguments:
        if parent == child:
            raise ForestError('Connecting to self')
        if not parent and child:
            raise ForestError('Trying to connect nodes, but other is missing (parent:%s, child%s)' % (parent, child))

        edge_type = child.__class__.default_edge_type

        # Check for circularity:
        if edge_type is not g.ARROW:
            # With arrows identical or circular edges are not a problem
            for old_edge in child.edges_up:
                if old_edge.edge_type == edge_type:
                    if old_edge.end == child and old_edge.start == parent:
                        raise ForestError('Identical edge exists already')
                    elif old_edge.start == child and old_edge.end == parent:
                        raise ForestError('Connection is circular')
        # Check for directionality
        if edge_type is g.CONSTITUENT_EDGE and not direction:
            raise ForestError('ConstituentNode connection needs a direction argument')

        # Create edge and make connections
        new_edge = self.create_edge(edge_type=edge_type, direction=direction)
        self.set_edge_ends(new_edge, parent, child)
        if hasattr(parent, 'rebuild_brackets'):
            parent.rebuild_brackets()
        if hasattr(child, 'rebuild_brackets'):
            child.rebuild_brackets()
        parent.update_label()
        child.update_label()
        self.update_root_status(child)
        return new_edge

    def disconnect_node(self, first=None, second=None, edge_type='', edge=None, ignore_missing=False):
        """ Removes and deletes a edge between two nodes
        :param first:
        :param second:
        :param edge_type:
        :param edge:
        :param ignore_missing:
        """
        forest('disconnect_node %s %s %s %s' % (first, second, edge_type, edge))
        if not edge:
            edge = first.get_edge_to(second, edge_type)
        if edge:
            if edge.start == first:
                first.poke('edges_down')
                first.edges_down.remove(edge)
                second.poke('edges_up')
                second.edges_up.remove(edge)
                self.update_root_status(second)
            elif edge.end == first:
                second.poke('edges_down')
                second.edges_down.remove(edge)
                first.poke('edges_up')
                first.edges_up.remove(edge)
                self.update_root_status(first)
            ForestSyntax.disconnect_edge(edge)
            self.delete_edge(edge)
        elif not ignore_missing:
            raise ForestError("Disconnecting nodes, but cannot find the edge between them")

    def replace_node(self, old_node, new_node, only_for_parent=None, replace_children=False, can_delete=True):
        """  When replacing a node we should make sure that edges get fixed too.
        :param old_node: node to be replaced -- if it gets orphaned, delete it
        :param new_node: replacement node
        :param only_for_parent: replace only one parent connection
        :param replace_children: new node also gains parenthood for old node's children
        :param can_delete: replaced node can be deleted
        :return:
        """
        forest('replace_node %s %s %s %s' % (old_node, new_node, only_for_parent, replace_children))

        assert (old_node != new_node)  # if this can happen, we'll probably have infinite loop somewhere
        new_node.current_position = old_node.current_position
        new_node.adjustment = old_node.adjustment
        new_node.algo_position = tuple(old_node.algo_position)
        new_node.update_visibility(active=True, fade=True)

        for edge in list(old_node.edges_up):
            if edge.start:
                align = edge.alignment
                parent = edge.start
                if only_for_parent and parent != only_for_parent:
                    continue
                self.disconnect_node(parent, old_node, edge.edge_type)
                self.connect_node(parent, child=new_node, direction=align)

        if replace_children and not only_for_parent:
            for edge in list(old_node.edges_down):
                child = edge.end
                if child:
                    align = edge.alignment
                    self.disconnect_node(old_node, child, edge.edge_type)
                    self.connect_node(new_node, child, direction=align)

        if (not old_node.edges_up) and can_delete:
            # old_node.update_visibility(active=False, fade=True)
            self.delete_node(old_node)

    # ########### Complex node operations ##############################

    def replace_node_with_merged_empty_node(self, node, edge, merge_to_left, new_node_pos, merger_node_pos):
        """ examples:
        If we have [A [B C]] ...
        and we do this for A, we get: [0 [A [B C]]]
        if we do this for B, we get: [A [[0 B] C]]

        :param node:
        :param edge:
        :param merge_to_left:
        :param new_node_pos:
        :param merger_node_pos:
        """
        forest('replace_node_with_merged_empty_node %s %s %s %s %s' % (
            node, edge, merge_to_left, new_node_pos, merger_node_pos))
        ex, ey = new_node_pos
        empty_node = self.create_empty_node(pos=(ex, ey, node.z))
        empty_node.adjustment = node.adjustment
        self.replace_node_with_merged_node(node, empty_node, edge, merge_to_left, merger_node_pos)

    def delete_unnecessary_merger(self, node):
        """

        :param node:
        :raise ForestError:
        """
        if not isinstance(node, ConstituentNode):
            raise ForestError("Trying to treat wrong kind of node as ConstituentNode and forcing it to binary merge")
        i = node.index
        left = node.left()
        right = node.right()
        child = None
        if left.is_placeholder():
            child = right
        elif right.is_placeholder():
            child = left
        # fixme: do same in ForestSyntax!
        parents = node.get_parents()
        parents_children = set()
        bad_parents = []
        good_parents = []
        for parent in parents:
            if child in parent.get_children():
                bad_parents.append(parent)
            else:
                good_parents.append(parent)
        if not (bad_parents or good_parents):
            self.disconnect_node(first=node, second=child)
        else:
            if bad_parents:
                # more complex case
                ctrl.add_message(
                    "Removing node would make parent to have same node as both left and right child. " + "Removing parent too.")
                self.disconnect_node(first=node, second=child)
                for parent in bad_parents:
                    for grandparent in parent.get_parents():
                        self.disconnect_node(first=grandparent, second=parent)
                        self.disconnect_node(first=parent, second=child)
                        self.connect_node(parent=grandparent, child=child)

            if good_parents:
                # normal case
                self.disconnect_node(first=node, second=child, ignore_missing=True)
                for parent in good_parents:
                    d = self.get_direction(parent, node)
                    self.disconnect_node(first=parent, second=node)
                    self.connect_node(parent=parent, child=child, direction=d)
        if i:
            child.set_index(i)
        self.delete_node(node)
        for parent in bad_parents:
            self.delete_node(parent)
            # if right.is_placeholder():
            # self.delete_node(right)
            # if left.is_placeholder():
            # self.delete_node(left)

    def replace_node_with_merged_node(self, replaced, new_node, edge, merge_to_left, merger_node_pos):
        """ This happens when touch area in edge going up from node N is clicked.
        [N B] -> [[x N] B] (left == True) or
        [N B] -> [[N x] B] (left == False)
        :param replaced:
        :param new_node:
        :param edge: Give the edge from node to specific parent, if the replacement is supposed to happen in one place
            only. Edge is the unique identifier for a node with multiple parents.
        :param merge_to_left:
        :param merger_node_pos:
        """
        forest('replace_node_with_merged_empty_node %s %s %s %s %s' % (
            replaced, new_node, edge, merge_to_left, merger_node_pos))
        start_node = None
        align = None
        if edge:  # ???? can't we take all parents
            start_node = edge.start
            align = edge.alignment

        mx, my = merger_node_pos
        # if new_node and old_node belong to same tree, this is a Move / Internal merge situation and we need to give
        # the new_node an index so it can be reconstructed as a trace structure
        moving_was_higher = self.is_higher_in_tree(new_node, replaced)
        # returns None if they are not in same tree
        if moving_was_higher is not None:
            if not new_node.index:
                new_node.index = self.chain_manager.next_free_index()
            # replace either the moving node or leftover node with trace if we are using traces
            if self.traces_are_visible():
                if moving_was_higher:
                    new_node = self.create_trace_for(new_node)
                else:
                    t = self.create_trace_for(new_node)
                    self.replace_node(new_node, t, can_delete=False)
        else:
            pass
            print('Nodes in different trees.')

        if edge:
            self.disconnect_node(edge=edge)

        if merge_to_left:
            left = new_node
            right = replaced
        else:
            left = replaced
            right = new_node

        merger_node = self.create_merger_node(left=left, right=right, pos=(mx, my, replaced.z))
        merger_node.adjustment = replaced.adjustment
        if edge:
            forest('connecting merger to parent')
            self.connect_node(start_node, merger_node, direction=align)

        if self.traces_are_visible():
            self.chain_manager.rebuild_chains()

    def create_merger_node(self, left=None, right=None, pos=None):
        """ Gives a merger node of two nodes. Doesn't try to fix their edges upwards
        :param left:
        :param right:
        :param pos:
        """
        forest('create_merger_node %s %s %s' % (left, right, str(pos)))
        if not pos:
            pos = (0, 0, 0)
        merger_const = ForestSyntax.constituent_merge(left, right)
        selecting_node = ForestSyntax.which_selects(left, right)
        merger_node = self.create_node_from_constituent(merger_const, pos=pos, result_of_merge=True,
                                                        inherits_from=selecting_node)
        self.connect_node(parent=merger_node, child=left, direction=g.LEFT)
        self.connect_node(parent=merger_node, child=right, direction=g.RIGHT)
        return merger_node

    # @time_me
    def copy_node(self, node):
        """ Copy a node and make a new tree out of it
        :param node:
        """
        forest('copy_node %s' % node)
        if not node:
            return
        new_c = ForestSyntax.constituent_copy(node)
        new_node = self.create_node_from_constituent(new_c, pos=node.current_position, result_of_select=True)
        self.undo_manager.record("Copied %s" % node)
        self.main.add_message("Copied %s" % node)
        return new_node

    # ### Triangles ##############################################

    def add_triangle_to(self, node):
        """

        :param node:
        """
        node.triangle = True
        fold_scope = self.list_nodes_once(node)
        not_my_children = set()
        for folded in fold_scope:
            parents = folded.get_parents()
            if folded is node:
                continue
            # allow recursive triangles -- don't overwrite existing fold
            elif folded.folding_towards:
                continue
            # multidominated nodes can be folded if all parents are in scope of fold
            elif folded.is_multidominated():
                can_fold = True
                for parent in parents:
                    if (parent not in fold_scope) or (parent in not_my_children):
                        not_my_children.add(folded)
                        can_fold = False
                        break
                if can_fold:
                    print('Folding multidominated node %s' % folded)
                    folded.fold_towards(node)
            # remember that the branch that couldn't be folded won't allow any of its children to be
            # folded either.
            elif parents and parents[0] in not_my_children:
                not_my_children.add(folded)
            else:
                folded.fold_towards(node)

    def remove_triangle_from(self, node):
        """

        :param node:
        """
        node.triangle = False
        fold_scope = [f for f in self.list_nodes_once(node, only_visible=False) if f.folding_towards is node]
        for folded in fold_scope:
            folded.folding_towards = None
            folded.folded_away = False
            folded.adjustment = node.adjustment
            folded.fixed_position = None
            folded.fade_in()
            folded.update_visibility()
            folded.update_bounding_rect()
        # this needs second round of update visibility, as child nodes may yet not be visible, so edges to them
        # won't be visible either.
        for folded in fold_scope:
            folded.update_visibility()
        node.update_visibility()  # edges from triangle to nodes below

    def can_fold(self, node):
        """

        :param node:
        :return:
        """
        return not node.triangle

    # ######## Utility functions ###############################

    def parse_features(self, string, node):
        """

        :param string:
        :param node:
        :return:
        """
        print('parse_features called')
        return self.parser.parse_definition(string, node)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    roots = Saved("roots") # the current line of trees
    nodes = Saved("nodes")
    edges = Saved("edges")
    others = Saved("others")
    settings = Saved("settings")
    rules = Saved("rules")
    vis_data = Saved("vis_data")
    derivation_steps = Saved("derivation_steps")
    merge_counter = Saved("merge_counter")
    select_counter = Saved("select_counter")
    comments = Saved("comments")
    gloss_text = Saved("gloss_text")
