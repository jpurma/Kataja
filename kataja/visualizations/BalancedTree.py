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


import kataja.globals as g
from Visualization import BaseVisualization
from kataja.singletons import prefs


class BalancedTree(BaseVisualization):
    """

    """
    name = 'Balanced trees'

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._directed = True
        self._linear = []

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
            node.physics_x = True
            node.physics_y = False
        else:
            node.physics_x = False
            node.physics_y = False


    def reselect(self):
        """


        """
        self.set_vis_data('rotation', self.get_vis_data('rotation') - 1)


    # @time_me
    def draw(self):
        """ Draws the trees from bottom to top, trying to fit every horizontal row to as small as possible """
        edge_height = prefs.edge_height
        edge_width = prefs.edge_width
        rows = []
        self._linear = []

        def _fill_grid(node, row):
            if not row < len(rows):
                rows.append([])
            x_pos = 0
            for n, x, width in rows[row]:
                x_pos += width
            rows[row].append((node, x_pos, node.width))
            node.move_to(x_pos + node.width / 2, row * edge_height * 2, 0, valign=g.TOP_ROW)
            for child in node.get_visible_children():
                _fill_grid(child, row + 1)

        for tree in self.forest:
            _fill_grid(tree.top, 0)
            self._linear.append(tree.sorted_constituents)
