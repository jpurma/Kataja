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
from kataja.singletons import prefs, ctrl
from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode


class BracketedLinearization(BaseVisualization):
    """

    """
    name = 'Bracketed linearization'

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._hits = {}
        self._max_hits = {}
        self._directed = True


    def prepare(self, forest, loading=False):
        """ This is called when switching to this visualization

        :param forest:
        :param loading:
        :param Forest forest:
        """
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        self.forest.settings.bracket_style(0)
        self.forest.settings.show_constituent_edges = False
        if not loading:
            self.forest.vis_data = {'name': self.__class__.name}
        for node in self.forest.visible_nodes():
            self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        node.locked_to_position = False
        node.reset_adjustment()
        if isinstance(node, ConstituentNode):
            node.update_visibility(brackets=self.forest.settings.bracket_style(), show_edges=False)
            node.bind_x = True
            node.bind_y = True
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.bind_x = False
            node.bind_y = False
        node.update_label()


    def reselect(self):
        """ if there are different modes for one visualization, rotating between different modes is triggered here. """
        if self.forest.settings.bracket_style() == 0:
            self.forest.settings.bracket_style(1)
            ctrl.add_message('major brackets')
        elif self.forest.settings.bracket_style() == 1:
            self.forest.settings.bracket_style(2)
            ctrl.add_message('all brackets')
        elif self.forest.settings.bracket_style() == 2:
            self.forest.settings.bracket_style(0)
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
                left = node.left()
                right = node.right()
                # we want to tile the words after each other and for that reason left and right edges
                # are more useful than the center.
                left_edge += self.forest.bracket_manager.count_bracket_space(node, left=True)
                node.computed_position = (left_edge + node.width / 2, 0, 0)
                if node.is_visible() and (not node.has_empty_label()):
                    left_edge += node.width
                if left:
                    used, left_edge = draw_node(left, used, left_edge)
                if right:
                    used, left_edge = draw_node(right, used, left_edge)
                left_edge += self.forest.bracket_manager.count_bracket_space(node, left=False)
            return used, left_edge

        start = 0
        for root in self.forest:
            if isinstance(root, ConstituentNode):
                used, start = draw_node(root, used=set(), left_edge=start)
                start += prefs.edge_width

