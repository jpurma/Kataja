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
from PoP.PoPDeriveH import Generate


class PoPDocument(KatajaDocument):
    """ Container and loader for Forest objects. Remember to not enable undo for any of the actions in here,
    as scope of undo should be a single Forest. """

    # unique = True
    #
    default_treeset_file = running_environment.plugins_path + '/PoP/POP.txt'

    @staticmethod
    def create_forests(filename=None, treelist=None, clear=False):
        """ This will read example sentences in form used by Ginsburg / Fong parser

        1 Tom read a book. (Chomsky 2015:10) ['C','Tpres',['D','n','Tom'],'v*','read','a','n',
        'book']
        2 They expected John to win. (Chomsky 2015:10) ['C','Tpast',['D','n','they'],'v*','expect',
        'toT',['D','n','John'],'vUnerg','win']
        3 Who do you expect to win. (Chomsky 2015:10) ['C_Q','Tpres',['D','n','you'],'v*','expect',
        'toT',['Q','n','who'],'vUnerg','win']

        :param treelist: lines of file like above. Lines that don't begin with number are ignored.
        """
        if clear:
            treelist = []
        elif not treelist:
            treelist = PoPDocument.load_treelist_from_text_file(PoPDocument.default_treeset_file) or []

        forests = []

        start = 0
        end = 10
        ug = Generate()

        for line in treelist:
            if "Japanese" in line:
                ug.language = "Japanese"
            elif "English" in line:
                ug.language = "English"
            sentence, lbracket, target_str = line.partition('[')
            if not (sentence and lbracket and target_str):
                continue
            sentence = sentence.strip()
            sentence_number = sentence[0]

            if not sentence_number.isdigit():
                continue
            sentence_number = int(sentence_number)
            if end and sentence_number > end:
                break
            elif sentence_number < start:
                continue
            sentence = sentence[2:]  # remove number and the space after it
            target_example = eval(lbracket + target_str)
            ug.out(sentence_number, sentence, target_example)
            forest = Forest(heading_text=sentence)
            forests.append(forest)
            so = ug.generate_derivation(target_example, forest=forest)
            ug.out("MRGOperations", ug.merge_counter)
            ug.out("FTInheritanceOp", ug.inheritance_counter)
            ug.out("FTCheckOp", ug.feature_check_counter)
        return forests