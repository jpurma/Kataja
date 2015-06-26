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

from kataja.BaseConstituentNode import BaseConstituentNode
from kataja.singletons import prefs
from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode
import kataja.globals as g
from kataja.visualizations.AsymmetricElasticTree import AsymmetricElasticTree


class LinearizedDynamicTree(AsymmetricElasticTree):
    """

    """
    name = 'Linearized Dynamic'

    def __init__(self):
        AsymmetricElasticTree.__init__(self)
        self.forest = None
        self._directed = True

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        if reset:
            self.forest.settings.show_constituent_edges = True
            self.forest.settings.bracket_style = g.NO_BRACKETS
            max_height_steps = max([len(list(self.forest.list_nodes_once(root))) for root in self.forest])
            self.set_vis_data('max_height_steps', max_height_steps)
            self.set_vis_data('height_steps', max_height_steps / 2)


        for node in self.forest.visible_nodes():
            self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        node.fixed_position = None
        node.adjustment = None
        node.update_label()
        node.update_visibility()
        if isinstance(node, BaseConstituentNode):
            if node.is_leaf_node():
                node.dyn_x = False
                node.dyn_y = False
            elif node.is_root_node():
                node.dyn_x = True
                node.dyn_y = False
            else:
                node.dyn_x = True
                node.dyn_y = True
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.dyn_x = True
            node.dyn_y = True


    def reselect(self):
        """ Linearization has  """
        hs = self.get_vis_data('height_steps')
        hs += 1
        if self.get_vis_data('max_heigh_steps') < hs:
            hs = 1
        self.set_vis_data('height_steps', hs)
        self.forest.main.add_message('Set height: %s' % hs)


    def draw(self):
        """


        """
        x = 0
        y = 0
        start_height = self.get_vis_data('height_steps') * prefs.edge_height

        for root in self.forest:
            if not isinstance(root, BaseConstituentNode):
                continue
            # linearized = ctrl.FL.Linearize(root.syntactic_object)
            depths = []
            total_width = 0
            nodelist = []
            for node in self.forest.list_nodes_once(root):
                if node == root:
                    node.dyn_x = True
                    node.dyn_y = False
                    rx, ry, rz = node.current_position
                    node.algo_position = (rx, 0, rz)
                elif node.is_leaf_node():
                    if node:
                        node.dyn_x = False
                        node.dyn_y = False
                        if node.folding_towards:
                            if node.folding_towards not in nodelist:
                                nodelist.append(node.folding_towards)
                        elif not node.is_visible():
                            pass
                        else:
                            nodelist.append(node)
                else:
                    node.dyn_x = True
                    node.dyn_y = True
            total_width = sum([node.width for node in nodelist]) + (10 * len(nodelist))
            offset = total_width / -2
            x = offset
            # measureDepth(rootnode,0)
            # depth=max(depths)
            for node in nodelist:
                nw = node.width
                x += nw / 2
                node.dyn_x = False
                node.dyn_y = False
                node.algo_position = (x, start_height, node.z)
                x += (nw / 2) + 10
