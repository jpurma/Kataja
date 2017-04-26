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

    def __init__(self, label=''):
        Node.__init__(self)
        if not label:
            label = 'gloss'
        self.label = label
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

    def move(self, md):
        if self.locked or self._dragged:
            return super().move(md)
        elif ctrl.forest.gloss is self and ctrl.forest.trees:
            return self.put_to_top_of_trees(), False
        return super().move(md)

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
        for tree in ctrl.forest.trees:
            if not (tree.top is self or tree.numeration):
                found = True
                br = tree.boundingRect()
                ty = br.y() + tree.y() - prefs.edge_height
                tx = br.center().x() + tree.x()
                if tx > x:
                    x = tx
                if ty < y:
                    y = ty
        if not found:
            x = 0
            y = 0
        if self.use_adjustment:
            ax, ay = self.adjustment
            x += ax
            y += ay
        ox, oy = self.current_position
        if ox != x or oy != y:
            self.current_position = x, y
            return True
        else:
            return False
