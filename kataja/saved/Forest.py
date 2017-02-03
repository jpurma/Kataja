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
import time
from PyQt5 import QtWidgets
from kataja.saved.movables.nodes.AttributeNode import AttributeNode

import kataja.globals as g
from kataja.ChainManager import ChainManager
from kataja.FreeDrawing import FreeDrawing
from kataja.ProjectionManager import ProjectionManager
from kataja.SavedField import SavedField
from kataja.SavedObject import SavedObject
from kataja.TreeManager import TreeManager
from kataja.UndoManager import UndoManager
from kataja.parser.INodeToKatajaConstituent import INodeToKatajaConstituent
from kataja.saved.DerivationStep import DerivationStepManager
from kataja.saved.Edge import Edge
from kataja.saved.movables.Node import Node
from kataja.saved.movables.Tree import Tree
from kataja.saved.movables.nodes.ConstituentNode import ConstituentNode
from kataja.saved.movables.nodes.FeatureNode import FeatureNode
from kataja.singletons import ctrl, classes
from kataja.utils import time_me


class Forest(SavedObject):
    """ Forest is a group of trees that together form one view.
    Often there needs to be more than one trees visible at same time,
     so that they can be compared or to show states of construction
      where some edges are not yet linked to the main root.
      Forest is the container for these.
      Forest also takes care of the operations manipulating, creating and
      removing trees. """

    def __init__(self, gloss_text='', comments=None, syntax=None):
        """ Create an empty forest. Gloss_text and comments are metadata
        about trees that doesn't belong to syntax implementation, so its kept here. Syntax
        implementations may still use it.

        By default, a new Forest doesn't create its nodes -- it doesn't do the derivation yet.
        This is to save speed and memory with large structures. If the is_parsed -flag is False
        when created, but once Forest is displayed, the derivation has to run and after that
        is_parsed is True.
        """
        super().__init__()
        self.nodes_from_synobs = {}
        self.main = ctrl.main
        self.main.forest = self  # assign self to be the active forest while
        # creating the managers.
        self.in_display = False
        self.visualization = None
        self.gloss = None
        self.is_parsed = False
        self.syntax = syntax or classes.get('SyntaxConnection')()
        self.parser = INodeToKatajaConstituent(self)
        self.undo_manager = UndoManager(self)
        self.chain_manager = ChainManager(self)
        self.tree_manager = TreeManager(self)
        self.free_drawing = FreeDrawing(self)
        self.projection_manager = ProjectionManager(self)
        self.derivation_steps = DerivationStepManager(self)
        self.old_label_mode = 0
        self.trees = []
        self.nodes = {}
        self.edges = {}
        self.groups = {}
        self.others = {}
        self.vis_data = {}
        self.width_map = {}
        self.traces_to_draw = {}
        self.comments = []
        self.gloss_text = ''
        self.ongoing_animations = set()
        self.halt_drawing = False
        self.gloss_text = gloss_text
        self.comments = comments

        # Update request flags
        self._do_edge_visibility_check = False
        #self.change_view_mode(ctrl.settings.get('syntactic_mode'))

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
        if not self.is_parsed:
            self.syntax.create_derivation(self)
            self.after_model_update('nodes', 0)
            self.is_parsed = True
        ctrl.add_watcher(self, 'palette_changed')
        ctrl.main.update_colors()
        self.add_all_to_scene()
        self.update_visualization()
        self.scene.keep_updating_visible_area = True
        self.scene.manual_zoom = False
        self.draw()  # do draw once to avoid having the first draw in undo stack.
        ctrl.graph_scene.fit_to_window()
        ctrl.resume_undo()
        ctrl.graph_view.setFocus()

    def retire_from_drawing(self):
        """ Announce that this forest should not try to work with scene
        anymore --
         some other forest is occupying the scene now.
        :return:
        """
        for item in self.get_all_objects():
            self.remove_from_scene(item, fade_out=False)
        ctrl.remove_from_watch(self)
        self.in_display = False

    def clear(self):
        if self.in_display:
            for item in self.get_all_objects():
                self.remove_from_scene(item, fade_out=False)
        self.nodes_from_synobs = {}
        self.gloss = None
        self.parser = INodeToKatajaConstituent(self)
        self.undo_manager = UndoManager(self)
        self.chain_manager = ChainManager(self)
        self.tree_manager = TreeManager(self)
        self.free_drawing = FreeDrawing(self)
        self.projection_manager = ProjectionManager(self)
        self.derivation_steps = DerivationStepManager(self)
        self.trees = []
        self.nodes = {}
        self.edges = {}
        self.groups = {}
        self.others = {}
        self.width_map = {}
        self.traces_to_draw = {}
        self.comments = []
        self.gloss_text = ''

    def forest_edited(self):
        """ Called after forest editing/free drawing actions that have changed the node graph.
        Analyse the node graph and update/rebuild syntactic objects according to graph.
        :return:
        """
        self.syntax.nodes_to_synobjs(self, [x.top for x in self.trees])

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

    def get_nodes_by_index(self, index) -> (Node, set):
        head = None
        traces = set()
        for node in self.nodes.values():
            if node.node_type == g.CONSTITUENT_NODE:
                if node.index == index:
                    if node.is_trace:
                        traces.add(node)
                    else:
                        head = node
        return head, traces


    def get_numeration(self):
        for tree in self.trees:
            if tree.numeration:
                return tree
        tree = Tree(numeration=True)
        self.add_to_scene(tree)
        self.trees.append(tree)
        tree.show()
        return tree

    def set_visualization(self, name):
        """ Switches the active visualization to visualization with given key
        :param name: string
        """
        if self.visualization and self.visualization.say_my_name() == name:
            self.visualization.reselect()
        else:
            vs = self.main.visualizations
            self.visualization = vs.get(name, vs.get(ctrl.settings.get('visualization'), None))
            self.vis_data = {'name': self.visualization.say_my_name()}
            self.visualization.prepare(self)
            ctrl.settings.set('hide_edges_if_nodes_overlap',
                              self.visualization.hide_edges_if_nodes_overlap, level=g.FOREST)
            self.scene.keep_updating_visible_area = True
        self.main.graph_scene.manual_zoom = False

    def restore_visualization(self):
        name = self.vis_data.get('name', ctrl.settings.get('visualization'))
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
        name = self.vis_data.get('name', ctrl.settings.get('visualization'))
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
            self.free_drawing.node_types.add(item.node_type)
            if item.syntactic_object:
                # remember to rebuild nodes_by_uid in undo/redo, as it is not
                #  stored in model
                self.nodes_from_synobs[item.syntactic_object.uid] = item
        elif isinstance(item, Edge):
            self.poke('edges')
            self.edges[item.uid] = item
            self.tree_manager.reserve_update_for_trees()
            self.free_drawing.edge_types.add(item.edge_type)
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
        for n in self.projection_manager.projections.values():
            if n.visual:
                yield n.visual
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
        if not constituent:
            return None
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
                isinstance(x, ConstituentNode) and x.is_visible())

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
        # fixme: put this back on when triangle animations work again
        #if not self.ongoing_animations:
        #    self.draw()

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
        assert self.is_parsed
        sc = ctrl.graph_scene
        sc.stop_animations()
        self.tree_manager.update_trees()
        for tree in self.trees:
            if tree.top:
                tree.top.update_visibility()  # fixme
        self.projection_manager.update_projections()
        self.update_forest_gloss()
        if self.visualization:
            self.visualization.prepare_draw()
            x = 0
            first = True
            for tree in self.trees:
                if tree.top:
                    #self.visualization.prepare_to_normalise(tree)
                    self.visualization.draw_tree(tree)
                    self.visualization.normalise_to_origo(tree)
                    #self.visualization.normalise_movers_to_top(tree)
                    br = tree.boundingRect()
                    if not first:
                        x -= br.left()
                    tree.move_to(x, 0)
                    x += br.right()
                    tree.start_moving()
                    first = False
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

    def simple_parse(self, text):
        return self.parser.simple_parse(text)

    def create_node_from_string(self, text):
        """
        :param text:
        """
        return self.parser.string_into_forest(text)

    def order_edge_visibility_check(self):
        """ Make sure that all edges are checked to update their visibility.
        This can be called multiple
        times, but the visibility check is done only once.
        """
        self._do_edge_visibility_check = True

    def edge_visibility_check(self):
        """ Perform check for each edge: hide them if their start/end is
        hidden, show them if necessary.
        """
        if not self._do_edge_visibility_check:
            return
        for edge in set(self.edges.values()):
            changed = edge.update_visibility()
            if changed:
                if edge.is_visible():
                    if ctrl.is_selected(edge):
                        ctrl.ui.add_control_points(edge)
                else:
                    ctrl.ui.remove_ui_for(edge)
        self._do_edge_visibility_check = False

    def update_label_shape(self):
        shape = ctrl.settings.get('label_shape')
        ctrl.release_editor_focus()
        for node in self.nodes.values():
            if node.node_type == g.CONSTITUENT_NODE:
                node.label_object.label_shape = shape
                node.update_label()

        parents = []
        for node in self.nodes.values():
            node.update_relations(parents)
        for parent in parents:
            parent.gather_children()
        self.prepare_width_map()

    def update_forest_gloss(self):
        """ Draw the gloss text on screen, if it exists. """
        strat = ctrl.settings.get('gloss_strategy')
        if strat:
            if strat == 'linearisation':
                gts = []
                for tree in self.trees:
                    gt = ctrl.syntax.linearize(tree.top)
                    if gt:
                        gts.append(gt)
                self.gloss_text = ' '.join(gts)
            elif strat == 'message':
                pass
            elif strat == 'manual':
                pass
            elif strat == 'no':
                self.gloss_text = ''
        else:
            self.gloss_text = ''

        if self.gloss_text and not ctrl.settings.get('syntactic_mode'):
            if not self.gloss:
                self.gloss = self.free_drawing.create_node(node_type=g.GLOSS_NODE)
                self.gloss.label = self.gloss_text
            elif self.gloss.text != self.gloss_text:
                self.gloss.label = self.gloss_text
            self.gloss.update_label()
            self.gloss.physics_x = False
            self.gloss.physics_y = False
            self.gloss.put_to_top_of_trees()
            self.gloss.show()
        elif self.gloss:
            self.remove_from_scene(self.gloss)
            self.gloss = None

    def compute_traces_to_draw(self, rotator) -> int:
        """ This is complicated, but returns a dictionary that tells for each index key
        (used by chains) in which position at trees to draw the node. Positions are identified by
        key of their immediate parent: {'i': ConstituentNode394293, ...} """
        # highest row = index at trees
        # x = cannot be skipped, last instance of that trace
        # i/j/k = index key
        # rows = rotation
        # * = use this node

        # 2 3 7 9 13 15 16
        # i j i i k  j  k
        #       x    x  x
        # * *     *
        #   * *   *
        #     *   *  *
        #       * *  *
        #       *    *  *
        # make an index-keyless version of this.
        trace_dict = {}
        sorted_parents = []
        required_keys = set()
        for tree in self:
            sortable_parents = []
            ltree = tree.sorted_nodes
            for node in ltree:
                if not hasattr(node, 'index'):
                    continue
                parents = node.get_parents(visible=True, similar=True)
                if len(parents) > 1:
                    node_key = node.uid
                    required_keys.add(node_key)
                    my_parents = []
                    for parent in parents:
                        if parent in ltree:
                            i = ltree.index(parent)
                            my_parents.append((i, node_key, parent, True))
                    if my_parents:
                        my_parents.sort()
                        a, b, c, d = my_parents[-1]  # @UnusedVariable
                        my_parents[-1] = a, b, c, False
                        sortable_parents += my_parents
            sortable_parents.sort()
            sorted_parents += sortable_parents
        if rotator < 0:
            rotator = len(sorted_parents) - len(required_keys)
        skips = 0
        for i, node_key, parent, can_be_skipped in sorted_parents:
            if node_key in required_keys:
                if skips == rotator or not can_be_skipped:
                    trace_dict[node_key] = parent.uid
                    required_keys.remove(node_key)
                else:
                    skips += 1
        self.traces_to_draw = trace_dict
        return rotator

    def should_we_draw(self, node, parent) -> bool:
        """ With multidominated nodes the child will eventually be drawn under one of its parents.
        Under which one is stored in traces_to_draw -dict. This checks if the node should be
        drawn under given parent.

        :param node:
        :param parent:
        :return:
        """
        if not self.traces_to_draw:
            return True
        if hasattr(node, 'index') and len(node.get_parents(similar=True, visible=True)) > 1:
            key = node.uid
            if key in self.traces_to_draw:
                if parent.uid != self.traces_to_draw[key]:
                    return False
        return True

    def prepare_width_map(self):
        """ A map of how much horizontal space each node would need -- it is better to do this
        once than recursively compute these when updating labels.
        :return:
        """
        def recursive_width(node):
            if node.is_leaf(only_similar=True, only_visible=True):
                if node.is_visible():
                    w = node.label_object.width
                else:
                    w = 0
            else:
                w = node.label_object.left_bracket_width() + node.label_object.right_bracket_width()
                for n in node.get_children(similar=True, visible=True):
                    if self.should_we_draw(n, node):
                        w += recursive_width(n)
            self.width_map[node.uid] = w
            node.update_label()
            return w

        self.width_map = {}
        for tree in self:
            recursive_width(tree.top)
        return self.width_map

    # ### Minor updates for forest elements
    # #######################################################################

    def reform_constituent_node_from_string(self, text, node):
        """

        :param text:
        :param node:
        """
        new_nodes = self.parser.string_into_forest(text)
        if new_nodes:
            self.free_drawing.replace_node(node, new_nodes[0])

    # View mode
    @time_me
    def change_view_mode(self, syntactic_mode):
        t = time.time()
        ctrl.settings.set('syntactic_mode', syntactic_mode, level=g.FOREST)
        label_text_mode = ctrl.settings.get('label_text_mode')
        if syntactic_mode:
            self.old_label_mode = label_text_mode
            if label_text_mode == g.NODE_LABELS:
                ctrl.settings.set('label_text_mode', g.SYN_LABELS, level=g.FOREST)
            elif label_text_mode == g.NODE_LABELS_FOR_LEAVES:
                ctrl.settings.set('label_text_mode', g.SYN_LABELS_FOR_LEAVES, level=g.FOREST)
        else:
            if self.old_label_mode == g.NODE_LABELS or \
                            self.old_label_mode == g.NODE_LABELS_FOR_LEAVES:
                ctrl.settings.set('label_text_mode', self.old_label_mode, level=g.FOREST)
        nodes = list(self.nodes.values())
        for node in nodes:
            node.update_label()
            node.update_visibility(skip_label=True)
        ctrl.call_watchers(self, 'view_mode_changed', value=syntactic_mode)
        if syntactic_mode:
            if ctrl.main.color_manager.paper().value() < 100:
                ctrl.settings.set('temp_color_theme', 'dk_gray', level=g.FOREST)
            else:
                ctrl.settings.set('temp_color_theme', 'gray', level=g.FOREST)
        else:
            ctrl.settings.set('temp_color_theme', '', level=g.FOREST)
        ctrl.main.update_colors()

    ### Watcher #########################

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to
        listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act
         accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        if signal == 'palette_changed':
            for other in self.others.values():
                other.update_colors()

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
    edges = SavedField("edges")  #, if_changed=reserve_update_for_trees)
    groups = SavedField("groups")
    others = SavedField("others")
    vis_data = SavedField("vis_data", watcher="visualization")
    derivation_steps = SavedField("derivation_steps")
    comments = SavedField("comments")
    gloss_text = SavedField("gloss_text")
    syntax = SavedField("syntax")
    is_parsed = SavedField("is_parsed")
    gloss = SavedField("gloss")
