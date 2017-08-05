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
def syntactic_state_to_nodes(forest, syn_state):
    """ This is a big important function to ensure that Nodes on display are only those that
    are present in syntactic objects. Clean up the residue, create those nodes that are
    missing and create the edges.
    :param forest: forest where everything happens
    :param syn_state: SyntaxState -instance
    :return:
    """
    free_drawing = forest.free_drawing

    if forest.syntax.display_modes:
        syntactic_state = forest.syntax.transform_trees_for_display(syntactic_state)

    forest.semantics_manager.clear()

    node_keys_to_validate = set(forest.nodes.keys())
    edge_keys_to_validate = set(forest.edges.keys())

    animate = True

    # Don't delete gloss node if we have message to show
    gloss_strat = ctrl.settings.get('gloss_strategy')
    if gloss_strat != 'no':
        if syn_state.msg and forest.gloss:
            if forest.gloss.uid in node_keys_to_validate:
                node_keys_to_validate.remove(forest.gloss.uid)

    #if numeration:
    #    num_tree = forest.get_numeration()

    scene_rect = ctrl.graph_view.mapToScene(ctrl.graph_view.rect()).boundingRect()
    sc_center = scene_rect.center().x()
    sc_middle = scene_rect.center().y()

    # ################ Helpers ###################################


    def iter_once(listlike):
        if isinstance(listlike, dict):
            for my_item in listlike.values():
                if my_item.uid not in done_nodes:
                    yield my_item
        elif isinstance(listlike, (list, set, tuple)):
            for my_item in listlike:
                if my_item.uid not in done_nodes:
                    yield my_item

    def iter_me(listlike):
        if isinstance(listlike, dict):
            for my_item in listlike.values():
                yield my_item
        elif isinstance(listlike, (list, set, tuple)):
            for my_item in listlike:
                yield my_item

    # ################ Nodes ###################################

    def recursive_add_const_node(me, parent_synobj):
        """ First we have to create new nodes close to existing nodes to avoid rubberbanding.
        To help this create a list of missing nodes with known positions.
        """
        done_nodes.add(me.uid)
        node = forest.get_node(me)
        if node:
            found_nodes.add(node.uid)
            node.label = me.label
            node.update_label()
        else:
            cns_to_create.append((me, parent_synobj))
        for part in iter_once(me.parts):
            recursive_add_const_node(part, me)
        for feat in me.get_features():
            if feat.uid not in done_nodes:
                recursive_add_feature_node(feat, me)

    def recursive_add_feature_node(me, parent_synobj):
        """ First we have to create new nodes close to existing nodes to avoid 
        rubberbanding.
        To help this create a list of missing nodes with known positions.
        """
        done_nodes.add(me.uid)
        node = forest.get_node(me)
        if node:
            found_nodes.add(node.uid)
            node.name = getattr(me, 'name', '')
            node.value = getattr(me, 'value', '')
            node.family = getattr(me, 'family', '')
            node.update_label()
        else:
            fns_to_create.append((me, parent_synobj))
        # we usually don't have feature structure, but lets assume that possibility
        if hasattr(me, 'parts'):
            for part in iter_once(me.parts):
                recursive_add_feature_node(part, me)
        if hasattr(me, 'features'):
            for feat in me.get_features():
                if feat.uid not in done_nodes:
                    recursive_add_feature_node(feat, me)
        if hasattr(me, 'checks'):
            if me.checks and me.checks.uid not in done_nodes:
                recursive_add_feature_node(me.checks, me)

    cns_to_create = []
    fns_to_create = []
    done_nodes = set()
    found_nodes = set()
    for tree_root in syn_state.tree_roots:
        recursive_add_const_node(tree_root, None)
    node_keys_to_validate -= found_nodes
    for syn_bare, syn_parent in cns_to_create:
        host = forest.get_node(syn_parent)
        pos = None
        if host:
            pos = host.scenePos()
        elif syn_bare.parts:
            for csyn in syn_bare.parts:
                child = forest.get_node(csyn)
                if child:
                    pos = child.scenePos()
                    break
        if not pos:
            x = sc_center + random.randint(-100, 100)
            y = sc_middle + random.randint(-100, 100)
            pos = (x, y)
        node = free_drawing.create_node(node_type=g.CONSTITUENT_NODE, pos=pos)
        node.set_syntactic_object(syn_bare)
        node.label = syn_bare.label

    for syn_feat, syn_host in fns_to_create:
        host = forest.get_node(syn_host)
        if host:
            pos = host.scenePos()
        else:
            pos = (0, 0)
        fnode = free_drawing.create_node(node_type=g.FEATURE_NODE, pos=pos)
        fnode.set_syntactic_object(syn_feat)
        fnode.name = getattr(syn_feat, 'name', '')
        fnode.value = getattr(syn_feat, 'value', '')
        fnode.family = getattr(syn_feat, 'family', '')

    # ################ Edges & Heads ###################################

    # I guess that ordering of connections will be broken because of making
    # and deleting connections in unruly fashion
    def connect_if_necessary(parent, child, edge_type):
        edge = parent.get_edge_to(child, edge_type)
        if not edge:
            free_drawing.connect_node(parent, child, edge_type=edge_type)
        else:
            found_edges.add(edge.uid)

    def connect_feature_if_necessary(parent, child, feature):
        edge = parent.get_edge_to(child, g.FEATURE_EDGE, extra=feature)
        if not edge:
            free_drawing.connect_node(parent, child, edge_type=g.FEATURE_EDGE, extra=feature)
        else:
            found_edges.add(edge.uid)


    def recursive_create_edges(synobj):
        """ All of the nodes exist already, now put the edges in place. Goes to the bottom and 
        then builds up. 
        :param synobj: 
        :return: 
        """
        node = forest.get_node(synobj)
        assert(node)
        if synobj.uid in done_nodes:
            return node
        done_nodes.add(synobj.uid)
        if node.node_type == g.CONSTITUENT_NODE:
            for part in iter_me(synobj.parts):
                child = recursive_create_edges(part)
                if child:
                    connect_if_necessary(node, child, g.CONSTITUENT_EDGE)
            if synobj.parts:
                features = list(synobj.get_features())
                semantics = getattr(synobj, 'semantics', None)
                if semantics:
                    sem_label, sem_array_n = semantics
                    forest.semantics_manager.add_to_array(node, sem_label, sem_array_n)
                checked_features = getattr(synobj, 'checked_features', None)
                if checked_features:
                    features += list(checked_features)
                for feature in features:
                    # Try to find where from this from this edge has been inherited.
                    # Connect this node to there.
                    nfeature = recursive_create_edges(feature)
                    # fixme! hack, blocked_inheritance is specific to MyParser
                    blocked = getattr(synobj, 'blocked_inheritance', None)
                    for child in iter_me(synobj.parts):
                        if blocked == child:
                            print('skip, skip')
                            continue
                        if feature in child.get_features():
                            nchild = recursive_create_edges(child)
                            connect_feature_if_necessary(node, nchild, nfeature)
                            break

            else:
                for feature in synobj.get_features():
                    nfeature = recursive_create_edges(feature)
                    if nfeature:
                        connect_feature_if_necessary(node, nfeature, nfeature)
            verify_edge_order_for_constituent_nodes(node)
        elif node.node_type == g.FEATURE_NODE:
            if hasattr(synobj, 'parts'):
                for part in iter_me(synobj.parts):
                    child = recursive_create_edges(part)
                    if child and child.node_type == g.FEATURE_NODE:
                        connect_if_necessary(node, child, g.CHECKING_EDGE)
            if hasattr(synobj, 'checks'):
                if synobj.checks:
                    checking_node = forest.get_node(synobj.checks)
                    if checking_node:
                        connect_if_necessary(checking_node, node, g.CHECKING_EDGE)
        return node

    def recursive_update_heads(node):
        if not node.syntactic_object:
            print(f'node "{node}" doesnt have syntactic object')
            return []
        my_label = node.syntactic_object.label
        my_label_parts = [x.strip('() ') for x in my_label.split(',')]
        if node in done_nodes:
            return [('_'.join([x.strip('() ') for x in n.label.split(',')]), n) for n in node.heads]
        done_nodes.add(node)
        heads = []
        res = []
        children = node.get_children(similar=True, visible=False)
        if children:
            for child in children:
                labels = recursive_update_heads(child)
                for label, head in labels:
                    if label in my_label:
                        heads.append(head)
                        res.append((label, head))
            node.heads = heads
            return res
        else:
            my_label_parts = ['_'.join(my_label_parts)]
            node.heads = [node]
            return [('_'.join(my_label_parts), node)]

    # There may be edges that go between trees and these cannot be drawn before nodes of all trees
    # exist.
    done_nodes = set()
    found_edges = set()
    for tree_root in syn_state.tree_roots:
        recursive_create_edges(tree_root)
    edge_keys_to_validate -= found_edges

    done_nodes = set()
    for tree_root in syn_state.tree_roots:
        recursive_update_heads(forest.get_node(tree_root))

    # for item in numeration:
    #    node, trees = recursive_create(item, set())
    #    if node and not trees:
    #        node.add_to_tree(num_tree)

    # ################ Deletion ###################################

    for key in node_keys_to_validate:
        node = forest.nodes.get(key, None)
        if node:
            free_drawing.delete_node(node, touch_edges=False, fade=animate)
    for key in edge_keys_to_validate:
        edge = forest.edges.get(key, None)  # most of these should be deleted already by prev.
        if edge:
            free_drawing.delete_edge(edge, fade=animate)

    # ############# Labels & node shapes ###############################

    forest.update_label_shapes()

    # ############# Groups #######################################

    def rec_add_item(item, result_set):
        result_set.append(forest.get_node(item))
        for part in item.get_parts():
            result_set = rec_add_item(part, result_set)
        return result_set

    # Update or create groups of transferred items
    old_groups = [gr for gr in forest.groups.values() if gr.get_label_text().startswith(
        'Transfer')]
    all_new_items = set()
    all_old_items = set()
    if old_groups:
        for group in old_groups:
            all_old_items.update(set(group.selection))

    if syn_state.transferred:
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
    # if mover:
    #     mover = forest.get_node(mover)
    #     if old_group:
    #         old_group.clear(remove=False)
    #         group = old_group
    #     else:
    #         group = free_drawing.create_group()
    #         group.purpose = 'mover'
    #         #group.set_label_text('Next mover')
    #         group.include_children = False
    #         group.fill = True
    #         group.outline = False
    #         group.update_colors('accent8')
    #     group.update_selection([mover])
    # else:
    #     if old_group:
    #         old_group.clear(remove=True)
    # ---------
    strat = ctrl.settings.get('gloss_strategy')
    if strat and strat == 'message':
        forest.gloss_text = syn_state.msg
    forest.update_forest_gloss()
    forest.guessed_projections = False
    #ctrl.graph_scene.fit_to_window(force=True)


def verify_edge_order_for_constituent_nodes(node):
    """ Verify that relations to children are in same order as in syntactic object. This
    depends on how syntax supports ordering.
    :return:
    """
    def strict_index(flist, feat):
        for i, fitem in enumerate(flist):
            if feat is fitem:
                return i


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
                if edge.edge_type == g.FEATURE_EDGE and edge.end:
                    si = strict_index(node.syntactic_object.features, edge.end.syntactic_object)
                    if si is not None:
                        new_order.append((si, edge))
                    else:
                        passed.append(edge)
                else:
                    passed.append(edge)
            new_order = [edge for i, edge in sorted(new_order)]
            node.edges_down = passed + new_order


