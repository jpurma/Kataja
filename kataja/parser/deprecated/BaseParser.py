# -*- coding: UTF-8 -*-

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


from kataja.singletons import ctrl, classes
from kataja.saved.movables.Presentation import TextArea, Image

latex_symbols_to_unicode = {'bar': '\u00AF', 'abar': '\u0100',  # small greek alphabet
                            'alpha': '\u03b1', 'beta': '\u03b2', 'gamma': '\u03b3', 'delta': '\u03b4',
                            'epsilon': '\u03b5', 'zeta': '\u03b6', 'eta': '\u03b7', 'theta': '\u03b8', 'iota': '\u03b9',
                            'kappa': '\u03ba', 'lambda': '\u03bb', 'mu': '\u03bc', 'nu': '\u03bd', 'xi': '\u03be',
                            'omicron': '\u03bf', 'pi': '\u03c0', 'rho': '\u03c1', 'varsigma': '\u03c2',
                            'sigma': '\u03c3', 'tau': '\u03c4', 'upsilon': '\u03c5', 'phi': '\u03c6', 'chi': '\u03c7',
                            'psi': '\u03c8', 'omega': '\u03c9', 'leftarrow': '\u2190', 'rightarrow': '\u2192',
                            'righthookarrow': '\u21aa'}

latex_scopes_to_tags = {'sup': 'sup', 'emph': 'i', 'textbf': 'b'}
# 'index':'sub'}

feature_markers = ('+', '-', '=', '>')
feature_names = ('index', 'dotlabel')
cosmetic_features = ('emph', 'textsc', 'overrightarrow', 'sup')
cases = ['NOM', 'ACC', 'PRT', 'GEN', 'DAT', 'ILL']

# # this doesn't work now because of preferences rearrangement
# def get_color_for_feature(feature_name):
# if feature_name in cases:
# return colors[cases.index(feature_name)]
# else:
# return colors[-1]


