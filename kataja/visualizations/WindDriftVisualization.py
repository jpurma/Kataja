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

from kataja.ConstituentNode import ConstituentNode
from kataja.singletons import prefs
from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode


class WindDriftTree(BaseVisualization):
    """

    """
    name = 'Wind drift linearization'

    def __init__(self):
        self.forest = None
        self._directed = True
        self._last_pos = (0, 0)
        self._grid_height = prefs.edge_height * 2
        self._grid_width = prefs.edge_width
        self._leftmost = None
        self._hits = {}
        self._max_hits = {}

    def prepare(self, forest, loading=False):
        """

        :param forest:
        :param loading:
        """
        self.forest = forest
        self._last_pos = (0, 0)
        self._leftmost = None
        self._hits = {}
        self._max_hits = {}
        self.forest.settings.bracket_style(0)
        self.forest.settings.show_constituent_edges = False
        if not loading:
            self.forest.vis_data = {'name': self.__class__.name}
        for node in self.forest.visible_nodes():
            self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        node.locked_to_position = False
        node.reset_adjustment()
        if isinstance(node, ConstituentNode):
            node.update_visibility(brackets=self.forest.settings.bracket_style(), show_edges=False)
            node.bind_x = True
            node.bind_y = True
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.bind_y = False
            node.bind_x = False
        node.update_label()


    def _draw_wind_drift_tree(self, topmost_node):

        def draw_node(node, parent):
            """

            :param node:
            :param parent:
            """
            right = node.right()
            left = node.left()
            if right:
                draw_node(right, node)
            if left:
                draw_node(left, node)
            self._reduce_node_count(node)
            if self._is_last_node(node):
                if not (left or right):  # bottom level nodes
                    x, y = self._last_pos
                    if self._leftmost:  # this isn't bottom right node
                        lx, y, z = self._leftmost.current_position
                        x = lx - self._leftmost.width / 2 - node.width / 2
                    self._leftmost = node
                    self._last_pos = (x, y)
                    node.computed_position = (x, y, 0)
                else:
                    x, y = self._last_pos
                    left_right_node = left.right()
                    if left_right_node:
                        y = min((y - self._grid_height, left_right_node.current_position[1] - self._grid_height))
                    else:
                        y -= self._grid_height
                    x += self._grid_height
                    self._last_pos = (x, y)
                    node.computed_position = (x, y, 0)

        draw_node(topmost_node, None)

    # @time_me
    def draw(self):
        """ We should draw recursively starting from right bottom edge and add layers when needed. """
        self._last_pos = (0, 0)
        for tree in self.forest:
            self._count_occurences_of_node(tree.root)
            if not isinstance(tree.root, ConstituentNode):
                continue
            self._draw_wind_drift_tree(tree.root)
