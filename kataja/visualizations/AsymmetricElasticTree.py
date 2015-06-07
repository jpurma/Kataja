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


from kataja.visualizations.BaseVisualization import BaseVisualization
import kataja.globals as g
from kataja.singletons import prefs


class AsymmetricElasticTree(BaseVisualization):
    """

    """
    name = 'Dynamic directed net'

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        if reset:
            self.forest.settings.bracket_style = g.NO_BRACKETS
            self.forest.settings.show_constituent_edges = True
            for node in self.forest.visible_nodes():
                self.reset_node(node)

    def calculate_movement(self, node):
        # Sum up all forces pushing this item away.
        """

        :param node:
        :return:
        """
        xvel = 0.0
        yvel = 0.0
        node_x, node_y, node_z = node.current_position  # @UnusedVariable
        for other in self.forest.visible_nodes():
            if other is node:
                continue
            other_x, other_y, other_z = other.current_position  # @UnusedVariable
            #print 'others: ', other_x, other_y, other_z
            dist_x, dist_y = int(node_x - other_x), int(node_y - other_y)
            dist2 = (dist_x * dist_x) + (dist_y * dist_y)
            if dist2 > 0:
                l = 72.0 / dist2
                xvel += dist_x * l
                yvel += dist_y * l
        # Now subtract all forces pulling items together.
        for edge in node.edges_down:
            if not edge.is_visible():
                continue
            if edge.alignment == g.LEFT:
                target_d_x = prefs.edge_width
            else:
                target_d_x = -prefs.edge_width
            target_d_y = -15
            start_x, start_y, start_z = edge.start_point  # @UnusedVariable
            end_x, end_y, end_z = edge.end_point  # @UnusedVariable
            d_x = start_x - end_x
            d_y = start_y - end_y
            rd_x = target_d_x - d_x
            rd_y = target_d_y - d_y
            xvel += rd_x * edge.pull
            yvel += rd_y * edge.pull

        for i, edge in enumerate(node.edges_up):
            if not edge.is_visible():
                continue
            if edge.alignment == g.LEFT:
                target_d_x = -prefs.edge_width
            else:
                target_d_x = prefs.edge_width
            target_d_y = 15
            start_x, start_y, start_z = edge.start_point  # @UnusedVariable
            end_x, end_y, end_z = edge.end_point  # @UnusedVariable
            d_x = end_x - start_x
            d_y = end_y - start_y
            rd_x = target_d_x - d_x
            rd_y = target_d_y - d_y
            xvel += rd_x * edge.pull / ((i + 1) * (i + 1))  # first branch has strongest pull
            yvel += rd_y * edge.pull # / ((i + 1) * (i + 1))

        # pull to center (0, 0)
        xvel += node_x * -0.008
        yvel += node_y * -0.008

        if not node.dyn_x:
            xvel = 0
        if not node.dyn_y:
            yvel = 0
        return xvel, yvel, 0


    def reset_node(self, node):
        """

        :param node:
        """
        node.fixed_position = None
        node.adjustment = None
        node.update_label()
        node.update_visibility()
        node.dyn_y = True
        node.dyn_x = True
