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


from kataja.singletons import prefs, ctrl
from kataja.visualizations.BaseVisualization import BaseVisualization
import kataja.globals as g


class BracketedLinearization(BaseVisualization):
    """ This should give the commonly used bracket notation, but instead of plain text, the elements are kataja
    nodes and the structure can be edited like any trees. Reselecting BracketedLinearization switches between different
    modes of showing brackets:

    0 - g.NO_BRACKETS - no brackets
    1 - g.MAJOR_BRACKETS - only use brackets for branches that are deeper than 1 node
    2 - g.ALL_BRACKETS - show all brackets

    """
    name = 'Bracketed linearization'

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
        print("brackets -- prepare")
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        if reset:
            self.forest.settings.bracket_style = g.NO_BRACKETS
            self.forest.settings.show_constituent_edges = False
            for node in self.forest.visible_nodes():
                self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)
        if node.node_type == g.CONSTITUENT_NODE:
            node.physics_x = False
            node.physics_y = False
            node.physics_z = False

    def show_edges_for(self, node):
        """ Bracket visualization never shows constituent edges
        :param node: Node
        :return:
        """
        return False

    def reselect(self):
        """ if there are different modes for one visualization, rotating between different modes is triggered here. """
        print("brackets -- reselect")
        if self.forest.settings.bracket_style == g.NO_BRACKETS:
            self.forest.settings.bracket_style = g.MAJOR_BRACKETS
            ctrl.add_message('major brackets')
        elif self.forest.settings.bracket_style == g.MAJOR_BRACKETS:
            self.forest.settings.bracket_style = g.ALL_BRACKETS
            ctrl.add_message('all brackets')
        elif self.forest.settings.bracket_style == g.ALL_BRACKETS:
            self.forest.settings.bracket_style = g.NO_BRACKETS
            ctrl.add_message('no brackets')
        for node in self.forest.visible_nodes():
            self.reset_node(node)

    def draw(self):
        """ We should draw recursively starting from right bottom edge and add layers when needed. """
        # print '** drawing (bracketed linearization) **'
        def draw_node(node, used=set(), left_edge=0):
            """

            :param node:
            :param used:
            :param left_edge:
            :return:
            """
            if node in used:
                return used, left_edge
            else:
                used.add(node)
                # we want to tile the words after each other and
                # for that reason left and right edges
                # are more useful than the center.
                left_edge += self.forest.bracket_manager.count_bracket_space(node, left=True)
                node.move_to(left_edge + node.width / 2, 0, 0)
                if node.is_visible() and (not node.has_empty_label()):
                    left_edge += node.width
                for child in node.get_visible_children():
                    used, left_edge = draw_node(child, used, left_edge)
                left_edge += self.forest.bracket_manager.count_bracket_space(node, left=False)
            return used, left_edge

        start = 0
        for tree in self.forest:
            if tree.top.node_type == g.CONSTITUENT_NODE:
                nodes_used, start = draw_node(tree.top, used=set(), left_edge=start)
                start += prefs.edge_width

