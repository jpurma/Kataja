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
from kataja.debug import vis

from kataja.ConstituentNode import ConstituentNode
from kataja.singletons import prefs
from kataja.FeatureNode import FeatureNode
from kataja.utils import caller
from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.visualizations.Grid import Grid
from kataja.GlossNode import GlossNode


class LeftFirstTree(BaseVisualization):
    """ Visualization that draws branches, starting from top and left. Each branch takes the space it needs, and may force next branch drawing to further down and right. """
    name = 'Left first tree'

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._hits = {}
        self._max_hits = {}
        self._directed = True
        self._indentation = 0

    def prepare(self, forest, loading=False):
        """

        :param forest:
        :param loading:
        """
        vis('preparing LeftFirstVisualization')
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        self.forest.settings.bracket_style(0)
        self.forest.settings.show_constituent_edges = True
        if not loading:
            self.forest.vis_data = {'name': self.__class__.name, 'rotation': 0}
        self._indentation = 0
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
            node.bind_x = True
            node.bind_y = True
            node.update_visibility(show_edges=True, scope=0, brackets=self.forest.settings.bracket_style())
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.bind_x = False
            node.bind_y = False


    @caller
    def reselect(self):
        """ if there are different modes for one visualization, rotating between different modes is triggered here. """
        self.forest.vis_data['rotation'] -= 1

    def _indent(self, node, c):
        left = node.left()
        if left:
            c += 2
            if c > self._indentation:
                self._indentation = c
            c = self._indent(left, c)
        right = node.right()
        if right:
            c = self._indent(right, c - 3)
        return c

    # Recursively put nodes to their correct position in grid
    def _fill_grid(self, grid, node, x, y, parent=None):
        if not self.should_we_draw(node, parent):
            return
        grid.set(x, y, node)
        left = node.left()
        if left:
            if isinstance(left, FeatureNode):
                self._fill_grid(grid, left, x - 1, y + 1, parent=node)
            else:
                grid.set(x - 1, y + 1, 1)
                self._fill_grid(grid, left, x - 2, y + 2, parent=node)
        elif self.forest.settings.draw_features and getattr(node.syntactic_object, 'feature_tree', None):
            vis("(1) drawing feature_tree, this shouldn't happen anymore!")
            self._fill_grid(grid, left, x - 1, y + 1, parent=node)

        right = node.right()
        if right:
            block_size = 2
            nx = x + 2
            ny = y + 2
            filler = 1
            while grid.get(nx - 2, ny + 2):  #
                grid.set(nx - 1, ny - 1, 1)
                grid.set(nx, ny, 1)  # this coordinate is now blocked, not by a node but a edge
                nx += 2
                ny += 2
            grid.set(nx - 1, ny - 1, 1)
            self._fill_grid(grid, right, nx, ny, parent=node)

        # if isinstance(right, FeatureNode):
        # block_size = 1
        #             else:
        #                 block_size = 2
        #             nx = x + block_size
        #             ny = y + block_size
        #             filler = block_size - 1
        #             while filler:
        #                 grid.set(nx - filler, ny - filler, 1)
        #                 filler -= 1
        #             while grid.get(nx - block_size, ny + block_size):
        #                 filler = block_size - 1
        #                 while filler:
        #                     grid.set(nx - filler, ny - filler, 1)
        #                     filler -= 1
        #                 grid.set(nx, ny, 1)  # this coordinate is now blocked, not by a node but a edge
        #                 nx += block_size
        #                 ny += block_size
        #             self._fill_grid(grid, right, nx, ny, parent = node)
        elif self.forest.settings.draw_features and getattr(node.syntactic_object, 'feature_tree', None):
            vis("(2) drawing feature_tree, this shouldn't happen anymore!")
            nx = x + 1
            ny = y + 1
            while grid.get(nx - 1, ny + 1):
                grid.set(nx, ny, 1)  # this coordinate is now blocked, not by a node but a edge
                nx += 1
                ny += 1
            self._fill_grid(grid, right, nx, ny, parent=node)

    def _merge_grids(self, grid, other_grid):
        if not other_grid:
            return grid
        paddings = []
        for row_n, row in enumerate(grid):
            rightmost_free = other_grid.last_filled_column(row_n) + 1
            left_empties = 0
            for node in row:
                if not node:
                    left_empties += 1
                else:
                    break
            paddings.append(rightmost_free - left_empties)
        padding = max(paddings) + prefs.spacing_between_trees
        for row_n, row in enumerate(grid):
            for col_n, node in enumerate(row):
                if node:
                    other_grid.set(col_n + padding, row_n, node)
        return other_grid

    # @time_me
    def draw(self):
        """ Draws the tree to a table or a grid, much like latex qtree and then scales the grid to the scene. """
        edge_height = prefs.edge_height
        edge_width = prefs.edge_width
        merged_grid = Grid()
        self._indentation = 0
        self.forest.vis_data['rotation'], self.traces_to_draw = self._compute_traces_to_draw(
            self.forest.vis_data['rotation'])
        for root in self.forest:
            grid = Grid()
            if isinstance(root, ConstituentNode):
                self._indent(root, 0)
                self._fill_grid(grid, root, self._indentation, 0)
                merged_grid = self._merge_grids(grid, merged_grid)

        tree_width = merged_grid._width * edge_width
        tree_height = merged_grid._height * edge_height
        offset_x = 0  # tree_w/-2
        y = 0

        # Actual drawing: set nodes to their places in scene
        extra_height = 0
        if merged_grid:
            # merged_grid.ascii_dump()
            extra_width = [0] * merged_grid._width
        else:
            extra_width = [0]
        # if node is extra wide, then move all columns to right from that point on
        # same for extra tall nodes. move everything down after that row

        all_nodes = set([x for x in self.forest.visible_nodes() if isinstance(x, ConstituentNode)])

        for y_i, row in enumerate(merged_grid):
            extra_height = 0
            prev_width = 0
            prev_rect = None
            x = offset_x
            for x_i, node in enumerate(row):
                if node and isinstance(node, ConstituentNode):

                    height_spillover = node.inner_rect.bottom() - edge_height
                    if height_spillover > extra_height:
                        extra_height = math.ceil(height_spillover / float(edge_height)) * edge_height
                    width_spillover = ((node.width + prev_width) / 2) - (edge_width * 4)
                    if width_spillover > extra_width[x_i]:
                        extra_width[x_i] = math.ceil(width_spillover / float(edge_width)) * edge_width
                    x += extra_width[x_i]
                    node.set_computed_position((x, y, 0))
                    prev_width = node.width
                    prev_rect = node.inner_rect
                    all_nodes.remove(node)
                else:
                    x += extra_width[x_i]
                x += edge_width
            y += edge_height + extra_height
        if all_nodes:
            vis('nodes left remaining: ', all_nodes)

