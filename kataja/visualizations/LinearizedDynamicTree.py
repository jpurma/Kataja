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

from kataja.singletons import prefs, log
from kataja.globals import NORMAL, BOTTOM_ROW, CONSTITUENT_NODE
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
            max_height_steps = max([len(tree.sorted_nodes) / 2 for tree in self.forest])
            self.set_data('max_height_steps', max_height_steps)
            self.set_data('height_steps', max_height_steps / 2)
            self.reset_nodes()
        self.validate_node_shapes()

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)
        if node.node_type == CONSTITUENT_NODE:
            if node.is_leaf():
                node.physics_x = False
                node.physics_y = False
            elif node.is_top_node():
                node.physics_x = True
                node.physics_y = False
        else:
            node.physics_x = True
            node.physics_y = True

    def reselect(self):
        """ Linearization has  """
        hs = self.get_data('height_steps')
        hs += 1
        if self.get_data('max_height_steps') < hs:
            hs = 1
        self.set_data('height_steps', hs)
        log.info('Set height: %s' % hs)

    def draw_tree(self, tree):
        """


        """

        top = tree.top
        if top.node_type != CONSTITUENT_NODE:
            return
        # linearized = ctrl.FL.Linearize(root.syntactic_object)
        nodelist = []
        top.physics_x = True
        top.physics_y = False
        for node in tree.sorted_nodes[1:]:
            if node.is_leaf() and node.node_type == CONSTITUENT_NODE:
                if node:
                    node.physics_x = False
                    node.physics_y = False
                    if node.folding_towards:
                        if node.folding_towards not in nodelist:
                            nodelist.append(node.folding_towards)
                    elif not node.is_visible():
                        pass
                    else:
                        nodelist.append(node)

            else:
                node.physics_x = True
                node.physics_y = True
        x = 0
        if nodelist:
            node_height = max((x.height for x in nodelist))
            start_height = self.get_data('height_steps') * (prefs.edge_height + node_height)

            for node in nodelist:
                nw = node.width
                x += nw / 2
                node.physics_x = False
                node.physics_y = False
                node.move_to(x, start_height, valign=BOTTOM_ROW)
                x += (nw / 2) + 10
