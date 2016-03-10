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
from kataja.Node import Node
from kataja.globals import GLOSS_EDGE, GLOSS_NODE

color_map = {'tense': 0, 'person': 2, 'number': 4, 'case': 6, 'unknown': 3}


class GlossNode(Node):
    """
    Node to display translation of a constituent
    """
    width = 20
    height = 20
    node_type = GLOSS_NODE
    name = ('Gloss', 'Glosses')
    short_name = "GNode"
    display = True

    viewable = {'label': {'order': 3}}
    editable = {'label': dict(name='Gloss', order=3, prefill='gloss',
                              tooltip='translation (optional)')}

    default_style = {'color': 'accent5', 'font': g.ITALIC_FONT, 'font-size': 10}

    default_edge = {'id': g.GLOSS_EDGE, 'shape_name': 'cubic', 'color': 'accent5', 'pull': .40,
                    'visible': True, 'arrowhead_at_start': False, 'arrowhead_at_end': False,
                    'labeled': False, 'name_pl': 'Gloss edges'}

    def __init__(self, text=''):
        Node.__init__(self)
        self._label = text or 'gloss'

    @property
    def hosts(self):
        """


        :return:
        """
        return self.get_parents(edge_type=GLOSS_EDGE)

    def if_changed_label(self, value):
        for host in self.hosts:
            host.gloss = value
        self.label = value
        self._inode_changed = True

    @property
    def label(self):
        for host in self.hosts:
            if host.gloss:
                return host.gloss
        return self._label

    @label.setter
    def label(self, value):
        for host in self.hosts:
            host.gloss = value
        self._label = value
        self._inode_changed = True

    @property
    def text(self):
        return self.label

    @text.setter
    def text(self, value):
        self._label = value
        self._inode_changed = True

    def __str__(self):
        return 'gloss: %s' % self.text

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #
