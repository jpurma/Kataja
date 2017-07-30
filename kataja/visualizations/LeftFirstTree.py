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
from kataja.singletons import prefs, ctrl
from kataja.utils import caller, time_me
import random


class LeftFirstTree(BaseVisualization):
    """ Visualization that draws branches, starting from top and left. Each
    branch takes the space it needs, and may force next branch drawing to
    further down and right. """
    name = 'Left first trees'
    banned_node_shapes = (g.BRACKETED, g.SCOPEBOX)

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._hits = {}
        self._max_hits = {}
        self._directed = True
        self._indentation = 0
        self._shuffle = False
        self.traces_to_draw = {}

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        self._indentation = 0
        self.validate_node_shapes()
        if reset:
            self.set_data('rotation', 0)
            self.reset_nodes()

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)
        if node.node_type == g.CONSTITUENT_NODE:
            node.physics_x = False
            node.physics_y = False

    @caller
    def reselect(self):
        """ if there are different modes for one visualization, rotating
        between different modes is triggered here. """
        self.set_data('rotation', self.get_data('rotation', 0) - 1)

    # Recursively put nodes to their correct position in grid
    def _put_to_grid(self, grid, node, x, y, parent=None):
        if node.locked_to_node:
            return
        elif not self.forest.should_we_draw(node, parent):
            return
        grid.set(x, y, node)

        children = [x for x in node.get_children(similar=True, visible=True)
                    if not x.locked_to_node]
        if not children:
            return
        x_shift = (len(children) // 2) * -2
        x_step = 2
        y_step = 2
        nx = x + x_shift
        ny = y + y_step
        onx = nx
        ony = ny
        if self._shuffle and len(children) > 1:
            random.shuffle(children)

        for child in children:
            blocked = True
            grandchildren = [x for x in child.get_children(similar=True, visible=True)
                             if not x.locked_to_node]
            count = 0
            while blocked and count < 10:
                # is the right node position available?
                blocked = grid.get(nx, ny)
                if not blocked:
                    # is the path to the right node position available?
                    path = grid.pixelated_path(x, y, nx, ny)
                    if nx > x:
                        path_marker = 2
                    else:
                        path_marker = 1
                    blocked = grid.is_path_blocked(path)
                    if not blocked:
                        # is there room for the left child of this node
                        if grandchildren:
                            if len(grandchildren) == 1:
                                child_pos_x, child_pos_y = nx, \
                                                           ny + y_step  #
                                                           #  middle
                            else:
                                child_pos_x, child_pos_y = nx - x_step, \
                                                           ny + y_step  #
                                                           #  reach left
                            blocked = grid.get(child_pos_x, child_pos_y)
                            if not blocked:
                                cpath = grid.pixelated_path(nx, ny,
                                                            child_pos_x,
                                                            child_pos_y)
                                blocked = grid.is_path_blocked(cpath)
                if blocked:
                    nx += x_step
                    ny += y_step
                count += 1
            if count == 10:
                print('******** too deep tree drawing *********')
                path = grid.pixelated_path(x, y, onx, ony)
                if nx > x:
                    path_marker = 2
                else:
                    path_marker = 1
            grid.fill_path(path, path_marker)
            self._put_to_grid(grid, child, nx, ny, parent=node)
            if len(children) > 2:
                nx += x_step
            elif len(children) == 2:
                nx += x_step * 2

    def prepare_draw(self):
        new_rotation = self.forest.compute_traces_to_draw(self.get_data('rotation'))
        self.set_data('rotation', new_rotation)

    def draw_tree(self, tree_top):
        """ Draws the trees to a table or a grid, much like latex qtree and
        then scales the grid to the scene. """
        edge_height = prefs.edge_height
        edge_width = prefs.edge_width
        merged_grid = Grid()
        self._indentation = 0
        self._shuffle = ctrl.settings.get('linearization_mode') == g.RANDOM_NO_LINEARIZATION
        if tree_top and tree_top.node_type == g.CONSTITUENT_NODE:
            self._put_to_grid(merged_grid, tree_top, 0, 0)
        offset_x = 0  # tree_w/-2
        y = 0
        # Actual drawing: set nodes to their places in scene
        extra_widths = [0] * merged_grid.width
        extra_heights = []
        #merged_grid.ascii_dump()
        # if node is extra wide, then move all columns to right from that point on
        # same for extra tall nodes. move everything down after that row
        for y_i, row in enumerate(merged_grid):
            extra_height = 0
            prev_width = 0
            prev_height = 0
            prev_x = 0

            x = offset_x
            for x_i, node in enumerate(row):
                if node and getattr(node, 'node_type', '') == g.CONSTITUENT_NODE:
                    cbr = node.future_children_bounding_rect(limit_height=True)
                    height_spillover = cbr.bottom() - edge_height
                    if height_spillover > extra_height:
                        if edge_height:
                            extra_height = math.ceil(
                                height_spillover / float(edge_height)) * edge_height
                        else:
                            extra_height = math.ceil(height_spillover)
                    width_spillover = ((cbr.width() + prev_width) / 2) - (edge_width * 2)
                    if width_spillover > extra_widths[x_i]:
                        if edge_width:
                            extra_widths[x_i] = math.ceil(
                                width_spillover / float(edge_width)) * edge_width
                        else:
                            extra_widths[x_i] = math.ceil(width_spillover)
                    # fix cases where bottom half of tall node is overlapped by edges from smaller
                    # node beside it.
                    if prev_height > cbr.height():
                        if x_i >= 1 and y_i < merged_grid.height - 2:
                            edge = merged_grid.get(x_i - 1, y_i + 1, raw=True)
                            left_neighbor = merged_grid.get(x_i - 2, y_i, raw=True)
                            # The problem happens with this kind of constellation:
                            #  ..././.
                            #  ..A.B..
                            #  .../.\. <--- the left edge here can be obstructed by A
                            if left_neighbor and edge and isinstance(edge, int):
                                edge_box_left_x = x - cbr.width() / 3 - edge_width
                                prev_box_right_x = prev_x + (prev_width / 2)
                                width_overlap = prev_box_right_x - edge_box_left_x
                                height_overlap = prev_height - cbr.height()
                                if extra_widths[x_i] < width_overlap:
                                    extra_widths[x_i] = width_overlap
                                if extra_height < height_overlap:
                                    extra_height = height_overlap
                    x += extra_widths[x_i]
                    prev_width = cbr.width()
                    prev_height = cbr.height()
                    prev_x = x
                else:
                    x += extra_widths[x_i]
                x += edge_width
            y += edge_height + extra_height
            extra_heights.append(extra_height)
        y = 0
        for y_i, row in enumerate(merged_grid):
            x = offset_x
            for x_i, node in enumerate(row):
                x += extra_widths[x_i]
                if node and getattr(node, 'node_type', '') == g.CONSTITUENT_NODE:
                    node.move_to(x, y, valign=g.TOP_ROW, align=g.CENTER_ALIGN)
                x += edge_width
            y += edge_height + extra_heights[y_i]
