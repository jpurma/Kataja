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

from kataja.singletons import prefs
from kataja.visualizations.BaseVisualization import BaseVisualization
import kataja.globals as g


class WindDriftTree(BaseVisualization):
    """

    """
    name = 'Wind drift linearization'

    def __init__(self):
        super().__init__()
        self.forest = None
        self._directed = True
        self._last_pos = (0, 0)
        self._grid_height = prefs.edge_height * 2
        self._grid_width = prefs.edge_width
        self._leftmost = None
        self._hits = {}
        self._max_hits = {}

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._last_pos = (0, 0)
        self._leftmost = None
        self._hits = {}
        self._max_hits = {}
        if reset:
            self.forest.settings.bracket_style = g.NO_BRACKETS
            self.forest.settings.show_constituent_edges = False
            for node in self.forest.visible_nodes():
                self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        node.fixed_position = None
        node.adjustment = None
        node.update_visibility()
        if node.node_type == g.CONSTITUENT_NODE:
            node.dyn_x = True
            node.dyn_y = True
        else:
            node.dyn_y = False
            node.dyn_x = False
        node.update_label()


    def _draw_wind_drift_tree(self, topmost_node):


        def draw_node(node, parent):
            """

            :param node:
            :param parent:
            """
            children = node.get_children()
            children.reverse()
            for child in children:
                draw_node(child, node)
            self._reduce_node_count(node)
            if self._is_last_node(node):
                if not children:  # bottom level nodes
                    x, y = self._last_pos
                    if self._leftmost:  # this isn't bottom right node
                        lx, y, z = self._leftmost.current_position
                        x = lx - self._leftmost.width / 2 - node.width / 2
                    self._leftmost = node
                    self._last_pos = (x, y)
                    node.algo_position = (x, y, 0)
                else:
                    x, y = self._last_pos
                    left = children[0]
                    lc = left.get_children()
                    if lc:
                        y = min((y - self._grid_height, lc[-1].current_position[1] - self._grid_height))
                    else:
                        y -= self._grid_height
                    x += self._grid_height
                    self._last_pos = (x, y)
                    node.algo_position = (x, y, 0)

        draw_node(topmost_node, None)

    # @time_me
    def draw(self):
        """ We should draw recursively starting from right bottom edge and add layers when needed. """
        self._last_pos = (0, 0)
        for tree in self.forest:
            self._count_occurences_of_node(tree.root)
            if tree.root.node_type != g.CONSTITUENT_NODE:
                continue
            self._draw_wind_drift_tree(tree.root)
