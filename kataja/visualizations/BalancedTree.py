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
from kataja.Visualization import BaseVisualization
from kataja.singletons import prefs


class BalancedTree(BaseVisualization):
    """

    """
    name = 'Balanced trees'
    banned_cn_shapes = (g.BRACKETED,)
    use_rotation = False

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
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

    # @time_me
    def draw_tree(self, tree_top):
        """ Divide and conquer, starting from bottom right. Results in a horizontal
        linearisation of leaves."""

        def recursive_position(node, x, y, largest_x):
            if node in self.done_nodes:
                return x, y, largest_x
            self.done_nodes.add(node)
            if node.locked_to_node:
                return x, y, largest_x
            children = list(reversed(node.get_children(visible=True, of_type=g.CONSTITUENT_NODE)))
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

    def normalise_to_origo(self, tree_top, shift_x=0, shift_y=0):
        pass