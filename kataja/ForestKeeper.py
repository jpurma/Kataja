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
from kataja.BaseModel import BaseModel


class ForestKeeperModel(BaseModel):
    """ Container and loader for Forest objects. Remember to not enable undo for any of the actions in here,
    as scope of undo should be a single Forest. """

    def __init__(self, host):
        super().__init__(host, unique=True)
        self.forests = []
        self.current_index = 0
        self.forest = None


class ForestKeeper:
    """ Container and loader for Forest objects. Remember to not enable undo for any of the actions in here,
    as scope of undo should be a single Forest. """

    def __init__(self, filename=None):
        self.model = ForestKeeperModel(self)
        if filename:
            treelist = self.load_treelist_from_file(filename)
        else:
            treelist = []
        self.create_forests(treelist)

    @property
    def forests(self):
        """ Keeps the list of forest instances, which each have their own settings, undo stacks etc.
        :return: list of Forest instances
        """
        return self.model.forests

    @forests.setter
    def forests(self, value):
        """ Keeps the list of forest instances, which each have their own settings, undo stacks etc.
        :param value: list of Forest instances
        """
        self.model.forests = value

    @property
    def current_index(self):
        """ Index of currently active forest in forests-list
        :return: int
        """
        return self.model.current_index

    @current_index.setter
    def current_index(self, value):
        """ Index of currently active forest in forests-list
        :param value: int
        """
        self.model.current_index = value

    @property
    def forest(self):
        """ Currently active forest
        :return: Forest instance
        """
        return self.model.forest

    @forest.setter
    def forest(self, value):
        """ Currently active forest
        :param value: Forest instance
        """
        self.model.forest = value

    def next_forest(self):
        """ Select the next forest in the list of forests. The list loops at end.
        :return: tuple (current_index (int), selected forest (Forest)
        """
        if not self.forests:
            return None
        if self.current_index < len(self.forests) - 1:
            self.current_index += 1
        else:
            self.current_index = 0
        if ctrl.undo_pile:
            print('undo pile has stuff we are about to discard: ', ctrl.undo_pile)
        ctrl.undo_pile = set()
        self.forest = self.forests[self.current_index]
        return self.current_index, self.forest

    def prev_forest(self):
        """ Select the previous forest in the list of forests. The list loops at -1.
        :return: tuple (current_index (int), selected forest (Forest)
        """
        if not self.forests:
            return None
        if self.current_index > 0:
            self.current_index -= 1
        else:
            self.current_index = len(self.forests) - 1
        if ctrl.undo_pile:
            print('undo pile has stuff we are about to discard: ', ctrl.undo_pile)
        ctrl.undo_pile = set()
        self.forest = self.forests[self.current_index]
        return self.current_index, self.forest

    @staticmethod
    def load_treelist_from_file(filename):
        """ Pretty dumb fileloader, to create a treelist (list of strings)
        :param filename: str, does nothing with the path.
        """
        try:
            f = open(filename, 'r', encoding='UTF-8')
            treelist = f.readlines()
            f.close()
        except FileNotFoundError:
            treelist = ['[A B]']
        return treelist

    def create_forests(self, treelist):
        """ This will read list of strings where each line defines a tree or an element of tree. Example:

        [.AspP [.Asp\\Ininom] [.vP [.KP [.K\\ng ] [.DP [.D´ [.D ] [.NP\\lola ]] [.KP [.K\\ng]
        [.DP [.D´ [.D ] [.NP\\alila ] ] [.KP\\{ni Maria} ]]]]] [.v´ [.v ] [.VP [.V ] [.KP\\{ang tubig}]]]]]
        Ininom = drank
        ng = NG
        ng = NG
        lola = grandma
        alila = servant
        ni Maria = NG Maria
        ang tubig = ANG water
        'Maria's grandmother's servant drank the water'

        :param treelist: list of strings, where a line can be a bracket tree or definition line for element
        in a tree
        """
        # Clear this screen before we start creating a mess
        print('----------- starting loading ------------')
        ctrl.disable_undo = True  # disable tracking of changes (e.g. undo)
        if self.forest:
            self.forest.retire_from_drawing()
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
                self.forests.append(Forest(buildstring=buildstring,
                                           definitions=definitions,
                                           gloss_text=gloss_text,
                                           comments=comments))
                started_forest = False
            # tree definition starts a new forest
            elif line and not started_forest:
                buildstring = line
                definitions = {}
                gloss_text = ''
                comments = []
            # another tree definition, append to previous
            elif line:
                buildstring += '\n' + line
        if started_forest:  # make sure that the last forest is also added
            self.forests.append(Forest(buildstring=buildstring,
                                       definitions=definitions,
                                       gloss_text=gloss_text,
                                       comments=comments))
        self.current_index = 0
        if self.forests:
            self.forest = self.forests[0]
            self.forest.undo_manager.init_if_empty()
            # self.save()
        # allow change tracking (undo) again
        ctrl.disable_undo = False