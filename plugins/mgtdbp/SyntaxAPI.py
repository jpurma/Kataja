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
from kataja.SavedField import SavedField
from kataja.singletons import ctrl, classes
from syntax.SyntaxAPI import SyntaxAPI as KatajaSyntaxAPI
from mgtdbp.Parser import load_grammar, load_grammar_from_file, Parser
import kataja.globals as g

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
        self.trees = []
        self.constituents = {}
        self.features = {}
        self.lexicon = {}
        self.rules = {}
        self.input_words = []
        self.input_text = ''
        self.parser = None
        self.start = 'C'
        self.display_mode = 1
        self.current_mode = 0
        for key, value in self.options.items():
            self.rules[key] = value.get('default')

    def load_lexicon(self, filename):
        self.lexicon = load_grammar_from_file(filename)

    def get_editable_lexicon(self):
        """ If it is possible to provide editable lexicon, where to get it
        :return:
        """
        return self.parser.printer.print_lexicon(self.parser.lex_trees) if self.parser else ''

    def get_editable_sentence(self):
        """ If the current systems supports parsing, return the current parsed string. User can
        edit it and retry parsing.
        :return:
        """
        return self.input_text

    def create_derivation(self, input_text=None, lexicon=None, semantics=None, forest=None):
        """ Attempt parsing with given sentence or tree and with given lexicon. If these are left
        out, do or redo parsing with instance's stored sentence, lexicon and semantics.

        If a forest is provided, derivation steps are created there.
        :return:
        """
        self._prepare_derivation_parameters(input_text, lexicon, semantics)
        self.parser = Parser(self.lexicon, -0.0001, forest=forest)
        # parser doesn't return anything, it pushes derivation steps to forest
        self.parser.parse(input_words=self.input_text.split(), start=self.start)

    def update_display_mode(self, syn_state):
        if self.display_mode == self.current_mode:
            print('No transform')
            return syn_state
        if self.display_mode == CONSTITUENT_TREE:
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

    def read_lexicon(self, lexdata):
        return load_grammar(lexdata)

    start = SavedField("start")