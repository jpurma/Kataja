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

from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.ConstituentNode import ConstituentNode
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode


class SymmetricElasticTree(BaseVisualization):
    """

    """
    name = 'Dynamic nondirected net'

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._directed = False

    def prepare(self, forest, loading=False):
        """

        :param forest:
        :param loading:
        """
        self.forest = forest
        self.forest.settings.bracket_style(0)
        self.forest.settings.show_constituent_edges = True
        if not loading:
            self.forest.vis_data = {'name': self.__class__.name}
        for node in self.forest.visible_nodes():
            self.reset_node(node)


    def reset_node(self, node):
        """

        :param node:
        """
        node.update_label()
        if isinstance(node, ConstituentNode):
            node.update_visibility(show_edges=True, scope=0, brackets=self.forest.settings.bracket_style())
            node.bind_y = False
            node.bind_x = False
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.bind_x = False
            node.bind_y = False
