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
from kataja.visualizations.BaseVisualization import BaseVisualization
import kataja.globals as g


class DynamicWidthTree(BaseVisualization):
    """

    """
    name = 'Dynamic width tree'


    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._directed = True
        self._linear = []
        self.push = 0

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._directed = True
        if reset:
            self.set_vis_data('push', 20)
            self.forest.settings.show_constituent_edges = True
            self.forest.settings.bracket_style = g.NO_BRACKETS
            for node in self.forest.visible_nodes():
                self.reset_node(node)
        self.push = self.get_vis_data('push')
        self._linear = self.linearize_all()

    def linearize_all(self):
        l = []
        for root in self.forest.roots:
            l.append(self.forest.list_nodes_once(root))
        return l


    def reset_node(self, node):
        """

        :param node:
        """
        node.fixed_position = None
        node.adjustment = None
        node.update_label()
        node.update_visibility()
        if node.node_type == g.CONSTITUENT_NODE:
            node.dyn_y = False
            node.dyn_x = True
        else:
            node.dyn_x = True
            node.dyn_y = True


    def reselect(self):
        """


        """
        push = self.get_vis_data('push')
        push -= 5
        if push > 30:
            push = 10
        if push < 5:
            push = 30
        self.set_vis_data('push', push)
        self.push = push
        ctrl.add_message('Push: %s' % push)


    def calculate_movement(self, node):
        # @time_me
        # Sum up all forces pushing this item away.
        """

        :param node:
        :return:
        """
        if node.node_type != g.CONSTITUENT_NODE:
            return BaseVisualization.calculate_movement(self, node)

        xvel = 0.0
        if not node.dyn_x:
            return 0, 0, 0

        node_x, node_y, node_z = node.current_position

        #vn = list(self.forest.visible_nodes())
        # for tree in self._linear:
        #     my_tree = node in tree
        #     for other in tree:
        #         other_x, other_y, other_z = other.current_position
        #         if other is node:
        #             continue
        #         if node.is_sibling(other):
        #
        my_tree = None
        for tree in self._linear:
            if node in tree:
                my_tree = tree
            for other in tree:
                if other is node:
                    continue

                other_x, other_y, other_z = other.current_position
                dist_x = int(node_x - other_x)
                dist_y = int(node_y - other_y)
                safe_zone = (other.width + node.width) / 2
                dist = math.hypot(dist_x, dist_y)
                if dist == 0 or dist == safe_zone:
                    continue
                if tree is my_tree and not (other.use_fixed_position or ctrl.pressed or not other.dyn_x): # and node.is_sibling(other):
                    index_diff = my_tree.index(node) - my_tree.index(other)
                    if index_diff < 0 and abs(dist_y) < 10:
                        # node is left to other, so dist_x should be negative
                        if dist_x > 0:
                            # jump to other side of node
                            print('jump left', -(dist_x + safe_zone + 5), dist_x, safe_zone, other)
                            return -(dist_x + safe_zone + 5), 0, 0
                    elif index_diff > 0 and abs(dist_y) < 10:
                        # node is right to other, so dist_x should be positive
                        if dist_x < 0:
                            # jump to other side of node
                            print('jump right', (-dist_x + safe_zone + 5), dist_x, safe_zone, other)
                            return (-dist_x + safe_zone + 5), 0, 0


                required_dist = dist - safe_zone
                pushing_force = min(random.random()*60, (500 / (required_dist * required_dist)))

                x_component = dist_x / dist
                xvel += pushing_force * x_component

        # Now subtract all forces pulling items together.
        #
        for edge in node.edges_up:
            if edge.is_visible():
                other = edge.start
                if other:
                    other_x, other_y, other_z = other.current_position
                    dist_x = int(node_x - other_x)
                    dist_y = int(node_y - other_y)
                    dist = math.hypot(dist_x, dist_y)
                    if dist == 0:
                        continue
                    safe_zone = (other.width + node.width) / 2
                    pulling_force = dist - safe_zone
                    x_component = dist_x / dist
                    xvel -= x_component * pulling_force * edge.pull * 0.3
        #
        # pull to center (0, 0)
        xvel += node_x * -0.004
        return xvel, 0, 0


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
