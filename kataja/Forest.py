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
import itertools

from kataja.ProjectionVisual import ProjectionData
from kataja.Tree import Tree
from kataja.errors import ForestError
from kataja.ForestSettings import ForestSettings, ForestRules
from kataja.Bracket import Bracket
from kataja.managers.BracketManager import BracketManager
from kataja.nodes.BaseConstituentNode import BaseConstituentNode
from kataja.nodes.ConstituentNode import ConstituentNode
from kataja.nodes.AttributeNode import AttributeNode
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.managers.ChainManager import ChainManager
from kataja.DerivationStep import DerivationStepManager
from kataja.nodes.Node import Node
from kataja.parser.INodeToKatajaConstituent import INodeToKatajaConstituent
from kataja.Presentation import TextArea, Image
from kataja.Edge import Edge
from kataja.managers.UndoManager import UndoManager
from kataja.nodes.FeatureNode import FeatureNode
from kataja.BaseModel import BaseModel, Saved
import kataja.globals as g


class Forest(BaseModel):
    """ Forest is a group of trees that together form one view.
    Often there needs to be more than one tree visible at same time,
     so that they can be compared or to show states of construction
      where some edges are not yet linked to the main root.
      Forest is the container for these.
      Forest also takes care of the operations manipulating, creating and
      removing trees. """

    short_name = "Forest"

    def __init__(self, buildstring='', definitions=None, gloss_text='', comments=None):
        """ Create an empty forest """
        super().__init__()
        self.nodes_from_synobs = {}
        self.main = ctrl.main
        self.main.forest = self  # assign self to be the active forest while
        # creating the managers.
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
        self.trees = []
        self.nodes = {}
        self.edges = {}
        self.edge_types = set()
        self.node_types = set()
        self.others = {}
        self.vis_data = {}
        self.projections = {}
        self.projection_rotator = itertools.cycle(range(0, 8))
        self.merge_counter = 0
        self.select_counter = 0
        self.comments = []
        self.gloss_text = ''
        self.guessed_projections = False

        if buildstring:
            self.create_trees_from_string(buildstring)
        if definitions:
            self.read_definitions(definitions)
        if gloss_text:
            self.gloss_text = gloss_text
        if comments:
            self.comments = comments

        # Update request flags
        self._do_edge_visibility_check = False

    def after_model_update(self, updated_fields, update_type):
        """ This is called after the item's model has been updated (e.g. by
        undo),
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
            1st wave creates the objects and calls __init__, and then
            iterates through and sets the values.
            2nd wave calls after_inits for all created objects. Now they can
            properly refer to each other and know their
                values.
        :return: None
        """
        # print('created a forest %s , its traces should be visible: %s ' % (
        # self, self.traces_are_visible()))
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
        self.draw()  # do draw once to avoid having the first draw in undo
        # stack.
        ctrl.undo_disabled = False

    def retire_from_drawing(self):
        """ Announce that this forest should not try to work with scene
        anymore --
         some other forest is occupying the scene now.
        :return:
        """
        scene = self.scene
        for item in self.get_all_objects():
            self.remove_from_scene(item)
        self.in_display = False

    def traces_are_visible(self):
        """ Helper method for checking if we need to deal with chains
        :return:
        """
        return not self.settings.uses_multidomination

    @staticmethod
    def list_nodes(first):
        """
        Do left-first iteration through all nodes. Can become quite large if
        there is lots of
         multidomination.
        :param first: Node, can be started from a certain point in structure
        :return: iterator through nodes
        """

        def _iterate(node):
            yield node
            for child in node.get_children():
                _iterate(child)

        return _iterate(first)

    @staticmethod
    def list_visible_nodes_once(first):
        """
        Do left-first iteration through all nodes and return an iterator
        where only first instance
         of each node is present.
        :param first: Node, can be started from a certain point in structure
        :return: iterator through nodes
        """
        result = []

        def _iterate(node):
            if node not in result:
                result.append(node)
                for child in node.get_visible_children():
                    _iterate(child)

        _iterate(first)
        return result

    @staticmethod
    def list_nodes_once(first):
        """
        Do left-first iteration through all nodes and return a list where
        only first instance of
        each node is present.
        :param first: Node, start from a certain point in structure
        :return: iterator through nodes
        """
        result = []

        def _iterate(node):
            if node not in result:
                result.append(node)
                for child in node.get_children():
                    _iterate(child)

        _iterate(first)
        return result

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
        return (x for x in self.nodes.values() if x.is_visible())

    def update_forest_gloss(self):
        """ Draw the gloss text on screen, if it exists. """
        if self.gloss_text:
            if prefs.show_gloss_text:
                if not self.gloss:
                    self.gloss = self.create_node(synobj=None, node_type=g.GLOSS_NODE)
                    self.gloss.text = self.gloss_text
            elif self.gloss:
                self.remove_from_scene(self.gloss)
                self.gloss = None
        elif self.gloss:
            self.remove_from_scene(self.gloss)
            self.gloss = None

    def set_visualization(self, name):
        """ Switches the active visualization to visualization with given key
        :param name: string
        """
        if self.visualization and self.visualization.say_my_name() == name:
            self.visualization.reselect()
        else:
            vs = self.main.visualizations
            self.visualization = vs.get(name, vs.get(prefs.default_visualization, None))
            self.vis_data = {'name': self.visualization.say_my_name()}
            self.visualization.prepare(self)
        self.main.graph_scene.manual_zoom = False

    def update_visualization(self):
        """ Verify that the active visualization is the same as defined in
        the vis_data (saved visualization state)
        :return: None
        """
        name = self.vis_data.get('name', prefs.default_visualization)
        if (not self.visualization) or name != self.visualization.say_my_name():
            self.set_visualization(name)

    # ### Maintenance and support methods
    # ################################################

    def __iter__(self):
        return self.trees.__iter__()

    def textual_form(self, tree=None, node=None):
        """ return (unicode) version of linearizations of all trees with
        traces removed --
            as close to original sentences as possible. If tree or node is given,
            return linearization of only that.
        :param tree: Tree instance
        :param node: Node instance
        """

        def _tree_as_text(tree, node, gap):
            """ Cheapo linearization algorithm for Node structures."""
            print('tree_as_text ', tree, node, gap)
            l = []
            if node in tree.sorted_constituents:
                i = tree.sorted_constituents.index(node)
                for n in tree.sorted_constituents[i:]:
                    l.append(str(n.syntactic_object))
            return gap.join(l)

        if tree:
            return _tree_as_text(tree, tree.top, ' ')
        elif node:
            return _tree_as_text(node.tree[0], node, ' ')
        else:
            trees = []
            for tree in self.trees:
                new_line = _tree_as_text(tree, tree.top, ' ')
                if new_line:
                    trees.append(new_line)
            return '/ '.join(trees)

    def syntax_trees_as_string(self):
        """


        :return:
        """
        s = []
        for tree in self.trees:
            if tree.top.is_constituent:
                s.append(tree.top.syntactic_object.print_tree())
        return '\n'.join(s)

    # Scene and storage ---------------------------------------------------------------

    def store(self, item):
        """ Confirm that item is stored in some dictionary or other storage
        in forest
        :param item:
        """
        # if isinstance(item, ConstituentNode):
        # self.nodes[item.key] = item
        # elif isinstance(item, FeatureNode):
        # self.features[item.key] = item

        if isinstance(item, Node):
            self.poke('nodes')
            self.nodes[item.save_key] = item
            self.node_types.add(item.node_type)
            if item.syntactic_object:
                # remember to rebuild nodes_by_uid in undo/redo, as it is not
                #  stored in model
                self.nodes_from_synobs[item.syntactic_object.save_key] = item
        elif isinstance(item, Edge):
            self.poke('edges')
            self.edges[item.save_key] = item
            self.edge_types.add(item.edge_type)
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

    def add_all_to_scene(self):
        """ Put items belonging to this forest to scene """
        if self.in_display:
            for item in self.get_all_objects():
                if not item.parentItem():
                    self.scene.addItem(item)

    def add_to_scene(self, item):
        """ Put items belonging to this forest to scene
        :param item:
        """
        if self.in_display:
            sc = item.scene()
            if not sc:
                self.scene.addItem(item)
            elif sc != self.scene:
                print('has scene already (%s), but not this scene. Overriding.' % sc)
                self.scene.addItem(item)

    def remove_from_scene(self, item):
        """ Remove item from this scene
        :param item:
        :return:
        """
        sc = item.scene()
        if sc == self.scene:
            sc.removeItem(item)
        elif sc:
            print('unknown scene for item %s : %s ' % (item, sc))
            sc.removeItem(item)
            print(' - removing anyways')

    # Getting objects ------------------------------------------------------

    def get_all_objects(self):
        """ Just return all objects governed by Forest -- not all scene objects 
        :return: iterator through objects
        """
        for n in self.trees:
            yield (n)
        for n in self.nodes.values():
            yield (n)
        for n in self.edges.values():
            yield (n)
        for n in self.others.values():
            yield (n)
        for n in self.projections.values():
            if n.visual:
                yield (n.visual)
        for n in self.bracket_manager.get_brackets():
            yield (n)

    def get_node(self, constituent):
        """
        Returns a node corresponding to a constituent
        :rtype : kataja.BaseConstituentNode
        :param constituent: syntax.BaseConstituent
        :return: kataja.ConstituentNode
        """
        return self.nodes_from_synobs.get(constituent.save_key, None)

    def get_constituent_edges(self):
        """ Return generator of constituent edges
        :return: generator
        """
        return (x for x in self.edges.values() if
                x.edge_type == g.CONSTITUENT_EDGE and x.is_visible())

    def get_constituent_nodes(self):
        """ Return generator of constituent nodes
        :return: generator
        """
        return (x for x in self.nodes.values() if
                isinstance(x, BaseConstituentNode) and x.isVisible())

    def get_feature_nodes(self):
        """ Return generator of feature nodes
        :return: generator
        """
        return (x for x in self.nodes.values() if isinstance(x, FeatureNode))

    def get_attribute_nodes(self):
        """ Return generator of attribute nodes
        :return: generator
        """
        return (x for x in self.nodes.values() if isinstance(x, AttributeNode))

    # Drawing and updating --------------------------------------------

    def draw(self):
        """ Update all trees in the forest according to current visualization
        """
        if not self.in_display:
            print("Why are we drawing a forest which shouldn't be in scene")
        print('draw for forest called')
        sc = ctrl.graph_scene
        sc.stop_animations()
        for tree in self.trees:
            tree.top.update_visibility()  # fixme
        self.bracket_manager.update_brackets()
        self.update_projections()
        self.update_forest_gloss()
        self.visualization.draw()
        if not sc.manual_zoom:
            sc.fit_to_window()
        sc.start_animations()
        ctrl.graph_view.repaint()

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

    # ##### Projections ##########################################

    def update_projection_map(self, node, old_head, new_head):
        """ Projection map keeps track of all projections, e.g. chains of nodes, where the head
        is projected through all of the member nodes. These projections may be displayed in
        various ways (see update_projection_visual).

         This method takes one node which has had its 'head' changed. It updates the projection
         chain accordingly, or creates a new chain, or deletes one.
        :param node: node instance with head attribute
        :param old_head: old value for head, None or node instance
        :param new_head: new value for head, None or node instance
        :return:
        """
        if old_head and old_head is not new_head:
            pd = self.projections.get(old_head.save_key, None)
            if pd:
                if old_head is node:
                    del self.projections[old_head.save_key]
                    if pd.visual:
                        self.remove_from_scene(pd.visual)
                else:
                    pd.remove_from_chain(old_head)
        if new_head:
            pd = self.projections.get(new_head.save_key, None)
            if not pd:
                pd = ProjectionData(new_head, next(self.projection_rotator))
                self.projections[new_head.save_key] = pd
            if node not in pd:
                pd.add_to_chain(node)

    def update_projection_visual(self, node, new_head):
        """ Take one node and update its projection displays according to current settings
        :param node:
        :param new_head:
        :return:
        """
        strong_lines = ctrl.fs.projection_strong_lines

        node.set_projection_display(None)
        for edge in node.get_edges_down(similar=True):
            edge.set_projection_display(None, None)
        for edge in node.get_edges_up(similar=True):
            edge.set_projection_display(None, None)

        if new_head:
            projection = self.projections[new_head.save_key]
            if ctrl.fs.projection_highlighter:
                if not projection.visual:
                    projection.add_visual()
                self.add_to_scene(projection.visual)
                projection.visual.update()
            else:
                if projection.visual:
                    self.remove_from_scene(projection.visual)
                    projection.visual = None
            if ctrl.fs.projection_colorized:
                color_id = projection.color_id
            else:
                color_id = None
            for edge in projection.get_edges():
                edge.set_projection_display(strong_lines, color_id)
            if len(projection.chain) > 1:
                for n in projection.chain:
                    n.set_projection_display(color_id)

    def update_projections(self):
        """ Try to guess projections in the tree based on labels and aliases, and once this is
        done, further updates check that the dict of projections is up to date. Calls to update
        the visual presentation of projections too.
        :return:
        """
        for tree in self.trees:
            for node in tree.sorted_constituents:
                if self.guessed_projections:
                    head = node.head
                else:
                    # don't use set_projection as it will rewrite labels and
                    # aliases around this node, making a mess
                    head = node.guess_projection()
                if head:
                    self.update_projection_map(node, None, head)
        for key, projection in list(self.projections.items()):
            if not projection.verify_chain():
                del self.projections[key]
                if projection.visual:
                    self.remove_from_scene(projection.visual)
        # fix labels to follow the guessed projections if we just guessed them.
        if not self.guessed_projections:
            for key, projection in list(self.projections.items()):
                projection.head.fix_projection_labels()
        self.guessed_projections = True
        self.update_projection_display()

    def update_projection_display(self):
        """ Don't change the projection data structures, but just draw them according to current
        drawing settings. It is quite expensive since the new settings may draw less than
        previous settings and this would mean removing projection visuals from nodes and edges.
        This is done by removing all projection displays before drawing them.
        :return:
        """
        strong_lines = ctrl.fs.projection_strong_lines
        colorized = ctrl.fs.projection_colorized
        highlighter = ctrl.fs.projection_highlighter
        for node in self.get_constituent_nodes():
            node.set_projection_display(None)
        for edge in self.get_constituent_edges():
            edge.set_projection_display(None, None)
        for key, projection in self.projections.items():
            if highlighter:
                if not projection.visual:
                    projection.add_visual()
                    self.add_to_scene(projection.visual)
                elif projection.visual.scene() != self.scene:
                    self.add_to_scene(projection.visual)
                projection.visual.update()
            else:
                if projection.visual:
                    self.remove_from_scene(projection.visual)
                    projection.visual = None
            if colorized:
                color_id = projection.color_id
            else:
                color_id = None

            if strong_lines or colorized:
                for edge in projection.get_edges():
                    edge.set_projection_display(strong_lines, color_id)
                if len(projection.chain) > 1:
                    for node in projection.chain:
                        node.set_projection_display(color_id)

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
        """ After disconnections there may be multidominated nodes whose
        parents are in different trees.
        In most of syntaxes these shouldn't happen: there is no disconnection
        activity to create such things.

        When user disconnects a node, it is to work with branches separately:
        a multidominated node should get its own
        copy.

        However there is a remote possibility for creating them by merging
        non-root node from another tree to
        construction, so the option should be there.

        :return:
        """
        pass

    # Trees ---------------------------------------------------------------

    def update_tree_for(self, node):
        """ Validate or create the trees (containers) for a given node.
        :param node: root to check. Only ConstituentNodes can be roots
        :return:
        """
        passed = set()
        my_tops = set()
        forest_tops = set((x.top for x in self.trees))

        def walk_to_top(n):
            """ Walk upwards in tree(s), starting from this node and find the topmost nodes.
            :param n:
            :return:
            """
            passed.add(n)
            parents = n.get_parents(only_similar=False, only_visible=False)
            if parents:
                for parent in parents:
                    if parent not in passed:
                        walk_to_top(parent)
            else:
                my_tops.add(n)

        walk_to_top(node)
        # now we have the topmost nodes _for this node_, so we can
        # check if there exists trees starting with these nodes.

        for my_top_node in my_tops:
            found = None
            for tree in list(self.trees):
                if my_top_node is tree.top:
                    found = tree
                    break
                elif not tree.is_valid():
                    self.remove_tree(tree)
            if found:
                # found a good tree, ask it to update.
                found.update_items()
            else:
                self.create_tree_for(my_top_node)
            # case where node still remains in an old tree but is disconnected and starting another tree
            for tree in list(my_top_node.tree):
                if tree.top not in my_tops:
                    # so we have a tree that is referring to structurally separate nodes (not in
                    # my_tops, the locally avaialable top nodes). Remove references to it from
                    # everyone down from here.
                    my_top_node.remove_from_tree(tree, recursive_down=True)

        if node not in my_tops:
            for tree in list(self.trees):
                if tree.top is node:
                    self.remove_tree(tree)
                elif not tree.top.is_top_node():
                    print('***** found a bad bad tree *****')
                    ctrl.main.add_message('***** found a bad bad tree *****')
                    self.remove_tree(tree)

    def create_tree_for(self, node):
        """ Create new tree around given node.
        :param node:
        :return:
        """
        tree = Tree(top=node)
        self.add_to_scene(tree)
        self.trees.append(tree)
        tree.show()
        tree.update_items()
        return tree

    def remove_tree(self, tree):
        """ Remove tree that has become unnecessary: either because it is subsumed into another
        tree or because it is empty.
        :param tree:
        :return:
        """
        for node in tree.sorted_nodes:
            node.remove_from_tree(tree)
        self.trees.remove(tree)
        self.remove_from_scene(tree)

    def get_first_free_constituent_name(self):
        """ Generate a name for constituent, ABCDEF... and then abcdef...,
        then AA, AB, AC...
         until a free (not used in this forest) is found.
        :return: String
        """
        names = [node.syntactic_object.label for node in self.nodes.values() if
                 node.node_type == g.CONSTITUENT_NODE and node.syntactic_object]
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

    # ### Primitive creation of forest objects ################################

    def create_node(self, synobj=None, relative=None, pos=None, node_type=1, text=None):
        """ This is generic method for creating all of the Node subtypes.
        Keep it generic!
        :param synobj: If syntactic object is passed here, the node created
        will be a wrapper around this syntactic object
        :param relative: node will be relative to given node, pos will be interpreted relative to
        given node and new node will have the same tree as a parent.
        :param pos:
        :param node_type:
        :return:
        """
        # First check that the node doesn't exist already
        if synobj:
            n = self.get_node(synobj)
            if n:
                return n

        node_class = ctrl.node_classes.get(node_type)
        # Create corresponding syntactic object if necessary
        if not synobj:
            if hasattr(node_class, 'create_synobj'):
                synobj = node_class.create_synobj(text)
        if synobj:
            node = node_class(synobj)
        else:
            node = node_class(text)
        # after_init should take care that syntactic object is properly
        # reflected by node's connections (call node.reflect_synobj()?)
        node.after_init()
        if relative:
            node.copy_position(relative)
        if pos:
            node.set_original_position(pos)
            # node.update_position(pos)

        #if not relative:
        #    self.update_tree_for(node)
        # if node is added to tree, it is implicitly added to scene. if not, this takes care of it:
        self.add_to_scene(node)
        # node.fade_in()

        # resetting node by visualization is equal to initializing node for
        # visualization. e.g. if nodes are locked to position in this vis,
        # then lock this node.
        if self.visualization:
            self.visualization.reset_node(node)
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
        host.update_trees()
        self.add_to_scene(AN)
        AN.update_visibility()
        return AN

    def create_edge(self, start=None, end=None, edge_type='', direction='', fade=False):
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
        if fade and self.in_display:
            rel.fade_in()
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


        # Cosmetic improvemet, if gloss is created by editing the gloss text
        # field. (not present anymore)
        # ee = ctrl.ui.get_node_edit_embed()
        # if ee and ee.isVisible():
        #     pos = ee.master_edit.pos()
        #     scene_pos = ctrl.graph_view.mapToScene(ee.mapToParent(pos))
        #     gn.set_original_position(scene_pos)
        return gn

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
        # self.update_tree_for(root_node)

    def create_trees_from_string(self, text):
        """ Use this to initially draw the trees from a bracket notation or
        whatever parser can handle. This doesn't clean up the forest before
        creating new nodes, so make sure that this is drawn on empty forest
        or be prepared for consequences.
        :param text: string that the parser can handle
        """
        text = text.strip()
        self.parser.parse_into_forest(text)
        if self.settings.uses_multidomination:
            self.settings.uses_multidomination = False
            self.traces_to_multidomination()
            # traces to multidomination will toggle uses_multidomination to True

    def read_definitions(self, definitions):
        """
        :param definitions: Try to set features and glosses according to
        definition strings for nodes in tree.
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
        index = node.index
        if not index:
            index = self.chain_manager.next_free_index()
            node.index = index
        assert index
        constituent = ctrl.Constituent(label='t', index=index)
        trace = self.create_node(synobj=constituent, relative=node)
        trace.is_trace = True
        # if new_chain:
        # self.chain_manager.rebuild_chains()
        # if self.settings.uses_multidomination:
        # trace.hide()
        return trace

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

    ############# Deleting items
    # ######################################################
    # item classes don't have to know how they relate to each others.
    # here when something is removed from scene, it is made sure that it is
    # also removed
    # from items that reference to it.

    def delete_node(self, node, ignore_consequences=False):
        """ Delete given node and its children and fix the tree accordingly
        :param node:
        :param ignore_consequences: don't try to fix things like connections,
        just delete.
        Note: This and other complicated revisions assume that the target tree is 'normalized' by
        replacing multidomination with traces. Each node can have only one parent.
        This makes calculation easier, just remember to call multidomination_to_traces and
        traces_to_multidomination after deletions.
        """
        # -- connections to other nodes --
        # print('deleting node: ', node)
        if not ignore_consequences:
            for edge in list(node.edges_down):
                if edge.end:
                    self.delete_node(edge.end)  # this will also disconnect node
                else:
                    self.disconnect_edge(edge)
            for edge in list(node.edges_up):
                self.disconnect_edge(edge)

        # -- ui elements --
        self.main.ui_manager.remove_ui_for(node)
        # -- brackets --
        self.bracket_manager.remove_brackets(node)
        # -- dictionaries --
        if node.save_key in self.nodes:
            self.poke('nodes')
            del self.nodes[node.save_key]
        # -- check if it is last of its type --
        found = False
        my_type = node.node_type
        for n in self.nodes.values():
            if n.node_type == my_type:
                found = True
                break
        if not found:
            self.node_types.remove(my_type)
        # -- synobj-to-node -mapping (is it used anymore?)
        if node.syntactic_object and node.syntactic_object.save_key in self.nodes_from_synobs:
            del self.nodes_from_synobs[node.syntactic_object.save_key]

        self.update_tree_for(node)
        # -- scene --
        self.remove_from_scene(node)
        # -- undo stack --
        node.announce_deletion()

    def delete_edge(self, edge, ignore_consequences=False):
        """ remove from scene and remove references from nodes
        :param edge:
        :param ignore_consequences: don't try to fix things like connections,
        just delete.
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
                    self.update_tree_for(start_node)
            if end_node:
                if edge in end_node.edges_down:  # shouldn't happen
                    end_node.poke('edges_down')
                    end_node.edges_down.remove(edge)
                if edge in end_node.edges_up:
                    end_node.poke('edges_up')
                    end_node.edges_up.remove(edge)
                    self.update_tree_for(end_node)
        # -- ui elements --
        self.main.ui_manager.remove_ui_for(edge)
        # -- dictionaries --
        if edge.save_key in self.edges:
            self.poke('edges')
            del self.edges[edge.save_key]
        # -- check if it is last of its type --
        found = False
        my_type = edge.edge_type
        for e in self.edges.values():
            if e.edge_type == my_type:
                found = True
                break
        if not found:
            self.edge_types.remove(my_type)
        # -- scene --
        self.remove_from_scene(edge)
        # -- undo stack --
        edge.announce_deletion()

    def delete_item(self, item, ignore_consequences=False):
        """ User-triggered deletion (e.g backspace on selection)
        :param item: item from selection. can be anything that can be selected
        :param ignore_consequences: don't try to fix remainders (because
        deletion is part of
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

    # there are edges that are initially not connected anywhere and which
    # need to be able to connect and disconnect
    # start and end points separately

    def set_edge_start(self, edge, new_start):
        """

        :param edge:
        :param new_start:
        """
        assert new_start.save_key in self.nodes
        if edge.start:
            edge.start.poke('edges_down')
            edge.start.edges_down.remove(edge)
        if edge.end:
            edge.end.disconnect_in_syntax(edge)
        edge.connect_end_points(new_start, edge.end)
        if edge.end:
            edge.end.connect_in_syntax(edge)
        new_start.poke('edges_down')
        new_start.edges_down.append(edge)

    def set_edge_end(self, edge, new_end):
        """

        :param edge:
        :param new_end:
        """
        assert new_end.save_key in self.nodes
        if edge.end:
            edge.end.disconnect_in_syntax(edge)
            edge.end.poke('edges_up')
            edge.end.edges_up.remove(edge)
            self.update_tree_for(edge.end)
        edge.connect_end_points(edge.start, new_end)
        new_end.poke('edges_up')
        new_end.edges_up.append(edge)
        new_end.connect_in_syntax(edge)
        self.update_tree_for(new_end)
        self.update_tree_for(edge.start)

    def fix_stubs_for(self, node):
        """ Make sure that node (ConstituentNode) has binary children.
        Creates stubs if needed, and removes stubs if
        node has two empty stubs.
        :param node: node to be fixed (ignore anything but constituent nodes)
        :return: None
        """
        if not isinstance(node, BaseConstituentNode):
            return
        real_children = []
        placeholders = []
        for child in node.get_children():
            if child.is_placeholder():
                placeholders.append(child)
            else:
                real_children.append(child)
        if len(real_children) == 1 and len(placeholders) == 0:
            align = node.get_edge_to(real_children[0]).alignment
            placeholder_align = g.NO_ALIGN
            if align == g.LEFT:
                placeholder_align == g.RIGHT
            elif align == g.RIGHT:
                placeholder_align == g.LEFT
            placeholder = self.create_placeholder_node(node.current_scene_position)
            self.connect_node(node, placeholder, direction=placeholder_align)
            node.update_trees()
        elif not real_children:
            for ph in placeholders:
                edge = node.get_edge_to(ph, g.CONSTITUENT_EDGE)
                if edge:
                    self.delete_edge(edge)
                self.delete_node(ph)

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
        """ Make sure that all edges are checked to update their visibility.
        This can be called multiple
        times, but the visibility check is done only once.
        """
        self._do_edge_visibility_check = True

    def edge_visibility_check(self):
        """ Perform check for each edge: hide them if their start/end is
        hidden, show them if necessary.
        changing edge.visible will cause chain reaction:
        edge.visible -> edge.if_changed_visible ->  edge.update_visibility
        """
        if self._do_edge_visibility_check:
            show_edges = self.settings.shows_constituent_edges
            for edge in self.edges.values():
                if edge.edge_type == g.CONSTITUENT_EDGE:
                    if not show_edges:
                        edge.visible = False
                        continue
                    start = edge.start
                    end = edge.end
                    if start and not start.is_visible():
                        edge.visible = False
                    elif end and not end.is_visible():
                        edge.visible = False
                    elif start and not self.visualization.show_edges_for(start):
                        edge.visible = False
                    elif not (start or end):
                        self.delete_edge(edge)
                    else:
                        edge.visible = True
                else:
                    if edge.start:
                        edge.visible = edge.start.is_visible()
                    else:
                        edge.visible = True
            self._do_edge_visibility_check = False

    def adjust_edge_visibility_for_node(self, node, visible):
        """

        :param node:
        :param visible:
        """
        if node.node_type == g.CONSTITUENT_NODE:
            if not visible:
                edges_visible = False
            elif self.visualization:
                edges_visible = self.visualization.show_edges_for(
                    node) and self.settings.shows_constituent_edges
            else:
                edges_visible = False
            for edge in node.edges_down:
                v = edge.visible
                if edge.edge_type == g.CONSTITUENT_EDGE:
                    edge.visible = edges_visible and (
                        (edge.end and edge.end.is_visible()) or not edge.end)
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
        self.update_tree_for(node)

    def add_comment_to_node(self, comment, node):
        """ Comments are connected the other way around compared to
        other unusual added nodes. Comments are parents and commented nodes
        are their children. It makes more sense in cases when you first add a
        comment and then drag an arrow out of it.

        :param comment:
        :param node:
        """
        self.connect_node(parent=node, child=comment, edge_type=g.COMMENT_EDGE)
        self.update_tree_for(node)

    def add_gloss_to_node(self, gloss, node):
        """

        :param gloss:
        :param node:
        """
        self.connect_node(parent=node, child=gloss)
        node.gloss = gloss.label
        self.update_tree_for(node)

    # ## order markers are special nodes added to nodes to signal the order
    # when the node was merged/added to forest
    #######################################################################

    def add_order_features(self, key='M'):
        """

        :param key:
        """
        help_text = ''
        show_label = False
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
                attr_node = self.create_attribute_node(node, attr_id, attribute_label=key,
                                                       show_label=show_label)

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
        if S and not self.settings.shows_select_order:
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

    # ### Minor updates for forest elements
    # #######################################################################

    def reform_constituent_node_from_string(self, text, node):
        """

        :param text:
        :param node:
        """
        new_nodes = self.parser.parse_into_forest(text)
        if new_nodes:
            self.replace_node(node, new_nodes[0])

    # ### Switching between multidomination and traces
    # ######################################

    def group_traces_to_chain_head(self):
        """


        """
        # print('group_traces_to_chain_head called in ', self)
        self.chain_manager.group_traces_to_chain_head()

    def traces_to_multidomination(self):
        """


        """
        # print('traces_to_multidomination called in ', self)
        self.chain_manager.traces_to_multidomination()
        for node in self.nodes.values():
            if hasattr(node, 'is_trace') and node.is_trace:
                print('We still have a visible trace after '
                      'traces_to_multidomination')
                # else:
                #    print('no is_trace -property')

    def multidomination_to_traces(self):
        """


        """
        # print('multidomination_to_traces called in ', self)
        self.chain_manager.multidomination_to_traces()


        # # if using traces, merge original and leave trace, or merge trace
        # and leave original. depending on which way the structure is built.
        # print '-------------------'
        # print 'dropping for merge'

        # print 'f.settings.use_multidomination:',
        # f.settings.use_multidomination
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

    def connect_node(self, parent=None, child=None, direction='', edge_type=None, fade_in=False):
        """ This is for connecting nodes with a certain edge. Calling this
        once will create the necessary links for both partners.
        Sanity checks:
        - Immediate circular links (child becomes immediate parent of its
        immediate parent) are not allowed.
        - If items are already linked with this edge type, error is raised.
        - Cannot link to itself.
        This needs to be robust.
        :param parent: Node
        :param child: Node
        :param direction:
        :param edge_type: optional, force edge to be of given type
        """

        #print('--- connecting node %s to %s ' % (child, parent))
        # Check for arguments:
        if parent == child:
            raise ForestError('Connecting to self')
        if not parent and child:
            raise ForestError('Trying to connect nodes, but other is missing (parent:%s, '
                              'child%s)' % (parent, child))

        if not edge_type:
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

        # Create edge and make connections
        new_edge = self.create_edge(edge_type=edge_type, direction=direction, fade=fade_in)
        new_edge.connect_end_points(parent, child)
        child.poke('edges_up')
        parent.poke('edges_down')
        if direction == g.LEFT:
            child.edges_up.insert(0, new_edge)
            parent.edges_down.insert(0, new_edge)
        else:
            child.edges_up.append(new_edge)
            parent.edges_down.append(new_edge)
        child.connect_in_syntax(new_edge)
        # fix other edge aligns: only one left align and one right align,
        # n center aligns, and if only one child, it has center align.
        edges = [edge for edge in parent.edges_down if edge.edge_type == edge_type]
        assert (edges)
        if len(edges) == 1:
            edges[0].alignment = g.NO_ALIGN
        elif len(edges) == 2:
            edges[0].alignment = g.LEFT
            edges[-1].alignment = g.RIGHT
        else:
            edges[0].alignment = g.LEFT
            for edge in edges[1:-1]:
                edge.alignment = g.NO_ALIGN
            edges[-1].alignment = g.RIGHT

        if hasattr(parent, 'rebuild_brackets'):
            parent.rebuild_brackets()
        if hasattr(child, 'rebuild_brackets'):
            child.rebuild_brackets()
        parent.update_label()
        child.update_label()
        #print('--- finished connect')

        return new_edge

    def disconnect_edge(self, edge):
        """ Does the local mechanics of edge removal
        :param edge:
        :return:
        """
        if edge.start:
            edge.start.poke('edges_down')
            edge.start.edges_down.remove(edge)
        if edge.end:
            edge.end.poke('edges_up')
            edge.end.edges_up.remove(edge)
            edge.end.disconnect_in_syntax(edge)
        self.delete_edge(edge)

    def disconnect_node(self, parent=None, child=None, edge_type='', ignore_missing=False,
                        edge=None):
        """ Removes and deletes a edge between two nodes. If asked to do so, can reset
        projections and tree ownerships, but doesn't do it automatically, as disconnecting is
        often part of more complex series of operations.
        :param parent:
        :param child:
        :param edge_type:
        :param ignore_missing: raise error if suitable edge is not found
        :param edge: if the edge that connects nodes is already identified, it can be given directly
        """
        # cut the projection between the nodes
        if edge:
            parent = edge.start
            child = edge.end
        if hasattr(parent, 'head') and hasattr(child, 'head'):
            if parent.head is child.head:
                print('trying to cut projection chain...')
                if hasattr(parent, 'set_projection'):
                    print('cutting projection chain...')
                    parent.set_projection(None)
        # then remove the edge
        if not edge:
            edge = parent.get_edge_to(child, edge_type)
            if not edge:
                if ignore_missing:
                    return
                else:
                    raise ForestError("Trying to remove edge that doesn't exist")
        self.disconnect_edge(edge)


    def replace_node(self, old_node, new_node, only_for_parent=None, replace_children=False,
                     can_delete=True):
        """  When replacing a node we should make sure that edges get fixed too.
        :param old_node: node to be replaced -- if all occurences get
        replaced, delete it
        :param new_node: replacement node
        :param only_for_parent: replace only one parent connection
        :param replace_children: new node also gains parenthood for old
        node's children
        :param can_delete: replaced node can be deleted
        :return:
        """
        # print('replace_node %s %s %s %s' % (old_node, new_node,
        # only_for_parent, replace_children))

        assert (old_node != new_node)  # if this can happen, we'll probably have
        # infinite loop somewhere
        new_node.copy_position(old_node)
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

        self.update_tree_for(new_node)
        if (not old_node.edges_up) and can_delete:
            # old_node.update_visibility(active=False, fade=True)
            self.delete_node(old_node)

    # ########### Complex node operations ##############################

    def delete_unnecessary_merger(self, node):
        """

        :param node:
        :raise ForestError:
        """
        if not isinstance(node, BaseConstituentNode):
            raise ForestError("Trying to treat wrong kind of node as ConstituentNode and "
                              "forcing it to binary merge")

        if hasattr(node, 'index'):
            i = node.index
        else:
            i = ''
        children = list(node.get_children())
        real_children = []
        placeholders = []
        trees = set(node.tree)
        for child in children:
            if child.is_placeholder():
                placeholders.append(child)
            else:
                real_children.append(child)
        for child in real_children:
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
                self.disconnect_node(node, child)
            else:
                if bad_parents:
                    # more complex case
                    m = "Removing node would make parent to have same node as " \
                        "both left and right child. " + "Removing parent too."
                    ctrl.add_message(m)
                    self.disconnect_node(node, child)
                    for parent in bad_parents:
                        for grandparent in parent.get_parents():
                            self.disconnect_node(grandparent, parent)
                            self.disconnect_node(parent, child)
                            self.connect_node(grandparent, child)

                if good_parents:
                    # normal case
                    self.disconnect_node(node, child, ignore_missing=True)
                    for parent in good_parents:
                        edge = parent.get_edge_to(node)
                        self.disconnect_node(parent, node)
                        self.connect_node(parent, child, direction=edge.alignment)
            if i:
                child.set_index(i)
            self.delete_node(node)
            for parent in bad_parents:
                self.delete_node(parent)
                # if right.is_placeholder():
                # self.delete_node(right)
                # if left.is_placeholder():
                # self.delete_node(left)
        for tree in trees:
            tree.update_items()

    def add_children_for_constituentnode(self, parent: BaseConstituentNode, pos=None,
                                         head_left=True):
        """ User adds children for leaf node. If binary nodes are used, new nodes are added in
        pairs. Because of this, be careful for using this in other than user-triggered situations.
        If the node where children is added is projecting, new node will take its identity and
        will become the one projecting.
        :param parent:
        :param pos:
        :param head_left: adding node to left or right -- if binary nodes, this marks which one
        will be projecting.
        :return:
        """
        # Let's spend some effort to do sanity check if parent can have
        # children added to it

        siblings = list(parent.get_ordered_children())
        if self.settings.only_binary_trees and len(siblings) > 1:
            raise ForestError("Trying to add third child for binary tree")

        # These steps are safe, connect node is smart enough to deal with
        # unary/ binary children.
        # 1) Create the child as asked to do
        new_node = self.create_node(relative=parent)
        new_node.current_position = pos
        if head_left:
            main_align = g.LEFT
            other_align = g.RIGHT
        else:
            main_align = g.RIGHT
            other_align = g.LEFT
        self.connect_node(parent=parent, child=new_node, direction=main_align, fade_in=True)

        # 2) create a pair if necessary
        if self.settings.only_binary_trees and not siblings:
            ox, oy, oz = pos
            if other_align == g.RIGHT:
                ox += 40
            else:
                ox -= 40
            other_node = self.create_node(relative=parent)
            other_node.current_position = ox, oy, oz
            self.connect_node(parent=parent, child=other_node, direction=other_align, fade_in=True)
        # 3) repair trees to include new nodes
        parent.update_trees()
        # 4) reassign projections
        if hasattr(parent, 'head') and parent.head and parent.head is parent:
            new_node.label = parent.label
            new_node.alias = parent.alias
            new_node.set_projection(new_node)
            parent.set_projection(new_node, replace_up=True)

    def merge_to_top(self, top, new, merge_to_left, merger_pos):
        """
        :param top:
        :param new:
        :param merge_to_left:
        :param merger_pos:
        :return:
        """
        if hasattr(new, 'index'):
            # if new_node and old_node belong to same tree, this is a Move /
            # Internal merge situation and we
            # need to give the new_node an index so it can be reconstructed
            # as a trace structure
            if new.tree is top.tree:
                if not new.index:
                    new.index = self.chain_manager.next_free_index()
                # replace either the moving node or leftover node with trace
                # if we are using traces
                if self.traces_are_visible():
                    t = self.create_trace_for(new)
                    self.replace_node(new, t, can_delete=False)
        if merge_to_left:
            left = new
            right = top
        else:
            left = top
            right = new
        p = merger_pos[0], merger_pos[1], top.z
        merger_node = self.create_merger_node(left=left, right=right, pos=p, new=new)
        merger_node.copy_position(top)
        merger_node.current_position = p
        if self.traces_are_visible():
            self.chain_manager.rebuild_chains()

    def insert_node_between(self, inserted, parent, child, merge_to_left, insertion_pos):
        """ This is an insertion action into a tree: a new merge is created
        and inserted between two existing constituents. One connection is
        removed, but three are created.
        This happens when touch area in edge going up from node N is clicked,
        or if a node is dragged there.

        :param parent:
        :param child:
        :param inserted:
        :param merge_to_left:
        :param insertion_pos:
        """
        if hasattr(inserted, 'index'):
            # if inserted and child belong to same tree, this is a Move /
            # Internal merge situation and we
            # need to give the new_node an index so it can be reconstructed
            # as a trace structure
            moving_was_higher = None
            for tree in inserted.tree:
                moving_was_higher = tree.is_higher_in_tree(inserted, child)
                if moving_was_higher is not None:
                    break
            # returns None if they are not in same tree
            if moving_was_higher is not None:
                if not inserted.index:
                    inserted.index = self.chain_manager.next_free_index()
                # replace either the moving node or leftover node with trace
                # if we are using traces
                if self.traces_are_visible():
                    if moving_was_higher:
                        inserted = self.create_trace_for(inserted)
                    else:
                        t = self.create_trace_for(inserted)
                        self.replace_node(inserted, t, can_delete=False)

        edge = parent.get_edge_to(child)
        # store the projection and alignment info before disconnecting the edges
        head = None
        if hasattr(parent, 'head') and hasattr(child, 'head') and parent.head is child.head:
            head = parent.head

        align = edge.alignment
        self.disconnect_edge(edge)
        if merge_to_left:
            left = inserted
            right = child
        else:
            left = child
            right = inserted
        p = insertion_pos[0], insertion_pos[1], child.z
        merger_node = self.create_merger_node(left=left, right=right, pos=p, create_tree=False, new=inserted)
        merger_node.copy_position(child)
        merger_node.current_position = p
        self.connect_node(parent, merger_node, direction=align)
        parent.update_trees()
        if head:
            merger_node.set_projection(head)
        if self.traces_are_visible():
            self.chain_manager.rebuild_chains()

    def create_merger_node(self, left=None, right=None, pos=None, create_tree=True, new=None):
        """ Gives a merger node of two nodes. Doesn't try to fix their edges
        upwards
        :param left:
        :param right:
        :param pos:
        """
        if not pos:
            pos = (0, 0, 0)
        merger_const = ctrl.FL.merge(left.syntactic_object, right.syntactic_object)
        merger_node = self.create_node(synobj=merger_const, relative=right)
        merger_node.current_position = pos
        self.add_merge_counter(merger_node)
        self.connect_node(parent=merger_node, child=left, direction=g.LEFT, fade_in=new is left)
        self.connect_node(parent=merger_node, child=right, direction=g.RIGHT, fade_in=new is right)
        if create_tree:
            self.update_tree_for(merger_node)
        return merger_node

    def copy_node(self, node):
        """ Copy a node and make a new tree out of it
        :param node:
        """
        if not node:
            return
        new_c = node.syntactic_object.copy()
        new_node = self.create_node(new_c)
        new_node.copy_position(node)
        self.add_select_counter(new_node)
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
            # multidominated nodes can be folded if all parents are in scope
            # of fold
            elif folded.is_multidominated():
                can_fold = True
                for parent in parents:
                    if (parent not in fold_scope) or (parent in not_my_children):
                        not_my_children.add(folded)
                        can_fold = False
                        break
                if can_fold:
                    folded.fold_towards(node)
            # remember that the branch that couldn't be folded won't allow
            # any of its children to be
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
        fold_scope = (f for f in self.list_nodes_once(node) if f.folding_towards is node)
        for folded in fold_scope:
            print('unfolding ', folded)
            folded.folding_towards = None
            folded.folded_away = False
            folded.copy_position(node)
            folded.fade_in()
            folded.update_visibility()
            folded.update_bounding_rect()
        # this needs second round of update visibility, as child nodes may
        # yet not be visible, so edges to them
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
        return self.parser.parse_definition(string, node)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    trees = Saved("trees")  # the current line of trees
    nodes = Saved("nodes")
    edges = Saved("edges")
    others = Saved("others")
    settings = Saved("settings")
    rules = Saved("rules")
    vis_data = Saved("vis_data", watcher="visualization")
    derivation_steps = Saved("derivation_steps")
    merge_counter = Saved("merge_counter")
    select_counter = Saved("select_counter")
    comments = Saved("comments")
    gloss_text = Saved("gloss_text")
