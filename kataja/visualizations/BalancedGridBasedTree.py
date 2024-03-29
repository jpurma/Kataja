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

import kataja.globals as g
from kataja.Grid import Grid
from kataja.saved.Movable import Movable
from kataja.singletons import prefs
from kataja.visualizations.BalancedTree import BalancedTree


class BalancedGridBasedTree(BalancedTree):
    """

    """
    name = 'Balanced grid-based tree'
    banned_cn_shapes = (g.BRACKETED, g.SCOPEBOX)
    use_rotation = False

    def draw_tree(self, tree_top):
        """ Divide and conquer algorithm using a grid. Result is much like latex qtree. 
        
        Grid L + Grid R -> rightmost free of L, leftmost node of R,  sum     max of sums=4 + padding=1 = 5
        .L.L..   .R.R..      +4                 - 1                    =3 
        .L....   R.R...      +2                 - 0                    =2
        ..L..L   ..R.R.      +6                 - 2                    =4
        .L....               +2                                      

        so Grid R starts from coords (5,0)
        .L.L..R.R..
        .L...R.R...
        ..L..L.R.R.
        .L.........                
        
        """
        only_similar = True
        edge_height = prefs.edge_height
        edge_width = prefs.edge_width / 2

        def _get_grid_size(mnode):
            br = mnode.future_children_bounding_rect(limit_height=False)
            node_width = br.width()
            node_height = br.height()
            node_offset_y = br.y()
            node_top_row = mnode.get_top_y()
            relative_start_height = (node_offset_y + node_top_row) / node_height
            eh = edge_height or 1
            height_in_rows = math.ceil(node_height / eh) or 1
            start_height = max(int(relative_start_height * height_in_rows), 0)
            width_in_columns = math.ceil(node_width / float(edge_width or 1)) + 1
            left_adjust = int(width_in_columns / -2)
            return left_adjust, -start_height, width_in_columns, height_in_rows

        def _build_grid(node, parent, done: set):
            last_drawn_child = None
            if node not in done and self.forest.should_we_draw(node, parent):
                done.add(node)
                if node.locked_to_node:
                    return Grid()
                nleft, ntop, nw, nh = _get_grid_size(node)
                grids = []
                if not node.is_triangle_host():
                    if only_similar:
                        children = node.get_children(visible=True)
                    else:
                        children = node.get_all_children(visible=True)
                    last_drawn_child = None
                    for child in children:
                        grid = _build_grid(child, node, done)
                        if grid:
                            grids.append(grid)
                            last_drawn_child = child
                # Recursion base case
                if not grids:
                    g = Grid()
                    x = 0
                    need_rows = 0
                elif len(grids) == 1:
                    g = grids[0]
                    cleft, ctop, cw, ch = _get_grid_size(last_drawn_child)
                    cx, cy = g.find_in_grid(last_drawn_child)
                    if cw >= nw:
                        x = cx
                    else:
                        x = cx - ((nw - cw) // 2)
                        if x < 0:
                            g.insert_columns(-x)
                            nleft -= x
                            x = 0
                    g.insert_row()
                    need_rows = nh + ntop
                else:
                    g = grids[0]
                    for right_grid in grids[1:]:
                        g.merge_grids(right_grid)
                    sx = 0
                    size = 0
                    nleft, ntop, nw, nh = _get_grid_size(node)
                    if not node.is_triangle_host():
                        if only_similar:
                            children = node.get_children(visible=True)
                        else:
                            children = node.get_all_children(visible=True)
                        for child in children:
                            size += 1
                            nx, ny = g.find_in_grid(child)
                            sx += nx
                    if size:
                        x = sx // size
                    else:
                        x = 0
                    g.insert_row()
                    need_rows = nh + ntop
                while need_rows:
                    g.insert_row()
                    need_rows -= 1
                g.set(x, 0, node, w=nw, h=nh, left=nleft, top=ntop)
                return g
            else:
                return Grid()

        merged_grid = _build_grid(tree_top, None, self.done_nodes)

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
                    node.move_to(width_now, height_now, valign=g.TOP, align=g.CENTER_ALIGN)
                width_now += edge_width
