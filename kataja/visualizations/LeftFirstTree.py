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
from kataja.debug import vis
from kataja.singletons import prefs
from kataja.utils import caller


class LeftFirstTree(BaseVisualization):
    """ Visualization that draws branches, starting from top and left. Each
    branch takes the space it needs, and may force next branch drawing to
    further down and right. """
    name = 'Left first trees'

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._hits = {}
        self._max_hits = {}
        self._directed = True
        self._indentation = 0

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        vis('preparing LeftFirstVisualization')
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        self._indentation = 0
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

    @caller
    def reselect(self):
        """ if there are different modes for one visualization, rotating
        between different modes is triggered here. """
        self.set_vis_data('rotation', self.get_vis_data('rotation') - 1)

    # Recursively put nodes to their correct position in grid
    def _put_to_grid(self, grid, node, x, y, parent=None):
        if not self.should_we_draw(node, parent):
            return
        grid.set(x, y, node)
        children = list(node.get_visible_children())
        if not children:
            return
        x_shift = (len(children) // 2) * -2
        x_step = 2
        y_step = 2
        first = True
        nx = x + x_shift
        ny = y + y_step
        for child in children:
            if first:
                blocked = grid.get(nx, ny)
                if not blocked:
                    path = grid.pixelated_path(x, y, nx, ny)
                    blocked = grid.is_path_blocked(path)
                    if not blocked:
                        if nx > x:
                            grid.fill_path(path, 2)
                        else:
                            grid.fill_path(path, 1)
                        self._put_to_grid(grid, child, nx, ny, parent=node)
                #assert not blocked
                first = False
                if len(children) > 2:
                    nx += x_step
                else:
                    nx += x_step * 2

            else:
                blocked = True
                grandchildren = list(child.get_visible_children())
                while blocked:
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
                grid.fill_path(path, path_marker)
                self._put_to_grid(grid, child, nx, ny, parent=node)
                nx += x_step

    # @time_me
    def draw(self):
        """ Draws the trees to a table or a grid, much like latex qtree and
        then scales the grid to the scene. """
        edge_height = prefs.edge_height
        edge_width = prefs.edge_width
        merged_grid = None
        self._indentation = 0
        new_rotation, self.traces_to_draw = self._compute_traces_to_draw(
            self.get_vis_data('rotation'))
        self.set_vis_data('rotation', new_rotation)
        for tree in self.forest:
            if tree.top.node_type == g.CONSTITUENT_NODE:
                grid = Grid()
                self._put_to_grid(grid, tree.top, 0, 0)
                if merged_grid:
                    extra_padding = 3
                    merged_grid.merge_grids(grid, extra_padding=extra_padding)
                else:
                    merged_grid = grid
        offset_x = 0  # tree_w/-2
        y = 0
        if not merged_grid:
            return

        # Actual drawing: set nodes to their places in scene
        extra_widths = [0] * merged_grid.width
        extra_heights = []

        # if node is extra wide, then move all columns to right from that point on
        # same for extra tall nodes. move everything down after that row
        all_nodes = set(self.forest.get_constituent_nodes())
        for item in all_nodes:
            if item.deleted:
                print('deleted item in forest.nodes: ', item.save_key)
        for y_i, row in enumerate(merged_grid):
            extra_height = 0
            prev_width = 0
            prev_height = 0
            prev_x = 0

            x = offset_x
            for x_i, node in enumerate(row):
                if node and getattr(node, 'node_type', '') == g.CONSTITUENT_NODE:
                    if not node.inner_rect:
                        node.update_bounding_rect()
                    height_spillover = node.inner_rect.bottom() - edge_height
                    if height_spillover > extra_height:
                        if edge_height:
                            extra_height = math.ceil(height_spillover / float(edge_height)) * edge_height
                        else:
                            extra_height = math.ceil(height_spillover)
                    width_spillover = ((node.width + prev_width) / 2) - (edge_width * 2)
                    if width_spillover > extra_widths[x_i]:
                        if edge_width:
                            extra_widths[x_i] = math.ceil(width_spillover / float(edge_width)) * \
                                                edge_width
                        else:
                            extra_widths[x_i] = math.ceil(width_spillover)
                    # fix cases where bottom half of tall node is overlapped by edges from smaller
                    # node beside it.
                    if prev_height > node.height:
                        if x_i >= 1 and y_i < merged_grid.height - 2:
                            edge = merged_grid.get(x_i - 1, y_i + 1, raw=True)
                            left_neighbor = merged_grid.get(x_i - 2, y_i, raw=True)
                            # The problem happens with this kind of constellation:
                            #  ..././.
                            #  ..A.B..
                            #  .../.\. <--- the left edge here can be obstructed by A
                            if left_neighbor and edge and isinstance(edge, int):
                                edge_box_left_x = x - node.width / 3 - edge_width
                                prev_box_right_x = prev_x + (prev_width / 2)
                                width_overlap = prev_box_right_x - edge_box_left_x
                                height_overlap = prev_height - node.height
                                if extra_widths[x_i] < width_overlap:
                                    extra_widths[x_i] = width_overlap
                                if extra_height < height_overlap:
                                    extra_height = height_overlap
                    x += extra_widths[x_i]
                    prev_width = node.width
                    prev_height = node.height
                    prev_x = x
                    if node not in all_nodes:
                        if not node.isVisible():
                            print('non-visible node included in visualization grid: ', node,
                              node.isVisible())
                        else:
                            print('whats wrong with node ', node)
                            print(node, node.save_key, node.deleted, node.parentObject(),
                                  node.trees)
                    else:
                        all_nodes.remove(node)
                else:
                    x += extra_widths[x_i]
                x += edge_width
            y += edge_height + extra_height
            extra_heights.append(extra_height)
        if all_nodes:
            print('nodes left remaining: ', all_nodes)
            for node in all_nodes:
                print(node, node.save_key, node.deleted, node.parentObject(), node.trees)
        y = 0
        for y_i, row in enumerate(merged_grid):
            x = offset_x
            for x_i, node in enumerate(row):
                x += extra_widths[x_i]
                if node and getattr(node, 'node_type', '') == g.CONSTITUENT_NODE:
                    node.move_to(x, y, 0, valign=g.TOP_ROW)
                x += edge_width
            y += edge_height + extra_heights[y_i]

