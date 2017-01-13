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
import random
import time

import kataja.globals as g

from kataja.singletons import ctrl
from kataja.utils import time_me


@time_me
def synobjs_to_nodes(forest, synobjs, numeration=None, other=None, msg=None, gloss=None,
                     transferred=None, mover=None):
    """ This is a big important function to ensure that Nodes on display are only those that
    are present in syntactic objects. Clean up the residue, create those nodes that are
    missing and create the edges.
    :param forest: forest where everything happens
    :param synobjs: syntactic objects
    :param numeration: list of objects waiting to be processed
    :param other: what else we need?
    :param msg: message associated with this derivation step, this will be used as gloss
    :param gloss: gloss text for the whole forest
    :param transferred: list of items spelt out/transferred. These will form a group
    :param mover: single items to point out as special. This will form a group
    :return:
    """
    free_drawing = forest.free_drawing

    if forest.syntax.display_modes:
        synobjs = forest.syntax.transform_trees_for_display(synobjs)
    node_keys_to_validate = set(forest.nodes.keys())
    edge_keys_to_validate = set(forest.edges.keys())

    # Don't delete gloss node if we have message to show
    gloss_strat = ctrl.settings.get('gloss_strategy')
    if gloss_strat != 'no':
        if msg and forest.gloss:
            if forest.gloss.uid in node_keys_to_validate:
                node_keys_to_validate.remove(forest.gloss.uid)

    def recursive_add_for_creation(me, parent_node, parent_synobj, done_nodes=None):
        """ First we have to create new nodes close to existing nodes to avoid rubberbanding.
        To help this create a list of missing nodes with known positions.
        """
        if done_nodes is None:
            done_nodes = set()
            done_nodes.add(me)
        else:
            done_nodes.add(me)
        if isinstance(me, list):
            for list_item in me:
                recursive_add_for_creation(list_item, parent_node, parent_synobj,
                                           done_nodes)
        else:
            node = forest.get_node(me)
            if node:
                if hasattr(me, 'label'):
                    node.label = me.label
                #node.update_label()
                found_nodes.add(node.uid)
                #if node.uid in node_keys_to_validate:
                #    node_keys_to_validate.remove(node.uid)
                if node.node_type == g.FEATURE_NODE and False:
                    node.locked_to_node = parent_node  # not me.unvalued
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
                    if part not in done_nodes:
                        recursive_add_for_creation(part, node, me, done_nodes)
            if hasattr(me, 'features'):
                if isinstance(me.features, dict):
                    for feat in me.features.values():
                        if feat not in done_nodes:
                            recursive_add_for_creation(feat, node, me, done_nodes)
                elif isinstance(me.features, (list, set, tuple)):
                    for feat in me.features:
                        if feat not in done_nodes:
                            recursive_add_for_creation(feat, node, me, done_nodes)

    # I guess that ordering of connections will be broken because of making
    # and deleting connections in unruly fashion
    def connect_if_necessary(parent, child, edge_type):
        edge = parent.get_edge_to(child, edge_type)
        if not edge:
            free_drawing.connect_node(parent, child, edge_type=edge_type)
        else:
            found_edges.add(edge.uid)
        #elif edge.uid in edge_keys_to_validate:
        #    edge_keys_to_validate.remove(edge.uid)


    def recursive_create_edges(synobj):
        node = forest.get_node(synobj)
        assert(node)
        if synobj in synobjs_done:
            return node
        synobjs_done.add(synobj)
        if node.node_type == g.CONSTITUENT_NODE:
            # part_count = len(synobj.get_parts())
            for part in synobj.get_parts():
                child = recursive_create_edges(part)
                if child:
                    connect_if_necessary(node, child, g.CONSTITUENT_EDGE)
            for feature in synobj.get_features():
                nfeature = recursive_create_edges(feature)
                if nfeature:
                    connect_if_necessary(node, nfeature, g.FEATURE_EDGE)
            verify_edge_order_for_constituent_nodes(node)
        elif node.node_type == g.FEATURE_NODE:
            if hasattr(synobj, 'get_parts'):
                for part in synobj.get_parts():
                    child = recursive_create_edges(part)
                    if child and child.node_type == g.FEATURE_NODE:
                        connect_if_necessary(node, child, g.CHECKING_EDGE)
            if hasattr(synobj, 'checks'):
                if synobj.checks:
                    checking_node = forest.get_node(synobj.checks)
                    if checking_node:
                        connect_if_necessary(checking_node, node, g.CHECKING_EDGE)
        return node

    def rec_add_item(item, result_set):
        result_set.append(forest.get_node(item))
        for part in item.get_parts():
            result_set = rec_add_item(part, result_set)
        return result_set

    #if numeration:
    #    num_tree = forest.get_numeration()

    scene_rect = ctrl.graph_view.mapToScene(ctrl.graph_view.rect()).boundingRect()
    sc_center = scene_rect.center().x()
    sc_middle = scene_rect.center().y()
    t = time.time()

    for tree_root in synobjs:
        if not tree_root:
            continue
        synobjs_done = set()
        nodes_to_create = []
        tree_counter = []
        found_nodes = set()
        most_popular_tree = None

        recursive_add_for_creation(tree_root, None, None)
        node_keys_to_validate -= found_nodes

        # noinspection PyArgumentList
        most_popular_trees = collections.Counter(tree_counter).most_common(1)
        if most_popular_trees:
            most_popular_tree = most_popular_trees[0][0]

        for syn_bare, pos in nodes_to_create:
            x, y = pos
            if x == 0 and y == 0:
                x = sc_center + random.randint(-100, 100)
                y = sc_middle + random.randint(-100, 100)
                if isinstance(syn_bare, ctrl.syntax.Feature):
                    y += 100
            if isinstance(syn_bare, ctrl.syntax.Constituent):
                node = free_drawing.create_node(node_type=g.CONSTITUENT_NODE, pos=(x, y))
                node.set_syntactic_object(syn_bare)
            elif isinstance(syn_bare, ctrl.syntax.Feature):
                node = free_drawing.create_node(node_type=g.FEATURE_NODE, pos=(x, y))
                node.set_syntactic_object(syn_bare)
            else:
                continue
            if most_popular_tree:
                most_popular_tree.add_node(node)

        found_edges = set()
        recursive_create_edges(tree_root)
        edge_keys_to_validate -= found_edges

        if most_popular_tree:
            most_popular_tree.top = forest.get_node(tree_root)
            most_popular_tree.update_items()
        else:
            forest.tree_manager.create_tree_for(forest.get_node(tree_root))

    # for item in numeration:
    #    node, trees = recursive_create(item, set())
    #    if node and not trees:
    #        node.add_to_tree(num_tree)
    # Delete invalid nodes and edges

    for key in node_keys_to_validate:
        node = forest.nodes.get(key, None)
        if node:
            # noinspection PyTypeChecker
            free_drawing.delete_node(node)
    for key in edge_keys_to_validate:
        edge = forest.edges.get(key, None)  # most of these should be deleted already by prev.
        if edge:
            # noinspection PyTypeChecker
            free_drawing.delete_edge(edge)

    f_mode = ctrl.settings.get('feature_positioning')
    shape = ctrl.settings.get('label_shape')
    parents = []
    for node in forest.nodes.values():
        node.update_relations(parents, shape=shape, position=f_mode)
        node.update_label()
    for parent in parents:
        parent.gather_children()

    # Update or create groups of transferred items
    old_groups = [gr for gr in forest.groups.values() if gr.get_label_text().startswith(
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
                    new_g = free_drawing.create_group()
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
                        new_g = free_drawing.create_group()
                        new_g.set_label_text('Transfer')
                        #new_g.fill = False
                        #new_g.outline = True
                        new_g.update_colors('accent5')
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

    # ---------
    # Update or create mover group
    old_group = None
    for group in forest.groups.values():
        if group.purpose == 'mover':
            old_group = group
            break
    if mover:
        mover = forest.get_node(mover)
        if old_group:
            old_group.clear(remove=False)
            group = old_group
        else:
            group = free_drawing.create_group()
            group.purpose = 'mover'
            #group.set_label_text('Next mover')
            group.include_children = False
            group.fill = True
            group.outline = False
            group.update_colors('accent8')
        group.update_selection([mover])
    else:
        if old_group:
            old_group.clear(remove=True)
    # ---------
    strat = ctrl.settings.get('gloss_strategy')
    if strat and strat == 'message':
        forest.gloss_text = msg
    forest.update_forest_gloss()
    forest.guessed_projections = False
    ctrl.graph_scene.fit_to_window(force=True)


def verify_edge_order_for_constituent_nodes(node):
    """ Verify that relations to children are in same order as in syntactic object. This
    depends on how syntax supports ordering.
    :return:
    """
    if isinstance(node.syntactic_object.parts, list):
        #  we assume that if parts use lists, then they are implicitly ordered.
        correct_order = node.syntactic_object.parts
        current_order = [edge.end.syntactic_object for edge in node.edges_down if edge.end
                         and edge.edge_type == g.CONSTITUENT_EDGE]
        if correct_order != current_order:
            new_order = []
            passed = []
            for edge in node.edges_down:
                if edge.edge_type == g.CONSTITUENT_EDGE and edge.end and \
                        edge.end.syntactic_object in node.syntactic_object.parts:
                    new_order.append((node.syntactic_object.parts.index(
                        edge.end.syntactic_object), edge))
                else:
                    passed.append(edge)
            new_order = [edge for i, edge in sorted(new_order)]
            node.edges_down = new_order + passed
    if node.syntactic_object.features and isinstance(node.syntactic_object.features, list):
        #  we assume that if features are in lists, then they are implicitly ordered.
        correct_order = node.syntactic_object.features
        current_order = [edge.end.syntactic_object for edge in node.edges_down if edge.end
                         and edge.edge_type == g.FEATURE_EDGE]
        if correct_order != current_order:
            new_order = []
            passed = []
            for edge in node.edges_down:
                if edge.edge_type == g.FEATURE_EDGE and edge.end and \
                        edge.end.syntactic_object in node.syntactic_object.features:
                    new_order.append((node.syntactic_object.features.index(
                        edge.end.syntactic_object), edge))
                else:
                    passed.append(edge)
            new_order = [edge for i, edge in sorted(new_order)]
            node.edges_down = passed + new_order


