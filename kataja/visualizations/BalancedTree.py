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
from PyQt5 import QtCore, QtWidgets

import kataja.globals as g
from kataja.Visualization import BaseVisualization
from kataja.singletons import ctrl, prefs


class BalancedTree(BaseVisualization):
    """

    """
    name = 'Balanced trees'
    banned_cn_shapes = (g.BRACKETED,)
    use_rotation = True

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._directed = True
        self._linear = []

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._directed = True
        if reset:
            self.set_data('rotation', 0)
            self.reset_nodes()
        self.validate_cn_shapes()

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

    def estimate_overlap_and_shift_tree(self, left_trees, right_tree):
        max_right = 0
        left_nodes = set()
        for left_tree in left_trees:
            for node in left_tree.get_sorted_nodes():
                if node.locked_to_node:
                    continue
                elif node.physics_x and node.physics_y:
                    continue
                elif not node.isVisible():
                    continue
                left_nodes.add(node)
                br = node.boundingRect()
                tx, ty = node.target_position
                right = br.x() + br.width() + tx
                if right > max_right:
                    max_right = right

        min_left = 1000
        nodes_to_move = []
        for node in right_tree.get_sorted_nodes():
            if node.locked_to_node:
                continue
            elif node.physics_x and node.physics_y:
                continue
            elif node in left_nodes:
                continue
            br = node.boundingRect()
            tx, ty = node.target_position
            left = br.x() + tx
            if left < min_left:
                min_left = left
            nodes_to_move.append(node)

        dist = (max_right - min_left) + 30
        for node in nodes_to_move:
            node.target_position = node.target_position[0] + dist, node.target_position[1]
            node.start_moving()


    # @time_me
    def draw_tree(self, tree_top):
        """ Divide and conquer, starting from bottom right. Results in a horizontal
        linearisation of leaves."""

        def recursive_position(node, x, y, largest_x):
            if node.locked_to_node:
                return x, y, largest_x
            children = node.get_children(visible=True, similar=True, reverse=True)
            if children and not node.is_triangle_host():
                smallest_y = y
                largest_x = x
                for child in children:
                    if self.forest.should_we_draw(child, node):
                        x, new_y, largest_x = recursive_position(child, x, y, largest_x)
                        if new_y < smallest_y:
                            smallest_y = new_y
                        x -= 8
                y = smallest_y
                my_rect = node.future_children_bounding_rect()
                y -= my_rect.bottom()
                y -= prefs.edge_height
                new_x = (largest_x + x) / 2
                node.move_to(new_x, y, valign=g.BOTTOM)
                return x, y + my_rect.top(), largest_x
            else:
                leaf_rect = node.future_children_bounding_rect(limit_height=False)
                x -= leaf_rect.right()
                node.move_to(x, y, valign=g.BOTTOM)
                return x + leaf_rect.left(), y + leaf_rect.top(), largest_x

        recursive_position(tree_top, 0, 0, 0)

