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

import ast

from plugins.Monorail.Parser import load_lexicon

from kataja.saved.Forest import Forest
from kataja.saved.KatajaDocument import KatajaDocument
from kataja.singletons import classes

try:
    # noinspection PyPackageRequirements
    from nltk.corpus import treebank

    has_nltk = True
except ImportError:
    treebank = None
    has_nltk = False


def as_list(node):
    if isinstance(node, list):
        if len(node) == 1:
            return as_list(node[0])
        elif len(node) == 2:
            return [as_list(node[0]), as_list(node[1])]
    return str(node)


NLTK_TREE_RANGE = (1, 5)


class Document(KatajaDocument):
    """ Container and loader for Forest objects. Remember to not enable undo for any of the actions
     in here, as scope of undo should be a single Forest. """

    def create_forests(self, filename=None, treelist=None, clear=False):
        """ This will read sentences to parse. One sentence per line, no periods etc.
        """
        filename = filename or Document.get_default_treeset_file()

        forests = []
        input_trees = []

        shared_lexicon = load_lexicon(Document.get_default_lexicon_file())
        print('loaded shared_lexicon: ', shared_lexicon)
        if treelist:
            input_trees = treelist
        elif has_nltk:
            print(f"reading trees {NLTK_TREE_RANGE[0]}-{NLTK_TREE_RANGE[1]} from NLTK's treebank")
            for i in range(*NLTK_TREE_RANGE):  # 199
                trees = treebank.parsed_sents(f'wsj_0{str(i).rjust(3, "0")}.mrg')
                for j, tree in enumerate(trees):
                    tree.chomsky_normal_form()
                    tree.collapse_unary()
                    input_trees.append(as_list(tree))
        else:
            readfile = open(filename, 'r')
            for line in readfile:
                line = line.strip()
                if line:
                    if line.startswith('[') and line.endswith(']'):
                        input_trees.append(ast.literal_eval(line))
                    else:
                        input_trees.append(line)

        for input_tree in input_trees:
            syn = classes.SyntaxAPI()
            syn.lexicon = shared_lexicon
            if isinstance(input_tree, list):
                syn.input_tree = input_tree
            else:
                syn.input_text = input_tree
            forest = Forest(heading_text=str(input_tree), syntax=syn)
            forests.append(forest)
        return forests
