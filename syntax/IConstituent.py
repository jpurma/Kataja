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


from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from syntax.BaseFeature import BaseFeature
# from copy import deepcopy

class IConstituent(SavedObject):
    """ IConstituent is the interface for constituents in syntax. """

    syntactic_object = True
    visible_in_label = []
    editable_in_label = []
    display_styles = {}
    editable = {}
    addable = []

    def __init__(self, label='', parts=None, uid='', features=None, head=None, **kw):
        super().__init__(**kw)
        self.label = None
        self.parts = None
        self.features = None
        self.head = None

    def __contains__(self, c):
        raise NotImplementedError

    def get_feature(self, key):
        """ Gets the local feature (within this constituent, not of its children) with key 'key'
        :param key: string for identifying feature type
        :return: feature object
        """
        raise NotImplementedError

    def add_part(self, new_part):
        """ Add constitutive part to this constituent
        :param new_part:
        """
        raise NotImplementedError

    def insert_part(self, new_part, index=0):
        """ Insert constitutive part to front of the parts list. Usefulness
        depends on the linearization method.
        :param new_part:
        :param index:
        :return:
        """
        raise NotImplementedError

    def remove_part(self, part):
        """ Remove constitutive part
        :param part:
        """
        raise NotImplementedError

    def replace_part(self, old_part, new_part):
        """
        :param old_part:
        :param new_part:
        :return:
        """
        raise NotImplementedError

    def set_head(self, head):
        """

        :param head:
        :return:
        """
        raise NotImplementedError

    def has_feature(self, key):
        """ Check the existence of feature within this constituent
        :param key: string for identifying feature type or Feature instance
        :return: bool
        """
        raise NotImplementedError

    def set_feature(self, key, value, family=''):
        """ Set constituent to have a certain feature. If the value given is Feature instance, then it is used,
        otherwise a new Feature is created or existing one modified.
        :param key: str, the key for finding the feature
        :param value:
        :param family: string, optional. If new feature belongs to a certain feature family, e.g. phi features.
        """
        raise NotImplementedError

    def remove_feature(self, key):
        """ Remove feature from a constituent. It's not satisfied, it is just gone.
        :param key: str, the key for finding the feature or for convenience, a feature instance to be removed
        """
        raise NotImplementedError

    def is_leaf(self):
        """ Check if the constituent is leaf constituent (no children) or inside a trees (has children).
        :return: bool
        """
        raise NotImplementedError

    def ordered_parts(self):
        """ Tries to do linearization between two elements according to theory being used.
        Easiest, default case is to just store the parts as a list and return the list in its original order.
        This is difficult to justify theoretically, though.
        :return: len 2 list of ordered nodes, or empty list if cannot be ordered.
        """
        raise NotImplementedError

    def copy(self):
        """ Make a deep copy of constituent. Useful for picking constituents from Lexicon.
        :return: BaseConstituent
        """
        raise NotImplementedError

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    features = SavedField("features")
    label = SavedField("label")
    parts = SavedField("parts")
    head = SavedField("head")
