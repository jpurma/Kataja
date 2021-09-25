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
from kataja.Visualization import BaseVisualization
from kataja.saved.Movable import Movable
from kataja.singletons import prefs


def left_bottom_is_bottom_center(i):
    """ Map left bottom magnet to bottom center
    :param i:
    :return:
    """
    if i == 8:
        return 9
    else:
        return i


def right_bottom_is_bottom_center(i):
    """ Map right bottom magnet to bottom center
    :param i:
    :return:
    """
    if i == 10:
        return 9
    else:
        return i


class HeadDownTree(BaseVisualization):
    """

    """
    name = 'Head down trees'
    banned_cn_shapes = (g.BRACKETED,)
    use_rotation = False

    def __init__(self):
        BaseVisualization.__init__(self)
        self.trees_width = 0

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self.trees_width = 0
        if reset:
            self.set_data('rotation', 0)
            self.reset_nodes()
        self.validate_cn_shapes()

    def prepare_draw(self):
        super().prepare_draw()
        self.trees_width = 0

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
            mnode_br = mnode.future_children_bounding_rect(limit_height=True)
            node_width = mnode_br.width()
            node_height = mnode_br.height()
            node_top_row = mnode.get_top_y()
            node_offset_y = mnode_br.y()
            if node_height == 0:
                relative_start_height = 0
            else:
                relative_start_height = (node_offset_y + node_top_row) / node_height

            if edge_height == 0:
                height_in_rows = 1
            else:
                height_in_rows = math.ceil(node_height / float(edge_height))  # + 1
            start_height = max(int(relative_start_height * height_in_rows), 0)

            if edge_width == 0:
                width_in_columns = 1
            else:
                width_in_columns = math.ceil(node_width / float(edge_width))
            left_adjust = int(width_in_columns / -2)
            return left_adjust, -start_height, width_in_columns, height_in_rows

        def _build_grid(node, parent=None):
            if node.locked_to_node:
                return Grid()
            elif self.forest.should_we_draw(node, parent):
                grids = []
                if not node.is_triangle_host():
                    children = node.get_children(visible=True)
                    for child in children:
                        grid = _build_grid(child, parent=node)
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
            """ Instead of putting merger node between the children, merger node goes above the
            head node. If there is no head node, default to left node.
            :param grid:
            :param node:
            :return:
            """
            x = 0
            nleft, ntop, nw, nh = _get_grid_size(node)
            children = node.get_children(visible=True)
            heads = node.get_heads()
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
            elif heads:
                projecting_child = None
                for child in children:
                    if not hasattr(child, 'heads'):
                        continue
                    if child in heads:
                        projecting_child = child
                if not projecting_child:
                    projecting_child = children[0]
                edge = node.get_edge_to(projecting_child)
                if edge.direction() == g.LEFT:
                    node.magnet_mapper = left_bottom_is_bottom_center
                elif edge.direction() == g.RIGHT:
                    node.magnet_mapper = right_bottom_is_bottom_center
                x, ny = grid.find_in_grid(projecting_child)
            grid.insert_row()
            need_rows = nh + ntop
            while need_rows:
                grid.insert_row()
                need_rows -= 1
            grid.set(x, 0, node, w=nw, h=nh, left=nleft, top=ntop)
            # this doesn't work because of potential xy_adjustment in grid
            # for child in children:
            #    nx, ny = grid.find_in_grid(child)
            #    path = grid.pixelated_path(x, 0, nx, ny)
            #    grid.fill_path(path)
            return grid

        merged_grid = _build_grid(node=tree_top)

        tree_width = merged_grid.width * edge_width
        tree_height = merged_grid.height * edge_height
        offset_x = 0 # tree_width / -2
        offset_y = 0
        offset_x += self.trees_width
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
        self.trees_width += tree_width

    def estimate_overlap_and_shift_tree(self, right_tree_top, left_nodes):
        pass

    def normalise_to_origo(self, tree_top, shift_x=0, shift_y=0):
        pass