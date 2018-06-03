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

import kataja.globals as g
from kataja.errors import ForestError
from kataja.saved.Edge import Edge
from kataja.saved.Group import Group
from kataja.saved.movables.Node import Node
from kataja.saved.movables.Image import Image
from kataja.saved.movables.nodes.ConstituentNode import ConstituentNode
from kataja.singletons import ctrl, classes, log
from kataja.nodes_to_synobjs import figure_out_syntactic_label
from kataja.utils import time_me
from kataja.parser.INodes import join_lines, ICommandNode, ITextNode, remove_triangle


class FreeDrawing:
    """ This is a class purely for legibility and code organisation. This operates on Forest data
    and each instance is inside a Forest-instance. FreeDrawing contains all graph-building
    operations related to Forest -- it manipulates Nodes and Edges and totally ignores syntactic
    objects. Node graphs created by FreeDrawing can then try to build matching syntactic objects,
    but it is not responsibility of methods here.
     """

    def __init__(self, forest):
        """ attach free drawing to specific forest. FreeDrawing can have non-permanent instance
        data, e.g. caches or helper dicts, but nothing here is saved.
        """
        self.f = forest
        self.edge_types = set()
        self.node_types = set()
        self._marked_for_deletion = set()
        self.label_rotator = 0

    @property
    def nodes(self):
        return self.f.nodes

    @property
    def edges(self):
        return self.f.edges

    @property
    def groups(self):
        return self.f.groups

    def poke(self, attribute):
        self.f.poke(attribute)

    # #### Comments #########################################

    def add_comment(self, comment):
        """ Add comment item to forest
        :param comment: comment item
        """
        self.f.comments.append(comment)

    def remove_comment(self, comment):
        """ Remove comment item from forest
        :param comment: comment item
        :return:
        """
        if comment in self.f.comments:
            self.f.comments.remove(comment)

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

    def next_free_label(self):
        self.label_rotator += 1
        if self.label_rotator == len(string.ascii_uppercase):
            self.label_rotator = 0
        return string.ascii_uppercase[self.label_rotator]

    # ### Primitive creation of forest objects ################################

    def create_node(self, label='', relative=None, pos=None, node_type=1, **kw):
        """ This is generic method for creating all of the Node subtypes.
        Keep it generic!
        :param label: label text for node, behaviour depends on node type, usually main text content
        :param relative: node will be relative to given node, pos will be interpreted relative to
        given node and new node will have the same trees as a parent.
        :param pos:
        :param node_type:
        :return:
        """
        node_class = classes.nodes.get(node_type)
        node = node_class(label=label, **kw)
        node.after_init()
        # resetting node by visualization is equal to initializing node for
        # visualization. e.g. if nodes are locked to position in this vis,
        # then lock this node.
        if self.f.visualization:
            self.f.visualization.reset_node(node)
        # it should however inherit settings from relative, if such are given
        if relative:
            node.copy_position(relative)
        if pos:
            node.set_original_position(pos)
            # node.update_position(pos)
        self.f.add_to_scene(node)
        node.update_visibility(fade_in=False, fade_out=False)
        return node

    def create_feature_node(self, label='feature', sign='', value='', family='', host=None):
        gn = self.create_node(label=label, sign=sign, value=value, family=family, relative=host,
                              node_type=g.FEATURE_NODE)
        if host:
            self.connect_node(host, child=gn)
        return gn

    def create_gloss_node(self, label='gloss', host=None):
        gn = self.create_node(label=label, relative=host, node_type=g.GLOSS_NODE)
        if host:
            self.connect_node(host, child=gn)
        return gn

    def create_comment_node(self, text=None, host=None, pixmap_path=None):
        cn = self.create_node(label=text, relative=host, node_type=g.COMMENT_NODE)
        if host:
            self.connect_node(host, child=cn)
        if pixmap_path:
            cn.set_image_path(pixmap_path)
        return cn

    def create_edge(self, start=None, end=None, edge_type='', fade=False, alpha=None):
        """

        :param start:
        :param end:
        :param edge_type:
        :param fade:
        :param alpha:
        :return:
        """
        rel = Edge(start=start, end=end, edge_type=edge_type, alpha=alpha)
        rel.after_init()
        self.f.store(rel)
        self.f.add_to_scene(rel)
        if fade and self.f.in_display and start.is_visible() and end.is_visible():
            rel.fade_in()
        return rel

    # not used
    def create_image(self, image_path):
        """

        :param image_path:
        :return:
        """
        im = Image(image_path)
        self.f.others[im.uid] = im
        self.f.add_to_scene(im)
        return im

    def create_trace_for(self, node):
        """

        :param node:
        :return:
        """
        index = node.index
        if not index:
            index = self.f.chain_manager.next_free_index()
            node.index = index
        trace = self.create_node(label='t', relative=node)
        trace.is_trace = True
        trace.index = index
        trace.update_label()
        return trace

    def create_arrow(self, start=None, end=None, text=None):
        """ Create an arrow (Edge) using the default arrow style

        :param p1: start point
        :param p2: end point
        :param text: explanatory text associated with the arrow
        :return:
        """
        start_point = None
        end_point = None
        if isinstance(p1, Node):
            start = p1
        elif isinstance(p1, tuple):
            start_point = p1
            start = None
        else:
            start_point = random.randint(-50, 50), random.randint(-50, 50)
            start = None
        if isinstance(p2, Node):
            end = p2
        elif isinstance(p2, tuple):
            end_point = p2
            end = None
        else:
            end_point = random.randint(-50, 50), random.randint(-50, 50)
            end = None
        arrow = Arrow(start=start, end=end, start_point=start_point,
                      end_point=end_point, text=text)
        self.f.store(arrow)
        self.f.add_to_scene(arrow)
        if fade and self.f.in_display:
            arrow.fade_in()
        ctrl.select(arrow)
        return arrow

    # ############ Deleting items  ######################################################
    # item classes don't have to know how they relate to each others.
    # here when something is removed from scene, it is made sure that it is
    # also removed
    # from items that reference to it.

    def delete_node(self, node, touch_edges=True, fade=True):
        """ Delete given node and its children and fix the trees accordingly
        :param node:
        :param touch_edges: don't try to set edge ends.
        just delete.
        :param fade: fade or disappear instantly
        """
        # block circular deletion calls
        if node in self._marked_for_deletion:
            return
        else:
            self._marked_for_deletion.add(node)

        # -- connections to other nodes --
        if touch_edges:
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
        if node.syntactic_object:
            if node.syntactic_object.uid in self.f.nodes_from_synobs:
                del self.f.nodes_from_synobs[node.syntactic_object.uid]

        assert (node.uid not in self.f.nodes)
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

        # if fading out, item scene position has to remain same during the fade. If disappear
        # instantly, it doesnt matter
        if node.parentItem():
            if fade:
                scpos = node.scenePos()
                node.setParentItem(None)
                node.set_original_position(scpos)
            else:
                node.setParentItem(None)

        if hasattr(node, 'on_delete'):
            node.on_delete()
        # -- scene --
        self.f.remove_from_scene(node, fade_out=fade)
        # -- undo stack --
        node.announce_deletion()
        # -- remove from selection
        ctrl.remove_from_selection(node)
        # -- remove circularity block
        self._marked_for_deletion.remove(node)

    def delete_edge(self, edge, touch_nodes=True, fade=True):
        """ remove from scene and remove references from nodes
        :param edge:
        :param ignore_consequences: don't try to fix things like connections,
        just delete.
        """
        # block circular deletion calls
        if edge in self._marked_for_deletion:
            print('already marked for deletion')
            return
        else:
            self._marked_for_deletion.add(edge)
        # -- connections to host nodes --
        start_node = edge.start
        end_node = edge.end
        # -- remove links to other edges
        if start_node:
            for edge_up in start_node.edges_up:
                if edge_up.end_links_to == edge:
                    edge_up.end_links_to = None

        if end_node:
            for edge_down in end_node.edges_down:
                if edge_down.start_links_to == edge:
                    edge_down.start_links_to = None
                    edge_down.update_start_symbol()
        # -- selections --
        ctrl.remove_from_selection(edge)
        if touch_nodes:
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
        ctrl.ui.remove_ui_for(edge)
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
        self.f.remove_from_scene(edge, fade_out=fade)
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
            self.delete_edge(item, touch_nodes=not ignore_consequences)
        elif isinstance(item, Node):
            self.delete_node(item, touch_edges=not ignore_consequences)

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
        edge.connect_end_points(new_start, edge.end)
        new_start.poke('edges_down')
        new_start.edges_down.append(edge)

    def set_edge_end(self, edge, new_end):
        """

        :param edge:
        :param new_end:
        """

        assert new_end.uid in self.nodes
        if edge.end:
            edge.end.poke('edges_up')
            edge.end.edges_up.remove(edge)
        edge.connect_end_points(edge.start, new_end)
        new_end.poke('edges_up')
        new_end.edges_up.append(edge)

    def add_feature_to_node(self, feature, node):
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
    def connect_node(self, parent=None, child=None, direction='', edge_type=None, fade_in=False,
                     alpha=None):
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
        :param alpha:
        """

        # print('--- connecting node %s to %s ' % (child, parent))
        # Check for arguments:
        if not (parent and child):
            raise ForestError('Trying to connect nodes, but other is missing (parent:%s, '
                              'child%s)' % (parent, child))
        if parent == child:
            raise ForestError('Connecting to self: ', parent, child)

        if not edge_type:
            edge_type = child.edge_type()

        # Check for circularity:
        for old_edge in child.edges_up:
            if old_edge.edge_type == edge_type:
                if old_edge.end == child and old_edge.start == parent \
                        and old_edge.alpha == alpha:
                    # raise ForestError('Identical edge exists already')
                    log.info('Identical edge exists already')
                    return
                elif old_edge.start == child and old_edge.end == parent:
                    raise ForestError('Connection is circular')

        # Create edge and make connections
        new_edge = self.create_edge(start=parent, end=child, edge_type=edge_type, fade=fade_in,
                                    alpha=alpha)

        for edge_up in parent.edges_up:
            if edge_up.alpha == new_edge.alpha:
                edge_up.end_links_to = new_edge
                new_edge.start_links_to = edge_up

        for edge_down in child.edges_down:
            if edge_down.alpha == new_edge.alpha:
                edge_down.start_links_to = new_edge
                new_edge.end_links_to = edge_down
                edge_down.update_start_symbol()

        new_edge.update_start_symbol()

        child.poke('edges_up')
        parent.poke('edges_down')
        if direction == g.LEFT:
            child.edges_up.insert(0, new_edge)
            parent.edges_down.insert(0, new_edge)
        else:
            child.edges_up.append(new_edge)
            parent.edges_down.append(new_edge)
        parent.reindex_edges()
        child.reindex_edges()
        if hasattr(child, 'on_connect'):
            child.on_connect(parent)
        return new_edge

    def disconnect_edge(self, edge):
        """ Does the local mechanics of edge removal
        :param edge:
        :return:
        """
        if edge.start:
            if edge in edge.start.edges_down:
                edge.start.poke('edges_down')
                edge.start.edges_down.remove(edge)
        if edge.end:
            if edge in edge.end.edges_up:
                edge.end.poke('edges_up')
                edge.end.edges_up.remove(edge)
        self.delete_edge(edge)

    def disconnect_node(self, parent=None, child=None, edge_type='', edge=None):
        """ Removes and deletes a edge between two nodes. If asked to do so, can reset
        projections and trees ownerships, but doesn't do it automatically, as disconnecting is
        often part of more complex series of operations.
        :param parent:
        :param child:
        :param edge_type:
        :param edge: if the edge that connects nodes is already identified, it can be given directly
        """
        if edge:
            parent = edge.start
            child = edge.end
        if not edge:
            edge = parent.get_edge_to(child, edge_type)

        if edge:
            self.disconnect_edge(edge)

        if parent:
            parent.reindex_edges()
        if child:
            child.reindex_edges()

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

        if old_node.pos():
            new_node.copy_position(old_node)
        new_node.update_visibility(fade_in=True)  # active=True,

        # add new node to relevant groups
        # and remove old node from them
        for group in self.groups.values():
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
            self.delete_node(old_node, touch_edges=False)

    # ########### Complex node operations ##############################

    def delete_unnecessary_merger(self, node):
        """

        :param node:
        :raise ForestError:
        """
        if not isinstance(node, ConstituentNode):
            raise ForestError("Trying to treat wrong kind of node as ConstituentNode and "
                              "forcing it to binary merge")

        if hasattr(node, 'index'):
            i = node.index
        else:
            i = ''
        children = list(node.get_children(similar=True, visible=False))
        for child in list(children):
            parents = node.get_parents(similar=True, visible=False)
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
                    log.info(m)
                    self.disconnect_node(node, child)
                    for parent in list(bad_parents):
                        for grandparent in list(parent.get_parents()):
                            self.disconnect_node(grandparent, parent)
                            self.disconnect_node(parent, child)
                            self.connect_node(grandparent, child)

                if good_parents:
                    # normal case
                    self.disconnect_node(node, child)
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

    def unary_add_child_for_constituentnode(self, new_node: ConstituentNode,
                                            old_node: ConstituentNode, add_left=True):
        """
        :param new_node:
        :param old_node:
        :param add_left:
        :return:
        """
        children = old_node.get_children(similar=True, visible=False)

        if len(children) != 1:
            return
        child = children[0]
        old_edge = old_node.get_edge_to(child)
        if add_left:
            self.connect_node(parent=old_node, child=new_node, direction=g.LEFT, fade_in=True)
        else:
            self.connect_node(parent=old_node, child=new_node, direction=g.RIGHT, fade_in=True)

    def add_sibling_for_constituentnode(self, new_node, old_node: ConstituentNode, add_left=True):
        """ Create a new merger node to top of this node and have this node and new node as its
        children.
        :param new_node:
        :param old_node:
        :param add_left: adding node to left or right -- if binary nodes, this marks which one
        will be projecting.
        :return:
        """
        new_node.heads = [new_node]

        if add_left:
            left = new_node
            right = old_node
        else:
            left = old_node
            right = new_node
        parent_info = [(e.start, e.direction()) for e in
                       old_node.get_edges_up(similar=True, visible=False)]

        for op, align in parent_info:
            self.disconnect_node(parent=op, child=old_node)

        merger_node = self.create_merger_node(left=left, right=right, new=new_node)

        for group in self.groups.values():
            if old_node in group:
                group.add_node(merger_node)

        for op, align in parent_info:
            self.connect_node(parent=op, child=merger_node, direction=align, fade_in=True)
        merger_node.heads = list(old_node.heads)

    def merge_to_top(self, top, new, merge_to_left=True):
        """
        :param top:
        :param new:
        :param merge_to_left:
        :param pos:
        :return:
        """
        if merge_to_left:
            left = new
            right = top
        else:
            left = top
            right = new
        self.create_merger_node(left=left, right=right, new=new, heads=top.heads)

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
        edge = parent.get_edge_to(child)
        # store the projection and alignment info before disconnecting the edges
        heads = []
        if parent.node_type == g.CONSTITUENT_NODE:
            heads = parent.heads

        direction = edge.direction()
        self.disconnect_edge(edge)
        if merge_to_left:
            left = inserted
            right = child
        else:
            left = child
            right = inserted

        # connections
        merger_node = self.create_merger_node(left=left, right=right, new=inserted)
        self.connect_node(parent, merger_node, direction=direction)

        # groups
        for group in self.groups.values():
            if parent in group:
                group.add_node(merger_node)

        # projections
        merger_node.set_heads(heads)

    def create_merger_node(self, left=None, right=None, new=None, heads=None):
        """ Gives a merger node of two nodes. Doesn't try to fix their edges
        upwards
        :param left:
        :param right:
        :param new: which one is the new node to add. This connection is animated in.
        :param heads: which one is head?
        """
        if new is left:
            old = right
        else:
            old = left
        lx, ly = left.current_scene_position
        rx, ry = right.current_scene_position
        pos = (lx + rx) / 2, (ly + ry) / 2 - ctrl.settings.get('edge_height')

        label = ''
        if heads:
            if isinstance(heads, Node):
                label = figure_out_syntactic_label(heads)
            elif isinstance(heads, list):
                if len(heads) == 1:
                    label = figure_out_syntactic_label(heads[0])
                if len(heads) == 2:
                    l1 = figure_out_syntactic_label(heads[0])
                    l2 = figure_out_syntactic_label(heads[1])
                    label = f"({l1}, {l2})"

        merger_node = self.create_node(label=label, relative=old)
        merger_node.current_position = pos
        self.connect_node(parent=merger_node, child=left, direction=g.LEFT, fade_in=new is left)
        self.connect_node(parent=merger_node, child=right, direction=g.RIGHT, fade_in=new is right)
        merger_node.set_heads(heads)
        return merger_node

    # ### Triangles ##############################################

    def add_or_update_triangle_for(self, root):
        """

        :param node:
        """

        def wrap_in_qroof(ilines):
            if len(ilines) > 1:
                parts = []
                for iline in ilines:
                    parts.append(iline)
                    parts.append('\n')
                parts.pop()
            elif isinstance(ilines[0], ICommandNode):
                parts = ilines
            elif isinstance(ilines[0], ITextNode):
                parts = ilines[0].parts
            else:
                parts = ilines
            return ICommandNode(command="qroof", parts=parts)

        if root not in root.triangle_stack:
            root.poke('triangle_stack')
            root.triangle_stack.append(root)
        fold_scope = self.f.list_nodes_once(root)[1:]
        folded = []
        bad_mothers = set()
        if not fold_scope:  # triangle is just visual addition to label
            # some parts in the visual label have to be marked with qroof-tag
            lines = root.label.splitlines()
            if len(lines) < 2:
                root.label = wrap_in_qroof(lines)
            else:
                root.label = join_lines([lines[0], wrap_in_qroof(lines[1:])])
            return

        # triangle_stack for node holds the ground truth of triangles. Folding and graphicsitem
        # parent relation are surface stuff.

        for node in fold_scope:
            if root not in node.triangle_stack:
                node.poke('triangle_stack')
                node.triangle_stack.append(root)
            # multidominated nodes can be folded if all parents are in scope
            # of fold
            parents = node.get_parents()
            if len(parents) > 1:
                can_fold = True
                for parent in parents:
                    if parent not in fold_scope:
                        bad_mothers.add(node)
                        can_fold = False
                        break
                if can_fold:
                    folded.append(node)
            else:
                folded.append(node)

        # remember that the branch that couldn't be folded won't allow
        # any of its children to be
        # folded either.

        def _remove_children(bad_mother: Node):
            for child in bad_mother.get_children(similar=False, visible=False):
                if child in folded:
                    folded.remove(child)
                    _remove_children(child)

        for bm in bad_mothers:
            _remove_children(bm)

        root.fold_into_me(folded)

    def remove_triangle_from(self, root):
        """
        :param node:
        """
        fold_scope = [f for f in self.f.list_nodes_once(root)]
        for node in fold_scope:
            if (not node.triangle_stack) or node.triangle_stack[-1] is not root:
                print('node in triangles fold scope doesnt have triangle root in triangle_stack:',
                      node)
            if node.triangle_stack and node.triangle_stack[-1] is root:
                node.poke('triangle_stack')
                node.triangle_stack.pop()
            if node.parentItem() == root:
                # lets see what happens to node positions -- this may lead to jumps we want to
                # eliminate here.
                node.release_from_locked_position()
            node.update_visibility()  # with triangle_stack reduced, hidden nodes may become
            # visible again.
            # movement back to visualisation positions is handled by visualisation redraw
        remove_triangle(root.label)
        root.update_label()
        # when unfolding a triangle you may unfold previous triangles. Their leaf nodes are now
        # in wrong positions and have to be redrawn. Update all contained triangles:
        [self.add_or_update_triangle_for(n) for n in fold_scope if n.is_triangle_host()]

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
        return group

    def create_group(self):
        group = Group(selection=[], persistent=True)
        self.f.add_to_scene(group)
        self.poke('groups')
        self.groups[group.uid] = group
        return group

    def remove_group(self, group):
        self.f.remove_from_scene(group)
        ctrl.ui.remove_ui_for(group)
        if group.uid in self.groups:
            self.poke('groups')
            del self.groups[group.uid]

    def get_group_color_suggestion(self):
        color_keys = set()
        for group in self.groups.values():
            color_keys.add(group.color_key)
        for i in range(1, 8):
            if 'accent%s' % i not in color_keys:
                return 'accent%s' % i

    def definitions_to_nodes(self, defs):
        leaves = {}
        for node in self.f.nodes.values():
            if node.is_leaf(only_similar=True, only_visible=False):
                leaves[self.f.parser.get_root_word(node.label)] = node
        for key, deffy in defs.items():
            if not key in leaves:
                print('missing key ', key)
                continue
            parts = [x.strip() for x in deffy.split(',')]
            node = leaves[key]
            for part in parts:
                if (part.startswith("'") and part.endswith("'")) or (
                            part.startswith('"') and part.endswith('"')):
                    # gloss node
                    label = part[1:-1]
                    gloss = self.create_gloss_node(label=label, host=node)
                elif part:
                    if ':' in part:
                        fparts = part.split(':')
                    else:
                        fparts = [part]
                    family = ''
                    value = ''
                    if len(fparts) > 2:
                        family = fparts[2]
                    if len(fparts) > 1:
                        value = fparts[1]
                    feature = self.create_feature_node(label=fparts[0], value=value, family=family,
                                                       host=node)
