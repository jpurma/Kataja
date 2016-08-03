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


import collections
import itertools
import statistics
import string
import random
import time

from PyQt5 import QtWidgets

import kataja.globals as g
from kataja.BracketManager import BracketManager
from kataja.ChainManager import ChainManager
from kataja.UndoManager import UndoManager
from kataja.Projection import Projection
from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from kataja.errors import ForestError
from kataja.parser.INodeToKatajaConstituent import INodeToKatajaConstituent
from kataja.singletons import ctrl, prefs, qt_prefs, classes
from kataja.saved.Group import Group
from kataja.saved.DerivationStep import DerivationStepManager
from kataja.saved.Edge import Edge
from kataja.saved.ForestSettings import ForestSettings, ForestRules
from kataja.saved.movables.Bracket import Bracket
from kataja.saved.movables.Node import Node
from kataja.saved.movables.Presentation import TextArea, Image
from kataja.saved.movables.Tree import Tree
from kataja.saved.movables.nodes.AttributeNode import AttributeNode
from kataja.saved.movables.nodes.BaseConstituentNode import BaseConstituentNode
from kataja.saved.movables.nodes.FeatureNode import FeatureNode
from kataja.utils import time_me


class Forest(SavedObject):
    """ Forest is a group of trees that together form one view.
    Often there needs to be more than one trees visible at same time,
     so that they can be compared or to show states of construction
      where some edges are not yet linked to the main root.
      Forest is the container for these.
      Forest also takes care of the operations manipulating, creating and
      removing trees. """

    def __init__(self, buildstring='', definitions=None, gloss_text='', comments=None,
                 synobjs=None):
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
        self.derivation_steps = DerivationStepManager(forest=self)
        self.trees = []
        self._update_trees = False
        self.nodes = {}
        self.edges = {}
        self.edge_types = set()
        self.node_types = set()
        self.groups = {}
        self.others = {}
        self.vis_data = {}
        self.projections = {}
        self.projection_rotator = itertools.cycle(range(3, 8))
        self.merge_counter = 0
        self.select_counter = 0
        self.comments = []
        self.gloss_text = ''
        self.ongoing_animations = set()
        self.guessed_projections = False
        self.halt_drawing = False
        self._marked_for_deletion = set()
        if synobjs:
            self.mirror_the_syntax(synobjs)
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
        :param updated_fields: list of names of elements that have been updated.
        :return: None
        """
        if 'nodes' in updated_fields:
            # rebuild from-syntactic_object-to-node -dict
            self.nodes_from_synobs = {}
            for node in self.nodes.values():
                if node.syntactic_object:
                    self.nodes_from_synobs[node.syntactic_object.uid] = node
            for tree in self.trees:
                tree.update_items()
        if 'vis_data' in updated_fields:
            self.restore_visualization()

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
        # self.nodes_by_uid[node.syntactic_object.uid] = node

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
        ctrl.disable_undo()
        self.update_colors()
        self.add_all_to_scene()
        self.update_visualization()
        self.scene.keep_updating_visible_area = True
        self.scene.manual_zoom = False
        self.draw()  # do draw once to avoid having the first draw in undo stack.
        ctrl.graph_scene.fit_to_window(soft=True)
        ctrl.resume_undo()

    def retire_from_drawing(self):
        """ Announce that this forest should not try to work with scene
        anymore --
         some other forest is occupying the scene now.
        :return:
        """
        for item in self.get_all_objects():
            self.remove_from_scene(item, fade_out=False)
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
            for child in node.get_children(similar=False, visible=False):
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
                for child in node.get_children(visible=True, similar=True):
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
                for child in node.get_children(similar=False, visible=False):
                    _iterate(child)

        _iterate(first)
        return result

    def visible_nodes(self):
        """ Any node that is visible. Ignore the type.
        :return:
        """
        return (x for x in self.nodes.values() if x.is_visible())

    # def constituents_grouped_to_trees(self):
    #     """ Return list of lists, where each list represents a tree and consists of flattened
    #     list of nodes belonging to that tree. This list of lists can be used to evaluate order
    #     and tree memberships of a single node, or used as a basis for constructing tree objects
    #
    #     Nodes are not necessarily constituent nodes!
    #     :return:
    #     """
    #     result = []
    #     roots = [n for n in self.nodes.values() if not n.get_parents()]
    #     for root in roots:
    #         result.append(Forest.list_nodes_once(root))
    #     return result
    #
    # def order_among_nodes(self, *nodes, source_list=None):
    #     """ Given iterable nodes, return list of lists that shows the nodes ordered by their
    #     topmost appearance in tree. e.g. given (A, B) and receiving
    #     [], [A, B], [A] would mean that there are three trees where in first A, B are not
    #     present, in second they are in this order and in third tree only A is present.
    #
    #     source_list can be given if there will be many similar comparisons, then the method won't
    #     recreate the source_list on every call
    #     :param nodes:
    #     :param source_list:
    #     :return:
    #     """
    #     if not source_list:
    #         source_list = self.constituents_grouped_to_trees()
    #     result = []
    #     for tree in source_list:
    #         sorted_nodes = []
    #         for item in tree:
    #             if item in nodes:
    #                 sorted_nodes.append(item)
    #         result.append(sorted_nodes)
    #     return result

    def get_numeration(self):
        for tree in self.trees:
            if tree.numeration:
                return tree
        tree = Tree(forest=self, numeration=True)
        self.add_to_scene(tree)
        self.trees.append(tree)
        tree.show()
        return tree

    def mirror_the_syntax(self, synobjs, numeration=None, other=None, msg=None, gloss=None,
                          transferred=None):
        """ This is a big important function to ensure that Nodes on display are only those that
        are present in syntactic objects. Clean up the residue, create those nodes that are
        missing and create the edges.
        :param synobjs: syntactic objects
        :param numeration: list of objects waiting to be processed
        :param other: what else we need?
        :param msg: message associated with this derivation step, this will be used as gloss
        :param gloss: gloss text for the whole forest
        :param transferred: list of items spelt out/transferred. These will form a group
        :return:
        """

        node_keys_to_validate = set(self.nodes.keys())
        edge_keys_to_validate = set(self.edges.keys())

        # Don't delete gloss node if we have message to show
        if msg and self.gloss:
            if self.gloss.uid in node_keys_to_validate:
                node_keys_to_validate.remove(self.gloss.uid)

        def recursive_add_for_creation(me, parent_node, parent_synobj):
            """ First we have to create new nodes close to existing nodes to avoid rubberbanding.
            To help this create a list of missing nodes with known positions.
            :param me:
            :param parent_node:
            :param parent_synobj:
            :return:
            """
            if isinstance(me, list):
                for item in me:
                    recursive_add_for_creation(item, parent_node, parent_synobj)
            else:
                node = self.get_node(me)
                if node:
                    if hasattr(me, 'label'):
                        node.label = me.label
                    node.update_label()
                    # print(me.label, node.label)
                    if node.uid in node_keys_to_validate:
                        node_keys_to_validate.remove(node.uid)
                    #x, y = node.current_scene_position
                    #all_known_x.append(x)
                    #all_known_y.append(y)
                    if node.node_type == g.FEATURE_NODE:
                        node.locked_to_node = parent_node # not me.unvalued
                    for tree in node.trees:
                        if not tree.numeration:
                            tree_counter.append(tree)
                    if parent_synobj and not parent_node:
                        nodes_to_create.append((parent_synobj, node.current_position))
                elif parent_node:
                    nodes_to_create.append((me, parent_node.current_position))
                else:
                    nodes_to_create.append((me, (0, 0)))
                if hasattr(me, 'get_parts'):
                    for part in me.get_parts():
                        recursive_add_for_creation(part, node, me)
                if hasattr(me, 'features'):
                    if isinstance(me.features, dict):
                        for feat in me.features.values():
                            recursive_add_for_creation(feat, node, me)
                    elif isinstance(me.features, (list, set, tuple)):
                        for feat in me.features:
                            recursive_add_for_creation(feat, node, me)

        # I guess that ordering of connections will be broken because of making
        # and deleting connections in unruly fashion
        def connect_if_necessary(parent, child, edge_type):
            edge = parent.get_edge_to(child, edge_type)
            if not edge:
                self.connect_node(parent, child, edge_type=edge_type, mirror_in_syntax=False)
            elif edge.uid in edge_keys_to_validate:
                edge_keys_to_validate.remove(edge.uid)

        def recursive_create_edges(synobj):
            node = self.get_node(synobj)
            if synobj in synobjs_done:
                return node
            synobjs_done.add(synobj)
            if isinstance(synobj, classes.Constituent):
                # part_count = len(synobj.get_parts())
                for part in synobj.get_parts():
                    child = recursive_create_edges(part)
                    if child:
                        connect_if_necessary(node, child, g.CONSTITUENT_EDGE)
                for feature in synobj.get_features():
                    nfeature = recursive_create_edges(feature)
                    if nfeature:
                        connect_if_necessary(node, nfeature, g.FEATURE_EDGE)
            elif isinstance(synobj, classes.Feature):
                if hasattr(synobj, 'get_parts'):
                    for part in synobj.get_parts():
                        child = recursive_create_edges(part)
                        if child and child.node_type == g.FEATURE_NODE:
                            connect_if_necessary(node, child, g.CHECKING_EDGE)
            return node

        def rec_add_item(item, result_set):
            result_set.append(self.get_node(item))
            for part in item.get_parts():
                result_set = rec_add_item(part, result_set)
            return result_set

        #if numeration:
        #    num_tree = self.get_numeration()

        #all_known_x = []
        #all_known_y = []

        scene_rect = ctrl.graph_view.mapToScene(ctrl.graph_view.rect()).boundingRect()
        #sc_left = scene_rect.x()
        sc_center = scene_rect.center().x()
        sc_middle = scene_rect.center().y()

        for tree_root in synobjs:
            synobjs_done = set()
            nodes_to_create = []
            tree_counter = []
            avg_x = 0
            avg_y = 0
            most_popular_tree = None
            recursive_add_for_creation(tree_root, None, None)
            #if all_known_x:
            #    avg_x = int(statistics.mean(all_known_x))
            #if all_known_y:
            #    avg_y = int(statistics.mean(all_known_y))

            # noinspection PyArgumentList
            most_popular_trees = collections.Counter(tree_counter).most_common(1)
            if most_popular_trees:
                most_popular_tree = most_popular_trees[0][0]

            for syn_bare, pos in nodes_to_create:
                x, y = pos
                if x == 0 and y == 0:
                    x = sc_center #left + 100
                    y = sc_middle #- 100
                if isinstance(syn_bare, classes.Constituent):
                    node = self.create_node(synobj=syn_bare, node_type=g.CONSTITUENT_NODE, pos=(x, y))
                elif isinstance(syn_bare, classes.Feature):
                    if syn_bare.unvalued and False:
                        x += sc_center + random.randint(-20, 10)
                        y += sc_middle + random.randint(20, 70)
                        node = self.create_node(synobj=syn_bare, node_type=g.FEATURE_NODE, pos=(x, y))
                    else:
                        node = self.create_node(synobj=syn_bare, node_type=g.FEATURE_NODE, pos=(x, y))
                else:
                    continue
                if most_popular_tree:
                    node.add_to_tree(most_popular_tree)

            # node.set_original_position(node.scene_position_to_tree_position((x, y)))
            recursive_create_edges(tree_root)

            if most_popular_tree:
                most_popular_tree.top = self.get_node(tree_root)
                most_popular_tree.update_items()
            else:
                self.create_tree_for(self.get_node(tree_root))

        # for item in numeration:
        #    node, trees = recursive_create(item, set())
        #    if node and not trees:
        #        node.add_to_tree(num_tree)
        # Delete invalid nodes and edges

        for key in node_keys_to_validate:
            node = self.nodes.get(key, None)
            if node:
                # noinspection PyTypeChecker
                self.delete_node(node)
        for key in edge_keys_to_validate:
            edge = self.edges.get(key, None)  # most of these should be deleted already by prev.
            if edge:
                # noinspection PyTypeChecker
                self.delete_edge(edge)
        for node in self.nodes.values():
            node.update_label()
            node.update_relations()

        # Update or create groups of transferred items
        old_groups = [gr for gr in self.groups.values() if gr.get_label_text().startswith(
            'Transfer')]
        all_new_items = set()
        all_old_items = set()
        if old_groups:
            for group in old_groups:
                all_old_items.update(set(group.selection))
        if transferred:
            new_groups = []
            if transferred:
                for transfer_top in transferred:
                    this_group = rec_add_item(transfer_top, [])
                    new_groups.append(this_group)
                    all_new_items.update(set(this_group))
            # Put items to groups if they aren't there
            if new_groups:
                if not old_groups:
                    for selection in new_groups:
                        new_g = self.create_group()
                        new_g.set_label_text('Transfer')
                        #new_g.fill = False
                        #new_g.outline = True
                        new_g.update_colors('accent5')
                        new_g.update_selection(selection)
                else:
                    # find partially matching group
                    for selection in new_groups:
                        group_to_add = None
                        for item in selection:
                            for group in old_groups:
                                if item in group.selection:
                                    group_to_add = group
                                    break
                            break
                        if group_to_add:
                            for item in selection:
                                group_to_add.add_node(item)
                        else:
                            new_g = self.create_group()
                            new_g.set_label_text('Transfer')
                            #new_g.fill = False
                            #new_g.outline = True
                            new_g.update_colors('accent5')
                            new_g.update_selection(selection)
                            new_g.update_selection(selection)
        if old_groups:
            # Remove items from groups where they don't belong
            items_to_remove = all_old_items - all_new_items
            to_remove = [[] for x in old_groups]
            for item in items_to_remove:
                for i, group in enumerate(old_groups):  # we can ignore newly created groups
                    if item in group.selection:
                        to_remove[i].append(item)
            for old_group, remove_list in zip(old_groups, to_remove):
                old_group.remove_nodes(remove_list)

        gt = ''
        if self.derivation_steps.is_first() or self.derivation_steps.is_last():
            if gloss and msg:
                gt = '\n'.join([gloss, '', msg.splitlines()[-1]])
            elif gloss:
                gt = gloss
            elif msg:
                gt = msg.splitlines()[-1]
        elif msg:
            gt = msg.splitlines()[-1]
        self.gloss_text = gt
        self.update_forest_gloss()
        self.guessed_projections = False

    def update_forest_gloss(self):
        """ Draw the gloss text on screen, if it exists. """
        if self.gloss_text:
            if not self.gloss:
                self.gloss = self.create_node(synobj=None, node_type=g.GLOSS_NODE)
                self.gloss.label = self.gloss_text
            elif self.gloss.text != self.gloss_text:
                self.gloss.label = self.gloss_text
            self.gloss.update_label()
            self.gloss.physics_x = False
            self.gloss.physics_y = False
            self.gloss.show()
        elif self.gloss:
            self.remove_from_scene(self.gloss)
            self.gloss = None

    def set_visualization(self, name, force=False):
        """ Switches the active visualization to visualization with given key
        :param name: string
        """
        if self.visualization and self.visualization.say_my_name() == name:
            self.visualization.reselect()
        else:
            vs = self.main.visualizations
            self.visualization = vs.get(name, vs.get(prefs.visualization, None))
            self.vis_data = {'name': self.visualization.say_my_name()}
            self.visualization.prepare(self)
            self.scene.keep_updating_visible_area = True
        self.main.graph_scene.manual_zoom = False

    def restore_visualization(self):
        name = self.vis_data.get('name', prefs.visualization)
        if (not self.visualization) or name != self.visualization.say_my_name():
            v = self.main.visualizations.get(name, None)
            if v:
                self.visualization = v
                v.prepare(self, reset=False)
                self.main.graph_scene.manual_zoom = False

    def update_visualization(self):
        """ Verify that the active visualization is the same as defined in
        the vis_data (saved visualization state)
        :return: None
        """
        name = self.vis_data.get('name', prefs.visualization)
        if (not self.visualization) or name != self.visualization.say_my_name():
            self.set_visualization(name)

    # ### Maintenance and support methods
    # ################################################

    def __iter__(self):
        return self.trees.__iter__()

    def textual_form(self, tree=None, node=None):
        """ return (unicode) version of linearizations of all trees with
        traces removed --
            as close to original sentences as possible. If trees or node is given,
            return linearization of only that.
        :param tree: Tree instance
        :param node: Node instance
        """

        def _tree_as_text(tree, node, gap):
            """ Cheapo linearization algorithm for Node structures."""
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
            if tree.top and tree.top.is_constituent:
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
            self.nodes[item.uid] = item
            self.node_types.add(item.node_type)
            if item.syntactic_object:
                # remember to rebuild nodes_by_uid in undo/redo, as it is not
                #  stored in model
                self.nodes_from_synobs[item.syntactic_object.uid] = item
        elif isinstance(item, Edge):
            self.poke('edges')
            self.edges[item.uid] = item
            self.reserve_update_for_trees()
            self.edge_types.add(item.edge_type)
        elif isinstance(item, TextArea):
            self.poke('others')
            self.others[item.uid] = item
        elif isinstance(item, Bracket):
            self.bracket_manager.store(item)

        else:
            key = getattr(item, 'uid', '') or getattr(item, 'key', '')
            if key and key not in self.others:
                self.poke('others')
                self.others[key] = item
            else:
                print('F trying to store broken type:', item.__class__.__name__)

    def add_all_to_scene(self):
        """ Put items belonging to this forest to scene """
        if self.in_display:
            for item in self.get_all_objects():
                sc = item.scene()
                if not sc:
                    self.scene.addItem(item)
                # if not item.parentItem():
                #    print('adding to scene: ', item)
                #    self.scene.addItem(item)

    def add_to_scene(self, item):
        """ Put items belonging to this forest to scene
        :param item:
        """
        if self.in_display:
            if isinstance(item, QtWidgets.QGraphicsItem):
                sc = item.scene()
                if not sc:
                    # print('..adding to scene ', item.uid )
                    self.scene.addItem(item)
                elif sc != self.scene:
                    # print('..adding to scene ', item.uid )
                    self.scene.addItem(item)
            if hasattr(item, 'deleted'):
                item.deleted = False

    def remove_from_scene(self, item, fade_out=True):
        """ Remove item from this scene
        :param item:
        :param fade_out: fade instead of immediate disappear
        :return:
        """
        if fade_out and hasattr(item, 'fade_out_and_delete'):
            item.fade_out_and_delete()

        elif isinstance(item, QtWidgets.QGraphicsItem):
            sc = item.scene()
            if sc == self.scene:
                # print('..removing from scene ', item.uid)
                sc.removeItem(item)
            elif sc:
                print('unknown scene for item %s : %s ' % (item, sc))
                sc.removeItem(item)
                print(' - removing anyways')
        else:
            print(type(item))

    # Getting objects ------------------------------------------------------

    def get_all_objects(self):
        """ Just return all objects governed by Forest -- not all scene objects 
        :return: iterator through objects
        """
        for n in self.trees:
            yield n
        for n in self.nodes.values():
            yield n
        for n in self.edges.values():
            yield n
        for n in self.others.values():
            yield n
        for n in self.projections.values():
            if n.visual:
                yield n.visual
        for n in self.bracket_manager.get_brackets():
            yield n
        for n in self.groups.values():
            yield n
        if self.gloss:
            yield self.gloss

    def get_node(self, constituent):
        """
        Returns a node corresponding to a constituent
        :rtype : kataja.BaseConstituentNode
        :param constituent: syntax.BaseConstituent
        :return: kataja.ConstituentNode
        """
        return self.nodes_from_synobs.get(constituent.uid, None)

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

    def animation_started(self, key):
        """ Announce animation that should be waited before redrawing
        :param key:
        :return:
        """
        self.ongoing_animations.add(key)

    def animation_finished(self, key):
        """ Check out animation that was waited for, when all are checked out, redraw forest
        :param key:
        :return:
        """
        if key in self.ongoing_animations:
            self.ongoing_animations.remove(key)
        if not self.ongoing_animations:
            print('animation finished!')
            self.draw()

    def flush_and_rebuild_temporary_items(self):
        """ Clean up temporary stuff that may be invalidated by changes made by undo/redo.
        Notice that draw() does some of this, don't have to do those here.
        :return:
        """
        # Selection and related UI
        legits = list(self.get_all_objects())
        ctrl.multiselection_start()
        for item in ctrl.selected:
            if item not in legits:
                ctrl.remove_from_selection(item)
        ctrl.multiselection_end()

    def draw(self):
        """ Update all trees in the forest according to current visualization
        """
        if self.halt_drawing:
            return
        if not self.in_display:
            print("Why are we drawing a forest which shouldn't be in scene")
        sc = ctrl.graph_scene
        sc.stop_animations()
        self.update_trees()
        for tree in self.trees:
            if tree.top:
                tree.top.update_visibility()  # fixme
        self.bracket_manager.update_brackets()
        self.update_projections()
        self.update_forest_gloss()
        self.visualization.draw()
        #if not sc.manual_zoom:
        #    sc.fit_to_window()
        sc.start_animations()
        ctrl.graph_view.repaint()

    def redraw_edges(self, edge_type=None):
        if edge_type:
            for edge in self.edges.values():
                if edge.edge_type == edge_type:
                    edge.update_shape()
        else:
            for edge in self.edges.values():
                edge.update_shape()

    def update_colors(self):
        """ Update colors to those specified for this Forest."""
        cm = ctrl.cm
        old_gradient_base = cm.paper()
        self.main.color_manager.update_colors()
        self.main.app.setPalette(cm.get_qt_palette())
        if old_gradient_base != cm.paper() and cm.gradient:
            self.main.graph_scene.fade_background_gradient(old_gradient_base, cm.paper())
        else:
            self.main.graph_scene.setBackgroundBrush(qt_prefs.no_brush)
        for other in self.others.values():
            other.update_colors()
        self.main.ui_manager.update_colors()

    # ##### Projections ##########################################

    @staticmethod
    def compute_projection_chains_for(head_node) -> list:
        """ Takes a node and looks at its parents trying to find if they are projections of this
        node. This doesn't rely on projection objects: this is the computation that builds
        chains necessary for creating projection objects.
        :param head_node:
        """
        chains = []

        def is_head_projecting_upwards(chain, node, head_node) -> None:
            chain.append(node)
            ends_here = True
            for parent in node.get_parents(similar=True, visible=False):
                if parent is head_node or parent.head_node is head_node:
                    ends_here = False
                    # create a copy of chain so that when the chain ends it will be added
                    # as separate chain to another projection branch
                    is_head_projecting_upwards(list(chain), parent, head_node)
            if ends_here and len(chain) > 1:
                chains.append(chain)
        is_head_projecting_upwards([], head_node, head_node)
        return chains

    def remove_projection(self, head_node):
        key = head_node.uid
        projection = self.projections.get(key, None)
        if projection:
            projection.set_visuals(False, False, False)
            del self.projections[key]

    def update_projections(self):
        """ Try to guess projections in the trees based on labels and aliases, and once this is
        done, create Projection objects that match all upward projections. Try to match
        Projection objects with existing visual markers for projections.
        :return:
        """
        # only do this the first time we load a new structure
        if not self.guessed_projections:
            for tree in self.trees:
                for node in tree.sorted_constituents:
                    node.guess_projection()
            self.guessed_projections = True

        # We want to keep using existing projection objects as much as possible so they won't change
        # colors randomly
        old_heads = set([x.head for x in self.projections.values()])

        new_heads = set()
        for node in list(self.nodes.values()):
            if node.node_type == g.CONSTITUENT_NODE and node.head_node is None:
                chains = Forest.compute_projection_chains_for(node)
                if chains:
                    new_heads.add(node)
                    projection = self.projections.get(node.uid, None)
                    if projection:
                        projection.update_chains(chains)
                    else:
                        projection = Projection(node, chains, next(self.projection_rotator))
                        self.projections[node.uid] = projection
        for head in old_heads - new_heads:
            self.remove_projection(head)
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
        for projection in self.projections.values():
            projection.set_visuals(strong_lines, colorized, highlighter)

    # #### Comments #########################################

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
        non-root node from another trees to
        construction, so the option should be there.

        :return:
        """
        pass

    # Trees ---------------------------------------------------------------

    def get_tree_by_top(self, top_node):
        """ Return tree where this node is the top node
        :param top_node:
        :return:
        """
        for tree in self.trees:
            if tree.top is top_node:
                return tree

    def reserve_update_for_trees(self, value=None):
        """ Tree members may have changed, go through them when updating them the next time.
        :param value: not used, it is for BaseModel compatibility
        :return:
        """
        self._update_trees = True

    def update_trees(self):
        """ Rebuild all trees, but try to be little smart about it: Tree where one node is added
        to top should keep its identity, and just reset the top node to be the new node.
        :return:
        """
        invalid_trees = []
        valid_tops = set()
        invalid_tops = set()
        for tree in self.trees:
            if not tree.top:
                if not tree.numeration:
                    print('tree without top, removing it')
                    self.remove_tree(tree)
            elif not tree.top.is_top_node():
                invalid_trees.append(tree)
                invalid_tops.add(tree.top)
            elif tree.top.deleted:
                invalid_trees.append(tree)
                invalid_tops.add(tree.top)
            else:
                valid_tops.add(tree.top)
        invalid_tops -= valid_tops
        top_nodes = set()
        for node in self.nodes.values():
            if node.is_top_node():
                top_nodes.add(node)
        unassigned_top_nodes = top_nodes - valid_tops
        # In   (Empty)
        #       /  \
        #     TrA  (Empty)
        #
        # Have TrA to take over the empty nodes
        for node in list(unassigned_top_nodes):
            for child in node.get_children(similar=False, visible=False):
                if child in invalid_tops:
                    tree = self.get_tree_by_top(child)
                    tree.top = child
                    tree.update_items()
                    invalid_tops.remove(child)
                    invalid_trees.remove(tree)
                    unassigned_top_nodes.remove(node)
                    break
        # Create new trees for other unassigned nodes:
        for node in unassigned_top_nodes:
            #print('unassigned top node needing for tree')
            print('creating separate tree for ', node)
            self.create_tree_for(node)
        # Remove trees that are part of some other tree
        for tree in invalid_trees:
            print('removing invalid tree: ', tree)
            self.remove_tree(tree)

        if self._update_trees:
            for tree in self.trees:
                tree.update_items()

        self._update_trees = False

        # Remove this if we found it to be unnecessary -- it is slow, and these problems
        # shouldn't happen -- this is more for debugging
        # Go through all nodes and check if they are ok.
        if False:
            for node in self.nodes.values():
                if node.is_top_node():
                    if not self.get_tree_by_top(node):
                        print('no tree found for potential top node: ', node)
                else:
                    # either parent should have the same trees or parents together should have same
                    # trees
                    union = set()
                    for parent in node.get_parents(similar=False, visible=False):
                        union |= parent.trees
                    problems = node.trees ^ union
                    if problems:
                        print('problem with trees: node %s belongs to trees %s, but its parents '
                              'belong to trees %s' % (node, node.trees, union))

    def create_tree_for(self, node):
        """ Create new trees around given node.
        :param node:
        :return:
        """
        tree = Tree(top=node, forest=self)
        self.add_to_scene(tree)
        self.trees.insert(0, tree)
        tree.show()
        tree.update_items()
        return tree

    def remove_tree(self, tree):
        """ Remove trees that has become unnecessary: either because it is subsumed into another
        trees or because it is empty.
        :param tree:
        :return:
        """
        for node in tree.sorted_nodes:
            node.remove_from_tree(tree)
        if tree in self.trees:
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

    def create_node(self, synobj=None, relative=None, pos=None, node_type=1, text=''):
        """ This is generic method for creating all of the Node subtypes.
        Keep it generic!
        :param synobj: If syntactic object is passed here, the node created
        will be a wrapper around this syntactic object
        :param relative: node will be relative to given node, pos will be interpreted relative to
        given node and new node will have the same trees as a parent.
        :param pos:
        :param node_type:
        :param text: label text for node, behaviour depends on node type
        :return:
        """
        # First check that the node doesn't exist already
        if synobj:
            n = self.get_node(synobj)
            if n:
                return n
        node_class = classes.nodes.get(node_type)
        # Create corresponding syntactic object if necessary
        if not synobj:
            if hasattr(node_class, 'create_synobj'):
                synobj = node_class.create_synobj(text, self)
        if synobj:
            node = node_class(syntactic_object=synobj, forest=self)
        else:
            node = node_class(text, forest=self)
        # after_init should take care that syntactic object is properly
        # reflected by node's connections (call node.reflect_synobj()?)
        node.after_init()
        # resetting node by visualization is equal to initializing node for
        # visualization. e.g. if nodes are locked to position in this vis,
        # then lock this node.
        if self.visualization:
            self.visualization.reset_node(node)
        # it should however inherit settings from relative, if such are given
        if relative:
            node.copy_position(relative)
        if pos:
            node.set_original_position(pos)
            # node.update_position(pos)
        self.add_to_scene(node)
        #node.fade_in()
        return node

    def create_gloss_node(self, host):
        gn = self.create_node(None, relative=host, node_type=g.GLOSS_NODE, text='gloss')
        self.connect_node(host, child=gn)
        return gn

    def create_comment_node(self, text=None, host=None, pixmap_path=None):
        cn = self.create_node(None, relative=host, text=text, node_type=g.COMMENT_NODE)
        if host:
            self.connect_node(host, child=cn)
        if pixmap_path:
            cn.set_image_path(pixmap_path)
        return cn

    def create_attribute_node(self, host, attribute_id, attribute_label, show_label=False):
        """

        :param host:
        :param attribute_id:
        :param attribute_label:
        :param show_label:
        :return:
        """
        AN = AttributeNode(forest=self, host=host, attribute_id=attribute_id,
                           attribute_label=attribute_label,
                           show_label=show_label)
        self.connect_node(host, child=AN)
        self.add_to_scene(AN)
        AN.update_visibility()
        return AN

    def create_edge(self, start=None, end=None, edge_type='', direction='', fade=False):
        """

        :param start:
        :param end:
        :param edge_type:
        :param direction:
        :return:
        """
        rel = Edge(forest=self, start=start, end=end, edge_type=edge_type)
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
        # ee = ctrl.ui_support.get_node_edit_embed()
        # if ee and ee.isVisible():
        #     pos = ee.master_edit.pos()
        #     scene_pos = ctrl.graph_view.mapToScene(ee.mapToParent(pos))
        #     gn.set_original_position(scene_pos)
        # return gn

    # not used
    def create_image(self, image_path):
        """

        :param image_path:
        :return:
        """
        im = Image(image_path)
        self.others[im.uid] = im
        self.add_to_scene(im)
        return im

    def simple_parse(self, text):
        return self.parser.simple_parse(text)

    def create_node_from_string(self, text):
        """
        :param text:
        :param simple_parse: If several words are given, merge them together
        """
        return self.parser.string_into_forest(text)

    def create_trees_from_string(self, text):
        """ Use this to initially draw the trees from a bracket notation or
        whatever parser can handle. This doesn't clean up the forest before
        creating new nodes, so make sure that this is drawn on empty forest
        or be prepared for consequences.
        :param text: string that the parser can handle
        """
        text = text.strip()
        self.parser.string_into_forest(text)
        if self.settings.uses_multidomination:
            self.settings.uses_multidomination = False
            self.traces_to_multidomination()
            # traces to multidomination will toggle uses_multidomination to True

    # noinspection PyMethodMayBeStatic
    def read_definitions(self, definitions):
        """
        :param definitions: Try to set features and glosses according to
        definition strings for nodes in trees.
        :return:
        """
        # todo: can we write feature/gloss definitions into node text elements?
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
        constituent = classes.Constituent(label='t')
        trace = self.create_node(synobj=constituent, relative=node)
        trace.is_trace = True
        trace.index = index
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
            edge.set_label_text(text)
        edge.show()
        ctrl.select(edge)
        return edge

    # ############ Deleting items  ######################################################
    # item classes don't have to know how they relate to each others.
    # here when something is removed from scene, it is made sure that it is
    # also removed
    # from items that reference to it.

    def delete_node(self, node, ignore_consequences=False):
        """ Delete given node and its children and fix the trees accordingly
        :param node:
        :param ignore_consequences: don't try to fix things like connections,
        just delete.
        Note: This and other complicated revisions assume that the target trees is 'normalized' by
        replacing multidomination with traces. Each node can have only one parent.
        This makes calculation easier, just remember to call multidomination_to_traces and
        traces_to_multidomination after deletions.
        """
        # block circular deletion calls
        if node in self._marked_for_deletion:
            return
        else:
            self._marked_for_deletion.add(node)
        node.deleted = True
        # remember parent nodes before we start disconnecting them
        parents = node.get_parents(similar=True, visible=False)

        # -- connections to other nodes --
        if not ignore_consequences:
            for edge in list(node.edges_down):
                if edge.end:
                    if edge.end.node_type == node.node_type:
                        # don't delete children by default, make them their own trees
                        self.disconnect_edge(edge)
                    else:
                        # if deleting node, delete its features, glosses etc. as well
                        self.delete_node(edge.end)
                else:
                    self.disconnect_edge(edge)
            for edge in list(node.edges_up):
                self.disconnect_edge(edge)

        # -- ui_support elements --
        ctrl.ui.remove_ui_for(node)
        # -- brackets --
        self.bracket_manager.remove_brackets(node)
        # -- groups --
        if ctrl.ui.selection_group and node in ctrl.ui.selection_group:
            ctrl.ui.selection_group.remove_node(node)
        for group in self.groups.values():
            if node in group:
                group.remove_node(node)

        # -- dictionaries --
        if node.uid in self.nodes:
            self.poke('nodes')
            del self.nodes[node.uid]
        # -- check if it is last of its type --
        found = False
        my_type = node.node_type
        for n in self.nodes.values():
            if n.node_type == my_type:
                found = True
                break
        if not found:
            if my_type in self.node_types:
                self.node_types.remove(my_type)
        # -- synobj-to-node -mapping (is it used anymore?)
        if node.syntactic_object and node.syntactic_object.uid in self.nodes_from_synobs:
            del self.nodes_from_synobs[node.syntactic_object.uid]
        # -- trees --
        old_trees = set(node.trees)
        for tree in old_trees:
            if tree.top is node:
                node.remove_from_tree(tree, recursive_down=False)
            else:
                tree.update_items()
        if node.parentItem():
            node.setParentItem(None)
        # -- scene --
        self.remove_from_scene(node)
        # -- undo stack --
        node.announce_deletion()
        # -- remove from selection
        ctrl.remove_from_selection(node)
        # -- remove circularity block
        self._marked_for_deletion.remove(node)

    def delete_edge(self, edge, ignore_consequences=False):
        """ remove from scene and remove references from nodes
        :param edge:
        :param ignore_consequences: don't try to fix things like connections,
        just delete.
        """
        # block circular deletion calls
        if edge in self._marked_for_deletion:
            return
        else:
            self._marked_for_deletion.add(edge)

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
            if end_node:
                if edge in end_node.edges_down:  # shouldn't happen
                    end_node.poke('edges_down')
                    end_node.edges_down.remove(edge)
                if edge in end_node.edges_up:
                    end_node.poke('edges_up')
                    end_node.edges_up.remove(edge)
        # -- ui_support elements --
        self.main.ui_manager.remove_ui_for(edge)
        # -- dictionaries --
        if edge.uid in self.edges:
            self.poke('edges')
            del self.edges[edge.uid]
        # -- check if it is last of its type --
        found = False
        my_type = edge.edge_type
        if my_type in self.edge_types:
            for e in self.edges.values():
                if e.edge_type == my_type:
                    found = True
                    break
            if not found:
                self.edge_types.remove(my_type)
        # -- scene --
        self.remove_from_scene(edge)
        # -- Order update for trees
        self.reserve_update_for_trees()
        # -- undo stack --
        edge.announce_deletion()
        # -- remove circularity block
        self._marked_for_deletion.remove(edge)

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
        assert new_start.uid in self.nodes
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
        assert new_end.uid in self.nodes
        if edge.end:
            edge.end.disconnect_in_syntax(edge)
            edge.end.poke('edges_up')
            edge.end.edges_up.remove(edge)
        edge.connect_end_points(edge.start, new_end)
        new_end.poke('edges_up')
        new_end.edges_up.append(edge)
        new_end.connect_in_syntax(edge)

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
        if not self._do_edge_visibility_check:
            return
        show_edges = self.settings.shows_constituent_edges
        for edge in list(self.edges.values()):
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
        C.set_feature(F.name, F)
        self.connect_node(parent=node, child=feature)

    def add_comment_to_node(self, comment, node):
        """ Comments are connected the other way around compared to
        other unusual added nodes. Comments are parents and commented nodes
        are their children. It makes more sense in cases when you first add a
        comment and then drag an arrow out of it.

        :param comment:
        :param node:
        """
        self.connect_node(parent=node, child=comment, edge_type=g.COMMENT_EDGE)

    def add_gloss_to_node(self, gloss, node):
        """

        :param gloss:
        :param node:
        """
        self.connect_node(parent=node, child=gloss)
        node.gloss = gloss.label

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
        for node in list(self.get_attribute_nodes()):
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
        new_nodes = self.parser.string_into_forest(text)
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

    def connect_node(self, parent=None, child=None, direction='', edge_type=None,
                     fade_in=False, mirror_in_syntax = True):
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
        :param fade_in:
        :param mirror_in_syntax: also connect synobjs -- on by default
        """

        #print('--- connecting node %s to %s ' % (child, parent))
        # Check for arguments:
        if parent == child:
            raise ForestError('Connecting to self')
        if not parent and child:
            raise ForestError('Trying to connect nodes, but other is missing (parent:%s, '
                              'child%s)' % (parent, child))

        if not edge_type:
            edge_type = child.edge_type()

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
        new_edge = self.create_edge(start=parent,
                                    end=child,
                                    edge_type=edge_type,
                                    direction=direction,
                                    fade=fade_in)
        child.poke('edges_up')
        parent.poke('edges_down')
        if direction == g.LEFT:
            child.edges_up.insert(0, new_edge)
            parent.edges_down.insert(0, new_edge)
        else:
            child.edges_up.append(new_edge)
            parent.edges_down.append(new_edge)
        if mirror_in_syntax:
            child.connect_in_syntax(new_edge)
        if hasattr(parent, 'rebuild_brackets'):
            parent.rebuild_brackets()
        if hasattr(child, 'rebuild_brackets'):
            child.rebuild_brackets()
        parent.update_label()
        child.update_label()
        #print('--- finished connect')
        if hasattr(child, 'on_connect'):
            child.on_connect(parent)
        return new_edge

    def partial_disconnect(self, edge, start=True, end=True):
        print('partial disconnect called')
        if start and edge.start:
            edge.start.poke('edges_down')
            edge.start.edges_down.remove(edge)
            edge.start = None
        if end and edge.end:
            edge.end.poke('edges_up')
            edge.end.edges_up.remove(edge)
            edge.end = None
        edge.update_end_points()

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
        projections and trees ownerships, but doesn't do it automatically, as disconnecting is
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
            if parent.head is child.head or parent.head_node is child:
                if hasattr(parent, 'set_projection'):
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
        if hasattr(child, 'on_disconnect'):
            child.on_disconnect(parent)

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

        if not set(new_node.trees) & set(old_node.trees):
            new_node.copy_position(old_node)
            new_node.update_visibility(active=True, fade=True)

        # add new node to relevant groups
        # and remove old node from them
        for group in list(self.groups.values()):
            if old_node in group:
                group.add_node(new_node)
                group.remove_node(old_node)

        for edge in list(old_node.edges_up):
            if edge.start:
                direction = edge.direction()
                parent = edge.start
                if only_for_parent and parent != only_for_parent:
                    continue
                self.disconnect_node(parent, old_node, edge.edge_type)
                self.connect_node(parent, child=new_node, direction=direction)

        if replace_children and not only_for_parent:
            for edge in list(old_node.edges_down):
                child = edge.end
                if child:
                    direction = edge.direction()
                    self.disconnect_node(old_node, child, edge.edge_type)
                    self.connect_node(new_node, child, direction=direction)

        if (not old_node.edges_up) and can_delete:
            # old_node.update_visibility(active=False, fade=True)
            self.delete_node(old_node, ignore_consequences=True)

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
        children = list(node.get_children(similar=True, visible=False))
        trees = set(node.trees)
        for child in list(children):
            parents = node.get_parents(similar=True, visible=False)
            parents_children = set()
            bad_parents = []
            good_parents = []
            for parent in list(parents):
                if child in parent.get_children(similar=True, visible=False):
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
                    for parent in list(bad_parents):
                        for grandparent in list(parent.get_parents()):
                            self.disconnect_node(grandparent, parent)
                            self.disconnect_node(parent, child)
                            self.connect_node(grandparent, child)

                if good_parents:
                    # normal case
                    self.disconnect_node(node, child, ignore_missing=True)
                    for parent in list(good_parents):
                        edge = parent.get_edge_to(node)
                        direction = edge.direction()
                        self.disconnect_node(parent, node)
                        self.connect_node(parent, child, direction=direction)
            if i:
                child.set_index(i)
            self.delete_node(node)
            for parent in list(bad_parents):
                self.delete_node(parent)
                # if right.is_placeholder():
                # self.delete_node(right)
                # if left.is_placeholder():
                # self.delete_node(left)
        for tree in list(trees):
            tree.update_items()

    def unary_add_child_for_constituentnode(self, old_node: BaseConstituentNode, add_left=True):
        """

        :param old_node:
        :param add_left:
        :return:
        """
        new_node = self.create_node(relative=old_node)
        children = old_node.get_children(similar=True, visible=False)

        if len(children) != 1:
            return
        child = children[0]
        old_edge = old_node.get_edge_to(child)
        if add_left:
            self.connect_node(parent=old_node, child=new_node, direction=g.LEFT, fade_in=True)
        else:
            self.connect_node(parent=old_node, child=new_node, direction=g.RIGHT, fade_in=True)

    def add_sibling_for_constituentnode(self, old_node: BaseConstituentNode, add_left=True):
        """ Create a new merger node to top of this node and have this node and new node as its
        children.
        :param old_node:
        :param add_left: adding node to left or right -- if binary nodes, this marks which one
        will be projecting.
        :return:
        """

        new_node = self.create_node(relative=old_node)

        if add_left:
            left = new_node
            right = old_node
        else:
            left = old_node
            right = new_node
        parent_info = [(e.start, e.direction(), e.start.head_node) for e in
                       old_node.get_edges_up(similar=True, visible=False)]

        for op, align, head in parent_info:
            self.disconnect_node(parent=op, child=old_node)

        merger_node = self.create_merger_node(left=left, right=right, new=new_node)

        # Fix trees to include new node and especially the new merger node
        for tree in set(old_node.trees):
            tree.recalculate_top()
            tree.update_items()

        for group in self.groups.values():
            if old_node in group:
                group.add_node(merger_node)

        for op, align, head in parent_info:
            self.connect_node(parent=op, child=merger_node, direction=align, fade_in=True)
        merger_node.copy_position(old_node)
        merger_node.set_projection(old_node)
        for op, align, head_node in parent_info:
            if head_node == old_node:
                op.set_projection(head_node)

    def merge_to_top(self, top, new, merge_to_left=True, pos=None):
        """
        :param top:
        :param new:
        :param merge_to_left:
        :param pos:
        :return:
        """
        if hasattr(new, 'index'): # fixme - this is bad idea
            # if new_node and old_node belong to same trees, this is a Move /
            # Internal merge situation and we
            # need to give the new_node an index so it can be reconstructed
            # as a trace structure
            if new.trees == top.trees:
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
        merger_node = self.create_merger_node(left=left, right=right, pos=pos, new=new)

        # Fix trees to include the new merger node
        for tree in set(top.trees):
            tree.recalculate_top()
            tree.update_items()
        merger_node.copy_position(top)

        if self.traces_are_visible():
            self.chain_manager.rebuild_chains()

    def insert_node_between(self, inserted, parent, child, merge_to_left, insertion_pos):
        """ This is an insertion action into a trees: a new merge is created
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
            # if inserted and child belong to same trees, this is a Move /
            # Internal merge situation and we
            # need to give the new_node an index so it can be reconstructed
            # as a trace structure
            shared_trees = list(set(inserted.trees) & set(child.trees))
            if shared_trees:
                moving_was_higher = shared_trees[0].is_higher_in_tree(inserted, child)
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
        if hasattr(parent, 'head') and hasattr(child, 'head') and parent.head is child.head or \
                parent.head_node is child:
            head = parent.head

        direction = edge.direction()
        self.disconnect_edge(edge)
        if merge_to_left:
            left = inserted
            right = child
        else:
            left = child
            right = inserted

        # connections
        p = insertion_pos[0], insertion_pos[1]
        merger_node = self.create_merger_node(left=left, right=right, pos=p, new=inserted)
        merger_node.copy_position(child)
        merger_node.current_position = merger_node.scene_position_to_tree_position(p)
        self.connect_node(parent, merger_node, direction=direction)

        # trees
        for tree in list(parent.trees):
            tree.update_items()

        # groups
        for group in self.groups.values():
            if parent in group:
                group.add_node(merger_node)

        # projections
        if head:
            merger_node.set_projection(head)

        # chains
        if self.traces_are_visible():
            self.chain_manager.rebuild_chains()

    def create_merger_node(self, left=None, right=None, pos=None, new=None, head=None):
        """ Gives a merger node of two nodes. Doesn't try to fix their edges
        upwards
        :param left:
        :param right:
        :param pos:
        :param new: which one is the new node to add. This connection is animated in.
        :param head: which one is head?
        """
        if not pos:
            pos = (0, 0)
        merger_const = ctrl.FL.merge(left.syntactic_object, right.syntactic_object)
        merger_const.after_init()
        merger_node = self.create_node(synobj=merger_const, relative=right)
        merger_node.current_position = pos
        self.add_merge_counter(merger_node)
        self.connect_node(parent=merger_node, child=left, direction=g.LEFT, fade_in=new is left)
        self.connect_node(parent=merger_node, child=right, direction=g.RIGHT, fade_in=new is right)
        if head:
            merger_node.set_projection(head)
        return merger_node

    def copy_node(self, node):
        """ Copy a node and make a new trees out of it
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
            elif len(parents) > 1:
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
            folded.folding_towards = None
            folded.folded_away = False
            folded.copy_position(node)
            folded.fade_in()
            folded.update_visibility()
            folded.update_bounding_rect()
            folded.after_move_function = None
        # this needs second round of update visibility, as child nodes may
        # yet not be visible, so edges to them
        # won't be visible either.
        for folded in fold_scope:
            folded.update_visibility()
        node.update_label()
        node.update_visibility()  # edges from triangle to nodes below

    def can_fold(self, node):
        """

        :param node:
        :return:
        """
        return not node.triangle

    # ######## Groups (Amoebas) ################################

    def turn_selection_group_to_group(self, selection_group):
        """ Take a temporary group into persistent group. Store it in forest. Remember to remove
        the source after this (selection groups are removed when selection changes).
        :param selection_group: temporary Group to turn
        :return: Group (persistent)
        """
        group = self.create_group()
        selection_group.hide()
        group.copy_from(selection_group)

    def create_group(self):
        group = Group(selection=[], persistent=True, forest=self)
        self.add_to_scene(group)
        self.poke('groups')
        self.groups[group.uid] = group
        return group

    def remove_group(self, group):
        self.remove_from_scene(group)
        ctrl.ui.remove_ui_for(group)
        if group.uid in self.groups:
            self.poke('groups')
            del self.groups[group.uid]

    def get_group_color_suggestion(self):
        color_keys = set()
        for group in self.groups.values():
            color_keys.add(group.color_key)
        for i in range(1,8):
            if 'accent%s' % i not in color_keys:
                return 'accent%s' % i

    # ######## Utility functions ###############################

    # def parse_features(self, string, node):
    #     """
    #
    #     :param string:
    #     :param node:
    #     :return:
    #     """
    #     return self.parser.parse_definition(string, node)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    trees = SavedField("trees")  # the current line of trees
    nodes = SavedField("nodes")
    edges = SavedField("edges", if_changed=reserve_update_for_trees)
    groups = SavedField("groups")
    others = SavedField("others")
    settings = SavedField("settings")
    rules = SavedField("rules")
    vis_data = SavedField("vis_data", watcher="visualization")
    derivation_steps = SavedField("derivation_steps")
    merge_counter = SavedField("merge_counter")
    select_counter = SavedField("select_counter")
    comments = SavedField("comments")
    gloss_text = SavedField("gloss_text")
    gloss = SavedField("gloss")
