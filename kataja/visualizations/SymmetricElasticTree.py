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
from kataja.Visualization import BaseVisualization, centered_node_position


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

    def calculate_movement(self, node, other_nodes, heat):
        """

        :param node:
        :param other_nodes:
        :return:
        """

        def similar_edges_up(edge):
            c = 0
            for e in edge.end.edges_up:
                if e is not edge and e.edge_type == edge.edge_type:
                    c += 1
            return c

        target_distance = 30
        inner_repulsion = 0.5
        outer_repulsion = 0.5
        pull = 0.5
        cbr = node.future_children_bounding_rect()
        node_x, node_y = centered_node_position(node, cbr)

        # Push nodes away
        push_x, push_y = self.elliptic_repulsion(node, node_x, node_y, other_nodes, inner_repulsion,
                                                 outer_repulsion)
        # print('node push: ', push_x, push_y)

        # Pull them to preferred distance
        pull_x = 0
        pull_y = 0
        connected = set()
        for e in node.get_edges_up_with_children():
            other = e.start
            while other.locked_to_node:
                other = other.locked_to_node
            if other is not node:
                connected.add((e.path.abstract_end_point, e.path.abstract_start_point,
                               target_distance * (similar_edges_up(e) + 1), e.pull))
        for e in node.get_edges_down_with_children():
            other = e.end
            while other.locked_to_node:
                other = other.locked_to_node
            if other is not node:
                connected.add((e.path.abstract_start_point, e.path.abstract_end_point,
                               target_distance * (similar_edges_up(e) + 1), e.pull))

        for (sx, sy), (ex, ey), preferred_dist, weight in connected:
            dist_x, dist_y = int(sx - ex), int(sy - ey)
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                continue
            x_component = dist_x / dist
            y_component = dist_y / dist

            pulling_force = dist - preferred_dist
            pull_x -= x_component * pulling_force * pull * weight
            pull_y -= y_component * pulling_force * pull * weight

        # print('node pull: ', pull_x, pull_y)

        return (push_x + pull_x) * heat, (push_y + pull_y) * heat  # round(xvel), round(yvel)

    def calculate_movement_good(self, node, other_nodes):
        """

        :param node:
        :param other_nodes:
        :return:
        """
        xvel = 0.0
        yvel = 0.0
        fbr = node.future_children_bounding_rect()
        my_w = fbr.width()
        my_h = fbr.height()
        node_x, node_y = node.node_center_position()

        connected = set()
        for e in node.get_edges_up_with_children():
            other = e.start
            while other.locked_to_node:
                other = other.locked_to_node
            if other is not node:
                connected.add(other)
        for e in node.get_edges_down_with_children():
            other = e.end
            while other.locked_to_node:
                other = other.locked_to_node
            if other is not node:
                connected.add(other)

        # Sum up all forces pushing this item away.
        for other in other_nodes:
            if other is node:
                continue
            fbr_other = other.future_children_bounding_rect()
            other_w = fbr_other.width()
            other_h = fbr_other.height()
            other_x, other_y = other.node_center_position()
            dist_x, dist_y = int(node_x - other_x), int(node_y - other_y)
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                continue
            if dist_y == 0:
                minimum_dist = (my_w + other_w) / 2
            elif dist_x == 0:
                minimum_dist = (my_h + other_h) / 2
            else:
                a = dist_x / dist_y
                if abs(a * my_w) < my_h:
                    minimum_dist = my_h
                else:
                    minimum_dist = my_w
                if abs(a * other_w) < other_h:
                    minimum_dist += other_h
                else:
                    minimum_dist += other_w
                minimum_dist /= 2

            repulsion = dist - minimum_dist
            if repulsion <= 0:
                repulsion = abs(repulsion)
            else:
                repulsion = 20 / (repulsion * repulsion)
            x_component = dist_x / dist
            y_component = dist_y / dist

            xvel += repulsion * x_component
            yvel += repulsion * y_component

            if other in connected:
                preferred_dist = minimum_dist + 20
                pulling_force = dist - preferred_dist
                if pulling_force > 1:
                    pulling_force = math.sqrt(math.sqrt(pulling_force))

                # pulling_force = dist * edge_pull * 0.4 #/ total_edges
                xvel -= x_component * pulling_force
                yvel -= y_component * pulling_force

        return round(xvel), round(yvel)

    def calculate_movement_old(self, node, other_nodes):
        """

        :param node:
        :param other_nodes:
        :return:
        """
        xvel = 0.0
        yvel = 0.0
        fbr = node.future_children_bounding_rect()
        node_x, node_y = centered_node_position(node, fbr)
        # Sum up all forces pushing this item away.
        for other in other_nodes:
            if other is node:
                continue
            fbr_other = other.future_children_bounding_rect()
            other_x, other_y = centered_node_position(other, fbr_other)
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
            other_x, other_y = centered_node_position(other, fbr_other)
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
        # if not node.edges_up:
        #    xvel += node_x * -0.006
        #    yvel += node_y * -0.006

        return round(xvel), round(yvel)
