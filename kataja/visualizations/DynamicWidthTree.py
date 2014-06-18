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


from kataja.ConstituentNode import ConstituentNode
from kataja.Controller import prefs, ctrl
from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode


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

    def prepare(self, forest, loading=False):
        """

        :param forest:
        :param loading:
        """
        self.forest = forest
        self._directed = True
        self.forest.settings.show_constituent_edges = True
        self.forest.settings.bracket_style(0)
        if not loading:
            self.forest.vis_data = {'name': self.__class__.name, 'push': 20}
        self.push = self.forest.vis_data['push']
        l = []
        for root in self.forest.roots:
            l += self.forest.list_nodes_once(root)
        self._linear = l
        for node in self.forest.visible_nodes():
            self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        node.locked_to_position = False
        node.reset_adjustment()
        node.update_label()
        if isinstance(node, ConstituentNode):
            node.update_visibility(show_edges=True, scope=0, brackets=self.forest.settings.bracket_style())
            node.bind_y = True
            node.bind_x = False
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.bind_x = False
            node.bind_y = False


    def reselect(self):
        """


        """
        push = self.forest.vis_data['push']
        push -= 5
        if push > 30:
            push = 10
        if push < 5:
            push = 30
        self.forest.vis_data['push'] = push
        self.push = push
        ctrl.add_message('Push: %s' % push)

    def calculate_movement(self, node):
        # like calculate_movement in elastic net, but only count x-dimension.
        # Sum up all forces pushing this item away.
        """

        :param node:
        :return:
        """
        if isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            return BaseVisualization.calculate_movement(self, node)
        xvel = 0.0
        node_x, node_y, node_z = node.get_current_position()
        if not isinstance(node, ConstituentNode):
            return 0, 0, 0
        # linear = self.forest.list_nodes_once(node.get_root_node())
        node_index = self._linear.index(node)
        for other_index, other in enumerate(self._linear):
            if other is node:
                continue
            leaf = other.is_leaf_node()
            other_x, other_y, other_z = other.get_current_position()
            width = (node.width + other.width) * .5  # / 2
            dist_y = other_y - node_y

            # --d2---------->  <-d1-----------
            # |   -d1->     |  |   <-d2-     |
            #  [ N ]   [  O  ]  [ O ]   [  N  ]
            d1 = int(other_x - width - node_x)  # 300 - 60 -240
            d2 = int(other_x + width - node_x)
            dx = 0
            if node_index < other_index:  # should be: NODE | OTHER
                if abs(dist_y) < 20:  # nodes in same row
                    if d1 < 0:  # is: OTHER | NODE
                        dx = -2  # (dist_x - width) / -10.0
                    elif d1 > 0:  # is: NODE | OTHER
                        dx = max((-1, -1.0 / d1))
                    else:  # |NOOTDHEER| node is overlapping with the other node
                        dx = -3  # abs(other.force / (dist_x + width))
                elif leaf and d1 < 0:  #  is: OTHER | NODE
                    dx = -.7
            else:  # should be: OTHER | NODE
                if abs(dist_y) < 20:  # nodes in same row
                    if d2 > 0:  # is: NODE | OTHER
                        dx = 2  # (dist_x + width) / -10.0
                    elif d2 < 0:  # is: OTHER | NODE
                        dx = min((1, -1.0 / d2))
                    else:  # |NOOTDHEER| node is overlapping with the other node
                        dx = 3  # abs(other.force / (dist_x - width))
                elif leaf and d2 > 0:  # leaf and is: NODE | OTHER
                    dx = .7
            xvel += dx
        # Now subtract all forces pulling items together.
        for edge in node.get_edges_up():
            edge_length_x = edge.start_point[0] - edge.end_point[0]
            if edge_length_x > prefs.edge_width:
                edge_length_x -= prefs.edge_width
                xvel += edge_length_x * edge.pull() / self.push
            elif edge_length_x < -prefs.edge_width:
                edge_length_x += prefs.edge_width
                xvel += edge_length_x * edge.pull() / self.push
        for edge in node.get_edges_down():
            edge_length_x = edge.end_point[0] - edge.start_point[0]
            if edge_length_x > prefs.edge_width:
                edge_length_x -= prefs.edge_width
                xvel += edge_length_x * edge.pull() / self.push
            elif edge_length_x < -prefs.edge_width:
                edge_length_x += prefs.edge_width
                xvel += edge_length_x * edge.pull() / self.push
        return xvel, 0, 0

    def draw(self):
        """ Draws the tree from bottom to top, trying to fit every horizontal row to as small as possible """
        edge_height = prefs.edge_height
        edge_width = prefs.edge_width
        rows = []

        def _fill_grid(node, row):
            if not row < len(rows):
                rows.append([])
            x_pos = 0
            for n, x, width in rows[row]:
                x_pos += width
            rows[row].append((node, x_pos, node.width))
            node.set_computed_position((x_pos + node.width, row * edge_height * 2, 0))
            left = node.left()
            if left:
                _fill_grid(left, row + 1)
            right = node.right()
            if right:
                _fill_grid(right, row + 1)

        for root_node in self.forest:
            _fill_grid(root_node, 0)
