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
        super().reset_node(node)
        if node.node_type == g.CONSTITUENT_NODE:
            node.physics_x = False
            node.physics_y = False
            node.physics_z = False

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

        def _get_grid_size(mnode):
            node_width = mnode.width
            node_height = mnode.height
            width = height = 1
            while node_width > edge_width:
                width += 2
                node_width -= 2 * edge_width
            while node_height > edge_height:
                height += 1
                node_height -= edge_height
            return width, height

        def _build_grid(node, parent=None):
            if self.should_we_draw(node, parent):
                grids = []
                children = node.get_visible_children()
                for child in children:
                    grids.append(_build_grid(child, parent=node))
                # Recursion base case
                if not grids:
                    g = Grid()
                    grid_width, grid_height = _get_grid_size(node)
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
                        left_grid.merge_grids(right_grid)
                        _add_merger_node(left_grid, node)
                        grids.append(left_grid)
                    return grids[0]
            else:
                return Grid()

        def _add_merger_node(grid, node):
            sx = 0
            size = 0
            children = list(node.get_visible_children())
            for child in children:
                size += 1
                nx, ny = grid.find_in_grid(child)
                sx += nx
            x = sx // size
            grid.insert_row()
            grid.insert_row()
            nw, nh = _get_grid_size(node)
            grid.set(x, 0, node, nw, nh)
            for child in children:
                nx, ny = grid.find_in_grid(child)
                path = grid.pixelated_path(x, 0, nx, ny)
                grid.fill_path(path)
            return grid


        for tree in self.forest:
            new_grid = _build_grid(node=tree.top)
            merged_grid.merge_grids(new_grid, extra_padding=2)

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
                    node.move_to(width_now, height_now, 0)
                width_now += edge_width
