# coding=utf-8
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
from syntax.utils import to_unicode
# from copy import deepcopy

class BaseConstituent(object):
    """ BaseConstituent is a default constituent used in syntax.
    It uses getters and setters so that other compatible constituent implementations can be built using the same interface. It is a primary datatype, needs to support saving and loading. """
    saved_fields = ['features', 'sourcestring', 'label', 'left', 'right', 'index', 'gloss', 'uid']


    def __init__(self, cid=u'', left=None, right=None, source='', data=None):
        """ BaseConstituent is a default constituent used in syntax.
        It uses getters and setters so that other compatible constituent implementations can be built using the same interface """
        if not data:
            data = {}
        if data:
            self.features = {}
            self.sourcestring = ''
            self.label = u''
            self.left = None
            self.right = None
            self.index = u''
            self.gloss = u''
            self.uid = id(self)
            self.save_key = self.uid
            self.load(data)
        else:
            self.features = {}
            self.sourcestring = source or cid
            self.label = to_unicode(cid)
            self.left = left
            self.right = right
            self.gloss = u''
            self.index = u''
            self.uid = id(self)
            self.save_key = self.uid

    def __str__(self):
        if self.index:
            return '_'.join((self.label.encode('utf-8', 'ignore'), self.index.encode('utf-8', 'ignore')))
        else:
            return self.label.encode('utf-8', 'ignore')


    def __unicode__(self):
        if self.index:
            return u'_'.join((self.label, self.index))
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
                return u"[.%s %s %s ]" % (self.index, self.left, self.right)
            else:
                return u"[ %s %s ]" % (self.left, self.right)


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

    def get_label(self):
        return self.label

    def get_index(self):
        return self.index

    def set_index(self, index):
        self.index = to_unicode(index)

    def get_feature(self, key):
        f = self.features.get(key, None)
        if f:
            return f.get()
        return None

    def has_feature(self, key):
        if isinstance(key, Feature):
            return key in self.features.values()
        return key in self.features.keys()

    def set_left(self, left):
        """ Derived classes can need more complex implementation """
        self.left = left


    def set_right(self, right):
        """ Derived classes can need more complex implementation """
        self.right = right


    def get_left(self):
        return self.left

    def get_right(self):
        return self.right

    def get_features(self):
        return self.features

    def set_feature(self, key, value):
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
        for key, feature in my_dict.items():
            if key == 'label':
                self.label = feature.get_value()
            elif key == 'index':
                self.set_index(feature.get_value())
            else:
                self.features[key] = feature

    def set_gloss(self, gloss):
        self.gloss = gloss

    def get_gloss(self):
        return self.gloss

    def del_feature(self, key):
        if isinstance(key, Feature):
            key = key.key
        if hasattr(self.features, key):
            del self.features[key]

    def is_leaf(self):
        return not (self.left or self.right)

    def copy(self):
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
