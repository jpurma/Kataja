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


from kataja.singletons import ctrl
from kataja.Forest import Forest
from kataja.Saved import Savable


class ForestKeeper(Savable):
    """ Container and loader for Forest objects """

    def __init__(self, filename=None):
        """

        :param List treelist:
        :param StringType file_name:
        """
        Savable.__init__(self, unique=True)
        self.saved.forests = []
        self.saved.current_index = 0
        self.saved.forest = None
        if filename:
            treelist = self.load_treelist_from_file(filename)
        else:
            treelist = []
        self.create_forests(treelist)



    @property
    def forests(self):
        return self.saved.forests

    @forests.setter
    def forests(self, value):
        self.saved.forests = value

    @property
    def current_index(self):
        return self.saved.current_index

    @current_index.setter
    def current_index(self, value):
        self.saved.current_index = value

    @property
    def forest(self):
        return self.saved.forest

    @forest.setter
    def forest(self, value):
        self.saved.forest = value


    def next_forest(self):
        """

        :return:
        """
        if not self.forests:
            return None
        if self.current_index < len(self.forests) - 1:
            self.current_index += 1
        else:
            self.current_index = 0
        self.forest = self.forests[self.current_index]
        return self.current_index, self.forest

    def prev_forest(self):
        """


        :return:
        """
        if not self.forests:
            return None
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.forests) - 1
        self.forest = self.forests[self.current_index]
        return self.current_index, self.forest


    def load_treelist_from_file(self, filename):
        """


        :param filename:
        :param StringType filename:
        """
        # f = codecs.open(filename, 'rb', encoding = 'utf-8')
        print(filename)
        try:
            f = open(filename, 'r', encoding='UTF-8')
            treelist = f.readlines()
            f.close()
        except FileNotFoundError:
            treelist = ['[A B]']
        return treelist

    def create_forests(self, treelist):
        """ This will read list of strings where each line defines a tree or an element of tree. Example:

        [.AspP [.Asp\\Ininom] [.vP [.KP [.K\\ng ] [.DP [.D´ [.D ] [.NP\\lola ]] [.KP [.K\\ng] [.DP [.D´ [.D ] [.NP\\alila ] ] [.KP\\{ni Maria} ]]]]] [.v´ [.v ] [.VP [.V ] [.KP\\{ang tubig}]]]]]
        Ininom = drank
        ng = NG
        ng = NG
        lola = grandma
        alila = servant
        ni Maria = NG Maria
        ang tubig = ANG water
        'Maria's grandmother's servant drank the water'

        :param treelist:list of strings, where a line can be a bracket tree or definition line for element in a tree
        """
        # Clear this screen before we start creating a mess
        if self.forest:
            self.forest.clear_scene()
        self.forests = []

        # buildstring is the bracket tree or trees.
        buildstring = []
        # definitions includes given definitions for constituents of this tree
        definitions = {}
        # gloss_text is the gloss for whole tree
        gloss_text = ''
        # comments are internal notes about the tree, displayed as help text or something
        comments = []
        started_forest = False

        for line in treelist:
            line = line.strip()
            line.split('=', 1)
            parts = line.split('=', 1)
            # comment line
            if line.startswith('#'):
                if started_forest:
                    comments.append(line[1:])
            # Definition line
            elif len(parts) > 1 and not line.startswith('['):
                started_forest = True
                word = parts[0].strip()
                values = parts[1]
                definitions[word] = values
            # Gloss text:
            elif line.startswith("'"):
                if started_forest:
                    if line.endswith("'"):
                        line = line[:-1]
                    gloss_text = line[1:]
            # empty line: finalize this forest
            elif started_forest and not line:
                self.forests.append(Forest(buildstring=buildstring, definitions=definitions, gloss_text=gloss_text, comments=comments))
                started_forest = False
            # tree definition starts a new forest
            elif line and not started_forest:
                buildstring = line
                definitions = {}
                gloss_text = ''
                comments = []
            # another tree definition, append to previous
            elif line and forest:
                buildstring += '\n' + line
        if started_forest:  # make sure that the last forest is also added
            self.forests.append(Forest(buildstring=buildstring, definitions=definitions, gloss_text=gloss_text, comments=comments))
        self.current_index = 0
        if self.forests:
            self.forest = self.forests[0]
            self.forest.undo_manager.init_if_empty()
            # self.save()



