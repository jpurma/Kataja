# coding=utf-8
""" ConfigurableFeature aims to be general implementation for a (syntactic) Feature """
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

from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField


class BaseFeature(SavedObject):
    """ BaseFeatures are the simplest feature implementation.
    BaseFeatures have name, which is used to identify and discriminate between features.
    BaseFeatures can have simple comparable items as values, generally assumed to be booleans or
    strings.
    Distinguishing between assigned and unassigned features is such a common property in
    minimalist grammars that it is supported by BaseFeature. 'assigned' is by default True,
    'unassigned' features have False.
    Family property can be used e.g. to mark phi-features or LF features.
    """

    syntactic_object = True

    visible_in_label = ['fname', 'value', 'family']
    editable_in_label = ['fname', 'value', 'family']
    display_styles = {'fname': {'getter': 'name_with_u_prefix'}}
    editable = {}
    addable = {}

    def __init__(self, name='Feature', value=None, assigned=True, family=''):
        super().__init__()
        self.assigned = assigned
        self.name = name
        self.value = value
        self.assigned = assigned
        self.family = family

    def has_value(self, prop):
        return self.value == prop

    @property
    def unassigned(self):
        return not self.assigned

    def name_with_u_prefix(self):
        print('name with u-prefix called')
        if not self.assigned:
            return 'u' + self.name
        else:
            return self.fname

    def satisfies(self, feature):
        return feature.unassigned and feature.name == self.name and self.assigned

    def __repr__(self):
        return "BaseFeature(fname=%r, value=%r, assigned=%r, family=%r)" % (self.name,
                                                                            self.value,
                                                                            self.assigned,
                                                                            self.family)

    def __str__(self):
        s = []
        if self.family:
            s.append(str(self.family))
        if self.assigned:
            s.append(str(self.name))
        else:
            s.append('u' + str(self.name))
        if self.value:
            s.append(str(self.value))
        return ":".join(s)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    name = SavedField("name")
    value = SavedField("value")
    assigned = SavedField("assigned")
    family = SavedField("family")
