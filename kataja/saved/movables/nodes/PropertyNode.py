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

import kataja.globals as g
from kataja.saved.movables.Node import Node
from kataja.uniqueness_generator import next_available_type_id


class PropertyNode(Node):
    """ This is somekind of a microfeature. I don't remember why it exists, but maybe time will tell. """
    __qt_type_id__ = next_available_type_id()
    width = 20
    height = 20
    node_type = g.PROPERTY_NODE
    display_name = ('Property', 'Properties')
    display = False
    default_style = {'fancy': {'color': 'accent6', 'font': g.SMALL_CAPS, 'font-size': 10},
                     'plain': {'color': 'accent6', 'font': g.SMALL_CAPS, 'font-size': 10}}

    default_edge = g.PROPERTY_EDGE

    def __init__(self, forest=None, property=None):
        Node.__init__(self, forest=forest, syntactic_object=property)
        # self.color = colors.text
