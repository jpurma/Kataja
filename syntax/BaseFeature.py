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
    role = "Feature"

    editable = {}
    addable = {}

    def __init__(self, name='Feature', value=None, family=''):
        super().__init__()
        self.name = name
        self.value = value
        self.family = family
        self.checks = None  # this has no syntactic effect but storing which feature this
        # feature has checked helps presentation

    def has_value(self, prop):
        return self.value == prop

    @property
    def unassigned(self):
        return self.unvalued()

    @property
    def assigned(self):
        return not self.unvalued()

    def unvalued(self):
        return self.value == 'u' or self.value == '='

    def satisfies(self, feature):
        return feature.unvalued() and feature.name == self.name and not self.unvalued()

    def __eq__(self, other):
        if other:
            return self.value == other.value and self.name == other.name and self.family == \
                                                                             other.family
        return False

    def copy(self):
        return self.__class__(name=self.name, value=self.value, family=self.family)

    def checked(self):
        return self.value.startswith('✓')

    def __str__(self):
        s = []
        signs = ('+', '-', '=', 'u', '✓')
        if len(self.value) == 1 and self.value in signs or len(self.value) == 2 and self.value[1]\
                in signs:
            s.append(self.value + str(self.name))
        elif self.value or self.family:
            s.append(str(self.name))
            s.append(str(self.value))
            if self.family:
                s.append(str(self.family))
        else:
            s.append(str(self.name))
        return ":".join(s)

    def __repr__(self):
        s = [str(self.name)]
        if self.value or self.family:
            s.append(str(self.value))
        if self.family:
            s.append(str(self.family))
        return ":".join(s)

    def __hash__(self):
        return id(self)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    name = SavedField("name")
    value = SavedField("value")
    family = SavedField("family")
    checks = SavedField("checks")

    @staticmethod
    def from_string(s):
        if not s:
            return
        if s[0] in '-=+':
            value = s[0]
            name = s[1:]
        else:
            value = ''
            name = s
        name, foo, family = name.partition(':')  # 'case:acc' -> name = 'case', subtype = 'acc'
        return BaseFeature(name, value, family)
