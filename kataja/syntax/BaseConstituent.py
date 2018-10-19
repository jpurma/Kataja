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


from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from kataja.syntax.IConstituent import IConstituent
from kataja.syntax.BaseFeature import BaseFeature


class BaseConstituent(SavedObject, IConstituent):
    """ BaseConstituent is a default constituent used in syntax.
    IConstituent inherited here gives the abstract blueprint of what methods Constituents should
    implement -- it is an optional aid to validate that your Constituent is about ok.
    Constituents need to inherit SavedObject and use SavedFields for saving permanent data,
    otherwise structures won't get saved properly, undo and snapshots won't work.

    Object inheritance is not used to recognise what are constituent implementations and what
    are not, instead classes have attribute 'role' that tells what part they play in e.g. plugin.
    So your implementation of Constituent needs at least to have role = "Constituent", but not
    necessarily inherit BaseConstituent or IConstituent.

    However, often it is easisest just to inherit BaseConstituent and make minor modifications
    to it.
    """

    # info for kataja engine
    syntactic_object = True
    role = "Constituent"

    editable = {}
    addable = {'features': {'condition': 'can_add_feature', 'add': 'add_feature', 'order': 20}
               }
    # 'parts': {'check_before': 'can_add_part', 'add': 'add_part', 'order': 10},

    def __init__(self, label='', parts=None, uid='', features=None, lexical_heads=None, **kw):
        """ BaseConstituent is a default constituent used in syntax.
        It is Savable, which means that the actual values are stored in separate object that is
        easily dumped to file. Extending this needs to take account if new elements should also
        be treated as savable, e.g. put them into. and make necessary property and setter.
         """
        SavedObject.__init__(self, **kw)
        self.label = label
        self.features = features or []
        self.parts = parts or []
        self.inherited_features = features or []
        self.checked_features = []
        self.lexical_heads = list(lexical_heads) if lexical_heads else [self]
        for feature in self.features:
            feature.host = self

    def __str__(self):
        return str(self.label)

    def __repr__(self):
        if self.is_leaf():
            return 'Constituent(label=%s)' % self.label
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

    def get_features(self):
        """ Getter for features, redundant for BaseConstituent (you could use c.features ) but it
        is better to use this consistently for compatibility with other implementations for
        constituent.
        :return:
        """
        return self.features

    def get_parts(self):
        """ Getter for parts, redundant for BaseConstituent (you could use c.parts ) but it
        is better to use this consistently for compatibility with other implementations for
        constituent.
        :return:
        """
        return self.parts

    def sorted_parts(self):
        return self.parts

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

    @property
    def is_ordered(self):
        return False

    def get_feature(self, key):
        """ Gets the first local feature (within this constituent, not of its children) with key
        'key'
        :param key: string for identifying feature type
        :return: feature object
        """
        for f in self.features:
            if f.name == key:
                return f

    def has_feature(self, key):
        """ Check the existence of feature within this constituent
        :param key: string for identifying feature type or Feature instance
        :return: bool
        """
        if isinstance(key, BaseFeature):
            return key in self.features
        else:
            return bool(self.get_feature(key))

    def add_feature(self, feature):
        """ Add an existing Feature object to this constituent.
        :param feature:
        :return:
        """
        if isinstance(feature, BaseFeature):
            self.poke('features')
            self.features.append(feature)
        else:
            raise TypeError

    def remove_feature(self, name):
        """ Remove feature from a constituent. It's not satisfied, it is just gone.
        :param fname: str, the name for finding the feature or for convenience, a feature
        instance to be removed
        """
        if isinstance(name, BaseFeature):
            if name in self.features:
                self.poke('features')
                self.features.remove(name)
        else:
            for f in list(self.features):
                if f.name == name:
                    self.poke('features')
                    self.features.remove(f)

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
            return list(self.parts)

    def get_heads(self):
        """ It is useful for constituent to be able to tell what is or which are its
        original projecting heads. A default implementation is just to save this information as a list.
        :return:
        """
        return self.lexical_heads

    def copy(self):
        """ Make a deep copy of constituent. Useful for picking constituents from Lexicon.
        :return: BaseConstituent
        """
        new_parts = []
        for part in self.parts:
            new = part.copy()
            new_parts.append(new)
        #fmap = dict([(f.uid, f.copy()) for f in set(self.features + self.checked_features)])
        #new_features = [fmap[f.uid] for f in self.features]
        #checked_features = [fmap[f.uid] for f in self.checked_features]
        new_features = [f.copy() for f in self.features]
        nc = self.__class__(label=self.label,
                            parts=new_parts,
                            features=new_features)
        #nc.checked_features = checked_features
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
    checked_features = SavedField("checked_features")
    inherited_features = SavedField("inherited_features")
    lexical_heads = SavedField("lexical_heads")

