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

    Feature checking and interactions between features are strictly not necessary to be 
    represented in features themselves, but often it helps when inspecting or modifying a structure.
    When creating a syntax model, one can link features by assigning another feature to 'checks' 
    or 'checked_by' -fields.

    Family -field can be used e.g. to additional classification of features, e.g. 
    phi-features, LF features etc.
    """

    syntactic_object = True
    role = "Feature"

    editable = {}
    addable = {}

    def __init__(self, name='Feature', sign='', value=None, family='', checks=None,
                 checked_by=None, strong=False):
        super().__init__()
        self.name = str(name)
        self.value = value
        self.sign = sign
        self.family = family
        # this is not strictly necessary, but being able to inform feature who checked what helps
        # presentation
        self.checks = checks
        self.checked_by = checked_by
        # feature strength was a concept in early minimalism, but I have repurposed it in my version
        self.strong = strong

    def has_value(self, prop):
        return self.value == prop

    def can_satisfy(self):
        return not (self.unvalued() or self.checks or self.checked_by)

    def is_needy(self):
        return self.unvalued()

    def unvalued(self):
        return self.sign == 'u' or self.sign == '=' or self.sign == '-'

    def would_satisfy(self, feature):
        return isinstance(feature,
                          BaseFeature) and feature.is_needy() and feature.name == self.name and \
               self.can_satisfy()

    def check(self, other):
        self.checks = other
        other.checked_by = self

    def __eq__(self, other):
        if other and isinstance(other, BaseFeature):
            return self.value == other.value and self.sign == other.sign and \
                   self.name == other.name and self.family == other.family
        return False

    def copy(self):
        return self.__class__(name=self.name, sign=self.sign, value=self.value,
                              family=self.family, strong=self.strong)

    def __str__(self):
        s = '✓' if self.checks or self.is_satisfied() else ''
        s += self.sign
        fam = ':' + self.family if self.family else ''
        val = ':' + self.value if self.value else ''
        return s + str(self.name) + val + fam

    def __repr__(self):
        c = '✓' if self.checks or self.is_satisfied() else ''
        s = [c + self.sign + str(self.name)]
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
    strong = SavedField("strong")
    sign = SavedField("sign")
    family = SavedField("family")
    checks = SavedField("checks")
    checked_by = SavedField("checked_by")

    @staticmethod
    def from_string(s):
        if not s:
            return
        if s[0] in simple_signs:
            sign = s[0]
            name = s[1:]
        else:
            sign = ''
            name = s
        parts = name.split(':')  # 'case:acc' -> name = 'case', subtype = 'acc'
        name = parts[0]
        value = parts[1] if len(parts) > 1 else ''
        family = parts[2] if len(parts) > 2 else ''
        return BaseFeature(name, sign, value, family)
