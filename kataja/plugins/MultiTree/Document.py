# -*- coding: UTF-8 -*-
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2019 Jukka Purma
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

import os
import time

from kataja.plugins.MultiTree.Parser import read_lexicon, linearize
from kataja.saved.Forest import Forest
from kataja.saved.KatajaDocument import KatajaDocument
from kataja.singletons import ctrl, classes


class Document(KatajaDocument):
    """ This class is required for Kataja compatibility. KatajaDocument defines what is loaded as a set of trees
        when this plugin is activated. E.g. what are the example sentences that this parser wants to parse for you.

        Note that this creates Forest objects that have the information about their input string and lexicon, but
        Forests shouldn't parse their sentences here yet. They call their parser only when the forest is displayed for
        first time. This is to allow faster handling of large sets of example sentences: The idea is that you don't try
        to parse 1000 examples at once, but such runs should be done without Kataja's overhead. Then Kataja is used to
        inspect what went wrong with cases starting at 783.
        """

    def __init__(self, name=None, uid=None):
        super().__init__(name=Document.get_default_treeset_file(), uid=uid)
        self._sentences = []

    @staticmethod
    def get_default_treeset_file():
        return os.path.join(ctrl.main.plugin_manager.active_plugin_path, 'sentences_en2.txt')

    @staticmethod
    def get_default_lexicon_file():
        return os.path.join(ctrl.main.plugin_manager.active_plugin_path, 'lexicon_en.txt')

    def create_forests(self, filename=None, treelist=None, clear=False):
        """ This will read sentences to parse. One sentence per line, no periods etc.
        """
        filename = filename or Document.get_default_treeset_file()

        forests = []
        self.lexicon = {}

        if treelist:
            sentences = treelist
        else:
            sentences = []
            readfile = open(filename, 'r')
            for line in readfile:
                line = line.strip()
                if line and not line.startswith('#'):
                    sentences.append(line)

        self.lexicon = read_lexicon(self.get_default_lexicon_file())

        self._sentences = sentences
        for sentence in sentences:
            syn = classes.SyntaxAPI()
            syn.input_text = sentence
            syn.lexicon = self.lexicon
            forest = Forest(heading_text=sentence, syntax=syn)
            forests.append(forest)
        return forests

    def parse_all_sentences(self):
        parser = classes.SyntaxAPI().parser
        parser.lexicon = self.lexicon
        succs = 0
        fails = 0
        i = 0
        t = time.time()
        for i, sentence in enumerate(self._sentences, 1):
            print(f'{i}. "{sentence}"')
            result_trees = parser.parse(sentence)
            if result_trees:
                succs += 1
                for result_tree in result_trees:
                    print('  -> ' + ' '.join(linearize(result_tree)))
            else:
                print(f'  -> fail')
                fails += 1

        print('=====================')
        print(f'    {succs}/{i} ')
        print('=====================')
        print('Parsing sentences took: ', time.time() - t)
