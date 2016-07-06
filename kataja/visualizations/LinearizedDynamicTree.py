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

from kataja.singletons import prefs
from kataja.globals import NO_BRACKETS, BOTTOM_ROW, CONSTITUENT_NODE
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
            self.forest.settings.bracket_style = NO_BRACKETS
            max_height_steps = max([len(tree.sorted_nodes) / 2 for tree in self.forest])
            self.set_vis_data('max_height_steps', max_height_steps)
            self.set_vis_data('height_steps', max_height_steps / 2)

        for node in self.forest.visible_nodes():
            self.reset_node(node)

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
        hs = self.get_vis_data('height_steps')
        hs += 1
        if self.get_vis_data('max_height_steps') < hs:
            hs = 1
        self.set_vis_data('height_steps', hs)
        self.forest.main.add_message('Set height: %s' % hs)

    def draw(self):
        """


        """
        x = 0
        y = 0
        tree_x = 0

        for tree in self.forest:
            old_x, tree_y = tree.current_position
            tree.move_to(tree_x, tree_y)
            top = tree.top
            if not top:
                continue
            elif top.node_type != CONSTITUENT_NODE:
                continue
            # linearized = ctrl.FL.Linearize(root.syntactic_object)
            depths = []
            nodelist = []
            top.physics_x = True
            top.physics_y = False
            rx, ry = top.current_position
            top.move_to(rx, 0)
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
            total_width = sum([node.width for node in nodelist]) + (10 * len(nodelist))
            tree_x += total_width
            offset = total_width / -2
            x = offset
            # measureDepth(rootnode,0)
            # depth=max(depths)

            if nodelist:
                node_height = max((x.height for x in nodelist))
                start_height = self.get_vis_data('height_steps') * (prefs.edge_height + node_height)

                for node in nodelist:
                    nw = node.width
                    x += nw / 2
                    node.physics_x = False
                    node.physics_y = False
                    node.move_to(x, start_height, valign=BOTTOM_ROW)
                    x += (nw / 2) + 10
