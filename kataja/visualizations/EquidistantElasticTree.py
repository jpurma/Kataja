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

from kataja.visualizations.BaseVisualization import BaseVisualization
import kataja.globals as g


class EquidistantElasticTree(BaseVisualization):
    """

    """
    name = 'Equidistant net'

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
            self.forest.settings.show_constituent_edges = True
            self.forest.settings.bracket_style = g.NO_BRACKETS
            for node in self.forest.visible_nodes():
                self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)

    def calculate_movement(self, node):
        # @time_me
        # Sum up all forces pushing this item away.
        """

        :param node:
        :return:
        """
        xvel = 0.0
        yvel = 0.0
        node_x, node_y = node.current_position
        vn = list(self.forest.visible_nodes())
        for other in vn:
            other_x, other_y = other.current_position
            if other is node:
                continue
            dist_x = int(node_x - other_x)
            dist_y = int(node_y - other_y)
            dist = math.hypot(dist_x, dist_y)
            if dist and dist < 100:
                l = (70.0 / (dist * dist)) * .5
                xvel += dist_x * l
                yvel += dist_y * l

        # Now subtract all forces pulling items together.
        for edge in node.edges_up:
            start_x, start_y = edge.start_point
            end_x, end_y = edge.end_point
            dist_x = start_x - end_x
            dist_y = start_y - end_y
            dist = math.hypot(dist_x, dist_y)
            if dist > 30:
                fx = (dist_x / dist) * (dist - 30)
                fy = (dist_y / dist) * (dist - 30)
                xvel += fx * edge.pull
                yvel += fy * edge.pull
            elif dist < 20:
                push = edge.pull / -2
                xvel += dist_x * push
                yvel += dist_y * push
            else:
                pass
        for edge in node.edges_down:
            start_x, start_y = edge.start_point
            end_x, end_y = edge.end_point
            dist_x = end_x - start_x
            dist_y = end_y - start_y
            dist = math.hypot(dist_x, dist_y)
            if dist > 30:
                # ang=math.atan2(by,bx)
                # fx=math.cos(ang)*(dist-30)
                # fy=math.sin(ang)*(dist-30)
                fx = (dist_x / dist) * (dist - 30)
                fy = (dist_y / dist) * (dist - 30)
                xvel += fx * edge.pull
                yvel += fy * edge.pull
            elif dist < 20:
                push = edge.pull / -2
                xvel += dist_x * push
                yvel += dist_y * push
            else:
                pass

        # pull to center (0, 0)
        xvel += node_x * -0.002
        yvel += node_y * -0.002

        if not node.physics_x:
            xvel = 0
        elif abs(xvel > 10):
            if xvel > 10:
                xvel = 10
            elif xvel < -10:
                xvel = -10
        if not node.physics_y:
           yvel = 0
        elif abs(yvel) > 10:
            if yvel > 10:
                yvel = 10
            elif yvel < -10:
                yvel = -10
        return xvel, yvel, 0
