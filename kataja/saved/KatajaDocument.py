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
from collections import OrderedDict

from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from kataja.singletons import ctrl, running_environment, classes
from kataja.utils import time_me


class KatajaDocument(SavedObject):
    """ Container and loader for Forest objects. Remember to not enable undo for any of the actions in here,
    as scope of undo should be a single Forest.

    :param name: Optional readable name for document
    :param filename: File name for saving the document. Initially empty, will be set on save
    """

    unique = True

    default_treeset_file = running_environment.resources_path + 'trees.txt'

    def __init__(self, name=None, filename=None, clear=False):
        super().__init__()
        self.name = name or filename or 'New project'
        self.filename = filename
        self.forests = [classes.Forest()]
        self.current_index = 0
        self.forest = self.forests[0]
        self.lexicon = {}
        self.structures = OrderedDict()
        self.constituents = OrderedDict()
        self.features = OrderedDict()
        self.play = True

    def new_forest(self):
        """ Add a new forest after the current one.
        :return: tuple (current_index (int), selected forest (Forest)
        """
        ctrl.undo_pile = set()
        #ctrl.undo_disabled = True
        if self.forest:
            self.forest.retire_from_drawing()
        forest = classes.Forest()
        self.current_index += 1
        self.poke('forests')  # <-- announce change in watched list-like attribute
        self.forests.insert(self.current_index, forest)
        self.forest = forest  # <-- at this point the signal is sent to update UI
        #ctrl.undo_disabled = False
        return self.current_index, self.forest

    def next_forest(self):
        """ Select the next forest in the list of forests. The list loops at end.
        :return: tuple (current_index (int), selected forest (Forest)
        """
        if not self.forests:
            return None
        if self.forest:
            self.forest.retire_from_drawing()
        if self.current_index < len(self.forests) - 1:
            return self.jump_to_forest(self.current_index + 1)
        else:
            return self.jump_to_forest(0)

    def prev_forest(self):
        """ Select the previous forest in the list of forests. The list loops at -1.
        :return: tuple (current_index (int), selected forest (Forest)
        """
        if not self.forests:
            return None
        if self.forest:
            self.forest.retire_from_drawing()
        if self.current_index > 0:
            return self.jump_to_forest(self.current_index - 1)
        else:
            return self.jump_to_forest(len(self.forests) - 1)

    def jump_to_forest(self, i):
        """ Jump to forest with given index,
        :return: tuple (current_index (int), selected forest (Forest)
        """
        if not self.forests:
            return 0, None
        if self.forest:
            self.forest.retire_from_drawing()
        if i < 0:
            i = 0
        elif i >= len(self.forests):
            i = len(self.forests) - 1
        self.current_index = i
        ctrl.undo_pile = set()
        self.forest = self.forests[self.current_index]
        return self.current_index, self.forest

    def play_animations(self, value, from_button=False):
        self.play = value
        if not from_button:
            action = self.ui.get_action('play_animations')
            action.update_ui_value()

    def build_lexicon_dict(self):
        self.constituents = OrderedDict()
        self.features = OrderedDict()
        self.structures = OrderedDict()
        for key, data in sorted(self.lexicon.items()):
            if data.startswith('['):
                self.structures[key] = data
            elif data.startswith('<'):
                self.features[key] = data
            elif key != 'lexicon_info':
                self.constituents[key] = data

    @staticmethod
    def load_treelist_from_text_file(filename):
        """ Pretty dumb fileloader, to create a treelist (list of strings)
        :param filename: str, does nothing with the path.
        """
        try:
            f = open(filename, 'r', encoding='UTF-8')
            treelist = f.readlines()
            f.close()
        except FileNotFoundError:
            treelist = ['[A B]', '[ A [ C B ] ]', '']
        return treelist

    @time_me
    def create_forests(self, filename=None, clear=False):
        """ This will read list of strings where each line defines a trees or an element of trees.
        This can be used to reset the KatajaDocument if no treeset or an empty treeset is given.

        It is common to override this method in plugins to provide custom commands for e.g.
        running parsers.

        Example of tree this can read:

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

        :param filename: (optional) file to load from
        :param clear: (optional) if True, start with an empty treeset and don't attempt to load
        examples
        """
        print('************* create forests ****************')

        if clear:
            treelist = []
        else:
            treelist = self.load_treelist_from_text_file(self.__class__.default_treeset_file) or []

        # Clear this screen before we start creating a mess
        ctrl.disable_undo() # disable tracking of changes (e.g. undo)
        if self.forest:
            self.forest.retire_from_drawing()
        self.forests = []

        # buildstring is the bracket trees or trees.
        buildstring = []
        # definitions includes given definitions for constituents of this trees
        definitions = {}
        # heading_text is the explanation or gloss for whole trees
        heading_text = ''
        # comments are internal notes about the trees, displayed as help text or something
        comments = []
        started_forest = False

        SyntaxAPI = classes.SyntaxAPI
        Forest = classes.Forest
        for line in treelist:
            line = line.strip()
            #line.split('=', 1)
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
                    heading_text = line[1:]
            # empty line: finalize this forest
            elif started_forest and not line:
                syn = SyntaxAPI()
                syn.input_tree = buildstring
                syn.lexicon = definitions
                forest = Forest(heading_text=heading_text,
                                comments=comments,
                                syntax=syn)
                self.forests.append(forest)
                started_forest = False
            # trees definition starts a new forest
            elif line and not started_forest:
                started_forest = True
                buildstring = line
                definitions = {}
                heading_text = ''
                comments = []
            # another trees definition, append to previous
            elif line:
                buildstring += '\n' + line
        if started_forest:  # make sure that the last forest is also added
            syn = SyntaxAPI()
            syn.input_tree = buildstring
            syn.lexicon = definitions
            forest = Forest(heading_text=heading_text,
                            comments=comments,
                            syntax=syn)
            self.forests.append(forest)
        if not self.forests:
            syn = SyntaxAPI()
            forest = Forest(heading_text='',
                            comments=[],
                            syntax=syn)
            self.forests.append(forest)
        self.current_index = 0
        self.forest = self.forests[0]
        # allow change tracking (undo) again
        ctrl.resume_undo()

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    forests = SavedField("forests")
    current_index = SavedField("current_index")
    forest = SavedField("forest", watcher="forest_changed")
    lexicon = SavedField("lexicon")
