# coding=utf-8
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

from kataja.Node import Node
import kataja.globals as g



class PropertyNode(Node):
    """ This is somekind of a microfeature. I don't remember why it exists, but maybe time will tell. """
    width = 20
    height = 20
    default_edge_type = g.PROPERTY_EDGE
    node_type = g.PROPERTY_NODE
    name = ('Property', 'Properties')
    short_name = "PropN"
    display = True
    default_style = {'color': 'accent6', 'font': g.SMALL_CAPS, 'font-size': 10,
                     'edge': g.PROPERTY_EDGE}

    default_edge = {'id': g.PROPERTY_EDGE, 'shape_name': 'linear', 'color': 'accent5', 'pull': .40,
                    'visible': True,'arrowhead_at_start': False, 'arrowhead_at_end': False,
                    'labeled': False}

    def __init__(self, property=None):
        Node.__init__(self, syntactic_object=property)
        # self.color = colors.text
