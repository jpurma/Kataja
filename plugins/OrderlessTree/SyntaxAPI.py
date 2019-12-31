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

from plugins.OrderlessTree.Parser import Parser
from kataja.singletons import ctrl
from kataja.syntax.SyntaxAPI import SyntaxAPI as KatajaSyntaxAPI


class SyntaxAPI(KatajaSyntaxAPI):
    """ This is required for Kataja compatibility. SyntaxAPI tells how each forest instance should access their parser
    and derive its given sentence. It also connects parser's lexicon and input sentence to lexicon panel so they can
     be edited there. """
    role = "SyntaxAPI"
    supports_editable_lexicon = True
    supports_secondary_labels = False
    display_modes = []

    def __init__(self, lexicon=None):
        super().__init__()
        self.parser = Parser(lexicon=lexicon, forest=None)

    def create_derivation(self, input_text=None, lexicon=None, semantics=None, forest=None):
        """ Attempt parsing with given sentence or tree and with given lexicon. If these are left
        out, do or redo parsing with instance's stored sentence, lexicon and semantics.

        If a forest is provided, derivation steps are created there.
        :return:
        """
        old_lexicon = self.lexicon
        if input_text:
            self.input_text = input_text

        if forest:
            self.parser.forest = forest
        if lexicon is not None:
            if isinstance(lexicon, str):
                lexicon = self.read_lexicon(lexicon)
            self.lexicon = lexicon
            self.parser.lexicon = lexicon
            ctrl.document.lexicon = lexicon

        print('parsing from the input text and provided lexicon')
        print('================================================')
        print('input_text: ', self.input_text)
        self.parser.parse(self.input_text)
        self.lexicon = self.parser.lexicon
        if old_lexicon != self.lexicon:
            ctrl.document.parse_all_sentences()
