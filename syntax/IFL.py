# coding=utf-8
""" Universal Grammar, collects Lexicon and Interfaces so that they can operate together."""
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

from kataja.BaseModel import BaseModel


class IFL(BaseModel):
    """ Interface for Faculty of Language, implementation should be able to perform the operations
     sent here."""

    short_name = "I-FL"

    def __init__(self):
        super().__init__(self)
        raise NotImplementedError

    def get_roots(self):
        """ List the constituent structures of the workspace, represented by their topmost element
        """
        raise NotImplementedError

    def get_constituent_from_lexicon(self, identifier):
        """ Fetch constituent from lexicon
        :param identifier:
        :return:
        """
        raise NotImplementedError

    def get_feature_from_lexicon(self, identifier):
        """ Fetch the feature matching the key from workspace
        :param identifier:
        :return:
        """
        raise NotImplementedError

    def merge(self, A, B, merge_type=None):
        """ Do Merge of given type, return result
        :param A:
        :param B:
        :param merge_type:
        :return:
        """
        raise NotImplementedError

    def linearize(self, A, linearization_type=None):
        """ Do linearisation for a structure, there may be various algorithms
        :param A:
        :param linearization_type:
        :return: list of leaf constituents ?
        """
        raise NotImplementedError

    def precedes(self, A, B):
        """
        :param A:
        :param B:
        :return:
        """
        raise NotImplementedError

    def feature_check(self, suitor, bride):
        """ Check if the features(?) match(?)
        :param suitor:
        :param bride:
        :return: bool
        """
        raise NotImplementedError

    def consume(self, suitor, bride):
        """ If successful feature check is supposed to do something for constituents or their features
        :param suitor:
        :param bride:
        :return: None
        """
        raise NotImplementedError

    def c_commands(self, A, B):
        """ Evaluate if A C-commands B
        :param A:
        :param B:
        :return: bool
        """
        raise NotImplementedError

    def parse(self, sentence, silent=False):
        """ Returns structure (constituent or list of constituents) if given sentence can be parsed. Not
        necessary to implement.
        :param sentence:
        :param silent:
        :return: :raise "Word '%s' missing from the lexicon" % word:
        """
        return None

    # Direct editing of FL constructs ##########################
    # these methods don't belong to assumed capabilities of FL, they are to allow Kataja editing
    # capabilities to directly create and modify FL structures.

    def k_create_constituent(self, **kw):
        """ Create constituent with provided values and return it
        :param kw:
        :return: IConstituent
        """
        raise NotImplementedError

    def k_get_constituent(self, key):
        """ Fetch the constituent matching the key from workspace
        :param key:
        :return:
        """
        raise NotImplementedError

    def k_get_feature(self, key):
        """ Fetch the feature matching the key from workspace
        :param key:
        :return:
        """
        raise NotImplementedError

    def k_construct(self, parent, children, purge_existing=True):
        """ Sets up connections between constituents without caring if there are syntactic
        operations to allow that
        :param parent:
        :param children:
        :param purge_existing:
        :return:
        """
        raise NotImplementedError

    def k_connect(self, parent, child):
        """ Tries to set parent-child connection
        :param parent:
        :param child:
        :return:

        """
        raise NotImplementedError

    def k_disconnect(self, parent, child):
        """ Tries to remove parent-child connection. Primitive: may leave binary trees to have empty
        branch.
        :param parent:
        :param child:
        :return:

        """
        raise NotImplementedError

    def k_replace(self, old_c, new_c, under_parent=None):
        """ Replace constituent with another, either in all occurences or only under specific parent
        :param old_c:
        :param new_c:
        :param under_parent:
        :return:
        """
        raise NotImplementedError

    def k_linearization_types(self):
        """ Return available options for linearization
        :return:
        """
        raise NotImplementedError

    def k_merge_types(self):
        """ Provide available merge types
        :return:
        """
        raise NotImplementedError

    def k_create_feature(self, **kw):
        """ Create feature with provided values and return it
        :param kw:
        :return: IConstituent
        """
        raise NotImplementedError

    # these are properties so they will get docstrings. Instead of reimplementing methods they should
    # use the base implementation and other implementations should modify the referred dicts instead.

    @property
    def k_available_rules(self):
        """ Return dict of info about features offered by this FL implementation.
        These may be used to create UI choices for these rules or limit available actions.

        Dict values should be dicts with at least
         {"options":[list of option_keys (str)], "default":option_key}
        :return: dict of rules
        """
        raise NotImplementedError
        # implement by uncommenting following and modify the class variable rules in your implementation
        # return self.__class__.available_rules

    def k_rules(self):
        """ Return dict of currently active rules
        :return: dict of rule:value -pairs.
        """
        raise NotImplementedError

    @property
    def k_ui_strings(self):
        """ Provide a dict that provides user-readable names for option_keys and help text for them if
        required.
        :return: dict where keys are option_keys and values are (readable_name, help_text) -tuples
        """
        raise NotImplementedError
        # implement by uncommenting following and modify the class variable rules in your implementation
        # return self.__class__.ui_strings

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #
