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

from kataja.singletons import ctrl, running_environment
from kataja.saved.Forest import Forest
from kataja.saved.KatajaDocument import KatajaDocument
from mgtdbpE.Parser import Parser, load_grammar
from kataja.singletons import classes

class Document(KatajaDocument):
    """ Container and loader for Forest objects. Remember to not enable undo for any of the actions
     in here, as scope of undo should be a single Forest. """

    # unique = True
    #
    default_treeset_file = running_environment.plugins_path + '/mgtdbpE/sentences.txt'

    def create_forests(self, filename=None, clear=False):
        """ This will read sentences to parse. One sentence per line, no periods etc.

        :param filename: not used
        :param clear: start with empty
        """
        if clear:
            treelist = ['hello']
        else:
            treelist = self.load_treelist_from_text_file(self.__class__.default_treeset_file) or \
                       ['hello']

        # Clear this screen before we start creating a mess
        ctrl.disable_undo() # disable tracking of changes (e.g. undo)
        if self.forest:
            self.forest.retire_from_drawing()
        self.forests = []

        grammar = load_grammar(filename=running_environment.plugins_path + '/mgtdbpE/mg0.txt')

        for line in treelist:
            sentence = line.strip()
            if (not sentence) or sentence.startswith('#'):
                continue
            syn = classes.get('SyntaxConnection')()
            syn.sentence = sentence
            syn.lexicon = grammar
            forest = Forest(heading_text=sentence, syntax=syn)
            self.forests.append(forest)
        self.current_index = 0
        self.forest = self.forests[0]
        # allow change tracking (undo) again
        ctrl.resume_undo()
