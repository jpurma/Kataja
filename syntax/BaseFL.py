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


import re

from syntax.BaseConstituent import BaseConstituent as Constituent
from kataja.singletons import ctrl
import kataja.globals as g


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


class FL(BaseModel):
    """ Interface for Faculty of Language, implementation should be able to perform the operations
     sent here."""

    short_name = "FL"
    available_rules = {"merge_types": dict(options=["set_merge", "pair_merge"], default="set_merge"),
                       "linearization_types": dict(options=["merge_asymmetry", "kayne"]),
                       "binary_branching_for_constituents": dict(options=[True, False], default=True),
                       "binary_branching_for_features": dict(options=[True, False], default=False),
                       }
    # key : ("readable name", "optional help text")
    ui_strings = {"set_merge": ("Set Merge", ""),
                  "pair_merge": ("Pair Merge", ""),
                  "merge_types": ("Merge types", ""),
                  "binary_branching_for_constituents":
                      ("Allow only binary branching with constituents", ""),
                  "binary_branching_for_features":
                      ("Features are forced to binary trees", "")
                  },


    def __init__(self):
        super().__init__(self)
        self.roots = []
        self.constituents = {}
        self.features = {}
        self.lexicon = {}
        self.rules = {}
        for key, value in self.available_rules.items():
            self.rules[key] = value.get('default')

    def get_roots(self):
        """ List the constituent structures of the workspace, represented by their topmost element
        """
        return self.roots

    def get_constituent_from_lexicon(self, identifier):
        """ Fetch constituent from lexicon
        :param identifier:
        :return:
        """
        return self.lexicon.get(identifier)

    def get_feature_from_lexicon(self, identifier):
        """ Fetch the feature matching the key from workspace
        :param identifier:
        :return:
        """
        return self.lexicon.get(identifier)

    def merge(self, a, b, merge_type=None):
        """ Do Merge of given type, return result
        :param a:
        :param b:
        :param merge_type:
        :return:
        """
        if not merge_type:
            merge_type = self.rules['merge_types']
        if merge_type == 'set_merge':
            head = a
            c = Constituent(parts=[a, b])
            c.set_head(head)
            return c
        elif merge_type == 'pair_merge':
            c = Constituent(parts=[a, b])
            c.set_head((a, b))
            return c
        else:
            raise NotImplementedError

    def linearize(self, a, linearization_type=None):
        """ Do linearisation for a structure, there may be various algorithms
        :param a:
        :param linearization_type: 'implicit', 'kayne' etc. if empty, use rules set for this FL
        :return: list of leaf constituents ?
        """
        def _implicit(const, result):
            """ Linearization that relies on parent-child nodes to be implicitly ordered by constituent
                implementation:
                constituent implements ordered_parts -method that can return [left, right] lists or
                even [first, second, third... ] lists. """
            o = const.ordered_parts()
            if not o:
                result.append(const)
            for child in o:
                _implicit(child, result)
            return result

        if not linearization_type:
            linearization_type = self.rules['linearization_types']
        if linearization_type == 'implicit':
            return _implicit(a, [])
        else:
            raise NotImplementedError

    def precedes(self, a, b, linearization_type=None):
        """
        :param a:
        :param b:
        :param linearization_type: 'implicit', 'kayne' etc. if empty, use rules set for this FL.
        :return: 1 if a precedes b, -1 if b precedes b, 0 if cannot say
        """
        def _implicit(const, i, j, found_i=None, found_j=None):
            """ Precedence that relies on parent-child nodes to be implicitly ordered by constituent
                implementation:
                constituent implements ordered_parts -method that can return [left, right] lists or
                even [first, second, third... ] lists. Precedence is computed by going through such
                trees from top down, left first and trying to match i and j. Once both are found from
                a same tree, their precedence can be stated. """
            o = const.ordered_parts()
            for c in o:
                result, found_i, found_j = _implicit(c, i, j, found_i, found_j)
                if result:
                    return result, found_i, found_j
            if not found_i and const is i:
                if found_j:
                    return -1, found_i, found_j
                else:
                    found_i = True
            if not found_j and const is j:
                if found_j:
                    return 1, found_i, found_j
                else:
                    found_j = True
            return 0, found_i, found_j

        if not linearization_type:
            linearization_type = self.rules['linearization_types']
        if linearization_type == 'implicit':
            found = 0
            for root in self.roots:
                found, foo, bar = _implicit(root, a, b, found_i=False, found_j=False)
                if found:
                    break
            return found
        else:
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

        const = ctrl.Constituent(**kw)
        self.constituents[const.key] = const
        return const

    def k_get_constituent(self, key):
        """ Fetch the constituent matching the key from workspace
        :param key:
        :return:
        """
        return self.constituents.get(key, None)

    def k_get_feature(self, key):
        """ Fetch the feature matching the key from workspace
        :param key:
        :return:
        """
        return self.features.get(key, None)

    def k_construct(self, parent, children, purge_existing=True):
        """ Sets up connections between constituents without caring if there are syntactic
        operations to allow that
        :param parent:
        :param children:
        :param purge_existing:
        :return:
        """
        raise NotImplementedError

    def k_connect(self, parent, child, align=None):
        """ Tries to set a parent-child connection. It may be necessary to
        force parts to be in specific order, alignment can be used to give
        hints about the order
        :param parent:
        :param child:
        :param align: edge alignment
        :return:

        """
        if child not in parent.parts:
            if align is None:
                parent.add_part(child)
            elif align == g.LEFT:
                parent.insert_part(child)
            else:
                parent.add_part(child)


    def k_disconnect(self, parent, child):
        """ Tries to remove parent-child connection. Primitive: may leave binary tree to have empty
        branch.
        :param parent:
        :param child:
        :return:

        """
        if child in parent.parts:
            parent.remove_part(child)

    def k_replace(self, old_c, new_c, under_parent=None):
        """ Replace constituent with another, either in all occurences or only under specific parent
        :param old_c:
        :param new_c:
        :param under_parent:
        :return:
        """
        if under_parent:
            if old_c in under_parent.parts:
                under_parent.replace_part(old_c, new_c)
        else:
            parents = [x for x in self.constituents.values() if old_c in x.parts]
            for parent in parents:
                self.k_replace(old_c, new_c, under_parent=parent)

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


    # def __init__(self, lexicon='testlexicon.txt', constituent=Constituent, feature=BaseFeature):
    #     self.Constituent = constituent
    #     self.Feature = feature
    #     self.lexicon = load_lexicon(lexicon, constituent, feature)
    #     self.workspace = {}
    #     self.structure = None
    #
    # def feature_check(self, left, right):
    #     """
    #
    #     :param left:
    #     :param right:
    #     :return:
    #     """
    #     matches = []
    #     selects = []
    #     for key, f_left in left.features.items():
    #         if key in iter(right.features.keys()):
    #             f_right = right.features[key]
    #             if (f_left.value == '-' and f_right.value == '+') or (f_left.value == '+' and f_right.value == '-'):
    #                 matches.append(key)
    #             if (f_left.value == '= ' and f_right.value == '+') or (f_left.value == '+' and f_right.value == '= '):
    #                 selects.append(key)
    #     return matches, selects
    #
    # def Merge(self, left, right):
    #     """
    #
    #     :param left: Constituent
    #     :param right: Constituent
    #     :return: Constituent
    #     """
    #     selected = self.merge_selects(left, right)
    #     new_id = selected.label
    #     print("Merging with label from left constituent:", new_id)
    #     # remove index (_i, _j ...) from Merged id so that indexing won't get broken
    #     #res = re.search(r'[^\\]_\{(.*)\}', new_id) or re.search(r'[^\\]_(.)', new_id)
    #     #if res:
    #     #    new_id = new_id[:new_id.rindex('_')]
    #     new = self.Constituent(new_id, left, right)
    #
    #     if not (left and right):
    #         return new
    #
    #     # this is experiment on case, old code commented below
    #     # new.left_features=left.features.items()
    #     # new.right_features=right.features.items()
    #     # new.features=left.features.copy()
    #     # new.features.update(right.features)
    #     # matches, selects=self.feature_check(left, right)
    #     # for key in matches+selects:
    #     # del new.features[key]
    #     return new
    #
    # def merge_selects(self, left, right):
    #     """ Implements selection in merge. By default left element (new element to be merged)
    #      selects.
    #     :param left:
    #     :param right:
    #     :return: constituent that should be selected
    #     """
    #     return left
    #
    #
    # def CCommands(self, A, B, context):
    #     """ C-Command edge needs the root constituent of the tree as a context, as
    #         my implementation of FL tries to do without constituents having access to their parents
    #     :param context:
    #     :param B:
    #     :param A:
    #     """
    #     closest_parents = _closest_parents(A, context, parent_list=[])
    #     # if 'closest_parent' for B is found within (other edge of) closest_parent, B sure is dominated by it.
    #     for parent in closest_parents:
    #         if B in parent:
    #             return True
    #     return False
    #
    # def getChildren(self, A):
    #     """ Returns immediate children of this element, [left, right] or [] if no children
    #     :param A:
    #     """
    #     children = []
    #     if A.left:
    #         children.append(A.left)
    #     if A.right:
    #         children.append(A.right)
    #     return children
    #
    # def getCCommanded(self, A, context):
    #     """ Returns elements c-commanded by this element
    #     :param context:
    #     :param A:
    #     """
    #     closest_parents = _closest_parents(A, context, parent_list=[])
    #     result = []
    #     for p in closest_parents:
    #         if p.left == A:
    #             result.append(p.right)
    #         else:
    #             result.append(p.left)
    #     return result
    #
    # def getAsymmetricCCommanded(self, A, context):
    #     """ Returns first elements c-commanded by this element that do not c-command this element
    #     :param context:
    #     :param A:
    #     """
    #     result = []
    #
    #     def _downward(item, A, result):
    #         if item.left:
    #             if not self.CCommands(item.left, A, context):
    #                 result.append(item.left)
    #             else:
    #                 result = _downward(item.left, A, result)
    #         if item.right:
    #             if not self.CCommands(item.right, A, context):
    #                 result.append(item.right)
    #             else:
    #                 result = _downward(item.right, A, result)
    #         return result
    #
    #     ccommanded = self.getCCommanded(A, context)
    #     for item in ccommanded:
    #         result = _downward(item, A, result)
    #     return result
    #
    # def parse(self, sentence, silent=False):
    #     """
    #
    #     :param sentence:
    #     :param silent:
    #     :return: :raise "Word '%s' missing from the lexicon" % word:
    #     """
    #     if not isinstance(sentence, list):
    #         sentence = [word.lower() for word in sentence.split()]
    #     for word in sentence:
    #         try:
    #             constituent = self.lexicon[word].copy()
    #         except KeyError:
    #             raise "Word '%s' missing from the lexicon" % word
    #         self.structure = self.Merge(constituent, self.structure)
    #     if not silent:
    #         print('Finished: %s' % self.structure)
    #     return self.structure
    #
    #
    # def Linearize(self, structure):
    #     """
    #
    #     :param structure:
    #     :return:
    #     """
    #
    #     def _lin(node, s):
    #         if node.left:
    #             _lin(node.left, s)
    #         if node.right:
    #             _lin(node.right, s)
    #         if not (node.left or node.right) and node not in s:
    #             s.append(node)
    #         return s
    #
    #     return _lin(structure, [])
    #
    #
    # @time_me
    # def CLinearize(self, structure):
    #     """ Bare phrase structure linearization. Like Kayne's, but allows ambiguous cases to exist. It is assumed that
    #      phonology deals with them, usually by having null element in ambiguous pair.
    #     :param structure:
    #     """
    #     # returns asymmetric c-command status between two elements
    #     def _asymmetric_c(A, B):
    #         AC = self.CCommands(A, B, structure)
    #         BC = self.CCommands(B, A, structure)
    #         if AC and BC:
    #             return None
    #         elif AC:
    #             return A, B
    #         elif BC:
    #             return B, A
    #         else:
    #             return None
    #
    #     # build a list of terminals
    #     def _lin(node, s):
    #         if node.left:
    #             _lin(node.left, s)
    #         if node.right:
    #             _lin(node.right, s)
    #         if not (node.left or node.right) and node not in s:
    #             s.append(node)
    #         return s
    #
    #     # first create a list (or set or whatever) of terminal nodes.
    #     terminals = _lin(structure, [])
    #     # create pairs of asymmetric c-commands
    #     if not terminals:
    #         return []
    #     t2 = list(terminals)
    #     pairs = []
    #     for a in list(t2):
    #         for b in t2:
    #             if a != b:
    #                 c = _asymmetric_c(a, b)
    #                 if c:
    #                     pairs.append(c)
    #         t2.pop(0)
    #     linear = []
    #     t2 = list(terminals)
    #     for item in list(t2):
    #         found = False
    #         for (a, b) in pairs:
    #             if b == item:
    #                 found = True
    #         if not found:
    #             for (a, b) in list(pairs):
    #                 if a == item:
    #                     pairs.remove((a, b))
    #                     found = True
    #             if found:
    #                 linear.append(item)
    #
    #     print(linear)
    #     return linear

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #
