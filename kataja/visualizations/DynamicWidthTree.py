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
from kataja.Visualization import centered_node_position
from kataja.saved.movables import Node
from kataja.visualizations.DivideAndConquerTree import DivideAndConquerTree


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

    def calculate_movement(self, node: 'Node', other_nodes: list, heat: float):
        cbr = node.future_children_bounding_rect()
        node_x, node_y = centered_node_position(node, cbr)
        x_vel = 0
        alpha = 0.4
        # attract
        cbr_w = cbr.width()
        cbr_h = cbr.height()

        # Sum up all forces pushing this item away.
        for other in other_nodes:
            other_cbr = other.future_children_bounding_rect()
            other_x, other_y = centered_node_position(other, other_cbr)
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                node_x += 5
                continue
            safe_zone = max(other_cbr.width() + cbr_w, other_cbr.height() + cbr_h) / 2
            safe_zone += 10
            if dist == safe_zone:
                pushing_force = 0.1
            elif dist < safe_zone:
                required_dist = abs(dist - safe_zone)
                pushing_force = required_dist / (dist * dist * alpha)
            else:
                continue
            x_vel += pushing_force * dist_x

        total_edges = 0
        edges = []
        for start, e in node.get_edges_up_with_children():
            total_edges += 1
            edges.append((start, e.pull))
        for end, e in node.get_edges_down_with_children():
            total_edges += 1
            edges.append((end, e.pull))

        for other, edge_pull in edges:
            other_cbr = other.future_children_bounding_rect()
            other_x, other_y = centered_node_position(other, other_cbr)
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            radius = max(other_cbr.width() + cbr_w, other_cbr.height() + cbr_h)
            if dist != 0 and dist - radius > 0:
                pulling_force = ((dist - radius) * edge_pull * alpha) / dist
                x_vel -= dist_x * pulling_force
            else:
                x_vel += 1

        if not total_edges:
            # pull to center (0, 0)
            x_vel += node_x * -0.009

        return round(x_vel * heat), 0

    def calculate_movement_old(self, node, other_nodes):
        cbr = node.future_children_bounding_rect()
        node_x, node_y = centered_node_position(node, cbr)
        old_x = node_x
        old_y = node_y
        alpha = 0.2

        close_ones = set()
        # attract
        down = node.edges_down
        for edge in down:
            other = edge.end
            if other.locked_to_node is node:
                continue
            if other.is_visible():
                other_cbr = other.future_children_bounding_rect()
                close_ones.add(other)
                other_x, other_y = centered_node_position(other, other_cbr)
                dist_x, dist_y = node_x - other_x, node_y - other_y
                dist = math.hypot(dist_x, dist_y)

                radius = (other_cbr.width() + cbr.width()) / 2
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
                other_cbr = other.future_children_bounding_rect()
                other_x, other_y = centered_node_position(other, other_cbr)
                dist_x, dist_y = node_x - other_x, node_y - other_y
                dist = math.hypot(dist_x, dist_y)
                radius = ((other_cbr.width() + cbr.width()) / 2) * 1.4
                if dist == 0 or dist - radius <= 0:
                    node_x -= 1
                else:
                    pulling_force = ((dist - radius) * edge.pull * alpha) / dist
                    node_x -= dist_x * pulling_force

        other_nodes = set(other_nodes) - close_ones
        other_nodes.remove(node)
        # repulse strongly
        alpha_strong = (alpha * 5) or 0.5
        alpha = alpha or 0.1
        # Sum up all forces pushing this item away.
        for other in other_nodes:
            if other.locked_to_node is node or node.locked_to_node is other:
                continue
            other_cbr = other.future_children_bounding_rect()
            other_x, other_y = centered_node_position(other, other_cbr)
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                node_x += 5
                continue
            safe_zone = ((other_cbr.width() + cbr.width()) / 2) * 1.4
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
            other_cbr = other.future_children_bounding_rect()
            other_x, other_y = centered_node_position(other, other_cbr)
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                node_x += 5
                continue
            safe_zone = ((other_cbr.width() + cbr.width()) / 2) * 1.4
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
        return xvel, 0
