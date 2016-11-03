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
from PyQt5 import QtCore

import kataja.globals as g
from kataja.Visualization import BaseVisualization
from kataja.singletons import prefs


class BalancedTree(BaseVisualization):
    """

    """
    name = 'Balanced trees'
    banned_node_shapes = (g.BRACKETED, g.SCOPEBOX)

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._directed = True
        self._linear = []

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._directed = True
        if reset:
            self.set_vis_data('rotation', 0)
            self.reset_nodes()
        self.validate_node_shapes()

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)
        if node.node_type == g.CONSTITUENT_NODE:
            node.physics_x = False
            node.physics_y = False
        else:
            node.physics_x = True
            node.physics_y = True


    def reselect(self):
        """


        """
        self.set_vis_data('rotation', self.get_vis_data('rotation', 0) - 1)


    # @time_me
    def draw(self):
        """ Divide and conquer, starting from bottom right. Results in a horizontal
        linearisation of leaves."""
        x_margin = 0 # prefs.edge_width / 2
        y_margin = 0 # prefs.edge_height / 2

        def recursive_position(node, x, y):
            if node.is_leaf():
                rect = QtCore.QRectF(node.boundingRect())
                rect.adjust(-x_margin, -y_margin, x_margin, y_margin)
                x -= rect.width() / 2
                rect.moveCenter(QtCore.QPoint(x, y))
                node.move_to(rect.center().x(), rect.center().y())
            else:
                rect = None
                uw = 0
                for child in node.get_children(visible=True, similar=True, reverse=True):
                    crect = recursive_position(child, x, y)
                    x -= crect.width()
                    if not rect:
                        rect = crect
                    else:
                        rect = rect.united(crect)
                    uw += crect.width()
                y -= rect.height()
                my_rect = QtCore.QRectF(node.boundingRect())
                my_rect.adjust(-x_margin, -y_margin, x_margin, y_margin)
                my_rect.moveCenter(QtCore.QPoint(rect.center().x(), y - (my_rect.height() / 2)))
                node.move_to(my_rect.center().x(), my_rect.center().y())
                rect = rect.united(my_rect)
            return rect

        tx = 0
        for tree in self.forest:
            total_rect = recursive_position(tree.top, 0, 0)
            rx = total_rect.x()
            ry = total_rect.y()
            for node in tree.sorted_constituents:
                nx, ny = node.target_position
                node.move_to(tx + nx - rx, ny - ry)
            tx += total_rect.width()

