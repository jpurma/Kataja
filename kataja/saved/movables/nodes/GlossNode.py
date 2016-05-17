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

color_map = {'tense': 0, 'person': 2, 'number': 4, 'case': 6, 'unknown': 3}


class GlossNode(Node):
    """
    Node to display translation of a constituent
    """
    __qt_type_id__ = next_available_type_id()
    width = 20
    height = 20
    node_type = GLOSS_NODE
    name = ('Gloss', 'Glosses')
    display = True
    is_syntactic = False

    visible_in_label = ['label']
    editable_in_label = ['label']
    display_styles = {}
    editable = {'label': dict(name='Gloss', prefill='gloss',
                              tooltip='translation (optional)')}

    default_style = {'fancy': {'color': 'accent5', 'font': g.ITALIC_FONT, 'font-size': 10},
                     'plain': {'color': 'accent5', 'font': g.ITALIC_FONT, 'font-size': 10}}

    default_edge = {'fancy': {'shape_name': 'cubic',
                              'color_id': 'accent5',
                              'pull': .40,
                              'visible': True,
                              'arrowhead_at_start': False,
                              'arrowhead_at_end': False,
                              'labeled': False},
                    'plain': {'shape_name': 'linear',
                              'color_id': 'accent5',
                              'pull': .40,
                              'visible': True,
                              'arrowhead_at_start': False,
                              'arrowhead_at_end': False,
                              'labeled': False},
                    'id': g.GLOSS_EDGE,
                    'name_pl': 'Gloss edges'
                    }

    def __init__(self, text='', forest=None):
        Node.__init__(self, forest=forest)
        if not text:
            text = 'gloss'
        self.label = text

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

    @property
    def text(self):
        return self.label

    @text.setter
    def text(self, value):
        self.label = value

    def __str__(self):
        return 'gloss: %s' % self.label

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #
