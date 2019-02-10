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

simple_signs = ('+', '-', '=', 'u', '_', '≤')


class BaseFeature(SavedObject):
    """ BaseFeatures are a simple feature implementation.
    BaseFeatures have name, which is used to distinguish between features.
    What is generally understood as value of feature in literature is split into two:
    sign and value.
    Sign is used to signify if the feature should be treated as unvalued,
    valued or as some other manner. Common signs are 'u', '=', or '-' to signify feature being
    unvalued or '+' or '' for feature to have value. (I have parsers that
    have >6 signs, e.g. to mark features that are unvalued, but won't get satisfied by one valued
    feature, or unvalued, but whose host becomes head if satisfied etc.)
    Value is used to express exclusive values that features give for their structures. Different
    semantic cases in finnish are good examples of such values: different cases like 'nom',
    'ill', 'ine', 'gen' are all values for
    feature named 'case'.
    Family -field can be used e.g. to additional classification of features, e.g.
    phi-features, LF features etc.
    Feature checking and interactions between features are not necessary to be
    represented in features themselves, but often it helps when inspecting or modifying a structure.
    When creating a syntax model, one can link features by assigning another feature to 'checks' 
    or 'checked_by' -fields.
    Feature strength is included into base feature properties, and a syntactic model can use it
    if it is found necessary.
    """

    syntactic_object = True
    role = "Feature"
    short_name = "F"
    editable = {}
    addable = {}

    def __init__(self, name='Feature', sign='', value=None, family='', checks=None,
                 checked_by=None, strong=False, parts=None, **kwargs):
        super().__init__()
        self.name = str(name)
        self.value = value
        self.sign = sign
        self.family = family
        # status of being checked, checking something and being in use could be deduced online,
        # based on feature's surroundings, but it is cheaper to store them.
        self.checks = checks
        self.checked_by = checked_by
        self.used = False
        # Feature strength was a concept in early minimalism, but I have repurposed it in my version
        self.strong = strong
        # If there are complex features, they should behave like constituents. Not used.
        self.parts = parts or []
        # It is useful to have a fast route from a feature to lexical element where it is used.
        self.host = None

    def has_value(self, prop):
        return self.value == prop

    def is_inactive(self):
        return self.used

    def can_satisfy(self):
        return not (self.unvalued() or self.checks or self.checked_by)

    def is_satisfied(self):
        return self.unvalued() and self.checked_by

    def is_needy(self):
        return self.unvalued()

    def unvalued(self):
        return self.sign == 'u' or self.sign == '=' or self.sign == '-'

    def would_satisfy(self, feature):
        return (
                isinstance(feature, BaseFeature) and
                feature.is_needy() and
                feature.name == self.name and
                self.can_satisfy()
                )

    def check(self, other):
        self.checks = other
        other.checked_by = self

    def __eq__(self, other):
        if other and isinstance(other, BaseFeature):
            return self.value == other.value and self.sign == other.sign and \
                   self.name == other.name and self.family == other.family
        return False

    def reset(self):
        self.checks = None
        self.checked_by = None
        self.used = False

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
    parts = SavedField("parts")
    host = SavedField("host")
    used = SavedField("used")

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
