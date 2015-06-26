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
from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.BaseConstituentNode import BaseConstituentNode
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode
import kataja.globals as g


class BalancedTree(BaseVisualization):
    """

    """
    name = 'Balanced tree'

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
        node.fixed_position = None
        node.adjustment = None
        node.update_label()
        node.update_visibility()
        if isinstance(node, BaseConstituentNode):
            node.dyn_x = False
            node.dyn_y = False
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.dyn_x = True
            node.dyn_y = True


    def reselect(self):
        """


        """
        self.set_vis_data('rotation', self.get_vis_data('rotation') - 1)


    # @time_me
    def draw(self):
        """ Draws the tree from bottom to top, trying to fit every horizontal row to as small as possible """
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
            node.algo_position = (x_pos + node.width / 2, row * edge_height * 2, 0)
            for child in node.get_visible_children():
                _fill_grid(child, row + 1)

        for root_node in self.forest:
            _fill_grid(root_node, 0)
            self._linear.append(self.forest.list_nodes_once(root_node))
