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

from kataja.BaseModel import BaseModel


class FeatureModel(BaseModel):
    """ Data model for Features
    :param host: the instance which is using this model
    """

    def __init__(self, host=None):
        super().__init__(host)
        self.fkey = ''
        self.values = []
        self.family = ''


class Feature:
    """ Features are primitive comparable and compatible parts. The class supports several kinds of features:
    Features have property "key" which is used to look for certain exact kind of features, e.g. 'number', 'gender', or
    'case'.
    Features can have property "value", which can be any object or list of objects. Feature matching algorithm can, for
    example, say that features with value '-' triggers a search for another feature with same key and non-'-' value.
    By having lists of other Features as values, Features can form feature trees.
    Feature property "family" allows grouping of features of same general type, which has not necessarily syntactic
    meaning. Family property can be used e.g. to mark phi-features or LF features.
    """

    def __init__(self, key=None, value=None, values=None, family=''):
        if not hasattr(self, 'model'):
            self.model = FeatureModel(self)
        if key and not (value or values): # e.g. 'nom:case:deletable'
            values = key.split(':')
            key = values.pop(0)
        elif not key:
            key = "AnonymousFeature"
        self.model.fkey = key
        if values:
            self.model.values = values
        elif value:
            self.model.values = [value]
        else:
            self.model.values = []
        self.model.family = family

    @property
    def save_key(self):
        """ Return the save_key from the model. It is a property from BaseModel.
        :return: str
        """
        return self.model.save_key


    @property
    def label(self):
        """ Label returns the feature key, identifier for which kind of feature this is.
        :return: str or ITextNode
        """
        return self.model.fkey

    @property
    def key(self):
        """ Feature key, identifier for which kind of feature this is.
        :return: str or ITextNode
        """
        return self.model.fkey

    @key.setter
    def key(self, value):
        """ Feature key, identifier for which kind of feature this is.
        :param value: str or ITextNode
        """
        if self.model.touch('fkey', value):
            self.model.fkey = value

    @property
    def value(self):
        """ Value of feature can mean different things on different syntactic models.
        a) At minimum, it can have boolean value, ('+', '-'), or (True, False).
        b) Tertiary: ('+', '-', '=')
        c) Value within a vocabulary: ('-', 'NOM', 'ACC', 'GEN', 'PRT)
        d) other string based value
        e) list of strings so that feature can satisfy several roles
        f) list of Features and strings, where strings are the values that this feature is bringing in, and
            other Features bring recursively their values. (Feature tree)

        when accessed with singular -- "value" -- the returned result is bool, str or ITextNode. This is a helper
          feature for syntactic models that have single value for features.
        :return: bool, str, ITextNode or None
        """
        if self.model.values:
            return self.model.values[0]
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
            other Features bring recursively their values. (Feature tree)

        when set with a singular "value" the value cannot be a list (it will be stored in a list anyways)
        :param value: bool, str, ITextNode
        """
        if self.value != value:
            self.model.poke('values')
            self.model.values = [value]

    @property
    def values(self):
        """ Value of feature can mean different things on different syntactic models.
        a) At minimum, it can have boolean value, ('+', '-'), or (True, False).
        b) Tertiary: ('+', '-', '=')
        c) Value within a vocabulary: ('-', 'NOM', 'ACC', 'GEN', 'PRT)
        d) other string based value
        e) list of strings so that feature can satisfy several roles
        f) list of Features and strings, where strings are the values that this feature is bringing in, and
            other Features bring recursively their values. (Feature tree)

        when accessed with plural "values" the returned result is list of values that can include other Features.
        :return: mixed list of bools, strings, ITextNodes and Features
        """
        return self.model.values

    @values.setter
    def values(self, value):
        """ Value of feature can mean different things on different syntactic models.
        a) At minimum, it can have boolean value, ('+', '-'), or (True, False).
        b) Tertiary: ('+', '-', '=')
        c) Value within a vocabulary: ('-', 'NOM', 'ACC', 'GEN', 'PRT)
        d) other string based value
        e) list of strings so that feature can satisfy several roles
        f) list of Features and strings, where strings are the values that this feature is bringing in, and
            other Features bring recursively their values. (Feature tree)

        when set with a singular "value" the value cannot be a list (it will be stored in a list anyways)
        :param value: bool, str, ITextNode
        """

        if isinstance(value, list):
            if self.model.touch('values', value):
                self.model.values = value
        elif self.model.touch('values', [value]):
            self.model.values = [value]

    @property
    def family(self):
        """ e.g. feature 'number' may belong to family 'phi'. Features don't need to have a family.
        :return: str
        """
        return self.model.family

    @family.setter
    def family(self, value):
        """ e.g. feature 'number' may belong to family 'phi'. Features don't need to have a family.
        :param value: string
        :return: None
        """
        self.model.family = value


    def add(self, prop):
        """ Add new value to existing values
        :param prop: str, boolean, Feature
        """
        if not prop in self.values:
            self.model.poke('values')
            self.values.append(prop)

    def remove(self, prop):
        """ Remove value from existing values, if it is in there.
        :param prop: value to remove
        :raise KeyError:
        """
        if prop in self.values:
            self.model.poke('values')
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
            if isinstance(v, Feature) and v.has_value(prop):
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
        return ":".join([self.key] + self.values)


if __name__ == "__main__":
    import doctest

    doctest.testmod(exclude_empty=True)
