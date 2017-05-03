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

import kataja.globals as g
from kataja.Visualization import BaseVisualization


class SymmetricElasticTree(BaseVisualization):
    """

    """
    name = 'Dynamic directionless net'
    hide_edges_if_nodes_overlap = False

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self.use_gravity = False

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        if reset:
            self.reset_nodes()
        self.validate_node_shapes()

    def reset_node(self, node):
        """

        :param node:
        """
        node.update_label()
        node.update_visibility()
        node.physics_x = True
        node.physics_y = True

    def calculate_movement(self, node, other_nodes):
        """

        :param node:
        :param other_nodes:
        :return:
        """
        xvel = 0.0
        yvel = 0.0
        fbr = node.future_children_bounding_rect()
        node_x, node_y = self.centered_node_position(node, fbr)
        # Sum up all forces pushing this item away.
        for other in other_nodes:
            if other is node:
                continue
            fbr_other = other.future_children_bounding_rect()
            other_x, other_y = self.centered_node_position(other, fbr_other)
            dist_x, dist_y = int(node_x - other_x), int(node_y - other_y)
            safe_zone = (fbr.width() + fbr_other.width()) / 2
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                continue
            required_dist = dist - safe_zone
            if required_dist < 1:
                pushing_force = 0.7
            else:
                pushing_force = 1 / (0.0001 * required_dist * required_dist)
                pushing_force = min(0.7, pushing_force)

            x_component = dist_x / dist
            y_component = dist_y / dist
            xvel += pushing_force * x_component
            yvel += pushing_force * y_component

        # Now subtract all forces pulling items together.
        total_edges = 0
        edges = []
        for e in node.get_edges_up_with_children():
            other = e.start
            while other.locked_to_node:
                other = other.locked_to_node
            if other is node:
                continue
            total_edges += 1
            edges.append((other, e.pull))
        for e in node.get_edges_down_with_children():
            other = e.end
            while other.locked_to_node:
                other = other.locked_to_node
            if other is node:
                continue
            total_edges += 1
            edges.append((other, e.pull))

        for other, edge_pull in edges:
            fbr_other = other.future_children_bounding_rect()
            other_x, other_y = self.centered_node_position(other, fbr_other)
            dist_x, dist_y = int(node_x - other_x), int(node_y - other_y)
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                continue
            safe_zone = (fbr.width() + fbr_other.width()) / 2
            pulling_force = (dist - safe_zone) * edge_pull * 0.4 / total_edges
            x_component = dist_x / dist
            y_component = dist_y / dist
            xvel -= x_component * pulling_force
            yvel -= y_component * pulling_force

        # pull to center (0, 0)
        #if not node.edges_up:
        #    xvel += node_x * -0.006
        #    yvel += node_y * -0.006

        return round(xvel), round(yvel)
