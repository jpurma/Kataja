# -*- coding: UTF-8 -*-
#############################################################################
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
#############################################################################


import string

from PyQt5 import QtWidgets

from kataja.ForestSettings import ForestSettings, ForestRules
from kataja.Bracket import Bracket
from kataja.BracketManager import BracketManager
from kataja.ConstituentNode import ConstituentNode
from kataja.AttributeNode import AttributeNode
from kataja.Controller import ctrl, prefs, qt_prefs
from kataja.ChainManager import ChainManager
from kataja.DerivationStep import DerivationStepManager
from kataja.GlossNode import GlossNode
from kataja.Node import Node
from kataja.Parser import Parser, BottomUpParser
from kataja.Presentation import TextArea, Image
from kataja.Edge import Edge
from kataja.UndoManager import UndoManager
from kataja.utils import next_free_index, to_tuple, time_me, quit, to_unicode
from kataja.FeatureNode import FeatureNode
from kataja.globals import CONSTITUENT_EDGE, FEATURE_EDGE, GLOSS_EDGE


ONLY_LEAF_LABELS = 0
ALL_LABELS = 1
ALIASES = 2

# alignment of edges -- in some cases it is good to draw left branches differently than right branches
NO_ALIGN = 0
LEFT = 1
RIGHT = 2


def restore_forest(key):
    print 'restore forest? who is calling this and is it doable?'
    assert (False)
    obj = None
    for forest in ctrl.forest_keeper:
        if forest.key == key:
            obj = forest
            break
    if not obj:
        assert (False)
        obj = Forest()
        obj._revived = True
    # ctrl.undo.repair_later(obj)
    return obj


# class Iterator:
#     """ Iterates through binary tree """
#     def __init__(self, host):
#         """ Iterator is given one node 'host' to begin with """
#         self._host = host
#         self._iter_stack = [host]
#         self._count = 0

#     def __iter__(self):
#         """ This is iterator by itself """
#         return self

#     def next(self):
#         """ Implements left-first -iteration through the tree. """
#         if self._iter_stack:
#             next = self._iter_stack.pop(0)
#             self._iter_stack = next.get_children() + self._iter_stack
#             self._count += 1
#             return next
#         else:
#             raise StopIteration

# class IterateOnce:
#     """ Iterator that returns each node only once """
#     def __init__(self, host):
#         """ Iterator is given one node 'host' to begin with """
#         self._host = host
#         self._iter_stack = [host]
#         self._count = 0
#         self._done = set()

#     def __iter__(self):
#         """ This is iterator by itself """
#         return self

#     def next(self):
#         """ Implements left-first -iteration through the tree. """
#         if self._iter_stack:
#             next = None
#             while self._iter_stack and not next:
#                 l = self._iter_stack.pop(0)
#                 if l not in self._done:
#                     next = l
#                     self._done.add(next)
#             if next:
#                 self._iter_stack = next.get_children() + self._iter_stack
#                 self._count += 1
#                 return next
#             else:
#                 raise StopIteration
#         else:
#             raise StopIteration

