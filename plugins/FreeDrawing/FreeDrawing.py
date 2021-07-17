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
from kataja.ForestDrawing import ForestDrawing
from kataja.errors import ForestError
from kataja.parser.INodes import as_text, extract_triangle
from kataja.saved.movables.Node import Node
from kataja.singletons import log, prefs


class FreeDrawing(ForestDrawing):
    """ These are additional drawing operations attached to forest """

    # ########### Complex node operations ##############################

    def delete_unnecessary_merger(self, node):
        if node.node_type != g.CONSTITUENT_NODE:
            raise ForestError("Trying to treat wrong kind of node as ConstituentNode and "
                              "forcing it to binary merge")

        i = node.index or ''
        children = list(node.get_children())
        for child in list(children):
            parents = node.get_parents()
            bad_parents = []
            good_parents = []
            for parent in list(parents):
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

    def unary_add_child_for_constituentnode(self, new_node, old_node, add_left=True):
        """
        :param new_node:
        :param old_node:
        :param add_left:
        :return:
        """
        children = old_node.get_children()

        if len(children) != 1:
            return
        child = children[0]
        old_edge = old_node.get_edge_to(child)
        if add_left:
            self.connect_node(parent=old_node, child=new_node, direction=g.LEFT, fade_in=True)
        else:
            self.connect_node(parent=old_node, child=new_node, direction=g.RIGHT, fade_in=True)

    def add_sibling_for_constituentnode(self, new_node, old_node, add_left=True):
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
        if merge_to_left:
            left = new
            right = top
        else:
            left = top
            right = new
        self.create_merger_node(left=left, right=right, new=new, heads=top.heads)

    def create_node_from_text(self, text):
        node = self.create_node(text, node_type=g.CONSTITUENT_NODE)
        return node

    def insert_node_between(self, inserted, parent, child, merge_to_left, insertion_pos):
        """ This is an insertion action into a trees: a new merge is created
        and inserted between two existing constituents. One connection is
        removed, but three are created.
        This happens when touch area in edge going up from node N is clicked,
        or if a node is dragged there.
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
        pos = (lx + rx) / 2, (ly + ry) / 2 - prefs.edge_height

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


def figure_out_syntactic_label(cn):
    if cn.triangle_stack:
        # as_text -function puts triangle symbol before triangle content, [1:] removes it.
        return as_text(extract_triangle(cn.label), omit_index=True)[1:]
    l = as_text(cn.label, omit_index=True)
    if l:
        return l.splitlines()[0]
    else:
        return ''

