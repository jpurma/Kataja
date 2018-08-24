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

from PyQt5 import QtCore
import kataja.globals as g
from kataja.singletons import prefs, ctrl
from kataja.visualizations.BalancedTree import BalancedTree

squeeze = True

class Block:
    def __init__(self, node: 'kataja.saved.Node', done=None):
        if done is None:
            done = set()
        self.node = node
        br = node.future_children_bounding_rect(limit_height=True)
        self.node_br = br
        self.left = br.left()
        self.top = br.top()
        self.width = br.width()
        self.height = br.height()
        self.x = 0
        self.y = 0
        self.child_blocks = []
        done.add(node)
        self.include_children(done)

    def __repr__(self):
        return f"Block('{self.node.label}', x={self.x}, y={self.y}, left={self.left}, top={self.top}, width={self.width}, height={self.height})"

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def first_child(self):
        return self.child_blocks[0]

    @property
    def last_child(self):
        return self.child_blocks[-1]

    @property
    def rect(self):
        return QtCore.QRectF(self.left, self.top, self.width, self.height)

    @property
    def right_edges(self):
        r = self.node_br.right()
        h = self.node_br.height()
        t = self.node_br.top()
        points = [(self.x + r, self.y + t), (self.x + r, self.y + t + h)]
        if self.child_blocks:
            return points + self.child_blocks[-1].right_edges
        return points

    @property
    def left_edges(self):
        l = self.node_br.left()
        h = self.node_br.height()
        t = self.node_br.top()
        points = [(self.x + l, self.y + t), (self.x + l, self.y + t + h)]
        if self.child_blocks:
            return points + self.child_blocks[0].left_edges
        return points

    def move(self, x, y, include_children=True):
        self.x += x
        self.y += y
        if include_children:
            for child in self.child_blocks:
                child.move(x, y)

    def trigger_move(self):
        self.node.move_to(self.x, self.y)
        for block in self.child_blocks:
            block.trigger_move()

    def include_children(self, done):
        children = self.node.get_children(similar=True, visible=True)
        width_sum = 0
        max_height = 0
        prev_sibling = None
        for child in children:
            if child in done or child.locked_to_node or not ctrl.forest.should_we_draw(child, self.node):
                continue
            child_block = Block(child, done)
            width_sum += child_block.width
            if child_block.height > max_height:
                max_height = child_block.height
            if prev_sibling:
                x = prev_sibling.x + prev_sibling.right - child_block.left
                child_block.move(x, 0)
            self.child_blocks.append(child_block)
            prev_sibling = child_block
        if not self.child_blocks:
            return

        if len(self.child_blocks) == 1:
            self.left = min((self.left, self.first_child.left))
            x_adjust = 0
        else:
            d = (self.first_child.x + self.last_child.x) / -2
            if width_sum >= self.width:
                self.left = d + self.first_child.left
                x_adjust = d
            else:
                x_adjust = d
        self.width = max((width_sum, self.width))
        for child in self.child_blocks:
            y_adjust = self.bottom + prefs.edge_height - child.top
            child.move(x_adjust, y_adjust)
        self.height += prefs.edge_height + max_height
        if squeeze and len(self.child_blocks) == 2:
            print('squeeze these: ---------------------')
            print(self.first_child.right_edges)
            print(self.last_child.left_edges)


class GridlessDivideAndConquerTree(BalancedTree):
    name = 'Gridless Balanced tree'
    banned_node_shapes = (g.BRACKETED, g.SCOPEBOX)

    def __init__(self):
        BalancedTree.__init__(self)
        self.forest = None
        self._directed = True
        self.grid_lines_y = {}
        self.grid_lines_x = {}
        self.traces_to_draw = None

    def prepare(self, forest: 'kataja.saved.Forest', reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._directed = True
        if reset:
            self.set_data('rotation', 0)
            self.reset_nodes()
        self.validate_node_shapes()

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)
        if node.node_type == g.CONSTITUENT_NODE:
            node.physics_x = False
            node.physics_y = False
        else:
            node.physics_x = True
            node.physics_y = True

    def has_free_movers(self):
        for node in self.forest.nodes.values():
            if node.isVisible() and (node.physics_x or node.physics_y):
                return True
        return True

    def reselect(self):
        """ Rotate between drawing multidominated elements close to their various parents
        """
        self.set_data('rotation', self.get_data('rotation') - 1)

    def prepare_draw(self):
        new_rotation = self.forest.compute_traces_to_draw(self.get_data('rotation'))
        self.set_data('rotation', new_rotation)

    def draw_tree(self, tree_top):
        top_block = Block(tree_top)
        top_block.trigger_move()

