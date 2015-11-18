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
import math

class LinearizedStaticTree(BalancedTree):
    """

    """
    name = 'Linearized static trees'

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
        edge_height = prefs.edge_height
        edge_width = prefs.edge_width / 2
        merged_grid = Grid()

        new_rotation, self.traces_to_draw = self._compute_traces_to_draw(
            self.get_vis_data('rotation'))
        self.set_vis_data('rotation', new_rotation)

        def _get_grid_size(mnode):
            node_width = mnode.width
            node_height = mnode.height
            node_top_row = mnode.get_top_row_y()
            relative_start_height = (node_height / 2.0 - node_top_row) / node_height
            height_in_rows = math.ceil(node_height / float(edge_height))
            start_height = int(relative_start_height * height_in_rows)
            width_in_columns = math.ceil(node_width / float(edge_width))
            left_adjust = int(width_in_columns / -2)
            return left_adjust, -start_height, width_in_columns, height_in_rows

        def _build_grid(node, parent=None):
            if self.should_we_draw(node, parent):
                grids = []
                children = node.get_visible_children()
                for child in children:
                    grids.append(_build_grid(child, parent=node))
                # Recursion base case
                if not grids:
                    g = Grid()
                    gleft, gtop, gwidth, gheight = _get_grid_size(node)
                    g.set(0, 0, node, w=gwidth, h=gheight, left=gleft, top=gtop)
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
            nleft, ntop, nw, nh = _get_grid_size(node)
            grid.insert_row()
            #grid.insert_row()
            need_rows = nh + ntop
            while need_rows:
                grid.insert_row()
                need_rows -= 1
            grid.set(x, 0, node, w=nw, h=nh, left=nleft, top=ntop)
            # this doesn't work because of potential xy_adjustment in grid
            #for child in children:
            #    nx, ny = grid.find_in_grid(child)
            #    path = grid.pixelated_path(x, 0, nx, ny)
            #    grid.fill_path(path)
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
        for y, row in enumerate(merged_grid):
            height_now += edge_height
            edge_height -= height_reduction
            width_now = offset_x
            for x, node in enumerate(row):
                if node and isinstance(node, Movable):
                    node.release()
                    node.move_to(width_now, height_now, 0, valign=g.TOP_ROW)
                width_now += edge_width
