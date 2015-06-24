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
from _collections_abc import Iterable

from kataja.Movable import Movable
from kataja.singletons import prefs
from kataja.visualizations.Grid import Grid
from kataja.visualizations.BalancedTree import BalancedTree
from kataja.BaseConstituentNode import BaseConstituentNode
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode
import kataja.globals as g


class LinearizedStaticTree(BalancedTree):
    """

    """
    name = 'Linearized static tree'

    def __init__(self):
        BalancedTree.__init__(self)
        self.forest = []
        self._directed = True
        self.grid_lines_y = {}
        self.grid_lines_x = {}
        self.traces_to_draw = None

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
            self.set_vis_data('rotation', 0)
            for node in self.forest.visible_nodes():
                self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        node.fixed_position = None
        node.adjustment = None
        node.update_label()
        node.update_visibility()
        if isinstance(node, BaseConstituentNode):
            node.dyn_x = False
            node.dyn_y = False
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.dyn_x = True
            node.dyn_y = True

    def reselect(self):
        """ Rotate between drawing multidominated elements close to their various parents
        """
        self.set_vis_data('rotation', self.get_vis_data('rotation') - 1)

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
        merged_grid = Grid()

        new_rotation, self.traces_to_draw = self._compute_traces_to_draw(
            self.get_vis_data('rotation'))
        self.set_vis_data('rotation', new_rotation)

        def _get_gride_size(mnode):
            node_width = mnode.width
            node_height = mnode.height
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
                grids = []
                children = node.get_children()
                for child in children:
                    grids.append(_build_grid(child, parent=node))
                # Recursion base case
                if not grids:
                    g = Grid()
                    grid_width, grid_height = _get_gride_size(node)
                    g.set(0, 0, node, grid_width, grid_height)
                    return g
                elif len(grids) == 1:
                    # hmmmm
                    print('case of 1 grid')
                    _add_merger_node(grids[0], node)
                    return grids[0]
                else:
                    while len(grids) > 1:
                        right_grid = grids.pop(-1)
                        left_grid = grids.pop(-1)
                        merged = _merge_grids(left_grid, right_grid)
                        _add_merger_node(merged, node)
                        grids.append(merged)
                    return grids[0]
            else:
                return Grid()

        def _add_merger_node(grid, node):
            sx = 0
            children = node.get_children()
            size = 0
            for child in children:
                size += 1
                nx, ny = grid.find_in_grid(child)
                sx += nx
            x = sx // size
            grid.insert_row()
            grid.insert_row()
            grid.insert_row()
            nw, nh = _get_gride_size(node)
            grid.set(x, 0, node, nw, nh)
            return grid

        def _merge_grids(left_grid=None, right_grid=None, extra_padding=0):
            paddings = []
            # actual merging of grids begins with calculating the closest fit for two grids
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
            return left_grid

        for root_node in self.forest:
            new_grid = _build_grid(node=root_node)
            merged_grid = _merge_grids(left_grid=merged_grid, right_grid=new_grid, extra_padding=2)

        tree_width = merged_grid.width * edge_width
        tree_height = merged_grid.height * edge_height
        offset_x = tree_width / -2
        offset_y = tree_height / -2
        height_reduction = (edge_height / 3.0) / (merged_grid.height or 1)
        height_now = offset_y

        # Actual drawing: set nodes to their places in scene
        merged_grid.ascii_dump()

        for y, row in enumerate(merged_grid):
            height_now += edge_height
            edge_height -= height_reduction
            width_now = offset_x
            for x, node in enumerate(row):
                if node and isinstance(node, Movable):
                    node.release()
                    node.algo_position = (width_now, height_now, 0)
                width_now += edge_width

        # draw_grid_lines = True
        # if draw_grid_lines:
        #     height_now = offset_y
        #     for y, row in enumerate(merged_grid):
        #         if y in self.grid_lines_y:
        #             self.grid_lines_y[y].setLine(offset_x, height_now, offset_x + tree_width, height_now)
        #         else:
        #             self.grid_lines_y[y] = self.forest.scene.addLine(offset_x, height_now, offset_x + tree_width,
        #                                                              height_now)
        #         height_now += edge_height
        #         edge_height -= height_reduction
        #     max_height = height_now
        #     width_now = offset_x
        #     for x, column in enumerate(merged_grid.row(0)):
        #         if x in self.grid_lines_x:
        #             self.grid_lines_x[x].setLine(width_now, offset_y, width_now, max_height)
        #         else:
        #             self.grid_lines_x[x] = self.forest.scene.addLine(width_now, offset_y, width_now, max_height)
        #         width_now += edge_width
