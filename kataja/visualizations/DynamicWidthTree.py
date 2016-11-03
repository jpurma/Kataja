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

from kataja.singletons import prefs, ctrl
from kataja.visualizations.DivideAndConquerTree import DivideAndConquerTree
import kataja.globals as g


class DynamicWidthTree(DivideAndConquerTree):
    """

    """
    name = 'Dynamic width trees'
    def __init__(self):
        super().__init__()
        self.use_gravity = False

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)
        if node.node_type == g.CONSTITUENT_NODE:
            node.physics_x = True
            node.physics_y = False
        elif node.node_type == g.FEATURE_NODE:
            node.physics_x = True
            node.physics_y = True

    def calculate_movement(self, node):
        # Sum up all forces pushing this item away.
        """

        :param node:
        :return:
        """

        node_x, node_y = node.centered_position
        old_x, old_y = node.centered_position
        alpha = 0.2

        close_ones = set()
        # attract
        down = node.edges_down
        for edge in down:
            other = edge.end
            if other.locked_to_node is node:
                continue
            if other.is_visible():
                close_ones.add(other)
                other_x, other_y = other.centered_position
                dist_x, dist_y = node_x - other_x, node_y - other_y
                dist = math.hypot(dist_x, dist_y)
                radius = (other.width + node.width) / 2
                if dist == 0 or dist - radius <= 0:
                    node_x += 1
                else:
                    pulling_force = ((dist - radius) * edge.pull * alpha) / dist
                    node_x -= dist_x * pulling_force

        up = node.edges_up
        for edge in up:
            other = edge.start
            if node.locked_to_node is other:
                continue
            if other.is_visible():
                close_ones.add(other)
                other_x, other_y = other.centered_position
                dist_x, dist_y = node_x - other_x, node_y - other_y
                dist = math.hypot(dist_x, dist_y)
                radius = ((other.width + node.width) / 2) * 1.4
                if dist == 0 or dist - radius <= 0:
                    node_x -= 1
                else:
                    pulling_force = ((dist - radius) * edge.pull * alpha) / dist
                    node_x -= dist_x * pulling_force

        all_nodes = set(self.forest.visible_nodes())
        other_nodes = all_nodes - close_ones
        other_nodes.remove(node)
        # repulse strongly
        alpha_strong = (alpha * 5) or 0.5
        alpha = alpha or 0.1
        for other in other_nodes:
            if other.locked_to_node is node or node.locked_to_node is other:
                continue
            other_x, other_y = other.centered_position  # @UnusedVariable
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                node_x += 5
                continue
            safe_zone = ((other.width + node.width) / 2) * 1.4
            if dist == safe_zone:
                continue
            if dist < safe_zone:
                required_dist = abs(dist - safe_zone)
                pushing_force = required_dist / (dist * dist * alpha_strong)
                node_x += pushing_force * dist_x
                if dist_x == 0:
                    node_x -= 1
        # repulse weakly
        for other in close_ones:
            other_x, other_y = other.centered_position  # @UnusedVariable
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                node_x += 5
                continue
            safe_zone = ((other.width + node.width) / 2) * 1.4
            if dist == safe_zone:
                continue
            if dist < safe_zone:
                required_dist = abs(dist - safe_zone)
                pushing_force = required_dist / (dist * dist * alpha)
                node_x += pushing_force * dist_x
                if dist_x == 0:
                    node_x -= 1

        if node.physics_x:
            xvel = node_x - old_x
        else:
            xvel = 0
        return xvel, 0, 0

