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

import math
import time

import kataja.globals as g
from kataja.Grid import Grid
from kataja.saved.Movable import Movable
from kataja.singletons import prefs
from kataja.visualizations.BalancedTree import BalancedTree
from kataja.utils import time_me

class DivideAndConquerTree(BalancedTree):
    """

    """
    name = 'Balanced grid-based tree'
    banned_node_shapes = (g.BRACKETED, g.SCOPEBOX)

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

    def reselect(self):
        """ Rotate between drawing multidominated elements close to their various parents
        """
        self.set_data('rotation', self.get_data('rotation') - 1)

    def prepare_draw(self):
        new_rotation = self.forest.compute_traces_to_draw(self.get_data('rotation'))
        self.set_data('rotation', new_rotation)

    def draw_tree(self, tree):
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

        def _get_grid_size(mnode):
            br = mnode.future_children_bounding_rect()
            node_width = br.width()
            node_height = br.height()
            node_offset_y = br.y()
            node_top_row = mnode.get_top_y()
            relative_start_height = (node_offset_y + node_top_row) / node_height
            height_in_rows = math.ceil(node_height / float(edge_height or 1)) - 1#+ 1
            start_height = max(int(relative_start_height * height_in_rows), 0)
            width_in_columns = math.ceil(node_width / float(edge_width or 1)) + 1
            left_adjust = int(width_in_columns / -2)
            return left_adjust, -start_height, width_in_columns, height_in_rows

        def _build_grid(node, parent=None, done:set=None):
            if self.forest.should_we_draw(node, parent) and node not in done:
                done.add(node)
                grids = []
                children = node.get_children(similar=True, visible=True)
                for child in children:
                    grid = _build_grid(child, parent=node, done=done)
                    if grid:
                        grids.append(grid)
                # Recursion base case
                if not grids:
                    g = Grid()
                    gleft, gtop, gwidth, gheight = _get_grid_size(node)
                    g.set(0, 0, node, w=gwidth, h=gheight, left=gleft, top=gtop)
                    return g
                elif len(grids) == 1:
                    # hmmmm
                    _add_merger_node(grids[0], node)
                    return grids[0]
                else:
                    combined = grids[0]
                    for right_grid in grids[1:]:
                        combined.merge_grids(right_grid)
                    _add_merger_node(combined, node)
                    return combined
            else:
                return Grid()

        def _add_merger_node(grid, node):
            sx = 0
            size = 0
            nleft, ntop, nw, nh = _get_grid_size(node)
            children = node.get_children(similar=True, visible=True)
            if len(children) == 1:
                cleft, ctop, cw, ch = _get_grid_size(children[0])
                cx, cy = grid.find_in_grid(children[0])
                if cw >= nw:
                    x = cx
                else:
                    x = cx - ((nw - cw) // 2)
                    if x < 0:
                        grid.insert_columns(-x)
                        nleft -= x
                        x = 0
            else:
                for child in children:
                    size += 1
                    nx, ny = grid.find_in_grid(child)
                    sx += nx
                if size:
                    x = sx // size
                else:
                    x = 0
            grid.insert_row()
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

        merged_grid = _build_grid(node=tree.top, done=set())

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
                    node.move_to(width_now, height_now, 0, valign=g.TOP_ROW, align=g.CENTER_ALIGN)
                width_now += edge_width

