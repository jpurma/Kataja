# coding=utf-8
""" BaseConstituent is a default constituent used in syntax.
It uses getters and setters so that other compatible implementations can be built using the same interface.
It is a primary datatype, needs to support saving and loading. """
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


from kataja.Saved import Savable
from syntax.ConfigurableFeature import Feature
# from copy import deepcopy

class BaseConstituent(Savable):
    """ BaseConstituent is a default constituent used in syntax.
    It uses getters and setters so that other compatible implementations can be built using the same interface.
    It is a primary datatype, needs to support saving and loading. """


    def __init__(self, cid='', left=None, right=None, source='', data=None):
        """ BaseConstituent is a default constituent used in syntax.
        It is Savable, which means that the actual values are stored in separate object that is easily dumped to file.
        Extending this needs to take account if new fields should also be treated as savable, e.g. put them into
        .saved. and make necessary property and setter.
         """
        Savable.__init__(self, restore=data)
        if not data:
            self.saved.features = {}
            self.saved.sourcestring = source or cid
            self.saved.label = cid
            self.saved.alias = ''
            self.saved.left = left
            self.saved.right = right
            self.saved.gloss = ''
            self.saved.index = ''

    def __str__(self):
        if self.index:
            return '_'.join((self.label, self.index))
        else:
            return self.label

    @property
    def features(self):
        return self.saved.features

    @features.setter
    def features(self, value):
        """
        :param value:
        """
        for key, feature in value.items():
            if key == 'label':
                self.label = feature.get_value()
            elif key == 'index':
                self.index = feature.get_value()
            else:
                self.saved.features[key] = feature

    @property
    def sourcestring(self):
        return self.saved.sourcestring

    @sourcestring.setter
    def sourcestring(self, value):
        self.saved.sourcestring = value

    @property
    def label(self):
        return self.saved.label

    @label.setter
    def label(self, value):
        self.saved.label = value

    @property
    def alias(self):
        return self.saved.alias

    @alias.setter
    def alias(self, value):
        self.saved.alias = value

    @property
    def left(self):
        return self.saved.left

    @left.setter
    def left(self, value):
        self.saved.left = value

    @property
    def right(self):
        return self.saved.right

    @right.setter
    def right(self, value):
        self.saved.right = value

    @property
    def gloss(self):
        return self.saved.gloss

    @gloss.setter
    def gloss(self, value):
        self.saved.gloss = value

    @property
    def index(self):
        return self.saved.index

    @index.setter
    def index(self, value):
        self.saved.index = value


    def __repr__(self):
        if self.is_leaf():
            if self.index:
                return 'Constituent(id=%s, index=%s)' % (self.label, self.index)
            else:
                return 'Constituent(id=%s)' % self.label
        else:
            if self.index:
                return "[.%s %s %s ]" % (self.index, self.left, self.right)
            else:
                return "[ %s %s ]" % (self.left, self.right)


    def __contains__(self, C):
        if self == C:
            return True
        if self.left:
            if self.left.__contains__(C):
                return True
        if self.right:
            if self.right.__contains__(C):
                return True
        else:
            return False


    def print_tree(self):
        if self.is_leaf():
            if self.index:
                return '%s_%s' % (self.label, self.index)
            else:
                return self.label
        else:
            if self.left:
                l = self.left.print_tree()
            else:
                l = '*0*'
            if self.right:
                r = self.right.print_tree()
            else:
                r = '*0*'
            if self.index:
                i = '.%s' % self.index
            else:
                i = ''
            return "[%s %s %s ]" % (i, l, r)



    def get_feature(self, key):
        """

        :param key:
        :return:
        """
        f = self.features.get(key, None)
        if f:
            return f.get()
        return None

    def has_feature(self, key):
        """

        :param key:
        :return:
        """
        if isinstance(key, Feature):
            return key in list(self.features.values())
        return key in list(self.features.keys())


    def set_feature(self, key, value):
        """

        :param key:
        :param value:
        """
        if isinstance(value, Feature):
            self.features[key] = value
        else:
            f = self.features.get(key, None)
            if f:
                f.set(value)
            else:
                f = Feature(key, value)
            self.features[key] = f


    def del_feature(self, key):
        """

        :param key:
        """
        if isinstance(key, Feature):
            key = key.key
        if hasattr(self.features, key):
            del self.features[key]

    def is_leaf(self):
        """


        :return:
        """
        return not (self.left or self.right)

    def copy(self):
        """


        :return:
        """
        if self.left:
            left = self.left.copy()
        else:
            left = None
        if self.right:
            right = self.right.copy()
        else:
            right = None
        new = self.__class__(self.label, left, right)
        for key, value in self.features.items():
            new.set_feature(key, value)
        return new

