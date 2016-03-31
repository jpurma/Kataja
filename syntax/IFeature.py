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

from kataja.BaseModel import BaseModel, Saved


class IFeature(BaseModel):
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
    short_name = "I-F"
    visible_in_label = []
    editable_in_label = []
    display_styles = {}
    editable = {}

    def __init__(self, key=None, value=None, values=None, family='', **kw):
        super().__init__(**kw)
        self.key = key
        self.value = value
        self.family = family

    @property
    def value(self):
        """ Value of feature can mean different things on different syntactic models. Get it now.
        """
        raise NotImplementedError("IFeature value(property)")

    @value.setter
    def value(self, value):
        """ Value of feature can mean different things on different syntactic models. Set it now.
        """
        raise NotImplementedError("IFeature value.setter")

    def add(self, prop):
        """ Add new value to existing values
        """
        raise NotImplementedError("IFeature add")

    def remove(self, prop):
        """ Remove value from existing values, if it is in there.
        :param prop: value to remove
        :raise KeyError:
        """
        raise NotImplementedError("IFeature remove")

    def has_value(self, prop):
        """ Return True if the feature has value prop
        :param prop: str, boolean, ITextNode
        :return: bool
        """
        raise NotImplementedError("IFeature has_value")

    def satisfies(self, feature):
        """ Return True if can satisfy a given feature
        :return: bool
        """
        raise NotImplementedError("IFeature satisfies")


    def __repr__(self):
        raise NotImplementedError("IFeature __repr__")

    def __str__(self):
        raise NotImplementedError("IFeature __str__")

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    key = Saved("key")
    values = Saved("values")
    family = Saved("family")

