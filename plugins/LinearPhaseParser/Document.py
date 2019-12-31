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


from kataja.saved.Forest import Forest
from kataja.saved.KatajaDocument import KatajaDocument
from kataja.singletons import classes, ctrl
from LanguageGuesser import LanguageGuesser

try:
    from plugins.LinearPhaseParser.LinearPhaseParser import LinearPhaseParser
    # noinspection PyPackageRequirements
    from context import Context
except ImportError:
    Context = None
    from LinearPhaseParser import LinearPhaseParser


class Document(KatajaDocument):
    """ This class is required for Kataja compatibility. KatajaDocument defines what is loaded as a set of trees
        when this plugin is activated. E.g. what are the example sentences that this parser wants to parse for you.

        Note that this creates Forest objects that have the information about their input string and lexicon, but
        Forests shouldn't parse their sentences here yet. They call their parser only when the forest is displayed for
        first time. This is to allow faster handling of large sets of example sentences: The idea is that you don't try
        to parse 1000 examples at once through Kataja - such runs should be done without Kataja's overhead. Then
        Kataja is used to inspect what went wrong with e.g. tree 783.
        """

    def __init__(self, name=None, uid=None):
        super().__init__(name=Document.get_default_treeset_file(), uid=uid)
        lexicon = self.get_default_lexicon_file()

        self.language_guesser = LanguageGuesser(lexicon)
        self.parsers = {}
        for language in self.language_guesser.languages:
            if callable(Context):
                context = Context()
            else:
                context = object()
            context.lexicon_file = ctrl.plugin_settings.lexicon_file
            context.ug_morphemes_file = ctrl.plugin_settings.ug_morphemes_file
            context.ug_morpheme_file = ctrl.plugin_settings.ug_morphemes_file
            context.redundancy_rules_file = ctrl.plugin_settings.redundancy_rules_file
            context.language = language
            self.parsers[language] = LinearPhaseParser(context)

    @staticmethod
    def get_default_treeset_file():
        return ctrl.plugin_settings.test_set_name

    @staticmethod
    def get_default_lexicon_file():
        return ctrl.plugin_settings.lexicon_file

    def create_forests(self, filename=None, treelist=None, clear=False):
        """ This will read sentences to parse. One sentence per line, no periods etc.
        """
        filename = filename or self.get_default_treeset_file()
        forests = []

        if treelist:
            sentences = treelist
        else:
            sentences = []
            only_new_sentences = []
            readfile = open(filename, 'r')
            for line in readfile:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('&'):
                    continue
                if line.startswith('%'):
                    sentences = []
                    line = line.lstrip('%')
                elif line.startswith('+'):
                    only_new_sentences.append(line)
                sentences.append(line)

            if only_new_sentences:
                sentences = only_new_sentences

        for sentence in sentences:
            lang = self.language_guesser.guess(sentence)
            syn = classes.SyntaxAPI(parser=self.parsers[lang], input_text=sentence)
            forest = Forest(heading_text=sentence, syntax=syn)
            forests.append(forest)
        return forests
