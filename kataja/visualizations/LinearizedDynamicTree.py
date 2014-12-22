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
from kataja.singletons import prefs
from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode
import kataja.globals as g


class LinearizedDynamicTree(BaseVisualization):
    """

    """
    name = 'Linearized Dynamic'

    def __init__(self):
        BaseVisualization.__init__(self)
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
            _max_height_steps = max([len(self.forest.list_nodes_once(root)) for root in self.forest])
            self.forest.vis_data = {'name': self.__class__.name, '_max_height_steps': _max_height_steps,
                                    '_height_steps': _max_height_steps / 2}

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
            node.update_visibility(show_edges=True, scope=0, brackets=self.forest.settings.bracket_style)
            if node.is_leaf_node():
                node.bind_x = True
                node.bind_y = True
            elif node.is_root_node():
                node.bind_x = False
                node.bind_y = True
            else:
                node.bind_x = False
                node.bind_y = False
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.bind_x = False
            node.bind_y = False


    def reselect(self):
        """ Linearization has  """
        self.forest.vis_data['_height_steps'] += 1
        if self.forest.vis_data['_max_height_steps'] < self.forest.vis_data['_height_steps']:
            self.forest.vis_data['_height_steps'] = 1
        self.forest.main.add_message('Set height: %s' % self.forest.vis_data['_height_steps'])


    def draw(self):
        """


        """
        x = 0
        y = 0
        start_height = self.forest.vis_data['_height_steps'] * prefs.edge_height

        for root in self.forest:
            if not isinstance(root, ConstituentNode):
                continue
            # linearized = ctrl.UG.Linearize(root.syntactic_object)
            depths = []
            total_width = 0
            nodelist = []
            for node in self.forest.list_nodes_once(root):
                if node == root:
                    node.bind_x = False
                    node.bind_y = True
                    rx, ry, rz = node.current_position
                    node.computed_position = (rx, 0, rz)
                elif node.is_leaf_node():
                    if node:
                        node.bind_x = True
                        node.bind_y = True
                        if node.folding_towards:
                            if node.folding_towards not in nodelist:
                                nodelist.append(node.folding_towards)
                        elif not node.is_visible():
                            pass
                        else:
                            nodelist.append(node)
                else:
                    node.bind_x = False
                    node.bind_y = False
            total_width = sum([node.width for node in nodelist]) + (10 * len(nodelist))
            offset = total_width / -2
            x = offset
            # measureDepth(rootnode,0)
            # depth=max(depths)
            for node in nodelist:
                nw = node.width
                x += nw / 2
                node.bind_x = True
                node.bind_y = True
                node.computed_position = (x, start_height, node.z)
                x += (nw / 2) + 10