class BaseParser:
    """ Methods to translate strings to trees or other objects. Base class Parser has general methods, subclasses have specific parsers. Parsers are created on fly and they generally shouldn't hold anything that needs long term storing or saving. (If they do, e.g. lexicons those should be moved to a more suitable place.) """


    def __init__(self, forest):
        """ Parsers have own lexicons to allow referencing to parsed objects """
        self.local_lexicon = {}
        self._definitions = {}
        self._gloss = ''
        self.forest = forest
        self.should_add_to_scene = True


    def detect_suitable_parser(self, text):
        """ There are several parser methods that can be used to create different kinds of objects
        :param text:
        """
        if text.startswith("'"):
            return self.text_area_parser
        elif text.startswith('%'):
            return self.image_parser
        elif text.startswith('['):
            return self.parse
        elif text.startswith('<<'):
            return self.advanced_reverse_tree_parser
        elif text.startswith('<'):
            return self.reverse_tree_parser
        elif text.startswith('>>'):
            return self.bottom_up_parser
        else:
            return self.parse

    # ## General methods

    def add_definition(self, word, definition):
        """

        :param word:
        :param definition:
        """
        self._definitions[word] = definition  # self.parse_definition(definition)
        # we don't want to create the features yet, separate words would get the same instance of feature then.

    def add_gloss(self, gloss):
        """

        :param gloss:
        """
        self._gloss = gloss

    def parse_definition(self, definition, host=None):
        """

        :param definition:
        :param host:
        :return:
        """
        definitions = [d.strip() for d in definition.split(',')]
        gloss = ''
        new_values = {}
        if host:
            features = host.features
        else:
            features = {}
        for dstring in definitions:
            if dstring.startswith("'") or dstring.startswith('"'):
                gloss = dstring
                continue
            parts = dstring.split(':', 1)
            if len(parts) > 1:
                key = parts[0]
                value = parts[1]
                new_values[key] = value
            elif len(parts) == 1:
                key = parts[0]
                new_values[key] = ''
        for key, value in new_values.items():
            if key in features:
                features[key].set(value)
            else:
                feature = classes.Feature(fname=key, value=value)
                features[key] = feature
        if gloss:
            features['gloss'] = gloss
        return features

    def add_local_lexicon(self, C):
        """

        :param C:
        """
        self.local_lexicon[C.label] = C

    def get_word(self, word):
        """

        :param word:
        :return:
        """
        return self.local_lexicon.get(word, None)

    def text_area_parser(self, text):
        """ string to TextArea
        :param text:
        """
        if text.startswith("'"):
            text = text[1:]
        ta = TextArea(text)
        self.forest.others[ta.save_key] = ta
        return ta

    def image_parser(self, text):
        """ string to Image
        :param text:
        """
        if text.startswith("%"):
            image_path = text[1:]
        else:
            image_path = text
        im = Image(image_path)
        self.forest.others[im.save_key] = im
        return im

    def _create_constituent(self, features):
        """ Uses parsed dict of features """
        label = features['label']
        if isinstance(label, classes.Feature):
            label = features['label'].value
        else:
            raise Exception("Label is not a proper Feature")
        lexicon_entry = ctrl.FL.lexicon.get(label, None)
        local_entry = self.local_lexicon.get(label, None)
        if local_entry:
            constituent = local_entry
        elif lexicon_entry:
            constituent = lexicon_entry.copy()
        else:
            constituent = classes.Constituent(label)
        constituent.set_features(features)
        self.add_local_lexicon(constituent)
        return constituent


    def _new_trace_from_constituent(self, constituent):
        node = self.forest.create_node(constituent)
        node.is_trace = True
        return node

    def _new_node_from_constituent(self, constituent):
        node = self.forest.create_node(synobj=constituent)
        self.forest.add_select_counter(node)
        return node

    def _new_merger_node_from_constituent(self, constituent):
        node = self.forest.create_node(synobj=constituent)
        self.forest.add_merge_counter(node)
        return node

        # not used
        # def _merge_trees(self, node, left, right):
        # if self.forest:
        # self.forest.update_roots()

        ### Bottom-up Parser, does not handle trees, but strings of words

        # def bottom_up_parser(self, buildstring):
        # """ stringToBottomUp
        # :param buildstring:
        # """
        #     print("Using bottom_up_parser")
        #     topmost_C = None
        #     self.indexes = []
        #     if buildstring.startswith('>>'):
        #         buildstring = buildstring[2:]
        #     self.tree_object = None
        #
        #     def _find_in_tree(const_id):
        #         def _find(const_id, X):
        #             if not X:
        #                 return None
        #             if X.label == const_id:
        #                 return X
        #             else:
        #                 found = None
        #                 if X.left:
        #                     found = _find(const_id, X.left)
        #                     if found:
        #                         return found
        #                 if X.right:
        #                     found = _find(const_id, X.right)
        #                 return found
        #
        #         return _find(const_id, topmost_C)
        #
        #     def _merge_up(word_string, topmost_C):
        #         features = self.parse_definition(definition=word_string)
        #         if 'label' not in features:
        #             features['label'] = word_string
        #             const_id = word_string
        #         else:
        #             const_id = features['label'].value
        #         dotlabel = features.get('dotlabel', None)
        #         if dotlabel:
        #             dotlabel = dotlabel.get_value()
        #             if not dotlabel:
        #                 assert False
        #         C = _find_in_tree(const_id)
        #         if not C:
        #             C = self._create_constituent(features=features)
        #             # index=utils.next_free_index(self.indexes)
        #             # self.indexes.append(index)
        #             # C.set_index(index)
        #             node = self._new_node_from_constituent(C)
        #             external_merge = True
        #         else:
        #             external_merge = False
        #             node = self.forest.get_node(C)
        #             index = node.index
        #             if not index:
        #                 index = next_free_index(self.indexes)
        #                 self.indexes.append(index)
        #                 node.index = index
        #             node = self.forest.create_trace_for(node)
        #         if topmost_C:
        #             if external_merge and topmost_C.label:
        #                 tid = topmost_C.label
        #             else:
        #                 tid = C.label
        #             topmost_C = ctrl.FL.Merge(C, topmost_C)
        #             topmost_C.label = C.label
        #             topmost_node = self.forest.create_node_from_constituent(topmost_C, result_of_merge=True)
        #             if dotlabel:
        #                 topmost_node.alias = dotlabel
        #             elif external_merge:
        #                 topmost_node.alias = tid
        #             left = self.forest.get_node(topmost_C.left)
        #             right = self.forest.get_node(topmost_C.right)
        #             # These are not implemented anymore:
        #             self.forest.mirror_syntactic_edges(topmost_node, left)
        #             self.forest.mirror_syntactic_edges(topmost_node, right)
        #             # self._merge_trees(node, left, right)
        #         else:
        #             topmost_C = C
        #         return topmost_C
        #
        #     count = 0
        #     word = []
        #     words = buildstring.strip().split()
        #     for word in words:
        #         topmost_C = _merge_up(word, topmost_C)
        #         count += 1
        #     root = self.forest.get_node(topmost_C)
        #     return root
        #
        #

