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
import itertools

from PyQt6 import QtWidgets

import kataja.globals as g
from kataja.ChainManager import ChainManager
from kataja.ForestDrawing import ForestDrawing
from kataja.ProjectionManager import ProjectionManager
from kataja.SavedField import SavedField
from kataja.SavedObject import SavedObject
from kataja.SemanticsManager import SemanticsManager
from kataja.Triangle import Triangle
from kataja.UndoManager import UndoManager
from kataja.globals import ViewUpdateReason
from kataja.parser.INodeToKatajaConstituent import INodeToKatajaConstituent
from kataja.saved.DerivationTree import DerivationTree
from kataja.saved.Edge import Edge
from kataja.saved.movables.Arrow import Arrow
from kataja.saved.movables.Node import Node
from kataja.settings.ForestSettings import ForestSettings
from kataja.singletons import ctrl, classes
from kataja.syntax.SyntaxState import SyntaxState


class Forest(SavedObject):
    """ Forest is a group of trees that together form one view.
    Often there needs to be more than one trees visible at same time,
     so that they can be compared or to show states of construction
      where some edges are not yet linked to the main root.
      Forest is the container for these.
      Forest also takes care of the operations manipulating, creating and
      removing trees. """

    def __init__(self, heading_text='', comments=None, syntax=None):
        """ Create an empty forest. Gloss_text and comments are metadata
        about trees that doesn't belong to syntax implementation, so its kept here. Syntax
        implementations may still use it.

        By default, a new Forest doesn't create its nodes -- it doesn't do the derivation yet.
        This is to save speed and memory with large structures. If the is_parsed -flag is False
        when created, but once Forest is displayed, the derivation has to run and after that
        is_parsed is True.
        """
        super().__init__()
        self._connections = []
        self.nodes_from_synobs = {}
        self.main = ctrl.main
        self.in_display = False
        self.visualization = None
        self.is_parsed = False
        self.syntax = syntax or classes.SyntaxAPI()

        self.parser = None
        self.undo_manager = None
        self.chain_manager = None
        self.drawing = None
        self.semantics_manager = None
        self.projection_manager = None
        self.settings = None
        self.derivation_tree = None

        self.old_label_mode = 0
        self.trees = []
        self.nodes = {}
        self.edges = {}
        self.arrows = {}
        self.groups = {}
        self.others = {}
        self.vis_data = {}
        self.width_map = {}
        self.traces_to_draw = {}
        self.comments = []
        self.heading_text = heading_text
        self.ongoing_animations = set()
        self.halt_drawing = False
        self.free_movers = False
        self.comments = comments

        # Update request flags
        self._do_edge_visibility_check = False
        self._do_recalculate_relative_positions = False

    def init_factories(self):
        """ Some initialisations are postponed to when the forest is selected for
        display. When there are hundreds of trees, initialising them at once is slow.
        :return:
        """
        self.derivation_tree = DerivationTree(self)
        self.settings = ForestSettings(self)
        self.parser = INodeToKatajaConstituent(self)
        self.undo_manager = UndoManager(self)
        self.chain_manager = ChainManager(self)
        self.drawing = ForestDrawing(self)
        self.semantics_manager = SemanticsManager(self)
        self.projection_manager = ProjectionManager(self)

    def after_model_update(self, updated_fields, transition_type):
        """ Compute derived effects of updated values in sensible order.
        :param updated_fields: field keys of updates
        :param transition_type: 0:edit, 1:CREATED, -1:DELETED
        :return: None
        """
        if 'nodes' in updated_fields:
            # rebuild from-syntactic_object-to-node -dict
            self.nodes_from_synobs = {}
            for node in self.nodes.values():
                if node.syntactic_object:
                    self.nodes_from_synobs[node.syntactic_object.uid] = node
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
        self.is_parsed = False
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
        self.connect_main()
        if not self.is_parsed:
            self.init_factories()
            self.syntax.create_derivation(forest=self, lexicon=ctrl.document.lexicon)
            self.derivation_tree.update_dimensions()
            self.after_model_update('nodes', 0)
            self.is_parsed = True
            self.derivation_tree.show_first_passing_parse()
            self.forest_edited()

        ctrl.main.update_colors()
        self.add_all_to_scene()
        self.update_visualization()
        self.draw()  # do draw once to avoid having the first draw in undo stack.
        ctrl.view_manager.update_viewport(ViewUpdateReason.NEW_FOREST)
        ctrl.resume_undo()
        ctrl.graph_view.setFocus()

    def retire_from_display(self):
        """ Announce that this forest should not try to work with scene
        anymore --
         some other forest is occupying the scene now.
        :return:
        """
        for item in self.get_all_objects():
            self.remove_from_scene(item, fade_out=False)
        self.in_display = False
        self.disconnect_main()

    def connect_main(self):
        self._connections += [ctrl.main.palette_changed.connect(self.others_update_colors)]

    def disconnect_main(self):
        for item in self._connections:
            if item:
                ctrl.main.palette_changed.disconnect(item)
        self._connections = []

    def clear(self):
        if self.in_display:
            for item in self.get_all_objects():
                self.remove_from_scene(item, fade_out=False)
        self.is_parsed = False
        self.nodes_from_synobs = {}
        self.parser = INodeToKatajaConstituent(self)
        self.undo_manager = UndoManager(self)
        self.chain_manager = ChainManager(self)
        self.drawing = ForestDrawing(self)
        self.projection_manager = ProjectionManager(self)
        self.derivation_tree = DerivationTree(self)
        self.trees = []
        self.nodes = {}
        self.edges = {}
        self.groups = {}
        self.arrows = {}
        self.others = {}
        self.width_map = {}
        self.traces_to_draw = {}
        self.comments = []
        self.heading_text = ''

    def forest_edited(self):
        """ Called after forest editing/free drawing actions that have changed the node graph.
        Analyse the node graph and update/rebuild syntactic objects according to graph.
        :return:
        """
        self.chain_manager.update()

        # Update list of trees
        new_tops = []
        for top in self.trees:
            if top.is_top_node(visible=True):
                if top not in new_tops:
                    new_tops.append(top)
            else:
                for nt in top.get_highest():
                    if nt not in new_tops:
                        new_tops.append(nt)
        for node in self.nodes.values():
            if node.node_type == g.CONSTITUENT_NODE and \
                    node.is_top_node(visible=True) and \
                    node not in new_tops:
                new_tops.append(node)

        self.trees = new_tops

    def add_step(self, syn_state: SyntaxState):
        """ Store given syntactic state as a derivation step. Forest can switch which derivation
        state it is currently displaying.
        :param syn_state: SyntaxState object
        :return:
        """
        self.derivation_tree.add_step(syn_state)

    def get_nodes_by_index(self, index) -> (Node, set):
        head = None
        traces = set()
        for node in self.nodes.values():
            if node.node_type == g.CONSTITUENT_NODE and node.index == index:
                if node.is_trace:
                    traces.add(node)
                else:
                    head = node
        return head, traces

    def set_visualization(self, name):
        """ Switches the active visualization to visualization with given key
        :param name: string
        """
        if self.visualization and self.visualization.say_my_name() == name:
            self.visualization.reselect()
        else:
            vs = self.main.visualizations
            self.visualization = vs.get(name, vs.get(self.settings.get('visualization'), None))
            self.vis_data = {'name': self.visualization.say_my_name()}
            self.visualization.prepare(self)
        ctrl.view_manager.update_viewport(ViewUpdateReason.MAJOR_REDRAW)

    def restore_visualization(self):
        name = self.vis_data.get('name', None) or self.settings.get('visualization')
        if (not self.visualization) or name != self.visualization.say_my_name():
            v = self.main.visualizations.get(name, None)
            if v:
                self.visualization = v
                v.prepare(self, reset=False)
                ctrl.view_manager.update_viewport(ViewUpdateReason.MAJOR_REDRAW)

    def update_visualization(self):
        """ Verify that the active visualization is the same as defined in
        the vis_data (saved visualization state)
        :return: None
        """
        name = self.vis_data.get('name', None) or self.settings.get('visualization')
        if (not self.visualization) or name != self.visualization.say_my_name():
            self.set_visualization(name)

    # ### Maintenance and support methods
    # ################################################

    def __iter__(self):
        return self.trees.__iter__()

    def textual_form(self, tree_top=None, node=None):
        """ return (unicode) version of linearizations of all trees with
        traces removed --
            as close to original sentences as possible. If trees or node is given,
            return linearization of only that.
        """

        def _tree_as_text(tree_top, delimiter=' '):
            """ Cheapo linearization algorithm for Node structures."""
            sorted_cons = tree_top.get_sorted_leaf_constituents()
            l = [str(n.syntactic_object) for n in sorted_cons]
            return delimiter.join(l)

        def _partial_tree_as_text(tree_top, node, delimiter=' '):
            """ Cheapo linearization algorithm for Node structures."""
            sorted_cons = tree_top.get_sorted_constituents()
            if node not in sorted_cons:
                return ''
            i = sorted_cons.index(node)
            l = [str(n.syntactic_object) for n in sorted_cons[i:]]
            return delimiter.join(l)

        if tree_top:
            return _tree_as_text(tree_top)
        elif node:
            return _partial_tree_as_text(node.get_highest(), node)
        else:
            trees = []
            for tree_top in self.trees:
                new_line = _tree_as_text(tree_top)
                if new_line:
                    trees.append(new_line)
            return '/ '.join(trees)

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
            if item.syntactic_object:
                # remember to rebuild nodes_by_uid in undo/redo, as it is not
                #  stored in model
                self.nodes_from_synobs[item.syntactic_object.uid] = item
        elif isinstance(item, Edge):
            self.poke('edges')
            self.edges[item.uid] = item
        elif isinstance(item, Arrow):
            self.poke('arrows')
            self.arrows[item.uid] = item
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
                parent = getattr(item, 'locked_to_node', None)
                if parent and parent is not item.parentItem():
                    item.setParentItem(parent)

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
        for item in itertools.chain(self.nodes.values(),
                                    self.edges.values(),
                                    self.arrows.values(),
                                    self.others.values(),
                                    self.projection_manager.projection_visuals if self.projection_manager else [],
                                    self.semantics_manager.all_items if self.semantics_manager else [],
                                    self.groups.values()):
            yield item

    def get_object_by_uid(self, uid):
        return self.nodes.get(uid, None) or self.edges.get(uid, None) \
               or self.groups.get(uid, None) or self.arrows.get(uid, None) or \
               self.others.get(uid, None)

    def get_node(self, constituent):
        """ Returns a node corresponding to a constituent """
        if not constituent:
            return None
        if not self.nodes_from_synobs:
            self.rebuild_synobj_dict()
        return self.nodes_from_synobs.get(constituent.uid, None)

    def rebuild_synobj_dict(self):
        if not self.nodes:
            return
        self.nodes_from_synobs = {}
        for node in self.nodes.values():
            if node.syntactic_object:
                self.nodes_from_synobs[node.syntactic_object.uid] = node

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
        # if not self.ongoing_animations:
        #    self.draw()

    def flush_and_rebuild_temporary_items(self):
        """ Clean up temporary stuff that may be invalidated by changes made by undo/redo.
        Notice that draw() does some of this, don't have to do those here.
        :return:
        """
        # Selection and related UI
        ctrl.multiselection_start()
        for item in ctrl.selected:
            if not self.get_object_by_uid(item.uid):
                ctrl.remove_from_selection(item)
        ctrl.multiselection_end()

    def draw(self, start_animations=False):
        """ Update all trees in the forest according to current visualization
        """
        if self.halt_drawing:
            print('halt drawing is on')
            return
        if not self.in_display:
            print("Why are we drawing a forest which shouldn't be in scene")
            return
        self.update_feature_ordering()
        self.update_forest_gloss()
        self.update_constituent_node_shapes()
        if self.visualization:
            self.visualization.prepare_draw()
            self.free_movers = self.visualization.has_free_movers()
            left_nodes = set()
            for tree_top in self.trees:
                self.visualization.draw_tree(tree_top)
                self.visualization.normalise_to_origo(tree_top)
                self.visualization.estimate_overlap_and_shift_tree(tree_top, left_nodes)
            # keep everything centered to minimise movement between steps
            # cp = ctrl.view_manager.center()
            # print('current center point: ', cp)
            # self.free_movers = self.visualization.normalise_all(-cp.x(), -cp.y())
            ctrl.view_manager.predictive = not self.free_movers

        self.chain_manager.after_draw_update()
        self.recalculate_positions_relative_to_nodes()
        ctrl.view_manager.update_viewport(ViewUpdateReason.MAJOR_REDRAW)
        if start_animations or True:
            ctrl.graph_scene.start_animations()
        ctrl.graph_view.resetCachedContent()
        ctrl.graph_view.repaint()

    def move_nodes(self, heat) -> bool:
        """ Animate nodes one tick toward their next position, or compute the next
        position in dynamic visualisation. Update edges and other forest elements that
         are drawn relative to node positions.
        :return:
        """
        nodes_are_moving = False
        for tree_top in self.trees:
            if not tree_top.isVisible():
                continue
            sorted_nodes = tree_top.get_sorted_nodes()
            to_normalize = []
            x_sum = 0
            y_sum = 0
            allow_normalization = True
            other_nodes = [x for x in sorted_nodes if not x.locked_to_node]

            for node in sorted_nodes:
                if not node.isVisible():
                    continue
                # Computed movement
                diff_x, diff_y, normalize, ban_normalization = node.move(other_nodes, heat)
                if allow_normalization and normalize and not ban_normalization:
                    # We cannot rely on movement alone to tell if node should be
                    # normalized. It is possible for node to remain still while other end of
                    # graph is wiggling, and to not normalize such node causes more wiggling.
                    to_normalize.append(node)
                    x_sum += diff_x
                    y_sum += diff_y
                if ban_normalization:
                    allow_normalization = False
                if abs(diff_x) + abs(diff_y) > 0.5:
                    node.is_moving = True
                    nodes_are_moving = True
                else:
                    node.is_moving = False

            # normalize movement so that the trees won't glide away
            if allow_normalization and to_normalize:
                avg_x = x_sum / len(to_normalize)
                avg_y = y_sum / len(to_normalize)
                for node in to_normalize:
                    node.current_position = (node.current_position[0] - avg_x,
                                             node.current_position[1] - avg_y)
        self.recalculate_positions_relative_to_nodes(forced=True)
        self.edge_visibility_check()
        return nodes_are_moving

    def redraw_edges(self, edge_type=None):
        if edge_type:
            for edge in self.edges.values():
                if edge.edge_type == edge_type:
                    edge.path.changed = True
                    edge.update_shape()
            if edge_type == g.CONSTITUENT_EDGE or edge_type == g.ADJUNCT_EDGE:
                for node in self.nodes.values():
                    if node.triangle_stack:
                        node.label_object.update_label(force_update=True)
        else:
            for edge in self.edges.values():
                edge.path.changed = True
                edge.update_shape()
            for node in self.nodes.values():
                if node.triangle_stack:
                    node.label_object.update_label(force_update=True)

    def order_edge_visibility_check(self):
        """ Make sure that all edges are checked to update their visibility.
        This can be called multiple
        times, but the visibility check is done only once.
        """
        self._do_edge_visibility_check = True

    def order_recalculation_of_positions_relative_to_nodes(self):
        self._do_recalculate_relative_positions = True

    def recalculate_positions_relative_to_nodes(self, forced=False):
        if self._do_recalculate_relative_positions or forced:
            self._do_recalculate_relative_positions = False
            for e in self.edges.values():
                e.make_path()
            # for area in f.touch_areas:
            # area.update_position()
            for group in self.groups.values():
                group.update_shape()
            self.semantics_manager.update_position()

    def edge_visibility_check(self):
        """ Perform check for each edge: hide them if their start/end is
        hidden, show them if necessary.
        """
        if not self._do_edge_visibility_check:
            return
        for edge in set(self.edges.values()) | set(self.arrows.values()):
            changed = edge.update_visibility()
            if changed:
                if edge.is_visible():
                    if ctrl.is_selected(edge):
                        ctrl.ui.add_control_points(edge)
                else:
                    ctrl.ui.remove_ui_for(edge)
        self._do_edge_visibility_check = False

    def update_constituent_node_shapes(self):
        """ Make sure that all nodes use right kind of label and that the locked-in children are 
        presented in right way.        
        :return: 
        """
        shape = self.settings.get('cn_shape')
        cnodes = [cn for cn in self.nodes.values() if cn.node_type == g.CONSTITUENT_NODE]
        position = self.settings.get('feature_positioning')
        checking_mode = self.settings.get('feature_check_display')
        fnodes = [f for f in self.nodes.values() if f.node_type == g.FEATURE_NODE]
        for fnode in fnodes:
            fnode.update_label()
        for fnode in fnodes:
            fnode.update_checking_display(shape=shape, position=position, checking_mode=checking_mode)
        for cnode in cnodes:
            cnode.label_object.cn_shape = shape
            cnode.update_label()
            cnode.setZValue(cnode.preferred_z_value())
            if cnode.is_triangle_host():
                Triangle.add_or_update_triangle_for(cnode)
            cnode.gather_children(position, shape)
            cnode.update_bounding_rect()
            cnode.update()
        self.prepare_width_map()

    def update_forest_gloss(self):
        """ Draw the gloss text on screen, if it exists. """
        strat = self.settings.get('gloss_strategy')
        if strat:
            if strat == 'linearisation':
                gts = []
                for tree_top in self.trees:
                    gt = self.syntax.linearize(tree_top)
                    if gt:
                        gts.append(gt)
                self.heading_text = ' '.join(gts)
            elif strat == 'message':
                pass
            elif strat == 'manual':
                pass
            elif strat == 'no':
                self.heading_text = ''
        else:
            self.heading_text = ''
        ctrl.ui.refresh_heading()

    def update_feature_ordering(self):

        def flat(listlike):
            res = []
            if not listlike:
                return res
            for xy in listlike:
                if isinstance(xy, tuple):
                    res.append(xy[0])
                    res.append(xy[1])
                else:
                    res.append(xy)
            return res

        def sort_attached_features(node):
            const = node.syntactic_object
            if const.parts:
                sorted_syn_feats = []
                feat_lists = [part.inherited_features for part in const.parts]
                found = False
                for j, feat in enumerate(itertools.chain(const.inherited_features,
                                                         flat(const.checked_features))):
                    for i, feat_list in enumerate(feat_lists):
                        if feat in feat_list:
                            sorted_syn_feats.append((i, feat_list.index(feat), feat))
                            found = True
                            break
                    if not found:
                        sorted_syn_feats.append((-1, j, feat))
                sorted_syn_feats = [f for i, j, f in sorted(sorted_syn_feats)]
            else:
                sorted_syn_feats = list(const.features)

            sortable_edges = [(sorted_syn_feats.index(e.origin.syntactic_object)
                               if e.origin and e.origin.syntactic_object in sorted_syn_feats else i + 100, e) for i, e in
                              enumerate(node.edges_down) if e.edge_type == g.FEATURE_EDGE]

            return [e for i, e in sorted(sortable_edges)]

        for cn in self.nodes.values():
            if cn.node_type == g.CONSTITUENT_NODE:
                if cn.syntactic_object:
                    cn.cached_sorted_feature_edges = sort_attached_features(cn)
                else:
                    cn.cached_sorted_feature_edges = [e for e in cn.edges_down
                                                      if e.edge_type == g.FEATURE_EDGE]

        for edge in self.edges.values():
            edge.cached_edge_start_index = edge.edge_start_index(from_cache=False)
            edge.cached_edge_end_index = edge.edge_end_index(from_cache=False)
            if edge.path:
                edge.path.cached_shift_for_start = None
                edge.path.cached_shift_for_end = None

    def compute_traces_to_draw(self, rotator) -> int:
        if self.settings.get('left_first_rotation'):
            self.compute_left_first_rotation()
            return 0
        else:
            return self.compute_highest_first_rotation(rotator)

    def compute_left_first_rotation(self):
        def add_children(node, parent):
            if node not in used:
                used.add(node)
                if hasattr(node, 'index') and parent:
                    trace_dict[node.uid] = parent.uid
                for child in node.get_all_children(visible=False):
                    add_children(child, node)

        trace_dict = {}
        used = set()
        for tree_top in self:
            add_children(tree_top, None)

        self.traces_to_draw = trace_dict
        return 0

    def compute_highest_first_rotation(self, rotator):
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
        for tree_top in self:
            sortable_parents = []
            ltree = tree_top.get_sorted_nodes()
            for n_index, node in enumerate(ltree):
                if not hasattr(node, 'index'):
                    continue
                parents = node.get_parents(visible=True)
                if len(parents) > 1:
                    node_key = node.uid
                    required_keys.add(node_key)
                    my_parents = []
                    for parent in parents:
                        if parent in ltree:
                            i = ltree.index(parent)
                            my_parents.append((max((i, n_index - 1)), node_key, parent, True))
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
        elif not parent:
            return node.uid not in self.traces_to_draw or not self.traces_to_draw[node.uid]
        elif hasattr(node, 'index') and len(node.get_parents(visible=True)) > 1:
            if node.uid in self.traces_to_draw:
                if parent.uid != self.traces_to_draw[node.uid]:
                    return False
        return True

    def prepare_width_map(self):
        """ A map of how much horizontal space each node would need -- it is better to do this
        once than recursively compute these when updating labels.
        :return:
        """
        done = set()

        def recursive_width(node):
            if node in done:
                return 0
            done.add(node)
            if node.is_leaf(visible=True):
                if node.is_visible():
                    w = node.label_object.width
                else:
                    w = 0
            else:
                w = node.label_object.left_bracket_width() + node.label_object.right_bracket_width()
                for n in node.get_children(visible=True):
                    if self.should_we_draw(n, node):
                        w += recursive_width(n)
            self.width_map[node.uid] = w
            return w

        self.width_map = {}
        for tree_top in self:
            recursive_width(tree_top)
        return self.width_map

    def others_update_colors(self):
        for other in self.others.values():
            other.update_colors()

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    trees = SavedField("trees")  # the current line of trees
    derivation_tree = SavedField("derivation_tree")  # Available parses
    nodes = SavedField("nodes")
    edges = SavedField("edges")
    arrows = SavedField("arrows")
    groups = SavedField("groups")
    others = SavedField("others")
    vis_data = SavedField("vis_data", watcher=ctrl.main.visualisation_changed)
    comments = SavedField("comments")
    heading_text = SavedField("heading_text")
    syntax = SavedField("syntax")
    is_parsed = SavedField("is_parsed")
    gloss = SavedField("gloss")
