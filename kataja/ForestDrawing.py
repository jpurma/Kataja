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
import random
import string

from PyQt6 import QtCore

import kataja.globals as g
from kataja.errors import ForestError
from kataja.saved.Edge import Edge
from kataja.saved.Group import Group
from kataja.saved.movables.Arrow import Arrow
from kataja.saved.movables.Image import Image
from kataja.saved.movables.Node import Node
from kataja.singletons import ctrl, classes, log


class ForestDrawing:
    """ This is a class purely for legibility and code organisation. This operates on Forest data
    and each instance is inside a Forest-instance. ForestDrawing contains all graph-building
    operations related to Forest. It manipulates Nodes and Edges and mostly ignores syntactic
    objects, assuming that corresponding syntactic relations are already created.
     """

    def __init__(self, forest):
        """ attach free drawing to specific forest. FreeDrawing can have non-permanent instance
        data, e.g. caches or helper dicts, but nothing here is saved.
        """
        self.forest = forest
        self._marked_for_deletion = set()
        self.label_rotator = 0

    @property
    def nodes(self):
        return self.forest.nodes

    @property
    def edges(self):
        return self.forest.edges

    @property
    def groups(self):
        return self.forest.groups

    def poke(self, attribute):
        self.forest.poke(attribute)

    @staticmethod
    def copy_node_position(source, target):
        """ Helper method for newly created items. Takes other item and copies movement related
        attributes from it (physics settings, locks, adjustment etc).
        """
        parent = target.parentItem()
        if parent is source.parentItem():
            target.current_position = source.current_position[0], source.current_position[1]
            target.target_position = source.target_position
        else:
            csp = source.current_scene_position
            nsp = QtCore.QPointF(csp[0], csp[1])
            if parent:
                nsp = parent.mapFromScene(nsp)
            else:
                nsp = target.mapFromScene(nsp)
            target.current_position = nsp.x(), nsp.y()
            target.target_position = nsp.x(), nsp.y()
        target.locked = source.locked
        target.use_adjustment = source.use_adjustment
        target.adjustment = source.adjustment
        target.physics_x = source.physics_x
        target.physics_y = source.physics_y

    # #### Comments #########################################

    def add_comment(self, comment):
        """ Add comment item to forest
        :param comment: comment item
        """
        self.forest.comments.append(comment)

    def remove_comment(self, comment):
        """ Remove comment item from forest
        :param comment: comment item
        :return:
        """
        if comment in self.forest.comments:
            self.forest.comments.remove(comment)

    def next_free_label(self):
        self.label_rotator += 1
        if self.label_rotator == len(string.ascii_uppercase):
            self.label_rotator = 0
        return string.ascii_uppercase[self.label_rotator]

    # ### Primitive creation of forest objects ################################

    def create_node(self, label='', relative=None, pos=None, node_type=1, synobj=None, **kw):
        """ This is generic method for creating all of the Node subtypes.
        Keep it generic!
        :param label: label text for node, behaviour depends on node type, usually main text content
        :param relative: node will be relative to given node, pos will be interpreted relative to
        given node and new node will have the same trees as a parent.
        :param pos:
        :param node_type:
        :param synobj:
        :return:
        """
        node_class = classes.nodes.get(node_type)
        node = node_class(label=label, forest=self.forest, **kw)
        if synobj:
            node.set_syntactic_object(synobj)
        node.after_init()
        # resetting node by visualization is equal to initializing node for
        # visualization. e.g. if nodes are locked to position in this vis,
        # then lock this node.
        if self.forest.visualization:
            self.forest.visualization.reset_node(node)
        # it should however inherit settings from relative, if such are given
        if relative:
            self.copy_node_position(source=relative, target=node)
        if pos:
            node.set_original_position(pos)
            # node.update_position(pos)
        self.forest.add_to_scene(node)
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
            gn.lock_to_node(host)

        gn.update_label()
        return gn

    def create_comment_node(self, text=None, host=None, pixmap_path=None):
        cn = self.create_node(label=text, relative=host, node_type=g.COMMENT_NODE)
        if host:
            self.connect_node(host, child=cn)
        if pixmap_path:
            cn.set_image_path(pixmap_path)
        return cn

    def create_edge(self, start=None, end=None, edge_type='', fade=False, origin=None):
        rel = Edge(self.forest, start=start, end=end, edge_type=edge_type, origin=origin)
        rel.after_init()
        self.forest.store(rel)
        self.forest.add_to_scene(rel)
        if fade and self.forest.in_display and start.is_visible() and end.is_visible():
            rel.fade_in()
        return rel

    # not used
    def create_image(self, image_path):
        im = Image(image_path)
        self.forest.others[im.uid] = im
        self.forest.add_to_scene(im)
        return im

    def create_trace_for(self, node):
        index = node.index
        if not index:
            index = self.forest.chain_manager.next_free_index()
            node.index = index
        trace = self.create_node(label='t', relative=node)
        trace.is_trace = True
        trace.index = index
        trace.update_label()
        return trace

    def create_arrow(self, p1, p2, text=None, fade=True):
        """ Create an arrow (Edge) using the default arrow style

        :param p1: start point
        :param p2: end point
        :param text: explanatory text associated with the arrow
        :param fade: fade in or appear instantly
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
        self.forest.store(arrow)
        self.forest.add_to_scene(arrow)
        if fade and self.forest.in_display:
            arrow.fade_in()
        ctrl.select(arrow)
        return arrow

    def create_node_from_text(self, text):
        node = self.create_comment_node(text)
        return node

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
        for group in list(self.groups.values()):
            if node in group:
                group.remove_node(node)

        # -- dictionaries --
        if node.uid in self.nodes:
            self.poke('nodes')
            del self.nodes[node.uid]
        if node.syntactic_object:
            if node.syntactic_object.uid in self.forest.nodes_from_synobs:
                del self.forest.nodes_from_synobs[node.syntactic_object.uid]

        assert (node.uid not in self.forest.nodes)

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
        self.forest.remove_from_scene(node, fade_out=fade)
        # -- undo stack --
        node.announce_deletion()
        # -- remove from selection
        ctrl.remove_from_selection(node)
        # -- remove circularity block
        self._marked_for_deletion.remove(node)

    def delete_edge(self, edge, touch_nodes=True, fade=True):
        """ remove from scene and remove references from nodes
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
        # -- scene --
        self.forest.remove_from_scene(edge, fade_out=fade)
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
        assert new_start.uid in self.nodes
        if edge.start:
            edge.start.poke('edges_down')
            edge.start.edges_down.remove(edge)
        edge.connect_end_points(new_start, edge.end)
        new_start.poke('edges_down')
        new_start.edges_down.append(edge)

    def set_edge_end(self, edge, new_end):
        assert new_end.uid in self.nodes
        if edge.end:
            edge.end.poke('edges_up')
            edge.end.edges_up.remove(edge)
        edge.connect_end_points(edge.start, new_end)
        new_end.poke('edges_up')
        new_end.edges_up.append(edge)

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
                     origin=None):
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
        :param origin:
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
                        and old_edge.origin == origin:
                    # raise ForestError('Identical edge exists already')
                    log.info('Identical edge exists already')
                    return
                elif old_edge.start == child and old_edge.end == parent:
                    raise ForestError('Connection is circular')

        # Create edge and make connections
        new_edge = self.create_edge(start=parent, end=child, edge_type=edge_type, fade=fade_in,
                                    origin=origin)

        for edge_up in parent.edges_up:
            if edge_up.has_similar_origin(new_edge):
                edge_up.end_links_to = new_edge
                new_edge.start_links_to = edge_up

        for edge_down in child.edges_down:
            if edge_down.has_similar_origin(new_edge):
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
            self.copy_node_position(source=old_node, target=new_node)
        new_node.update_visibility(fade_in=ctrl.play)  # active=True,

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

    # ######## Groups ################################

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
        self.forest.add_to_scene(group)
        self.poke('groups')
        self.groups[group.uid] = group
        return group

    def remove_group(self, group):
        self.forest.remove_from_scene(group)
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

    def definitions_to_nodes(self, defstring):

        leaves = {}
        for node in self.forest.nodes.values():
            if node.is_leaf():
                leaves[self.forest.parser.get_root_word(node.label)] = node
        for line in defstring.splitlines():
            if '::' not in line:
                continue
            key, value = line.split('::', 1)
            key = key.strip()
            if not key in leaves:
                print('missing key ', key)
                continue
            parts = [x.strip() for x in value.split(',')]
            node = leaves[key]
            for part in parts:
                if (part.startswith("'") and part.endswith("'")) or (
                        part.startswith('"') and part.endswith('"')):
                    # gloss node
                    label = part[1:-1]
                    self.create_gloss_node(label=label, host=node)
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
                    self.create_feature_node(label=fparts[0], value=value, family=family,
                                             host=node)
