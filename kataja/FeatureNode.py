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
import sys

from kataja.Controller import qt_prefs
from kataja.globals import FEATURE_EDGE, FEATURE_NODE
from kataja.Node import Node


color_map = {'tense': 0, 'order': 1, 'person': 2, 'number': 4, 'case': 6, 'unknown': 3}


class FeatureNode(Node):
    """

    """
    width = 20
    height = 20
    default_edge_type = FEATURE_EDGE
    saved_fields = ['label_font']
    saved_fields = list(set(Node.saved_fields + saved_fields))
    node_type = FEATURE_NODE


    def __init__(self, feature=None, forest=None, restoring=False):
        if not forest:
            raise Exception("Forest is missing")
        Node.__init__(self, syntactic_object=feature, forest=forest)
        self.level = 2
        self.save_key = 'FN%s' % self.syntactic_object.uid
        self.label_font = qt_prefs.sc_font
        # if feature.get_value() in color_map:
        # self.color = colors.feature_palette[color_map[feature.get_value()]]
        # else:
        #    self.color = colors.feature
        if not restoring:
            self.update_identity()
            self.update_label()
            self.boundingRect(update=True)
            self.update_visibility()


    # implement color() to map one of the d['rainbow_%'] colors here. Or if bw mode is on, then something else.

    def compute_start_position(self, host):
        """ Makes features start at somewhat predictable position, if they are of common kinds of features. If not, then some random noise is added to prevent features sticking together
        :param host:
        """
        x, y, z = host.get_current_position()
        k = self.syntactic_object.key
        if k in color_map:
            x += color_map[k]
            y += color_map[k]
        else:
            x += random.uniform(-4, 4)
            y += random.uniform(-4, 4)
        self.set_original_position((x, y, z))

    def get_text_for_label(self):
        """ This should be overridden if there are alternative displays for label """
        f = self.syntactic_object
        if f.key in color_map:
            return str(f.get_value_string())
        else:
            return str(f)
            # u'%s:%s' % (self.syntactic_object.key, self.syntactic_object.get_value_string())

    def __str__(self):
        return 'feature %s' % self.syntactic_object

    def __unicode__(self):
        return 'feature %s' % self.syntactic_object


