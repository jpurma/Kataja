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
import kataja.globals as g


class AsymmetricElasticTree(BaseVisualization):
    """

    """
    name = 'Dynamic directed net'

    def __init__(self):
        BaseVisualization.__init__(self)
        self._directed = True
        self.forest = None

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        if reset:
            self.forest.settings.bracket_style = g.NO_BRACKETS
            self.forest.settings.show_constituent_edges = True
            self.forest.vis_data = {'name': self.__class__.name}
            for node in self.forest.visible_nodes():
                self.reset_node(node)


    def reset_node(self, node):
        """

        :param node:
        """
        node.locked_to_position = False
        node.reset_adjustment()
        node.update_label()
        node.update_visibility()
        node.bind_y = False
        node.bind_x = False
