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
from kataja.globals import GLOSS_NODE
from kataja.saved.movables.Node import Node
from kataja.uniqueness_generator import next_available_type_id


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

    editable_fields = {
        'label': dict(name='', prefill='gloss', tooltip='translation (optional)')
    }

    default_style = {
        'fancy': {
            'color_key': 'accent5',
            'font_id': g.ITALIC_FONT,
            'font-size': 10,
            'visible': True
        },
        'plain': {
            'color_key': 'accent5',
            'font_id': g.ITALIC_FONT,
            'font-size': 10,
            'visible': True
        }
    }

    default_edge = g.GLOSS_EDGE

    def __init__(self, label='', forest=None):
        Node.__init__(self, forest=forest)
        if not label:
            label = 'gloss'
        self.label = label
        self._gravity = 1.5

    @property
    def hosts(self):
        return self.get_parents(of_type=GLOSS_NODE)

    def if_changed_label(self, value):
        for host in self.hosts:
            host.gloss = value
        self.label = value

    @property
    def text(self):
        return self.label

    @text.setter
    def text(self, value):
        host = self.get_host()
        self.label = value
        if host:
            host.set_gloss = value

    def get_host(self):
        for parent in self.get_parents(of_type=g.CONSTITUENT_NODE):
            return parent

    def update_label(self):
        host = self.get_host()
        if host:
            self.label = host.get_gloss()
        super().update_label()

    def __str__(self):
        return 'gloss "%s"' % self.label
