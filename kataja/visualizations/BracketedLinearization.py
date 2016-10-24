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


import kataja.globals as g
from kataja.Settings import FOREST
from kataja.Visualization import BaseVisualization
from kataja.singletons import prefs, log, ctrl


class BracketedLinearization(BaseVisualization):
    """ This should give the commonly used bracket notation, but instead of plain text, the elements are kataja
    nodes and the structure can be edited like any trees. Reselecting BracketedLinearization switches between different
    modes of showing brackets:
    """
    name = 'Bracketed linearization'
    banned_node_shapes = ()

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._hits = {}
        self._max_hits = {}
        self._directed = True

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        self.validate_node_shapes()
        if reset:
            self.reset_nodes()

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)
        if node.node_type == g.CONSTITUENT_NODE:
            node.physics_x = False
            node.physics_y = False

    def show_edges_for(self, node):
        """ Bracket visualization never shows constituent edges
        :param node: Node
        :return:
        """
        return False

    def reselect(self):
        """ if there are different modes for one visualization, rotating between different modes
        is triggered here. """

        ls = ctrl.settings.get('label_shape')
        if ls == g.BOX:
            ls = g.NORMAL
        else:
            ls += 1
        ctrl.settings.set('label_shape', ls, level=FOREST)
        for node in self.forest.visible_nodes():
            self.reset_node(node)

    def draw(self):
        """ Bracket manager's width map tells the required widths and labels know already how to
        draw themselves """

        width_map = self.forest.prepare_width_map()
        ls = ctrl.settings.get('label_shape')
        if ls == g.BRACKETED or ls == g.NORMAL:
            y_shift = 0
        elif ls == g.CARD:
            y_shift = 12
        else:
            y_shift = 4

        def draw_node(node, used=set(), left_edge=0, y=0):
            if node in used:
                return used, left_edge
            else:
                used.add(node)
                nw = width_map[node.uid]

                node.move_to(left_edge, y, valign=g.BOTTOM_ROW, align=g.LEFT_ALIGN)
                le = left_edge + node.label_object.left_bracket_width()
                for child in node.get_children(visible=True, similar=True):
                    used, le = draw_node(child, used, le, y + y_shift)
                left_edge += nw
            return used, left_edge

        start = 0

        for tree in self.forest:
            if tree.top:
                if tree.top.node_type == g.CONSTITUENT_NODE:
                    nodes_used, start = draw_node(tree.top, used=set(), left_edge=start)
                    start += prefs.edge_width

