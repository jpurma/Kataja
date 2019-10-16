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

from kataja.syntax.SyntaxAPI import SyntaxAPI as KatajaSyntaxAPI


class SyntaxAPI(KatajaSyntaxAPI):
    """ This is required for Kataja compatibility. SyntaxAPI tells how each forest instance should access their parser
    and derive its given sentence. It also connects parser's lexicon and input sentence to lexicon panel so they can
     be edited there. """
    role = "SyntaxAPI"
    supports_editable_lexicon = True
    supports_secondary_labels = False
    display_modes = []

    def __init__(self, parser, input_text=''):
        super().__init__()
        self.input_text = input_text
        self.parser = parser
        self.lexicon_interface = parser.lexicon
        self.lexicon = parser.lexicon.d

    def get_editable_lexicon(self):
        """ Get lexicon as an editable string (as in a text file) """
        if isinstance(self.lexicon, dict):
            s = []
            for key, const_list in self.lexicon.items():
                for const in const_list:
                    s.append(f'{key} :: {const.morphology} {" ".join(sorted(const.features))}')
            s.sort()
            return '\n'.join(s)
        else:
            return self.lexicon

    def load_lexicon(self, filename):
        self.lexicon = self.lexicon_interface.load_lexicon(filename)
        return self.lexicon

    def read_lexicon(self, lexdata, lexicon=None):
        if isinstance(lexdata, str):
            lexdata = lexdata.splitlines()
        self.lexicon = self.lexicon_interface.load_lexicon(lines=lexdata)
        return self.lexicon

    def _prepare_derivation_parameters(self, input_text, lexicon, semantics):
        if lexicon:
            if isinstance(lexicon, dict):
                self.lexicon = lexicon
            else:
                self.lexicon = self.read_lexicon(lexicon)
        if input_text:
            self.input_text = input_text

    def create_derivation(self, input_text=None, lexicon=None, semantics=None, forest=None):
        """ Attempt parsing with given sentence or tree and with given lexicon. If these are left
        out, do or redo parsing with instance's stored sentence, lexicon and semantics.

        If a forest is provided, derivation steps are created there.
        :return:
        """
        self._prepare_derivation_parameters(input_text, lexicon, semantics)

        if forest:
            self.parser.forest = forest
        print('parsing from the input text and provided lexicon')
        print('================================================')
        print('input_text: ', self.input_text)
        self.parser.parse(self.input_text.split())