class Forest:
    """ Forest is a group of trees that together form one view.
    Often there needs to be more than one tree visible at same time,
     so that they can be compared or to show states of construction
      where some edges are not yet linked to the main root.
      Forest is the container for these.
      Forest also takes care of the operations manipulating, creating and
      removing trees. """
    saved_fields = ['roots', 'nodes', 'edges', 'others', 'chain_manager', 'settings', 'derivation_steps',
                    'merge_counter', 'select_counter', '_comments', '_parser', '_gloss_text', '_buildstring',
                    'undo_manager', 'vis_data']


    def __init__(self, main, restoring=''):
        """ Create an empty forest """
        self.save_key = 'forest_%s' % id(self)
        self.main = main
        self.roots = []  # the current line of trees
        self.nodes = {}
        # self.features = {}
        self.edges = {}
        self.bracket_manager = BracketManager(self)
        self.others = {}
        self.chain_manager = ChainManager(self)
        self.gloss = None
        self.settings = ForestSettings(self, prefs)
        self.rules = ForestRules(self, prefs)
        self.visualization = None  # BalancedTree()
        self.vis_data = {}
        self.derivation_steps = DerivationStepManager(self)
        self.merge_counter = 0
        self.select_counter = 0
        self._comments = []
        self._parser = BottomUpParser(self)
        # self._parser = Parser(self)
        self._gloss_text = u''
        self._buildstring = ''
        self.undo_manager = UndoManager(self)


    def after_restore(self, changes):
        """ Changes in some fields may cause need for manual fixes or running methods to update derived variables """
        print 'changes in forest: ', changes.keys()
        if 'vis_data' in changes:

            old_vis, new_vis = changes['vis_data']
            # if visualization keeps the same, it can use vis_data directly, it doesn't need to 
            # prepare again. 
            if old_vis['name'] != new_vis['name']:
                # if visualization is changed, then it should change the visualization object and not let it to use the new_vis_data.  
                print 'changing visualization to: ', new_vis['name']
                self.visualization = self.main.visualizations[new_vis['name']]
                self.visualization.set_forest(self)

    def get_scene(self):
        return self.main.graph_scene


    #@time_me
    def list_nodes(self, first):
        res = []

        def _iterate(node):
            res.append(node)
            for child in node.get_children():
                _iterate(child)

        _iterate(first)
        return res

    #@time_me
    def list_nodes_once(self, first):
        res = []

        def _iterate(node):
            if not node in res:
                res.append(node)
                for child in node.get_children():
                    _iterate(child)

        _iterate(first)
        return res

        # from ConstituentNode.py
        # fix me

    #     def linearized(self, gaps = False):
    #         l = []
    #         for node in linearize(self, []):
    #             if node.is_leaf():
    #                 if node.is_trace:
    #                     if gaps:
    #                         l.append(u'_')
    #                     else:
    #                         continue
    #                 else:
    #                     l.append(to_unicode(self.alias or node.syntactic_object))
    #         return u' '.join(l)


    def info_dump(self):
        if hasattr(self, 'key'):
            print '----- Forest %s ------' % self.save_key
            print '| Nodes: %s' % len(self.nodes)
            print '| Edges: %s' % len(self.edges)
            print '| Others: %s' % len(self.others)
            print '| Visualization: ', self.visualization
            print '| Color scheme: ', self.settings.hsv()
        else:
            print 'odd forest, not initialized.'


    def build(self, buildstring):
        """ Populate forest from a buildstring, store buildstring for reference """
        self._buildstring = buildstring
        self.create_tree_from_string(buildstring)

    def set_gloss_text(self, gloss):
        self._gloss_text = gloss

    def draw_gloss_text(self):
        """ Create a gloss text, a freeform translation of tree in some familiar language """
        if self._gloss_text:
            if not self.gloss:
                self.gloss = QtWidgets.QGraphicsTextItem(parent=None)
                self.gloss.setTextWidth(400)
                self.gloss.setDefaultTextColor(ctrl.cm().drawing())
                self.gloss.setFont(qt_prefs.font)  # @UndefinedVariable
                # self.gloss.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
            self.gloss.setPlainText(u"‘" + self._gloss_text + u"’")
            self.gloss.show()
        else:
            if self.gloss:
                self.remove_item_from_scene(self.gloss)
                self.gloss = None

    def change_visualization(self, key):
        if self.visualization and self.visualization.__class__.name == key:
            self.visualization.reselect()
        else:
            self.visualization = self.main.visualizations[key]
            self.visualization.prepare(self)
        self.main.graph_scene.reset_zoom()

    #### Maintenance and support methods ################################################

    def __iter__(self):
        return self.roots.__iter__()

    def textual_form(self, root=None):
        """ return (unicode) version of linearizations of all trees with traces removed --
            as close to original sentences as possible. If root is given, return linearization of only that. """

        def _tree_as_text(root_node, gap):
            """ Cheapo linearization algorithm for Node structures."""
            l = []
            for node in self.list_nodes_once(root_node):
                l.append(unicode(node.syntactic_object))
            return gap.join(l)

        if root:
            return _tree_as_text(root, u' ')
        else:
            roots = []
            for root in self.roots:
                roots.append(_tree_as_text(root, u' '))
            return u'/ '.join(roots)

    def store(self, item):
        """ Confirm that item is stored in some dictionary or other storage in forest """
        # if isinstance(item, ConstituentNode):
        #    self.nodes[item.key] = item
        # elif isinstance(item, FeatureNode):
        #    self.features[item.key] = item
        if isinstance(item, Node):
            self.nodes[item.save_key] = item
        elif isinstance(item, Edge):
            self.edges[item.save_key] = item
        elif isinstance(item, TextArea):
            self.others[item.save_key] = item
        elif isinstance(item, Bracket):
            self.bracket_manager.store(item)

        else:
            key = getattr(item, 'save_key', '') or getattr(item, 'key', '')
            if key and key not in self.others:
                self.others[key] = item
            else:
                print 'F trying to store broken type:', item.__class__.__name__


    def get_all_objects(self):
        return self.nodes.values() + self.edges.values() + self.others.values() + self.bracket_manager.get_brackets()

    def clear_scene(self):
        """ Disconnect related graphic items from GraphScene """
        scene = self.get_scene()
        if scene.displayed_forest != self.main.forest:
            return
        if self.gloss:
            scene.removeItem(self.gloss)
        for item in self.get_all_objects():
            scene.removeItem(item)
        self.gloss = None

    def add_all_to_scene(self):
        """ Put items belonging to this forest to scene """
        if ctrl.loading:
            return
        scene = self.get_scene()
        if scene.displayed_forest != self.main.forest:
            return
        for item in self.get_all_objects():
            scene.addItem(item)

    def add_to_scene(self, item):
        """ Put items belonging to this forest to scene """
        if ctrl.loading:
            return
        scene = self.get_scene()
        if scene.displayed_forest != self.main.forest:
            return
        scene.addItem(item)


    def update_all(self):
        """ Go through the visible tree and check that every node that should exist exists and
        that every edge of every type that should exist is there too.
        Then check that there isn't any objects that shouldn't be there """
        self.update_roots()
        for root in self.roots:
            root.update_visibility()
        self.bracket_manager.update_brackets()
        self.draw_gloss_text()


    def update_colors(self, adjusting = False):
        cm = ctrl.cm()
        old_gradient_base = cm.paper()
        self.main.color_manager.update_colors(prefs, self.settings, adjusting=adjusting)
        #colors.update_colors(prefs, self.settings, adjusting=adjusting)
        self.main.app.setPalette(cm.get_qt_palette())
        if old_gradient_base != cm.paper() and cm.gradient:
            self.main.graph_scene.fade_background_gradient(old_gradient_base, cm.paper())
        else:
            self.main.graph_scene.setBackgroundBrush(qt_prefs.no_brush)
        #for node in self.nodes.values():
        #    node.update_colors()
        #for edge in self.edges.values():
        #    edge.update_colors()
        for other in self.others.values():
            other.update_colors()
        #self.bracket_manager.update_colors()
        if self.gloss:
            self.gloss.setDefaultTextColor(cm.drawing())
        self.main.ui_manager.update_colors()


    def visible_nodes(self):
        """
            :rtype kataja.Node
         """
        return self.nodes.values()
        # for n in self.nodes.values():
        #     if n and n.is_visible():
        #         yield n
        #     else:
        #         print 'skipping hidden node', n

    def get_node(self, constituent):
        """
        Returns a node corresponding to a constituent
        :param syntax.BaseConstituent constituent:
        :rtype kataja.ConstituentNode
        """
        return self.nodes.get('CN%s' % constituent.uid, None)

    def get_constituent_edges(self):
        return [x for x in self.edges.values() if x.edge_type == 'constituent_edge' and x.is_visible()]

    def get_constituent_nodes(self):
        return [x for x in self.nodes.values() if isinstance(x, ConstituentNode) and x.isVisible()]

    def get_feature_nodes(self):
        return [x for x in self.nodes.values() if isinstance(x, FeatureNode)]

    def get_attribute_nodes(self):
        return [x for x in self.nodes.values() if isinstance(x, AttributeNode)]

    def add_comment(self, comment):
        self._comments.append(comment)

    #@time_me
    def update_roots(self):
        self.roots = []
        for node in self.nodes.values():
            if not node.edges_up:
                self.roots.append(node)
                # print '*** updating roots ***: ', len(self.roots)


    # refactor this, implementation is not good
    def is_higher_in_tree(self, node_A, node_B):
        node_A_root = node_A_index = node_B_root = node_B_index = 999
        found_A = False
        found_B = False
        for root_index, root in enumerate(self.roots):
            for index, node in enumerate(self.list_nodes_once(root)):
                if (not found_A) and node == node_A:
                    node_A_root = root_index
                    node_A_index = index
                elif (not found_B) and node == node_B:
                    node_B_root = root_index
                    node_B_index = index
                if found_A and found_B:
                    break
            if found_A and found_B:
                break
        if node_A_root != node_B_root:
            return -1
        return int(node_A_index < node_B_index)

    def index_in_tree(self, node):
        for root in self.roots:
            for i, n in enumerate(self.list_nodes_once(root)):
                if n is node:
                    return i
        return -1

    def get_first_free_constituent_name(self):
        names = [node.syntactic_object.get_label() for node in self.nodes.values() if
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

    #### Primitive creation of forest objects ###################################

    #@time_me
    def create_node_from_constituent(self, C, pos=None, result_of_merge=False, result_of_select=False,
                                     replacing_merge=0, replacing_select=0, silent=False):
        """ All of the node creation should go through this! """
        node = self.get_node(C)
        if not node:
            node = ConstituentNode(constituent=C, forest=self)
        else:
            assert (False)
        if pos:
            node.set_original_position(pos)
        self.add_to_scene(node)
        node.update_visibility()
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
            print "ConstituentNode doesn't announce its origin"
            raise KeyError

        # for key, feature in C.get_features().items():
        #    self.create_feature_node(node, feature)
        if self.visualization:
            self.visualization.reset_node(node)
        return node

    def create_feature_node(self, host, syntactic_feature):
        FN = FeatureNode(syntactic_feature, self)
        FN.compute_start_position(host)
        self._connect_node(host, child=FN, edge_type=FN.__class__.default_edge_type)
        self.add_to_scene(FN)
        FN.update_visibility()
        return FN

    def create_attribute_node(self, host, attribute_id, attribute_label, show_label=False):
        AN = AttributeNode(host, attribute_id, attribute_label, show_label=show_label, forest=self)
        self._connect_node(host, child=AN, edge_type=AN.__class__.default_edge_type)
        self.add_to_scene(AN)
        AN.update_visibility()
        return AN

    def create_edge(self, start=None, end=None, edge_type='', direction=''):
        #print 'creating edge ', start, end, edge_type
        rel = Edge(self, start=start, end=end, edge_type=edge_type, direction=direction)
        if ctrl.loading:
            pass
        else:
            self.add_to_scene(rel)
        return rel

    def create_bracket(self, host=None, left=True):
        br = self.bracket_manager.create_bracket(host, left)
        self.add_to_scene(br)
        return br


    def create_gloss_node(self, host_node):
        """ Creates the gloss node for existing constituent node and necessary connection Doesn't do any checks """
        gn = GlossNode(host_node)
        self._connect_node(child=gn, parent=host_node, edge_type=gn.__class__.default_edge_type)
        self.add_to_scene(gn)
        return gn

    # not used
    def create_image(self, image_path):
        im = Image(image_path)
        self.others[im.save_key] = im
        self.add_to_scene(im)
        return im

    def create_node_from_string(self, text='', pos=None):
        root_node = self._parser.parse(text)
        self.add_to_scene(root_node)
        self.update_roots()

    # @time_me
    def create_tree_from_string(self, text, replace=False):
        """ This will probably end up resulting one tree, but during parsing there may be multiple roots/trees """
        if replace:
            self.roots = []
        text = text.strip()
        if text.startswith('\gll'):
            self._gloss_text = text[5:].strip('{} ')
        parser_method = self._parser.detect_suitable_parser(text)
        parser_method(text)
        self.update_roots()
        if self.settings.uses_multidomination():
            self.traces_to_multidomination()
        else:
            self.chain_manager.rebuild_chains()

    def create_trace_for(self, node):
        index = node.get_index()
        new_chain = False
        if not index:
            index = self.next_free_index()
            node.set_index(index)
            new_chain = True
        assert (index)
        constituent = ctrl.Constituent('t', source='t_' + index)
        constituent.set_index(index)
        trace = self.create_node_from_constituent(constituent, silent=True)
        trace.is_trace = True
        if new_chain:
            self.chain_manager.rebuild_chains()
        if self.settings.uses_multidomination():
            trace.hide()
        return trace

    def create_empty_node(self, pos, give_label=True):
        if give_label:
            label = self.get_first_free_constituent_name()
        else:
            label = ''
        C = ctrl.Constituent(label)
        node = self.create_node_from_constituent(C, pos, result_of_select=True)
        return node


    ############# Deleting items ######################################################
    # item classes don't have to know how they relate to each others.
    # here when something is removed from scene, it is made sure that it is also removed
    # from items that reference to it.

    def delete_node(self, node):
        """ Delete given node and its children and fix the tree accordingly
        Note: This and other complicated revisions assume that the target tree is 'normalized' by replacing multidomination
        with traces. Each node can have only one parent. This makes calculation easier, just remember to call multidomination_to_traces
        and traces_to_multidomination after deletions.
        """
        # -- connections to other nodes --
        for edge in node.edges_up:
            self._disconnect_node(edge=edge)
        for edge in node.edges_down:
            if edge.end:
                self.delete_node(edge.end)  # this will also disconnect node
            else:
                self._disconnect_node(edge=edge)
        # -- ui elements --
        self.main.ui_manager.delete_ui_elements_for(node)
        # -- brackets --
        self.bracket_manager.remove_brackets(node)
        # -- dictionaries --
        del self.nodes[node.save_key]
        self.update_roots()
        # -- scene --
        sc = node.scene()
        if sc:
            sc.removeItem(node)


    def delete_edge(self, edge):
        """ remove from scene and remove references from nodes """
        # -- connections to host nodes --
        start_node = edge.start
        end_node = edge.end
        if start_node:
            if edge in start_node.edges_down:
                start_node.edges_down.remove(edge)
            if edge in start_node.edges_up:  # shouldn't happen
                start_node.edges_up.remove(edge)
        if end_node:
            if edge in end_node.edges_down:  # shouldn't happen
                end_node.edges_down.remove(edge)
            if edge in end_node.edges_up:
                end_node.edges_up.remove(edge)
        # -- ui elements --
        self.main.ui_manager.delete_ui_elements_for(edge)
        # -- dictionaries --
        del self.edges[edge.save_key]
        # -- scene --
        sc = edge.scene()
        if sc:
            sc.removeItem(edge)


    def delete_item(self, item):
        # def remove_stored(self, item):
        #     """ Remove item from various storages """
        #     if isinstance(item, Node):
        #         if item.key in self.nodes:
        #             del self.nodes[item.key]
        #     elif isinstance(item, Edge):
        #         if item.key in self.edges:
        #             del self.edges[item.key]
        #     elif isinstance(item, TextArea):
        #         if item.key in self.others:
        #             del self.others[item.key]
        #     elif isinstance(item, Bracket):
        #         if item.key in self.brackets:
        #             del self.brackets[item.key]
        #     else:
        #         key = getattr(item, 'key', '')
        #         if key and key in self.others:
        #             del self.others[item.key]
        #         else:
        #             print 'F trying to remove broken item:', item.__class__.__name__
        pass


    # ## order markers are special nodes added to nodes to signal the order when the node was merged/added to forest
    #######################################################################

    def add_order_features(self, key='M'):
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
            if callable(val):
                val = val()
            if val:
                self.create_attribute_node(node, attr_id, attribute_label=key, show_label=show_label)


    def remove_order_features(self, key='M'):
        for node in self.get_attribute_nodes():
            if node.attribute_label == key:
                self.delete_node(node)


    def update_order_features(self, node):
        M = node.get_attribute_nodes('M')
        S = node.get_attribute_nodes('S')
        if M and not self.settings.shows_merge_order():
            self.delete_node(M)
        elif self.settings.shows_merge_order() and (not M) and node.merge_order:
            self.create_attribute_node(node, 'merge_order', attribute_label='M', show_label=True)
        if S and not self.settings.show_select_order:
            self.delete_node(S)
        elif self.settings.shows_select_order() and (not S) and node.select_order:
            self.create_attribute_node(node, 'select_order', attribute_label='S', show_label=False)

    def add_select_counter(self, node, replace=0):
        if replace:
            node.select_order = replace
        else:
            self.select_counter += 1
            node.select_order = self.select_counter
        self.update_order_features(node)

    def add_merge_counter(self, node, replace=0):
        if replace:
            node.select_order = replace
        else:
            self.merge_counter += 1
            node.merge_order = self.merge_counter
        self.update_order_features(node)


    #### Minor updates for forest elements #######################################################################


    def reform_constituent_node_from_string(self, text, node):
        new_node = self._parser.parse(text)
        self._replace_node(node, new_node)

    # not used
    def edit_node_alias(self, node, text):
        # this just changes the node without modifying its identity
        assert (False)
        node.alias = text

    # not used
    def rebuild_constituent_node(self, node, text):
        # I think this has to be done by removing the old node and replacing it with a new one.
        new_node = self._parser.parse(text, forest=self)
        self._replace_node(node, new_node)

    #### Switching between multidomination and traces ######################################

    def group_traces_to_chain_head(self):
        self.chain_manager.group_traces_to_chain_head()

    def traces_to_multidomination(self):
        self.chain_manager.traces_to_multidomination()

    def multidomination_to_traces(self):
        self.chain_manager.multidomination_to_traces()


        # # if using traces, merge original and leave trace, or merge trace and leave original. depending on which way the structure is built.
        # print '-------------------'
        # print 'dropping for merge'

        # print 'f.settings.use_multidomination:', f.settings.use_multidomination
        # if not f.settings.use_multidomination:
        #     new_trace = f.create_trace_for(dropped_node)
        #     new_trace.set_original_position(dropped_node.get_current_position())
        #     chain = f.get_chain(dropped_node.get_index())
        #     traces_first = f.traces_go_first()
        #     if traces_first:
        #         if f.is_higher_in_tree(self.host, dropped_node):
        #             new_node = new_trace
        #         else:
        #             new_node = dropped_node
        #             dropped_node._replace_node(new_trace)
        #     else:
        #         if f.is_higher_in_tree(self.host, dropped_node):
        #             new_node = dropped_node
        #             dropped_node._replace_node(new_trace)
        #         else:
        #             new_node = new_trace
        # else:
        #     new_node = dropped_node
        # top_node, left_node, right_node = self.merge_to_host(new_node)
        # ctrl.on_cancel_delete = []
        # left_node._hovering = False
        # right_node._hovering = False
        # return True


    #### Undoable commands ###############################################################

    def disconnect_node_from_tree(self, node):
        """ Delete node from tree and make a new tree out of it """
        self.main.add_message("Disconnecting node %s" % node)
        if self.settings.uses_multidomination():
            self.multidomination_to_traces()
            if node.get_index():
                chain = self.get_chain(node.get_index())
                for l in chain:
                    self.delete_node(l)
            else:
                self.delete_node(node)
            self.update_roots()
            self.chain_manager.rebuild_chains()
            # self._fix_chains()
            self.traces_to_multidomination()
        else:
            self.delete_node(node)
            self.chain_manager.rebuild_chains()
            # self._fix_chains()
        self.undo_manager.record("Disconnected node %s" % node)
        return None

    def command_delete(self, node):
        """ Undoable UI interface for deletion """
        self.main.add_message("Deleting node %s" % node)
        if self.settings.uses_multidomination():
            self.multidomination_to_traces()
            if node.get_index():
                chain = self._chains[node.get_index()]
                for l in chain:
                    self.delete_node(l)
            else:
                self.delete_node(node)
            self.chain_manager.rebuild_chains()
            # self._fix_chains()
            self.traces_to_multidomination()
        else:
            self.delete_node(node)
            self.chain_manager.rebuild_chains()
            # self._fix_chains()
        self.undo_manager.record("Delete node %s" % node)
        return None

    def undoable_delete_node(self, node):
        # add things to undo stack
        # affected = [self]
        #########
        self.undo_manager.record('delete constituent')
        is_root = node.is_root_node()
        if not self.settings.uses_multidomination():
            if node.is_chain_head():
                key = node.get_index()
                chain = self.get_chain(key)
                stub = None
                if len(chain) > 1:
                    next_node, dummy_next_parent = chain[1]
                    for edge in node.edges_up:
                        if edge.edge_type == node.__class__.default_edge_type:
                            start = edge.start
                            self._disconnect_node(node, edge.start, edge.edge_type)
                            if not start.left():
                                stub = self.create_empty_node(pos=to_tuple(start.pos()))
                                self._connect_node(start, child=stub, direction='left')
                            elif not start.right():
                                stub = self.create_empty_node(pos=to_tuple(start.pos()))
                                self._connect_node(start, child=stub, direction='right')
                    self._replace_node(next_node, node)
                    self.delete_node(next_node)
                    if stub:
                        ctrl.select(stub)
                    return
                else:
                    self.remove_chain(node.get_index, delete_traces=False)
            elif node.is_trace:
                self.remove_from_chain(node)
        for edge in list(node.edges_up):
            start = edge.start
            self._disconnect_node(node, edge.start, edge.edge_type)
            if start.is_empty_node():
                self.delete_node(start)
            elif prefs.default_binary_branching:
                if not start.left():
                    stub = self.create_empty_node(pos=edge.start_point)
                    self._connect_node(start, child=stub, direction='left')
                elif not start.right():
                    stub = self.create_empty_node(pos=edge.start_point)
                    self._connect_node(start, child=stub, direction='right')
        for edge in list(node.edges_down):
            end = edge.end
            self._disconnect_node(node, edge.end, edge.edge_type)
            if end.is_empty_node():
                self.delete_node(end)
        ctrl.remove_from_selection(node)
        self.delete_node(node)
        return

    def undoable_delete_edge(self, R):
        # add things to undo stack
        self.undo_manager.record('delete edge')
        #########
        if R.start:
            R.start.edges_down.remove(R)
            if R.start.is_empty_node():
                self.delete_node(R.start)
            elif prefs.default_binary_branching:
                if not R.start.left():
                    stub = self.create_empty_node(pos=to_tuple(R.start.pos()), root=False)
                    R.start._connect_node(child=stub, direction='left')
                elif not R.start.right():
                    stub = self.create_empty_node(pos=to_tuple(R.start.pos()), root=False)
                    R.start._connect_node(child=stub, direction='right')
        if R.end:
            R.end.edges_up.remove(R)
            if not R.end.edges_up:
                if R.end.is_empty_node():
                    self.delete_node(R.end)
        ctrl.remove_from_selection(R)
        self.delete_edge(R)
        return


    #### Connecting and disconnecting items ##########################
    #
    # Since the "trees" are not necessarily trees, but can have circular
    # edges, recursive or composite methods are not very reliable for
    # making or removing connections between nodes. It is better to do it
    # here on forest level.
    #
    # These manipulations should be low level operations only called from
    # by forest's higher level methods.
    #

    def _reflect_connection_in_syntax(self, edge):
        """ This edge has been created into the graph.
        Verify that there exists a syntactic edge corresponding to this, if doesn't,
        create it. """
        if edge.edge_type == CONSTITUENT_EDGE:
            C_start = edge.start.syntactic_object
            C_end = edge.end.syntactic_object
            if edge.align == LEFT:
                if C_start.get_left() != C_end:
                    if C_start.get_left():
                        print '***** warning! constituent %s has left and we are overwriting it with %s' % (
                            C_start, C_end)
                    C_start.set_left(C_end)
            elif edge.align == RIGHT:
                if C_start.get_right() != C_end:
                    if C_start.get_right():
                        print '***** warning! constituent %s has right and we are overwriting it with %s' % (
                            C_start, C_end)
        elif edge.edge_type == FEATURE_EDGE:
            constituent = edge.start.syntactic_object
            feature = edge.end.syntactic_object
            if not constituent.has_feature(feature.key):
                constituent.set_feature(feature.key, feature)

    def _connect_node(self, parent=None, child=None, edge_type='', direction='', to_index=-1):
        """ This is for connecting nodes with a certain edge. Calling this once will create the necessary links for both partners.
            Sanity checks:
            - Immediate circular links (child becomes immediate parent of its immediate parent) are not allowed.
            - If items are already linked with this edge type, error is raised.
            - Cannot link to itself.
          """
        if parent == child:
            raise
        if not parent and child:
            raise
        edge_type = edge_type or parent.__class__.default_edge_type
        new_edge = self.create_edge(start=parent, end=child, edge_type=edge_type, direction=direction)
        for old_edge in child.edges_up:
            if old_edge.edge_type == edge_type:
                if old_edge.end == child and old_edge.start == parent:
                    print 'edge exists already', old_edge
                    raise
                elif old_edge.start == child and old_edge.end == parent:
                    print 'circular edge'
                    raise
        child.edges_up.append(new_edge)
        if direction == '' or direction == 'right' or direction == 2:
            parent.edges_down.append(new_edge)
        else:
            parent.edges_down.insert(0, new_edge)
        self._reflect_connection_in_syntax(new_edge)
        if parent.left():
            if not parent.left_bracket:
                parent.left_bracket = self.create_bracket(host=parent, left=True)
        if parent.right():
            if not parent.right_bracket:
                parent.right_bracket = self.create_bracket(host=parent, left=False)
        return new_edge

    def _reflect_disconnection_in_syntax(self, edge):
        """ This edge has been disconnected in graph and soon will be removed altogether.
        Verify that there doesn't exist syntactic edge corresponding to this, and if does,
        remove it. """
        if edge.edge_type == CONSTITUENT_EDGE:
            C_start = edge.start.syntactic_object
            C_end = edge.end.syntactic_object
            if edge.align == LEFT:
                if C_start.get_left():
                    C_start.set_left(None)
            elif edge.align == RIGHT:
                if C_end.get_right():
                    C_end.set_right(None)
        elif edge.edge_type == FEATURE_EDGE:
            constituent = edge.start.syntactic_object
            feature = edge.end.syntactic_object
            if edge.start and edge.end and constituent.has_feature(feature):
                constituent.del_feature(feature)


    def _disconnect_node(self, first=None, second=None, edge_type='', edge=None):
        """ Removes and deletes a edge between two nodes """
        if not edge:
            edge = first.get_edge_to(second, edge_type)
        if edge:
            if edge.start == first:
                first.edges_down.remove(edge)
                second.edges_up.remove(edge)
            elif edge.end == first:
                second.edges_down.remove(edge)
                first.edges_up.remove(edge)
            self._reflect_disconnection_in_syntax(edge)
            self.delete_edge(edge)
        else:
            assert (False)

    def _replace_node(self, old_node, new_node, only_for_parent=None, replace_children=False):
        """ When replacing a node we should make sure that edges get fixed too. """
        assert (old_node != new_node)  # if this can happen, we'll probably have infinite loop somewhere
        new_node.set_current_position(old_node.get_current_position())
        new_node.set_adjustment(old_node.get_adjustment())
        new_node.set_computed_position(old_node.get_computed_position())
        new_node.update_visibility(active=True, fade=True)

        for edge in list(old_node.edges_up):
            if edge.start:
                align = edge.align
                parent = edge.start
                if only_for_parent and parent != only_for_parent:
                    continue
                self._disconnect_node(parent, old_node, edge.edge_type)
                self._connect_node(parent, child=new_node, edge_type=edge.edge_type, direction=align)

        if replace_children and not only_for_parent:
            for edge in list(old_node.edges_down):
                child = edge.end
                if child:
                    align = edge.align
                    self._disconnect_node(old_node, child, edge.edge_type)
                    self._connect_node(new_node, child, edge_type=edge.edge_type, direction=align)

        if not old_node.edges_up:
            old_node.update_visibility(active=False, fade=True)


    ############ Complex node operations ##############################


    # @time_me
    def merge_nodes(self, node_A, node_B):
        if node_B in node_A:
            self.main.add_message('Cannot Merge into itself')
            return
        if node_B.is_root_node():
            merger = self._merge(node_A, node_B)
        else:
            merger = self._merge_and_tuck(node_A, node_B)
        self.undo_manager.record(u"Merge %s with %s" % (unicode(node_A), unicode(node_B)))
        self.main.add_message(u"Merge %s with %s" % (unicode(node_A), unicode(node_B)))
        return merger

    def _merge(self, node_A, node_B):
        """ Merge between two roots.
        If using multidomination, then merge itself is simple, but we still need to create a trace constituent to be used when switched to trace view.
        If using trace view, create a trace and merge it to node_B.
        """
        print "who is using this??? _merge(A,B)"
        assert (False)

        if not node_A.parents:
            external_merge = True
        else:
            external_merge = False
            # old_parents=list(node_A.parents)
        index = node_A.get_index()
        if external_merge:
            if index:
                # this is a strange case, but needs to be covered. there is no reason for singular constituent to have an index
                if index in self._chains:
                    index = next_free_index(self._chains.keys())
                    node_A.set_index(index)
                self.add_to_chain(index, node_A)  # now we have a chain with single node in it.
            else:
                pass
                # simplest case, just do a merge, no traces or indexes
        else:  # internal merges always involve chains
            if not index:
                # need to create a new trace index for merged constituent and a matching trace
                index = next_free_index(self._chains.keys())
                node_A.set_index(index)
                self.add_to_chain(index, node_A)
            # needs to create a trace for trace view
            trace = self.create_trace_for(node_A)
            self._insert_into_chain(index, trace)
            if not self.settings.uses_multidomination():
                self._replace_node(node_A, trace)

        merger_const = ctrl.UG.Merge(node_A.syntactic_object, node_B.syntactic_object)
        merger_node = self.create_node_from_constituent(merger_const, pos=node_A.get_current_position(),
                                                        result_of_merge=True)
        merger_node._connect_node(child=node_A)
        merger_node._connect_node(child=node_B)
        # needs to check if trees should be removed or merger node set as a root node
        self.update_roots()
        if self.visualization:
            self.visualization.reset_node(merger_node)
        return merger_node

    # this won't work
    def _merge_and_tuck(self, node_A, node_B):
        """ Merge becomes a bit more complicated if node_B already has parents. Then the merger is tugged between parents and merged item."""

        merger_const = ctrl.UG.Merge(node_A.syntactic_object, node_B.syntactic_object)
        merger_node = self.create_node_from_constituent(merger_const, pos=node_A.get_current_position(),
                                                        result_of_merge=True)
        # does it matter which one is the active partner here?
        # in a simple merge, node_A is active -- it is moving --, but it already may have parents. these are not affected.
        # node_B is a root node of some root and becomes the right side node of merger.
        # in this case node_B has parents too, and for them node_B should be replaced with the new merged node
        # ReplaceConstituentNode works only with nodes, it doesn't change constituent structure. How to do that nicely?
        # In principle, UG doesn't have to support that. Modified ConstituentNode.
        self._replace_node(node_B, merger_node)
        self.update_roots()
        if self.visualization:
            self.visualization.reset_node(merger_node)
        return merger_node

        # def merge_to_host(self, merged_node):

    #     ctrl.on_cancel_delete = []
    #     x, y, z = self.host.get_current_position()
    #     f = self.host.forest
    #     if not merged_node:
    #         merged_node = f.create_empty_node(pos = (x, y, z), root = False)
    #         ctrl.on_cancel_delete.append(merged_node)
    #     if self.top:
    #         top_node = f.create_empty_node(pos = (x, y - prefs.edge_height, z), root = False)
    #         ctrl.on_cancel_delete.append(top_node)
    #         if self.left:
    #             # merge top left
    #             left_node = merged_node
    #             right_node = self.host
    #             merged_node.set_computed_position((x - 2 * prefs.edge_width, y, z))

    #         else:
    #             # merge top right
    #             left_node = self.host
    #             right_node = merged_node
    #             merged_node.set_computed_position((x + 2 * prefs.edge_width, y, z))
    #     else:
    #         sister_node = f.create_empty_node(pos = (x, y + prefs.edge_height, z), root = False)
    #         ctrl.on_cancel_delete.append(sister_node)
    #         top_node = self.host
    #         if self.left:
    #             # merge bottom left
    #             left_node = merged_node
    #             right_node = sister_node
    #         else:
    #             # merge bottom right
    #             left_node = sister_node
    #             right_node = merged_node
    #         left_node.set_computed_position((x - prefs.edge_width, y + prefs.edge_height, z))
    #         right_node.set_computed_position((x + prefs.edge_width, y + prefs.edge_height, z))


    #     top_node._connect_node(child = left_node, direction = 'left', mirror_in_syntax = True)
    #     top_node._connect_node(child = right_node, direction = 'right', mirror_in_syntax = True)
    #     if self.top:
    #         f.add_root(top_node)
    #     left_node._hovering = False
    #     right_node._hovering = False
    #     ctrl.select(merged_node)
    #     return top_node, left_node, right_node


    def replace_node_with_merged_empty_node(self, N, R, merge_to_left, new_node_pos, merger_node_pos):
        ex, ey = new_node_pos
        empty_node = self.create_empty_node(pos=(ex, ey, N.z))
        self.replace_node_with_merged_node(N, empty_node, R, merge_to_left, merger_node_pos)


    def replace_node_with_merged_node(self, N, new_node, R, merge_to_left, merger_node_pos):
        """ This happens when touch area in edge R going up from node N is clicked.
        [N B] -> [[x N] B] (left == True) or
        [N B] -> [[N x] B] (left == False)
        """
        print 'called replace_node_with_merged_empty_node'
        if R:
            start_node = R.start
            end_node = R.end
            align = R.align
            self._disconnect_node(edge=R)

        mx, my = merger_node_pos
        if merge_to_left:
            merger_node = self.create_merger_node(left=new_node, right=N, pos=(mx, my, N.z))
        else:
            merger_node = self.create_merger_node(left=N, right=new_node, pos=(mx, my, N.z))
        if R:
            print 'connecting merger to parent'
            self._connect_node(start_node, merger_node, direction=align)
        self.update_roots()

    def create_merger_node(self, left=None, right=None, pos=(0, 0, 0)):
        """ Gives a merger node of two nodes. Doesn't try to fix their edges upwards """
        merger_const = ctrl.UG.Merge(left.syntactic_object, right.syntactic_object)
        merger_node = self.create_node_from_constituent(merger_const, pos=pos, result_of_merge=True)
        self._connect_node(parent=merger_node, child=left, direction='left')
        self._connect_node(parent=merger_node, child=right, direction='right')
        self.update_roots()
        return merger_node


    # @time_me
    def cut_and_merge(self, node_A, node_B):
        if node_B in node_A:
            self.main.add_message('Cannot move into itself')
            return
        self._cut_and_merge(node_A, node_B)
        self.undo_manager.record("Moved %s on %s" % (node_A, node_B))
        self.main.add_message("Moved %s on %s" % (node_A, node_B))

    def _cut_and_merge(self, node_A, node_B):
        """ First remove all connections between node_A and its parents and then merge it to node_B """
        parents = node_A.get_parents()
        if parents:
            for parent in set(parents):
                parent._disconnect_node(node_A)
        if node_B.is_root_node():
            self._merge(node_A, node_B)
        else:
            self._merge_and_tuck(node_A, node_B)
        self.update_roots()


    def _copy_node(self, node):
        new_c = node.syntactic_object.copy()
        new_node = self.create_node_from_constituent(new_c, pos=node.get_current_position(), result_of_select=True)
        return new_node


    # @time_me
    def copy_node(self, node):
        """ Copy a node and make a new tree out of it """
        if not node:
            return
        new_node = self._copy_node(node)
        self.update_roots()
        self.undo_manager.record("Copied %s" % node)
        self.main.add_message("Copied %s" % node)
        return new_node


    ##### Dragging ##############################################

    def prepare_touch_areas_for_dragging(self, excluded=set()):
        print '---- preparing for dragging ------'
        um = self.main.ui_manager
        um.remove_touch_areas()
        for root in self.roots:
            if root in excluded:
                continue
            um.create_touch_area(root, 'top_left', for_dragging=True)
            um.create_touch_area(root, 'top_right', for_dragging=True)
        for edge in self.get_constituent_edges():
            if edge.start in excluded or edge.end in excluded:
                continue
            um.create_touch_area(edge, 'left', for_dragging=True)
            um.create_touch_area(edge, 'right', for_dragging=True)


    ######### Utility functions ###############################

    def parse_features(self, string, node):
        return self._parser.parse_definition(string, node)

