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

import random

from kataja.globals import FEATURE_EDGE, FEATURE_NODE
from kataja.Node import Node
from kataja.singletons import ctrl


color_map = {'tense': 0, 'order': 1, 'person': 2, 'number': 4, 'case': 6, 'unknown': 3}


class FeatureNode(Node):
    """
    Node to express a feature of a constituent
    """
    width = 20
    height = 20
    default_edge_type = FEATURE_EDGE
    node_type = FEATURE_NODE

    def __init__(self, feature=None):
        Node.__init__(self, syntactic_object=feature)

    def after_init(self):
        """ Call after putting values in place
        :return:
        """
        self.update_label()
        self.update_bounding_rect()
        self.update_visibility()
        ctrl.forest.store(self)

    # implement color() to map one of the d['rainbow_%'] colors here. Or if bw mode is on, then something else.

    def compute_start_position(self, host):
        """ Makes features start at somewhat predictable position, if they are of common kinds of features.
        If not, then some random noise is added to prevent features sticking together
        :param host:
        """
        x, y, z = host.current_position
        k = self.syntactic_object.key
        if k in color_map:
            x += color_map[k]
            y += color_map[k]
        else:
            x += random.uniform(-4, 4)
            y += random.uniform(-4, 4)
        self.set_original_position((x, y, z))

    def update_label(self):
        """

        :return:
        """
        Node.update_label(self)
        self._label_complex.show()
        print(self.opacity())


    def get_html_for_label(self):
        """ This should be overridden if there are alternative displays for label """
        f = self.syntactic_object
        if not f:
            return 'orphaned feature node'
        if f.key in color_map:
            return str(f.get_value_string())
        else:
            return str(f)
            # u'%s:%s' % (self.syntactic_object.key, self.syntactic_object.get_value_string())

    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        painter.setPen(self.contextual_color())
        #if ctrl.pressed == self or self._hovering or ctrl.is_selected(self):
        #    painter.drawRoundedRect(self.inner_rect, 5, 5)


    def __str__(self):
        return 'feature %s' % self.syntactic_object