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
import random

from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.ConstituentNode import ConstituentNode
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode
import kataja.globals as g
from kataja.singletons import prefs


class SymmetricElasticTree(BaseVisualization):
    """

    """
    name = 'Dynamic directionless net'

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
            self.forest.vis_data = {'name': self.__class__.name}
            for node in self.forest.visible_nodes():
                self.reset_node(node)


    def reset_node(self, node):
        """

        :param node:
        """
        node.update_label()
        node.update_visibility()
        if isinstance(node, ConstituentNode):
            node.dyn_y = False
            node.dyn_x = False
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.dyn_x = False
            node.dyn_y = False

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
            dist_x, dist_y = int(node_x - other_x), int(node_y - other_y)
            safe_zone = (other.width + node.width) / 2
            dist = math.hypot(dist_x, dist_y)
            if dist == 0 or dist == safe_zone:
                continue
            required_dist = dist - safe_zone
            pushing_force = 500 / (required_dist * required_dist)
            pushing_force = min(random.random()*60, pushing_force)

            x_component = dist_x / dist
            y_component = dist_y / dist
            xvel += pushing_force * x_component
            yvel += pushing_force * y_component

        # Now subtract all forces pulling items together.
        for edge in node.edges_down:
            other = edge.end
            other_x, other_y, other_z = other.current_position
            dist_x, dist_y = int(node_x - other_x), int(node_y - other_y)
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                continue
            safe_zone = (other.width + node.width) / 2
            pulling_force = (dist - safe_zone) * edge.pull * 0.4
            x_component = dist_x / dist
            y_component = dist_y / dist
            xvel -= x_component * pulling_force
            yvel -= y_component * pulling_force

        for edge in node.edges_up:
            other = edge.start
            other_x, other_y, other_z = other.current_position
            dist_x, dist_y = (node_x - other_x, node_y - other_y)
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                continue
            safe_zone = (other.width + node.width) / 2
            pulling_force = (dist - safe_zone) * edge.pull * 0.4
            x_component = dist_x / dist
            y_component = dist_y / dist
            xvel -= x_component * pulling_force
            yvel -= y_component * pulling_force

        # pull to center (0, 0)
        xvel += node_x * -0.003
        yvel += node_y * -0.003

        if not node.dyn_x:
            xvel = 0
        if not node.dyn_y:
            yvel = 0
        return xvel, yvel, 0
