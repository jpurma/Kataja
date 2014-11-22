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


from syntax.ConfigurableFeature import Feature
# from copy import deepcopy

class BaseConstituent(object):
    """ BaseConstituent is a default constituent used in syntax.
    It uses getters and setters so that other compatible implementations can be built using the same interface.
    It is a primary datatype, needs to support saving and loading. """
    saved_fields = ['features', 'sourcestring', 'label', 'left', 'right', 'index', 'gloss', 'uid']


    def __init__(self, cid='', left=None, right=None, source='', data=None):
        """ BaseConstituent is a default constituent used in syntax.
        It uses getters and setters so that other compatible constituent implementations can be built using the same interface """
        if not data:
            data = {}
        if data:
            self.features = {}
            self.sourcestring = ''
            self.label = ''
            self.left = None
            self.right = None
            self.index = ''
            self.gloss = ''
            self.uid = id(self)
            self.save_key = self.uid
            self.load(data)
        else:
            self.features = {}
            self.sourcestring = source or cid
            self.label = cid
            self.left = left
            self.right = right
            self.gloss = ''
            self.index = ''
            self.uid = id(self)
            self.save_key = self.uid

    def __str__(self):
        if self.index:
            return '_'.join((self.label, self.index))
        else:
            return self.label


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


    def get_label(self):
        """


        :return:
        """
        return self.label

    def get_index(self):
        """


        :return:
        """
        return self.index

    def set_index(self, index):
        """

        :param index:
        """
        self.index = index

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

    def set_left(self, left):
        """ Derived classes can need more complex implementation
        :param left:
        """
        self.left = left


    def set_right(self, right):
        """ Derived classes can need more complex implementation
        :param right:
        """
        self.right = right


    def get_left(self):
        """


        :return:
        """
        return self.left

    def get_right(self):
        """


        :return:
        """
        return self.right

    def get_features(self):
        """


        :return:
        """
        return self.features

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

    def set_features(self, my_dict):
        """

        :param my_dict:
        """
        for key, feature in my_dict.items():
            if key == 'label':
                self.label = feature.get_value()
            elif key == 'index':
                self.set_index(feature.get_value())
            else:
                self.features[key] = feature

    def set_gloss(self, gloss):
        """

        :param gloss:
        """
        self.gloss = gloss

    def get_gloss(self):
        """


        :return:
        """
        return self.gloss

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

    def load(self, data):
        """
        :param data:
        :return:
        """