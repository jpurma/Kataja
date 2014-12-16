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
import collections

from kataja.singletons import qt_prefs
from kataja.globals import ATTRIBUTE_EDGE, ATTRIBUTE_NODE
from kataja.Node import Node


color_map = {'S': 0, 'order': 1, 'M': 2, 'unknown': 3}


def ordinal(value):
    if isinstance(value, int):
        val = value
    elif isinstance(value, str) and value.isdigit():
        val = int(value)
    else:
        try:
            val = int(value)
        except ValueError:
            return ''
    val_str = str(val)

    if val_str.endswith('1') and not val_str.endswith('11'):
        suffix = 'st'
    elif val_str.endswith('2') and not val_str.endswith('12'):
        suffix = 'nd'
    elif val_str.endswith('3') and not val_str.endswith('13'):
        suffix = 'rd'
    else:
        suffix = 'th'
    return val_str+suffix


class AttributeNode(Node):
    """

    """
    width = 20
    height = 20
    default_edge_type = ATTRIBUTE_EDGE
    saved_fields = ['host']
    node_type = ATTRIBUTE_NODE


    def __init__(self, host, attribute_id, attribute_label='', show_label=False, restoring=False):
        """

        :param host: 
        :param attribute_id: 
        :param attribute_label: 
        :param show_label: 
        :param forest: 
        :param restoring: 
        :raise: 
        """
        Node.__init__(self, syntactic_object=None)
        self.saved.host = host
        self.saved.attribute_label = attribute_label or attribute_id
        self.saved.attribute_id = attribute_id
        self._show_label = show_label
        self.force = 72
        self.help_text = ""
        # if self.attribute_label in color_map:
        # self.color = colors.feature_palette[color_map[self.attribute_label]]
        #else:
        #    self.color = colors.feature
        if not restoring:
            # compute start position -- similar to FeatureNode, but happens on init
            # because host is given
            x, y, z = self.host.current_position
            k = self.attribute_label
            if k in color_map:
                x += color_map[k]
                y += color_map[k]
            else:
                x += random.uniform(-4, 4)
                y += random.uniform(-4, 4)
            self.set_original_position((x, y, z))
            self.update_help_text()
            self.update_identity()
            self.update_label()
            self.update_bounding_rect()
            self.update_visibility()

    @property
    def host(self):
        return self.saved.host

    @host.setter
    def host(self, value):
        self.saved.host = value

    @property
    def attribute_label(self):
        return self.saved.attribute_label

    @attribute_label.setter
    def attribute_label(self, value):
        self.saved.attribute_label = value

    @property
    def attribute_id(self):
        return self.saved.attribute_id

    @attribute_id.setter
    def attribute_id(self, value):
        self.saved.attribute_id = value



    def update_help_text(self):
        if self.attribute_id == 'select_order':
            self.help_text = "'{host}' was Selected {value_ordinal} when constructing the tree."
        elif self.attribute_id == 'merge_order':
            self.help_text = "'{host}' was Merged {value_ordinal} when constructing the tree."


    def set_help_text(self, text):
        self.help_text = text
        self.update_status_tip()

    def update_status_tip(self):
        if self.help_text:
            self.status_tip = self.help_text.format(host=self.host, value=self.value, value_ordinal=ordinal(self.value), label=self.attribute_label)
        else:
            self.status_tip = "Attribute %s for %s" % (self.get_html_for_label(), self.host)

    def get_html_for_label(self):
        """ This should be overridden if there are alternative displays for label 
        :returns : str 
        """

        if self._show_label:
            return '%s:%s' % (self.attribute_label, self.value)
        else:
            return self.value
            # u'%s:%s' % (self.syntactic_object.key, self.syntactic_object.get_value_string())

    @property
    def value(self):
        val = getattr(self.host, self.attribute_id, '')
        if isinstance(val, collections.Callable):
            return val()
        else:
            return val


    def __str__(self):
        """
        :returns : str
        """
        return 'AttributeNode %s' % self.attribute_label


