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
#     """ C-Command edge needs the root constituent of the trees as a context, as
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
