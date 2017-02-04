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

from abc import ABCMeta, abstractmethod


class IConstituent(metaclass=ABCMeta):
    """ IConstituent is an abstract/interface class to help define your own
    Constituent implementations. If you inherit IConstituent, all of its methods have to be
    implemented or build fails. (It is better to fail at this stage.)
    BaseConstituent is the default implementation."""

    syntactic_object = True
    editable = {}
    addable = []

    @abstractmethod
    def __init__(self, label='', parts=None, uid='', features=None, **kw):
        NotImplemented

    @abstractmethod
    def __str__(self):
        return NotImplemented

    @abstractmethod
    def __repr__(self):
        return NotImplemented

    @abstractmethod
    def __contains__(self, c):
        return NotImplemented

    @abstractmethod
    def get_features(self):
        """ Getter for features, redundant for BaseConstituent (you could use c.features ) but it
        is better to use this consistently for compatibility with other implementations for
        constituent.
        :return:
        """
        return NotImplemented

    @abstractmethod
    def get_parts(self):
        """ Getter for parts, redundant for BaseConstituent (you could use c.parts ) but it
        is better to use this consistently for compatibility with other implementations for
        constituent.
        :return:
        """
        return NotImplemented

    @abstractmethod
    def print_tree(self):
        """ Bracket trees representation of the constituent structure. Now it is same as str(self).
        :return: str
        """
        return NotImplemented

    @abstractmethod
    def can_add_part(self, **kw):
        """
        :param kw:
        :return:
        """
        return NotImplemented

    @abstractmethod
    def add_part(self, new_part):
        """ Add constitutive part to this constituent (append to parts)
        :param new_part:
        """
        return NotImplemented

    @abstractmethod
    def insert_part(self, new_part, index=0):
        """ Insert constitutive part to front of the parts list. Usefulness
        depends on the linearization method.
        :param new_part:
        :param index:
        :return:
        """
        return NotImplemented

    @abstractmethod
    def remove_part(self, part):
        """ Remove constitutive part
        :param part:
        """
        return NotImplemented

    @abstractmethod
    def replace_part(self, old_part, new_part):
        """
        :param old_part:
        :param new_part:
        :return:
        """
        return NotImplemented

    @abstractmethod
    def get_feature(self, key):
        """ Gets the first local feature (within this constituent, not of its children) with key
        'key'
        :param key: string for identifying feature type
        :return: feature object
        """
        return NotImplemented

    @abstractmethod
    def get_secondary_label(self):
        """ Visualisation can switch between showing labels and some other information in label
        space. If you want to support this, have "support_secondary_labels = True"
        in SyntaxConnection and provide something from this getter.
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def has_feature(self, key):
        """ Check the existence of feature within this constituent
        :param key: string for identifying feature type or Feature instance
        :return: bool
        """
        return NotImplemented

    @abstractmethod
    def add_feature(self, feature):
        """ Add an existing Feature object to this constituent.
        :param feature:
        :return:
        """
        return NotImplemented

    @abstractmethod
    def remove_feature(self, name):
        """ Remove feature from a constituent. It's not satisfied, it is just gone.
        :param fname: str, the name for finding the feature or for convenience, a feature
        instance to be removed
        """
        return NotImplemented

    @abstractmethod
    def is_leaf(self):
        """ Check if the constituent is leaf constituent (no children) or inside a trees (has children).
        :return: bool
        """
        return NotImplemented

    @abstractmethod
    def ordered_parts(self):
        """ Tries to do linearization between two elements according to theory being used.
        Easiest, default case is to just store the parts as a list and return the list in its original order.
        This is difficult to justify theoretically, though.
        :return: len 2 list of ordered nodes, or empty list if cannot be ordered.
        """
        return NotImplemented

    @abstractmethod
    def copy(self):
        """ Make a deep copy of constituent. Useful for picking constituents from Lexicon.
        :return: BaseConstituent
        """
        return NotImplemented

