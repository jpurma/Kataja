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

    def get_editable_lexicon(self):
        """ If it is possible to provide editable lexicon (str), where to get it
        :return:
        """
        return super().get_editable_lexicon()

    def derive_from_editable_lexicon(self, forest, input_text, lexdata, semantics=''):
        """ Take edited version of get_editable_lexicon output and try derivation with it.
        """
        print('calling derive_from_editable_lexicon', lexdata)
        ctrl.disable_undo()
        forest.clear()
        self.input_text = input_text
        self.lexicon = read_lexicon(lexdata)
        parse(input_text.split(), self.lexicon, forest)

        ds = forest.derivation_steps
        ds.derivation_step_index = len(ds.derivation_steps) - 1
        ds.jump_to_derivation_step(ds.derivation_step_index)
        forest.prepare_for_drawing()
        ctrl.resume_undo()

    def get_editable_sentence(self):
        """ If the current systems supports parsing, return the current parsed string. User can
        edit it and retry parsing.
        :return:
        """
        return self.input_text

    def create_derivation(self, forest):
        """ This is always called to initially turn syntax available here and some input into a
        structure. Resulting structures are used to populate a forest.
        :return:
        """
        print('create_derivation: ', self.lexicon)
        print('===========================')
        t = time.time()
        recipe = []
        self.input_tree = remove_punctuation(self.input_tree)
        list_to_monorail(self.input_tree, [], recipe)
        print('turned to monorail tree : ', time.time() - t)
        self.lexicon = deduce_lexicon_from_recipe(recipe)
        print('deduced lexicon: ', time.time() - t)
        parse_from_recipe(recipe, self.lexicon, forest)
        print('parsed from recipe: ', time.time() - t)
        flat_sentence = flatten(self.input_tree)
        print('flattened sentence tree: ', time.time() - t)
        self.input_text = ' '.join(flat_sentence)
        parse(flat_sentence, self.lexicon, forest)
        print('parsed with new lexicon: ', time.time() - t)

        ds = forest.derivation_steps
        ds.derivation_step_index = len(ds.derivation_steps) - 1
        ds.jump_to_derivation_step(ds.derivation_step_index)

    def set_display_mode(self, i):
        self.display_mode = i

    def next_display_mode(self):
        self.display_mode += 1
        if self.display_mode == len(self.display_modes):
            self.display_mode = 0
        return self.display_modes[self.display_mode]

    def update_display_mode(self, syn_state):
        if self.display_mode == self.current_mode:
            print('No transform')
            return syn_state
        if self.display_mode == CONSTITUENT_TREE:
            log.info('Changing to constituent tree')
            ctrl.settings.set_node_setting('visible', True, g.FEATURE_NODE, level=g.DOCUMENT)
            ctrl.settings.set('label_text_mode', g.SYN_LABELS_FOR_LEAVES, level=g.DOCUMENT)
            ctrl.settings.set('feature_positioning', g.HORIZONTAL_ROW, level=g.DOCUMENT)
            ctrl.settings.set('feature_check_display', g.NO_CHECKING_EDGE, level=g.DOCUMENT)
            ctrl.settings.set_edge_setting('visible', False, g.CONSTITUENT_EDGE, level=g.DOCUMENT)
            ctrl.settings.set('node_shape', g.NORMAL, level=g.DOCUMENT)
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
            ctrl.settings.set_node_setting('visible', False, g.FEATURE_NODE, level=g.DOCUMENT)
            ctrl.settings.set('label_text_mode', g.CHECKED_FEATURES, level=g.DOCUMENT)
            ctrl.settings.set('feature_positioning', g.HORIZONTAL_ROW, level=g.DOCUMENT)
            ctrl.settings.set('feature_check_display', g.NO_CHECKING_EDGE, level=g.DOCUMENT)
            ctrl.settings.set_edge_setting('visible', True, g.CONSTITUENT_EDGE, level=g.DOCUMENT)
            ctrl.settings.set('node_shape', g.FEATURE_SHAPE, level=g.DOCUMENT)
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

