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
from PyQt5 import QtCore, QtWidgets

import kataja.globals as g
from kataja.Visualization import BaseVisualization
from kataja.singletons import ctrl


class BalancedTree(BaseVisualization):
    """

    """
    name = 'Balanced trees'
    banned_node_shapes = (g.BRACKETED,)

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
            self.set_data('rotation', 0)
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
        self.set_data('rotation', self.get_data('rotation', 0) - 1)

    def prepare_draw(self):
        new_rotation = self.forest.compute_traces_to_draw(self.get_data('rotation'))
        self.set_data('rotation', new_rotation)

    # @time_me
    def draw_tree(self, tree):
        """ Divide and conquer, starting from bottom right. Results in a horizontal
        linearisation of leaves."""

        x_margin = 0 # prefs.edge_width / 2
        y_margin = 0 # prefs.edge_height / 2

        def recursive_position(node, x, y):
            if node.locked_to_node:
                return QtCore.QRectF()
            if node.is_leaf(only_similar=True, only_visible=True):
                leaf_rect = QtCore.QRectF(node.future_children_bounding_rect(limit_height=True))
                x -= leaf_rect.width() / 2
                cp = QtCore.QPoint(x, y)
                leaf_rect.moveCenter(cp)
                node.move_to(leaf_rect.center().x(), leaf_rect.center().y(), align=g.CENTER_ALIGN,
                             valign=g.BOTTOM_ROW)
                return leaf_rect
            else:
                combined_rect = None
                for child in node.get_children(visible=True, similar=True, reverse=True):
                    if self.forest.should_we_draw(child, node):
                        childrens_rect = recursive_position(child, x, y)
                        x -= childrens_rect.width()
                        if not combined_rect:
                            combined_rect = childrens_rect
                        else:
                            combined_rect = combined_rect.united(childrens_rect)
                if not combined_rect:
                    leaf_rect = QtCore.QRectF(node.future_children_bounding_rect(limit_height=True))
                    x -= leaf_rect.width() / 2
                    cp = QtCore.QPoint(x, y)
                    leaf_rect.moveCenter(cp)
                    node.move_to(leaf_rect.center().x(), leaf_rect.center().y(),
                                 align=g.CENTER_ALIGN, valign=g.BOTTOM_ROW)
                    combined_rect = leaf_rect

                y -= combined_rect.height()
                my_rect = QtCore.QRectF(node.boundingRect())
                cp = QtCore.QPoint(combined_rect.center().x(), y - (my_rect.height() / 2))
                my_rect.moveCenter(cp)
                node.move_to(my_rect.center().x(), my_rect.center().y(), align=g.CENTER_ALIGN,
                             valign=g.BOTTOM_ROW)
                combined_rect = combined_rect.united(my_rect)
                return combined_rect
        recursive_position(tree.top, 0, 0)
