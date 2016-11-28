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
import ast


class Document(KatajaDocument):
    """ Container and loader for Forest objects. Remember to not enable undo for any of the actions in here, as scope of undo should be a single Forest. """

    # unique = True
    #
    default_treeset_file = running_environment.plugins_path + '/mgtdbpE/sentences.txt'

    def create_forests(self, treelist=None):
        """ This will read sentences to parse. One sentence per line, no periods etc. 

        :param treelist: lines of file like above.
        """
        if not treelist:
            treelist = []

        # Clear this screen before we start creating a mess
        ctrl.disable_undo() # disable tracking of changes (e.g. undo)
        if self.forest:
            self.forest.retire_from_drawing()
        self.forests = []

        grammar = load_grammar(running_environment.plugins_path + '/mgtdbpE/mg0.txt')

        for line in treelist:
            sentence = line.strip()
            if (not sentence) or sentence.startswith('#'):
                continue
            forest = Forest(gloss_text=sentence)
            self.forests.append(forest)
            parser = Parser(grammar, -0.0001, forest=forest)
            my_success, my_dnodes = parser.parse(sentence=sentence, start='C')
            print(my_success)
        self.current_index = 0
        self.forest = self.forests[0]
        # allow change tracking (undo) again
        ctrl.resume_undo()
