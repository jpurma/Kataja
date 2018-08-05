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
from mgtdbp.Parser import sentences
from kataja.singletons import classes


class Document(KatajaDocument):
    """ Container and loader for Forest objects. Remember to not enable undo for any of the actions
     in here, as scope of undo should be a single Forest. """

    # unique = True
    #
    default_treeset_file = running_environment.plugins_path + '/mgtdbpE/sentences.txt'

    @staticmethod
    def create_forests(filename=None, clear=False):
        """ This will read sentences to parse. One sentence per line, no periods etc.

        :param filename: not used
        :param clear: start with empty
        """
        forests = []
        for grammar, start, sentence in sentences:
            sentence = sentence.strip()
            if (not sentence) or sentence.startswith('#'):
                continue
            syn = classes.SyntaxAPI()
            syn.load_lexicon(grammar)
            syn.input_text = sentence
            syn.start = start
            forest = Forest(heading_text=sentence, syntax=syn)
            forests.append(forest)
        return forests