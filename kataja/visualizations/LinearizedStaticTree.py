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

from kataja.Movable import Movable
from kataja.singletons import prefs
from kataja.visualizations.Grid import Grid
from kataja.visualizations.BalancedTree import BalancedTree
from kataja.ConstituentNode import ConstituentNode
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode
import kataja.globals as g


class LinearizedStaticTree(BalancedTree):
    """

    """
    name = 'Linearized static tree'


    def __init__(self):
        BalancedTree.__init__(self)
        self.forest = None
        self._directed = True

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._directed = True
        if reset:
            self.forest.settings.bracket_style = g.NO_BRACKETS
            self.forest.settings.show_constituent_edges = True
            self.forest.vis_data = {'name': self.__class__.name, 'rotation': 0}
            for node in self.forest.visible_nodes():
                self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        node.locked_to_position = False
        node.reset_adjustment()
        node.update_label()
        if isinstance(node, ConstituentNode):
            node.update_visibility(show_edges=True, scope=0, brackets=self.forest.settings.bracket_style)
            node.bind_x = True
            node.bind_y = True
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.bind_x = False
            node.bind_y = False


    def reselect(self):
        """


        """
        self.forest.vis_data['rotation'] -= 1


    # @time_me
    def draw(self):
        """ Divide and conquer algorithm using a grid. Result is much like latex qtree. 
        
        Grid L + Grid R -> rightmost free of L, leftmost node of R,  sum     max of sums=4 + padding=1 = 5
        .L.L..   .R.R..      +4                 - 1                    =3 
        .L....   R.R...      +2                 - 0                    =2
        ..L..L   ..R.R.      +6                 - 2                    =4
        .L....               +2                                      
        
        .L.L..R.R..
        .L...R.R...
        ..L..L.....
        .L.....R.R.

        so Grid R starts from coords (5,0)
        .L.L..R.R..
        .L...R.R...
        ..L..L.R.R.
        .L.........                
        
        """
        print('doing LinearizedStaticTree')
        edge_height = prefs.edge_height
        edge_width = prefs.edge_width / 2
        edge_width = 10
        print(prefs.edge_width, edge_width)
        merged_grid = Grid()

        self.forest.vis_data['rotation'], self.traces_to_draw = self._compute_traces_to_draw(
            self.forest.vis_data['rotation'])


        def _get_gride_size(node):
            node_width = node.width
            node_height = node.height
            width = height = 1
            while node_width > edge_width:
                width += 2
                node_width -= edge_width
            while node_height > edge_height:
                height += 2
                node_height -= edge_height
            return width, height

        def _build_grid(node, parent=None):
            if self.should_we_draw(node, parent):
                left_grid = None
                right_grid = None
                left_child = node.left()
                if left_child:
                    left_grid = _build_grid(left_child, parent=node)
                right_child = node.right()
                if right_child:
                    right_grid = _build_grid(right_child, parent=node)

                # Recursion base case
                if not (left_child or right_child):
                    g = Grid()
                    grid_width, grid_height = _get_gride_size(node)
                    g.set(0, 0, node, grid_width, grid_height)
                    return g
                else:
                    return _merge_grids(left_grid, right_grid, node)
            else:
                return Grid()

        def _merge_grids(left_grid=None, right_grid=None, combining_node=None, extra_padding=1):
            paddings = []
            # actual merging of grids begins with calculating the closest fit for two grids

            if not (right_grid or left_grid):
                assert False

            if left_grid and right_grid:
                for row_n, right_side_row in enumerate(right_grid):
                    # measuring where the right border of the left grid should be.
                    rightmost_free = left_grid.last_filled_column(row_n) + 1
                    # measuring where the left border of the right grid should be
                    left_side_empties = right_grid.first_filled_column(row_n)
                    paddings.append(rightmost_free - left_side_empties)
                if paddings:
                    padding = max(paddings) + extra_padding
                else:
                    padding = extra_padding
                for row_n, right_row in enumerate(right_grid):
                    for col_n, right_row_node in enumerate(right_row):
                        if right_row_node:
                            left_grid.set(col_n + padding, row_n, right_row_node)
                combined_grid = left_grid
            elif left_grid:
                combined_grid = left_grid
            elif right_grid:
                combined_grid = right_grid

            if not combining_node:  # if this was about setting two finished trees besides each others, then leave now
                return combined_grid
            # drawing the merger node
            left_root = combining_node.left()
            right_root = combining_node.right()
            if right_root and not left_root:
                x, y = combined_grid.find_in_grid(right_root)
            elif left_root and not right_root:
                x, y = combined_grid.find_in_grid(left_root)
            elif left_root and right_root:
                lx, ly = combined_grid.find_in_grid(left_root)
                rx, ry = combined_grid.find_in_grid(right_root)
                x = (lx + rx) // 2

            combined_grid.insert_row()
            combined_grid.insert_row()
            nw, nh = _get_gride_size(combining_node)
            combined_grid.set(x, 0, combining_node, nw, nh)
            return combined_grid

        for root_node in self.forest:
            new_grid = _build_grid(node=root_node)
            merged_grid = _merge_grids(left_grid=merged_grid, right_grid=new_grid, extra_padding=3)

        tree_width = merged_grid._width * edge_width
        tree_height = merged_grid._height * edge_height
        offset_x = tree_width / -2
        offset_y = tree_height / -2
        height_reduction = (edge_height / 3.0) / (merged_grid._height or 1)
        height_now = offset_y

        # Actual drawing: set nodes to their places in scene
        print(merged_grid)
        merged_grid.ascii_dump()

        for y, row in enumerate(merged_grid):
            height_now += edge_height
            edge_height -= height_reduction
            for x, node in enumerate(row):
                if node and isinstance(node, Movable):
                    node.release()
                    node.computed_position = ((x * edge_width) + offset_x, height_now, 0)

