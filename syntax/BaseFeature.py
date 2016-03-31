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

from kataja.BaseModel import Saved
from syntax.IFeature import IFeature


class BaseFeature(IFeature):
    """ Features are primitive comparable and compatible parts. The class supports several kinds of features:
    Features have property "key" which is used to look for certain exact kind of features, e.g. 'number', 'gender', or
    'case'.
    Features can have property "value", which can be any object or list of objects. Feature matching algorithm can, for
    example, say that features with value '-' triggers a search for another feature with same key and non-'-' value.
    By having lists of other Features as values, Features can form feature trees.
    Feature property "family" allows grouping of features of same general type, which has not necessarily syntactic
    meaning. Family property can be used e.g. to mark phi-features or LF features.
    """

    syntactic_object = True
    short_name = "F"

    visible_in_label = ['key', 'value', 'family']
    editable_in_label = ['key', 'value', 'family']
    display_styles = {}
    editable = {}
    addable = {}

    def __init__(self, key=None, value=None, values=None, family=''):
        super().__init__()
        if key and not (value or values): # e.g. 'nom:case:deletable'
            values = key.split(':')
            key = values.pop(0)
        elif not key:
            key = "Feature"
        self.key = str(key)
        if values:
            self.values = values
        elif value:
            self.values = [value]
        else:
            self.values = []
        self.family = family


    @property
    def value(self):
        """ Value of feature can mean different things on different syntactic models.
        a) At minimum, it can have boolean value, ('+', '-'), or (True, False).
        b) Tertiary: ('+', '-', '=')
        c) Value within a vocabulary: ('-', 'NOM', 'ACC', 'GEN', 'PRT)
        d) other string based value
        e) list of strings so that feature can satisfy several roles
        f) list of Features and strings, where strings are the values that this feature is bringing in, and
            other Features bring recursively their values. (Feature trees)

        when accessed with singular -- "value" -- the returned result is bool, str or ITextNode. This is a helper
          feature for syntactic models that have single value for features.
        :return: bool, str, ITextNode or None
        """
        if self.values:
            return self.values[0]
        else:
            return None

    @value.setter
    def value(self, value):
        """ Value of feature can mean different things on different syntactic models.
        a) At minimum, it can have boolean value, ('+', '-'), or (True, False).
        b) Tertiary: ('+', '-', '=')
        c) Value within a vocabulary: ('-', 'NOM', 'ACC', 'GEN', 'PRT)
        d) other string based value
        e) list of strings so that feature can satisfy several roles
        f) list of Features and strings, where strings are the values that this feature is bringing in, and
            other Features bring recursively their values. (Feature trees)

        when set with a singular "value" the value cannot be a list (it will be stored in a list anyways)
        :param value: bool, str, ITextNode
        """
        if self.value != value:
            self.poke('values')
            self.values = [value]


    def add(self, prop):
        """ Add new value to existing values
        :param prop: str, boolean, Feature
        """
        if not prop in self.values:
            self.poke('values')
            self.values.append(prop)

    def remove(self, prop):
        """ Remove value from existing values, if it is in there.
        :param prop: value to remove
        :raise KeyError:
        """
        if prop in self.values:
            self.poke('values')
            self.values.remove(prop)
        else:
            raise KeyError

    def has_value(self, prop):
        """ Return True if the prop is found in values either directly or recursively.
        :param prop: str, boolean, ITextNode
        :return: bool
        """
        if prop in self.values:
            return True
        for v in self.values:
            if isinstance(v, BaseFeature) and v.has_value(prop):
                return True
        return False

    def satisfies(self, feature):
        """ Return True if this feature has same key as given feature and the value is not '-'
        :param feature: feature to satisfy
        :return: bool
        """
        return feature.key == self.key and self.value != '-'

    def __repr__(self):
        return "Feature(key=%s, values=%s, family=%s)" % (self.key, repr(self.values), self.family)

    def __str__(self):
        return ":".join([str(self.key)] + [str(x) for x in self.values])

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    key = Saved("key")
    values = Saved("values")
    family = Saved("family")


if __name__ == "__main__":
    import doctest

    doctest.testmod(exclude_empty=True)
