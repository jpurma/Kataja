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

from kataja.Controller import qt_prefs
from kataja.globals import ATTRIBUTE_EDGE, ATTRIBUTE_NODE
from kataja.Node import Node
from utils import to_unicode


color_map = {'S': 0, 'order': 1, 'M': 2, 'unknown': 3}


class AttributeNode(Node):
    """

    """
    width = 20
    height = 20
    default_edge_type = ATTRIBUTE_EDGE
    saved_fields = ['host', 'label_font', '_color']
    saved_fields = list(set(Node.saved_fields + saved_fields))
    node_type = ATTRIBUTE_NODE


    def __init__(self, host, attribute_id, attribute_label='', show_label=False, forest=None, restoring=False):
        """

        :param host: 
        :param attribute_id: 
        :param attribute_label: 
        :param show_label: 
        :param forest: 
        :param restoring: 
        :raise: 
        """
        if not forest:
            raise
        Node.__init__(self, syntactic_object=None, forest=forest)
        self.level = 2
        self.save_key = 'AN%s' % id(self)
        self.host = host
        self.attribute_label = attribute_label or attribute_id
        self.attribute_id = attribute_id
        self._show_label = show_label
        self.label_font = qt_prefs.sc_font
        # if self.attribute_label in color_map:
        #    self.color = colors.feature_palette[color_map[self.attribute_label]]
        #else:
        #    self.color = colors.feature
        if not restoring:
            # compute start position -- similar to FeatureNode, but happens on init
            # because host is given
            x, y, z = self.host.get_current_position()
            k = self.attribute_label
            if k in color_map:
                x += color_map[k]
                y += color_map[k]
            else:
                x += random.uniform(-4, 4)
                y += random.uniform(-4, 4)
            self.set_original_position((x, y, z))
            self.update_identity()
            self.update_label()
            self.boundingRect(update=True)
            self.update_visibility()


    def get_text_for_label(self):
        """ This should be overridden if there are alternative displays for label 
        :rtype : unicode
        """
        val = getattr(self.host, self.attribute_id, u'')
        if callable(val):
            val = val()
        if self._show_label:
            return u'%s:%s' % (self.attribute_label, val)
        else:
            return to_unicode(val)
            # u'%s:%s' % (self.syntactic_object.key, self.syntactic_object.get_value_string())

    def __str__(self):
        """
        :rtype : str
        """
        return 'AttributeNode %s' % self.attribute_label

    def __unicode__(self):
        """
        :rtype : unicode
        """
        return u'AttributeNode %s' % self.attribute_label


