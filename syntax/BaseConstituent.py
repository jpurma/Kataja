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


from kataja.BaseModel import BaseModel, Saved
from syntax.ConfigurableFeature import Feature
# from copy import deepcopy

class BaseConstituent(BaseModel):
    """ BaseConstituent is a default constituent used in syntax.
    It uses getters and setters so that other compatible implementations can be built using the same interface.
    It is a primary datatype, needs to support saving and loading. """

    short_name = "BC"

    def __init__(self, label='', left=None, right=None, source=''):
        """ BaseConstituent is a default constituent used in syntax.
        It is Savable, which means that the actual values are stored in separate object that is easily dumped to file.
        Extending this needs to take account if new fields should also be treated as savable, e.g. put them into
        . and make necessary property and setter.
         """
        super().__init__()
        self.features = {}
        self.sourcestring = source or label
        self.label = label
        self.alias = ''
        self.parts = []
        self.gloss = ''
        self.index = ''
        if left:
            self.left = left
        if right:
            self.right = right

    def __str__(self):
        if self.index:
            return '%s_%s' % (self.label, self.index)
        else:
            return str(self.label)

    def before_set_features(self, value):
        """ If given features include 'label' or 'index', put them to their right place, otherwise update with
        new values. If and empty value is given, set features to empty.
        :param value: dict of features
        """
        if value:
            if "label" in value:
                v = value["label"]
                if isinstance(v, Feature):
                    self.label = v.value
                else:
                    self.label = v
                del value["label"]
            if "index" in value:
                v = value["index"]
                if isinstance(v, Feature):
                    self.index = v.value
                else:
                    self.index = v
                del value["index"]
            return value
        else:
            return {}

    @property
    def left(self):
        """ This is the left child -- to be used only if syntactic theory can make such distinction locally in
        constituent itself. Another option is to do the ordering as a result of derivation, and then you will
        probably need to call some UG -ordering method.
        :return: BaseConstituent instance or None
        """
        if self.parts:
            return self.parts[0]
        else:
            return None

    @left.setter
    def left(self, value):
        """ This is the left child -- to be used only if syntactic theory can make such distinction locally in
        constituent itself. Another option is to do the ordering as a result of derivation, and then you will
        probably need to call some UG -ordering method.
        :param value: BaseConstituent instance or None
        """
        if not self.parts:
            self.poke('parts')
            self.parts = [value]
        elif self.parts[0] != value:
            self.poke('parts')
            self.parts[0] = value

    @property
    def right(self):
        """ This is the right child -- to be used only if syntactic theory can make such distinction locally in
        constituent itself. Another option is to do the ordering as a result of derivation, and then you will
        probably need to call some UG -ordering method.
        :return: BaseConstituent instance or None
        """
        if self.parts and len(self.parts) > 1:
            return self.parts[1]
        else:
            return None

    @right.setter
    def right(self, value):
        """ This is the right child -- to be used only if syntactic theory can make such distinction locally in
        constituent itself. Another option is to do the ordering as a result of derivation, and then you will
        probably need to call some UG -ordering method.
        :param value: BaseConstituent instance or None
        """
        if self.parts:
            if len(self.parts) > 1:
                if self.parts[1] == value:
                    return
                self.poke('parts')
                self.parts[1] = value
            else:
                self.poke('parts')
                self.parts.append(value)
        else:
            self.poke('parts')
            self.parts = [None, value]


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

    def __contains__(self, c):
        if self == c:
            return True
        if self.left:
            if self.left.__contains__(c):
                return True
        if self.right:
            if self.right.__contains__(c):
                return True
        else:
            return False

    def print_tree(self):
        """ Bracket tree representation of the constituent structure. Now it is same as str(self).
        :return: str
        """
        return self.__repr__()

    def get_feature(self, key):
        """ Gets the local feature (within this constituent, not of its children) with key 'key'
        :param key: string for identifying feature type
        :return: feature object
        """
        f = self.features.get(key, None)
        return f

    def has_feature(self, key):
        """ Check the existence of feature within this constituent
        :param key: string for identifying feature type or Feature instance
        :return: bool
        """
        if isinstance(key, Feature):
            return key in list(self.features.values())
        return key in list(self.features.keys())

    def set_feature(self, key, value, family=''):
        """ Set constituent to have a certain feature. If the value given is Feature instance, then it is used,
        otherwise a new Feature is created or existing one modified.
        :param key: str, the key for finding the feature
        :param value:
        :param family: string, optional. If new feature belongs to a certain feature family, e.g. phi features.
        """
        if isinstance(value, Feature):
            self.poke('features')
            self.features[key] = value
        else:
            f = self.features.get(key, None)
            if f:
                f.set(value)
            else:
                f = Feature(key, value)
                self.poke('features')
            self.features[key] = f

    def del_feature(self, key):
        """ Remove feature from a constituent. It's not satisfied, it is just gone.
        :param key: str, the key for finding the feature or for convenience, a feature instance to be removed
        """
        if isinstance(key, Feature):
            key = key.key
        if hasattr(self.features, key):
            self.poke('features')
            del self.features[key]

    def is_leaf(self):
        """ Check if the constituent is leaf constituent (no children) or inside a tree (has children).
        :return: bool
        """
        return not self.parts

    def ordering(self):
        """ Tries to do linearization between two elements according to theory being used.
        Easiest, default case is to just store the parts as a list and return the list in its original order.
        This is difficult to justify theoretically, though.
        :return: len 2 list of ordered nodes, or empty list if cannot be ordered.
        """
        ordering_method = 1
        if ordering_method == 1:
            if len(self.parts) == 2 and self.parts[0] and self.parts[1]:
                return list(self.parts)
            else:
                return []

    def copy(self):
        """ Make a deep copy of constituent. Useful for picking constituents from Lexicon.
        :return: BaseConstituent
        """
        new_parts = []
        for part in self.parts:
            new = part.copy()
            new_parts.append(new)
        nc = self.__class__(self.label)
        nc.sourcestring = self.sourcestring
        nc.alias = self.alias
        nc.gloss = self.gloss
        nc.index = self.index
        for key, value in self.features.items():
            nc.set_feature(key, value)
        nc.parts = new_parts
        return nc

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    features = Saved("features", before_set=before_set_features)
    sourcestring = Saved("sourcestring")
    label = Saved("label")
    alias = Saved("alias")
    parts = Saved("parts")
    gloss = Saved("gloss")
    index = Saved("index")
