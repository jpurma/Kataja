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

import collections
import random

import kataja.globals as g
from kataja.SavedField import SavedField
from kataja.globals import ATTRIBUTE_NODE
from kataja.saved.movables.Node import Node
from kataja.uniqueness_generator import next_available_type_id

color_map = {'S': 0, 'order': 1, 'M': 2, 'unknown': 3}


def ordinal(value):
    """

    :param value:
    :return:
    """
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
    return val_str + suffix


class AttributeNode(Node):
    """

    """
    width = 20
    height = 20
    node_type = ATTRIBUTE_NODE
    display_name = ('Attribute', 'Attributes')
    display = False
    __qt_type_id__ = next_available_type_id()


    default_style = {'fancy': {'color_id': 'accent4', 'font_id': g.SMALL_CAPS, 'font-size': 10},
                     'plain': {'color_id': 'accent4', 'font_id': g.SMALL_CAPS, 'font-size': 10}}

    default_edge = g.ATTRIBUTE_EDGE

    def __init__(self, forest=None, host=None, attribute_id=None, attribute_label='',
                 show_label=False, restoring=False):
        """

        :param host: 
        :param attribute_id: 
        :param attribute_label: 
        :param show_label: 
        :param forest: 
        :param restoring: 
        :raise: 
        """
        self.help_text = ""
        Node.__init__(self, forest=forest, syntactic_object=None)
        self.host = host
        self.attribute_label = attribute_label or attribute_id
        self.attribute_id = attribute_id
        self._show_label = show_label
        # if self.attribute_label in color_map:
        # self.color = colors.feature_palette[color_map[self.attribute_label]]
        # else:
        # self.color = colors.feature
        if not restoring:
            # compute start position -- similar to FeatureNode, but happens on init
            # because host is given
            x, y = self.host.current_position
            k = self.attribute_label
            if k in color_map:
                x += color_map[k]
                y += color_map[k]
            else:
                x += random.uniform(-4, 4)
                y += random.uniform(-4, 4)
            self.set_original_position((x, y))
            self.update_help_text()
            self.update_label()
            self.do_size_update = True
            self.update_visibility()

    def update_help_text(self):
        """


        """
        if self.attribute_id == 'select_order':
            self.help_text = "'{host}' was Selected {value_ordinal} when constructing the trees."
        elif self.attribute_id == 'merge_order':
            self.help_text = "'{host}' was Merged {value_ordinal} when constructing the trees."

    def set_help_text(self, text):
        """

        :param text:
        """
        self.help_text = text
        self.update_status_tip()

    def update_status_tip(self):
        """


        """
        if self.help_text:
            self.status_tip = self.help_text.format(host=self.host, value=self.value, value_ordinal=ordinal(self.value),
                                                    label=self.attribute_label)
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
        """


        :return:
        """
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

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    host = SavedField("host")
    attribute_label = SavedField("attribute_label")
    attribute_id = SavedField("attribute_id")

