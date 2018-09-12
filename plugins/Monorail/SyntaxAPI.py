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

from kataja.SavedObject import SavedObject
from kataja.singletons import ctrl, classes, log
from syntax.SyntaxAPI import SyntaxAPI as KatajaSyntaxAPI
from Monorail.Parser import remove_punctuation, list_to_monorail, deduce_lexicon_from_recipe, \
    parse_from_recipe, parse, flatten, read_lexicon
import kataja.globals as g
import time

CONSTITUENT_TREE = 0
FEATURE_TREE = 1


class SyntaxAPI(KatajaSyntaxAPI):
    role = "SyntaxAPI"
    supports_editable_lexicon = True
    supports_secondary_labels = False
    display_modes = ['Constituent tree', 'Feature tree']

    def __init__(self):
        SavedObject.__init__(self)
        self.Constituent = classes.Constituent
        self.Feature = classes.Feature
        self.input_tree = []
        self.trees = []
        self.constituents = {}
        self.features = {}
        self.lexicon = {}
        self.rules = {}
        self.input_text = ''
        self.parser = None
        self.display_mode = 0
        self.current_mode = 0
        for key, value in self.options.items():
            self.rules[key] = value.get('default')

    def load_lexicon(self, filename):
        self.lexicon = []

    def get_editable_sentence(self):
        """ If the current systems supports parsing, return the current parsed string. User can
        edit it and retry parsing.
        :return:
        """
        print(repr(self.input_text))
        return self.input_text

    def create_derivation(self, input_text=None, lexicon=None, semantics=None, forest=None):
        """ Attempt parsing with given sentence or tree and with given lexicon. If these are left
        out, do or redo parsing with instance's stored sentence, lexicon and semantics.

        If a forest is provided, derivation steps are created there.
        :return:
        """
        self._prepare_derivation_parameters(input_text, lexicon, semantics)

        if self.input_tree:
            print('parsing from the given tree while deriving a lexicon')
            print('====================================================')
            t = time.time()
            recipe = []
            input_tree = remove_punctuation(self.input_tree)
            list_to_monorail(input_tree, [], recipe)
            print('turned to monorail tree : ', time.time() - t)
            self.lexicon = deduce_lexicon_from_recipe(recipe, self.lexicon)
            print('deduced lexicon: ', time.time() - t)
            parse_from_recipe(recipe, self.lexicon, forest)
            print('parsed from recipe: ', time.time() - t)
            flat_sentence = flatten(input_tree)
            print('flattened sentence tree: ', time.time() - t)
            self.input_text = ' '.join(flat_sentence)
            parse(flat_sentence, self.lexicon, forest)
            print('parsed with new lexicon: ', time.time() - t)
        else:
            print('parsing from the input text and provided lexicon')
            print('================================================')
            parse(self.input_text.split(), self.lexicon, forest)

    def update_display_mode(self, syn_state):
        if self.display_mode == self.current_mode:
            print('No transform')
            return syn_state
        if self.display_mode == CONSTITUENT_TREE:
            log.info('Changing to constituent tree')
            ctrl.doc_settings.set_node_setting('visible', True, g.FEATURE_NODE)
            ctrl.doc_settings.set('label_text_mode', g.NODE_LABELS_FOR_LEAVES)
            ctrl.doc_settings.set('feature_positioning', g.HORIZONTAL_ROW)
            ctrl.doc_settings.set('feature_check_display', g.NO_CHECKING_EDGE)
            ctrl.doc_settings.set_for_edge_type('visible', False, g.CONSTITUENT_EDGE)
            ctrl.doc_settings.set('cn_shape', g.NORMAL)
            res = []
            for synobj in syn_state.tree_roots:
                if synobj.class_name == 'Constituent':
                    synobj = self.to_constituent(synobj)
                res.append(synobj)
            syn_state.tree_roots = res
            self.current_mode = self.display_mode
            for node in ctrl.forest.nodes.values():
                node.update_visibility()
            return syn_state
        elif self.display_mode == FEATURE_TREE:
            log.info('Changing to feature tree')
            ctrl.doc_settings.set_node_setting('visible', False, g.FEATURE_NODE)
            ctrl.doc_settings.set('label_text_mode', g.CHECKED_FEATURES)
            ctrl.doc_settings.set('feature_positioning', g.HORIZONTAL_ROW)
            ctrl.doc_settings.set('feature_check_display', g.NO_CHECKING_EDGE)
            ctrl.doc_settings.set_for_edge_type('visible', True, g.CONSTITUENT_EDGE)
            ctrl.doc_settings.set('cn_shape', g.FEATURE_SHAPE)
            res = []
            for synobj in syn_state.tree_roots:
                if synobj.class_name == 'Constituent':
                    synobj = self.to_feature_constituent(synobj)
                res.append(synobj)
            syn_state.tree_roots = res
            self.current_mode = self.display_mode
            for node in ctrl.forest.nodes.values():
                node.update_visibility()
            return syn_state
        return syn_state

    def to_constituent(self, synobj):
        return synobj

    def to_feature_constituent(self, synobj):
        #if synobj.parts:
        #    synobj.label = ' '.join([str(x) for x in synobj.checked_features])
        #    for part in synobj.parts:
        #        self.to_feature_constituent(part)
        return synobj

