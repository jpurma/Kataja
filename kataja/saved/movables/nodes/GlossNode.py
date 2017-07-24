# coding=utf-8
"""
GlossNode is a Node to display translation or explanation of a constituent
"""
#############################################################################
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
#############################################################################
import kataja.globals as g
from kataja.globals import GLOSS_EDGE, GLOSS_NODE
from kataja.saved.movables.Node import Node
from kataja.uniqueness_generator import next_available_type_id
from kataja.singletons import ctrl, prefs

class GlossNode(Node):
    """
    Node to display translation of a constituent
    """
    __qt_type_id__ = next_available_type_id()
    width = 20
    height = 20
    node_type = GLOSS_NODE
    display_name = ('Gloss', 'Glosses')
    display = True
    is_syntactic = False

    editable = {'label': dict(name='Gloss', prefill='gloss',
                              tooltip='translation (optional)')}

    default_style = {'fancy': {'color_id': 'accent5', 'font_id': g.ITALIC_FONT, 'font-size': 10},
                     'plain': {'color_id': 'accent5', 'font_id': g.ITALIC_FONT, 'font-size': 10}}

    default_edge = g.GLOSS_EDGE

    def __init__(self, label='', static=False):
        Node.__init__(self)
        if not label:
            label = 'gloss'
        self.label = label
        self.static = static
        self._gravity = 1.5

    @property
    def hosts(self):
        """


        :return:
        """
        return self.get_parents(visible=False, of_type=GLOSS_EDGE)

    def if_changed_label(self, value):
        for host in self.hosts:
            host.gloss = value
        self.label = value

    @property
    def text(self):
        return self.label

    @text.setter
    def text(self, value):
        self.label = value

    def __str__(self):
        return 'gloss "%s"' % self.label

    def move(self, other_nodes: list) -> (int, int, bool, bool):
        """ Special behavior for glosses that describe the whole forest
        :return: diff_x, diff_y, normalize, ban_normalization  -- announce how much we moved and if 
        the movement is such that it should be included in normalization calculations. 
        Any node can prevent normalization altogether, as it is harmful in cases where there is 
        a good reason for many free moving feature nodes to flock into one direction.  
        """
        if (not (self.locked or self._dragged)) and ctrl.forest.gloss is self and ctrl.forest.trees:
            self.put_to_top_of_trees()
            return 0, 0, False, False
        else:
            return super().move(other_nodes)

    def on_delete(self):
        if self is ctrl.forest.gloss:
            ctrl.forest.gloss = None
            ctrl.settings.set('gloss_strategy', 'no', level=g.FOREST)
            # this is called just in case that somebody tries to clear ctrl.forest.gloss and we are
            # not there anymore.
            ctrl.forest.remove_from_scene(self, fade_out=False)

    def put_to_top_of_trees(self):
        """ Assume that this is gloss for the whole treeset, move this immediately to top of the
        trees.
        :return: has this moved or not
        """
        x = 0
        y = 100
        found = False
        my_tree = None
        for tree_top in ctrl.forest.trees:
            found = True
            br = tree_top.boundingRect()
            ty = br.y() + tree_top.y() - prefs.edge_height
            tx = br.center().x() + tree_top.x()
            if tx > x:
                x = tx
            if ty < y:
                y = ty
        if not found:
            x = 0
            y = 0
        # We should move the tree containing gloss node, not gloss node itself.
        if not my_tree:
            my_tree = self
        my_tree.static = True
        if my_tree.use_adjustment:
            ax, ay = my_tree.adjustment
            x += ax
            y += ay
        ox, oy = my_tree.current_position
        if ox != x or oy != y:
            my_tree.current_position = x, y
            return True
        else:
            return False
