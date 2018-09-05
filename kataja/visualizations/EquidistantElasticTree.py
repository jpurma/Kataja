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

import itertools

import kataja.globals as g
from kataja.Visualization import BaseVisualization, centered_node_position


class EquidistantElasticTree(BaseVisualization):
    """

    """
    name = 'Equidistant Elastic Tree'
    banned_cn_shapes = (g.BRACKETED, g.SCOPEBOX)
    hide_edges_if_nodes_overlap = False

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._directed = False

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        if reset:
            self.reset_nodes()
        self.validate_cn_shapes()

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)

    def calculate_movement(self, node, other_nodes, heat):
        """ Try to keep the edge between start_point and end_point at a certain length. This has 
        the effect that positioning of edge magnets ends up adjusting the form of the graph. 
        :param node:
        :param other_nodes:
        :return:
        """
        assert (not node.locked_to_node)
        assert (node.is_visible() and node.isVisible())

        xvel = 0.0
        yvel = 0.0
        cbr = node.future_children_bounding_rect()
        node_x, node_y = centered_node_position(node, cbr)

        # Sum up all forces pushing this item away.
        for other in other_nodes:
            if other is node:
                continue
            other_cbr = other.future_children_bounding_rect()
            other_x, other_y = centered_node_position(other, other_cbr)
            dist_x = int(node_x - other_x)
            dist_y = int(node_y - other_y)
            safe_zone = max(cbr.width() + other_cbr.width(), cbr.height() + other_cbr.height()) / 2
            safe_zone += 10
            dist = max((1, math.hypot(dist_x, dist_y)))
            if dist < safe_zone:
                push = (safe_zone - dist) * 0.005  # push > 0
                xvel += dist_x * push
                yvel += dist_y * push
            elif dist < 200:
                l = 70.0 / (dist * dist)  # l > 0
                xvel += dist_x * l
                yvel += dist_y * l
        # Now subtract all forces pulling items together.
        total_edges = 0
        edges = []
        for start, e in node.get_edges_up_with_children():
            total_edges += 1
            edges.append((e.end_point, e.start_point, e.pull))
        for end, e in node.get_edges_down_with_children():
            total_edges += 1
            edges.append((e.start_point, e.end_point, e.pull))
        for my_point, other_point, edge_pull in edges:
            node_x, node_y = my_point
            other_x, other_y = other_point
            dist_x = int(node_x - other_x)
            dist_y = int(node_y - other_y)
            dist = math.hypot(dist_x, dist_y)
            safe_zone = 20
            target_zone = safe_zone + 30
            if dist > target_zone:
                pull = (dist - target_zone) * edge_pull * -0.005  # pull < 0
                pull /= total_edges
                xvel += dist_x * pull
                yvel += dist_y * pull
            elif dist < safe_zone:
                push = (safe_zone - dist) * edge_pull * 0.05  # push > 0
                xvel += dist_x * push
                yvel += dist_y * push

        # pull roots to center (0, 0)
        if not node.edges_up:
            xvel += node_x * -0.02
            yvel += node_y * -0.02
        return round(xvel * heat), round(yvel * heat)
