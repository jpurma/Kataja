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


import kataja.globals as g
from kataja.errors import ForestError
from kataja.saved.Edge import Edge
from kataja.saved.Group import Group
from kataja.saved.movables.Node import Node
from kataja.saved.movables.Presentation import Image
from kataja.saved.movables.nodes.AttributeNode import AttributeNode
from kataja.saved.movables.nodes.ConstituentNode import ConstituentNode
from kataja.singletons import ctrl, classes, log


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


    # ### Primitive creation of forest objects ################################

    def create_node(self, label='', relative=None, pos=None, node_type=1):
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
        node = node_class(label=label)
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
        return node

    def create_gloss_node(self, host):
        gn = self.create_node(label='gloss', relative=host, node_type=g.GLOSS_NODE)
        self.connect_node(host, child=gn)
        return gn

    def create_comment_node(self, text=None, host=None, pixmap_path=None):
        cn = self.create_node(label=text, relative=host, node_type=g.COMMENT_NODE)
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
        AN = AttributeNode(forest=self.f, host=host, attribute_id=attribute_id,
                           label=attribute_label,
                           show_label=show_label)
        self.connect_node(host, child=AN)
        self.f.add_to_scene(AN)
        AN.update_visibility()
        return AN

    def create_edge(self, start=None, end=None, edge_type='', fade=False):
        """

        :param start:
        :param end:
        :param edge_type:
        :param fade:
        :return:
        """
        rel = Edge(start=start, end=end, edge_type=edge_type)
        rel.after_init()
        self.f.store(rel)
        self.f.add_to_scene(rel)
        if fade and self.f.in_display:
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
        assert index
        trace = self.create_node(relative=node)
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

    def create_arrow_from_node_to_point(self, start_node, end_point):
        edge = self.create_edge(start=None, end=None, edge_type=g.ARROW)
        edge.connect_start_to(start_node)
        edge.set_end_point(end_point)
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
        for tree in node.trees:
            tree.deleted_nodes.add(node)

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
        # -- trees --
        old_trees = set(node.trees)
        for tree in old_trees:
            if tree.top is node:
                tree.remove_node(node, recursive_down=False)
            else:
                tree.update_items()
        if node.parentItem():
            node.setParentItem(None)
        if hasattr(node, 'on_delete'):
            node.on_delete()
        # -- scene --
        self.f.remove_from_scene(node)
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
        # -- make sure that edge is not accidentally restored while fading away
        edge.start = None
        edge.end = None
        # -- scene --
        self.f.remove_from_scene(edge)
        # -- Order update for trees
        self.f.tree_manager.reserve_update_for_trees()
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
    def connect_node(self, parent=None, child=None, direction='', edge_type=None,
                     fade_in=False):
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
                                    fade=fade_in)
        child.poke('edges_up')
        parent.poke('edges_down')
        if direction == g.LEFT:
            child.edges_up.insert(0, new_edge)
            parent.edges_down.insert(0, new_edge)
        else:
            child.edges_up.append(new_edge)
            parent.edges_down.append(new_edge)
        if hasattr(child, 'on_connect'):
            child.on_connect(parent)
        return new_edge

    def partial_disconnect(self, edge, start=True, end=True):
        print('partial disconnect called, start: %s, end: %s' % (start, end))
        if start and edge.start:
            edge.start.poke('edges_down')
            edge.start.edges_down.remove(edge)
            bx, by = edge.start.bottom_center_magnet()
            edge.start = None
            edge.set_start_point(bx, by + 10)
        if end and edge.end:
            edge.end.poke('edges_up')
            bx, by = edge.end.top_center_magnet()
            edge.end.edges_up.remove(edge)
            edge.end = None
            edge.set_end_point(bx, by - 10)
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
            new_node.update_visibility(fade_in=True)  # active=True,

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
        if not isinstance(node, ConstituentNode):
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
                # if right.is_placeholder():
                # self.delete_node(right)
                # if left.is_placeholder():
                # self.delete_node(left)
        for tree in list(trees):
            tree.update_items()

    def unary_add_child_for_constituentnode(self, old_node: ConstituentNode, add_left=True):
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

    def add_sibling_for_constituentnode(self, old_node: ConstituentNode, add_left=True):
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
        parent_info = [(e.start, e.direction(), e.start.heads) for e in
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
        merger_node.heads = [old_node]
        for op, align, head_nodes in parent_info:
            if old_node in head_nodes:
                op.heads = list(head_nodes)  # fixme: not sure if we treat multiple heads right
                # here

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
                    new.index = self.f.chain_manager.next_free_index()
                # replace either the moving node or leftover node with trace
                # if we are using traces
                if self.f.chain_manager.traces_are_visible():
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

        if self.f.chain_manager.traces_are_visible():
            self.f.chain_manager.rebuild_chains()

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
                    inserted.index = self.f.chain_manager.next_free_index()
                # replace either the moving node or leftover node with trace
                # if we are using traces
                if self.f.chain_manager.traces_are_visible():
                    if moving_was_higher:
                        inserted = self.create_trace_for(inserted)
                    else:
                        t = self.create_trace_for(inserted)
                        self.replace_node(inserted, t, can_delete=False)

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
        if heads:
            if child in heads:
                merger_node.set_heads(heads)
                heads.remove(child)
                heads.append(merger_node)
                parent.set_heads(heads)

        # chains
        if self.f.chain_manager.traces_are_visible():
            self.f.chain_manager.rebuild_chains()

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
        merger_node = self.create_node(relative=right)
        merger_node.current_position = pos
        self.connect_node(parent=merger_node, child=left, direction=g.LEFT, fade_in=new is left)
        self.connect_node(parent=merger_node, child=right, direction=g.RIGHT, fade_in=new is right)
        merger_node.set_heads(head)
        return merger_node

    # ### Triangles ##############################################

    def add_triangle_to(self, node):
        """

        :param node:
        """
        node.triangle = True
        fold_scope = self.f.list_nodes_once(node)
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
        fold_scope = (f for f in self.f.list_nodes_once(node) if f.folding_towards is node)
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
        for i in range(1,8):
            if 'accent%s' % i not in color_keys:
                return 'accent%s' % i



