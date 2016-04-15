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


from kataja.Saved import SavedField
from syntax.IConstituent import IConstituent
from syntax.BaseFeature import BaseFeature
# from copy import deepcopy

class BaseConstituent(IConstituent):
    """ BaseConstituent is a default constituent used in syntax.
    It uses getters and setters so that other compatible implementations can be built using the same interface.
    It is a primary datatype, needs to support saving and loading. """

    # info for kataja engine
    syntactic_object = True
    short_name = "C"

    visible_in_label = ['label']
    editable_in_label = ['label']
    display_styles = {}
    editable = {}
    addable = {'features': {'condition': 'can_add_feature', 'add': 'add_feature', 'order': 20}
               }
    # 'parts': {'check_before': 'can_add_part', 'add': 'add_part', 'order': 10},

    def __init__(self, label='', parts=None, save_key='', features=None, head=None, **kw):
        """ BaseConstituent is a default constituent used in syntax.
        It is Savable, which means that the actual values are stored in separate object that is easily dumped to file.
        Extending this needs to take account if new elements should also be treated as savable, e.g. put them into
        . and make necessary property and setter.
         """
        super().__init__(**kw)
        self.label = label
        self.head = head
        self.features = features or {}
        self.parts = parts or []

    def __str__(self):
        return str(self.label)

    def __repr__(self):
        if self.is_leaf():
            return 'Constituent(id=%s)' % self.label
        else:
            return "[ %s ]" % (' '.join((x.__repr__() for x in self.parts)))

    def __contains__(self, c):
        if self == c:
            return True
        for part in self.parts:
            if c in part:
                return True
        else:
            return False

    def print_tree(self):
        """ Bracket trees representation of the constituent structure. Now it is same as str(self).
        :return: str
        """
        return self.__repr__()

    def can_add_part(self, **kw):
        """
        :param kw:
        :return:
        """
        return True

    def add_part(self, new_part):
        """ Add constitutive part to this constituent (append to parts)
        :param new_part:
        """
        self.poke('parts')
        self.parts.append(new_part)

    def insert_part(self, new_part, index=0):
        """ Insert constitutive part to front of the parts list. Usefulness
        depends on the linearization method.
        :param new_part:
        :param index:
        :return:
        """
        self.poke('parts')
        self.parts.insert(index, new_part)

    def remove_part(self, part):
        """ Remove constitutive part
        :param part:
        """
        self.poke('parts')
        self.parts.remove(part)

    def replace_part(self, old_part, new_part):
        """
        :param old_part:
        :param new_part:
        :return:
        """
        if old_part in self.parts:
            i = self.parts.index(old_part)
            self.poke('parts')
            self.parts[i] = new_part
        else:
            raise IndexError

    def set_head(self, head):
        """

        :param head:
        :return:
        """
        self.head = head

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
        if isinstance(key, BaseFeature):
            return key in list(self.features.values())
        return key in list(self.features.keys())

    def add_feature(self, feature):
        """ Add an existing Feature object to this constituent.
        :param feature:
        :return:
        """
        if isinstance(feature, BaseFeature):
            self.poke('features')
            self.features[feature.key] = feature
        else:
            raise TypeError

    def set_feature(self, key, value, family=''):
        """ Set constituent to have a certain feature. If the value given is Feature instance, then it is used,
        otherwise a new Feature is created or existing one modified.
        :param key: str, the key for finding the feature
        :param value:
        :param family: string, optional. If new feature belongs to a certain feature family, e.g. phi features.
        """
        if isinstance(value, BaseFeature):
            self.poke('features')
            self.features[key] = value
        else:
            f = self.features.get(key, None)
            if f:
                f.set(value)
            else:
                f = BaseFeature(key, value)
                self.poke('features')
            self.features[key] = f

    def remove_feature(self, key):
        """ Remove feature from a constituent. It's not satisfied, it is just gone.
        :param key: str, the key for finding the feature or for convenience, a feature instance to be removed
        """
        if isinstance(key, BaseFeature):
            key = key.key
        if hasattr(self.features, key):
            self.poke('features')
            del self.features[key]

    def is_leaf(self):
        """ Check if the constituent is leaf constituent (no children) or inside a trees (has children).
        :return: bool
        """
        return not self.parts

    def ordered_parts(self):
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
        new_features = self.features.copy()
        nc = self.__class__(label=self.label,
                            parts=new_parts,
                            features=new_features,
                            head=self.head)
        return nc

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    features = SavedField("features")
    sourcestring = SavedField("sourcestring")
    label = SavedField("label")
    parts = SavedField("parts")
    head = SavedField("head")
