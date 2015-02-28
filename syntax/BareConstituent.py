# coding=utf-8
""" BareConstituents are version of BaseConstituent that stores features as trees.
This may have significance at some point. They are primary objects and need to support saving and loading. """
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

from syntax.BaseConstituent import BaseConstituent
from syntax.ConfigurableFeature import Feature
# from copy import copy
# from types import UnicodeType

class BareConstituent(BaseConstituent):
    """ BareConstituents are version of BaseConstituent that stores features as trees.
    This may have significance at some point. They are primary objects and need to support saving and loading. """

    def __init__(self, cid='', left=None, right=None, source=''):
        BaseConstituent.__init__(self, cid, left, right, source)
        self.feature_tree = None

    def get_feature(self, key):
        """

        :param key:
        :return:
        """
        f = self.features.get(key, None)
        if f:
            return f.get()
        return None

    def remove_feature(self, value):
        del self.features[value.key]


    def set_feature(self, key, value):
        """ Puts feature to feature dictionary and returns corresponding Feature object
        :param value:
        :param key:
        """
        if not key in self.features:
            if isinstance(value, Feature):
                self.features[key] = value
            else:
                self.features[key] = Feature(key, value)
        else:
            if isinstance(value, Feature):
                self.features[key] = value
            else:
                self.features[key].set(value)
        return self.features[key]

    def merge_to_feature_tree(self, feature):
        """

        :param feature:
        """
        if self.feature_tree:
            merged = Feature()
            merged.left = feature
            merged.right = self.feature_tree
            self.feature_tree = merged
        else:
            self.feature_tree = feature
            # print self.feature_tree

    def __repr__(self):
        if self.is_leaf():
            if self.index:
                return 'Constituent(id=%s, index=%s)' % (self.label, self.index)
            else:
                return 'Constituent(id=%s)' % self.label
        else:
            if self.index:
                ir = '.' + self.index
            else:
                ir = ''
            if self.left:
                lr = repr(self.left)
            else:
                lr = ''
            if self.right:
                rr = repr(self.right)
            else:
                rr = ''
            return "[%s %s %s ]" % (ir, lr, rr)

