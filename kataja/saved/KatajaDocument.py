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
import os

from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from kataja.singletons import ctrl, classes, prefs
from kataja.settings.DocumentSettings import DocumentSettings


def definitions_as_text(defs):
    return '\n'.join([f'{key} :: {value}' for key, value in defs.items()])


class KatajaDocument(SavedObject):
    """ Container and loader for Forest objects. Remember to not enable undo for any of the actions in here,
    as scope of undo should be a single Forest.

    :param name: Optional readable name for document
    """

    unique = True

    def __init__(self, name=None, uid=None):
        super().__init__(uid=uid)
        self.name = name or 'New project'
        self.filename = name
        self.settings = DocumentSettings(self)
        self.forests = []
        self.current_index = 0
        self.forest = None
        self.lexicon = {}
        self.play = True
        self.has_filename = False

    @staticmethod
    def get_default_treeset_file():
        return os.path.join(ctrl.main.plugin_manager.active_plugin_path, 'sentences.txt')

    @staticmethod
    def get_default_lexicon_file():
        return os.path.join(ctrl.main.plugin_manager.active_plugin_path, 'lexicon.txt')

    def retire_from_display(self):
        if self.forest:
            self.forest.retire_from_display()

    def load_default_forests(self, tree=None):
        """ Loads and initializes a new set of trees. Has to be done before
        the program can do anything sane.
        """
        filename = ''
        treelist = None
        if isinstance(tree, str):
            if tree.strip().startswith('['):
                treelist = [tree]
            else:
                filename = tree
        elif isinstance(tree, list):
            treelist = tree
        forests = self.create_forests(filename=filename, clear=False, treelist=treelist if tree else None)
        if forests:
            self.forests = forests
            self.set_forest(forests[0])

    def new_forest(self):
        """ Add a new forest after the current one.
        :return: tuple (current_index (int), selected forest (Forest)
        """
        ctrl.undo_pile = set()
        forest = classes.Forest()
        self.poke('forests')  # <-- announce change in watched list-like attribute
        self.forests.insert(self.current_index + 1, forest)
        self.set_forest_by_index(self.current_index + 1)

    def next_forest(self):
        """ Select the next forest in the list of forests. The list loops at end.
        :return: tuple (current_index (int), selected forest (Forest)
        """
        i = self.current_index + 1 if self.current_index < len(self.forests) - 1 else 0
        self.set_forest_by_index(i)

    def prev_forest(self):
        """ Select the previous forest in the list of forests. The list loops at -1.
        :return: tuple (current_index (int), selected forest (Forest)
        """
        i = self.current_index - 1 if self.current_index > 0 else len(self.forests) - 1
        self.set_forest_by_index(i)

    def set_forest_by_index(self, i):
        """ Jump to forest with given index,
        :return: tuple (current_index (int), selected forest (Forest)
        """
        if not self.forests:
            return 0, None
        if i < 0:
            i = 0
        elif i >= len(self.forests):
            i = len(self.forests) - 1
        new_forest = self.forests[i]
        self.set_forest(new_forest)

    def set_forest(self, forest, force=False):
        if (not forest) or (forest is self.forest and not force):
            return self.current_index, forest
        elif self.forest:
            self.forest.retire_from_display()
        self.current_index = self.forests.index(forest)
        ctrl.undo_pile = set()
        self.forest = forest
        ctrl.disable_undo()
        if forest.is_parsed:
            forest.derivation_tree.show_parse(forest.derivation_tree.current_branch_index)
        forest.prepare_for_drawing()
        ctrl.resume_undo()
        ctrl.main.forest_changed.emit()

    def update_forest(self):
        self.set_forest(self.forest, force=True)

    def play_animations(self, value, from_button=False):
        self.play = value
        if not from_button:
            action = self.ui.get_action('play_animations')
            action.update_ui_value()

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


    def create_forests(self, filename=None, treelist=None, clear=False):
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
        :param treelist: (optional) list of lines (str) that can be converted to trees, like file.readlines()
        :param clear: (optional) if True, start with an empty treeset and don't attempt to load
        examples
        """

        if filename:
            treelist = KatajaDocument.load_treelist_from_text_file(filename)
        elif clear:
            treelist = []
        elif not treelist:
            treelist = KatajaDocument.load_treelist_from_text_file(KatajaDocument.get_default_treeset_file()) or []

        forests = []

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
                syn.lexicon = definitions_as_text(definitions)
                forest = Forest(heading_text=heading_text,
                                comments=comments,
                                syntax=syn)
                forests.append(forest)
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
            syn.lexicon = definitions_as_text(definitions)
            forest = Forest(heading_text=heading_text,
                            comments=comments,
                            syntax=syn)
            forests.append(forest)
        if not forests:
            syn = SyntaxAPI()
            forest = Forest(heading_text='',
                            comments=[],
                            syntax=syn)
            forests.append(forest)
        return forests

    def create_save_data(self):
        """
        Make a large dictionary of all objects with all of the complex stuff
        and circular references stripped out.
        :return: dict
        """
        savedata = {}
        open_references = {}
        savedata['kataja_plugin_name'] = prefs.active_plugin_name
        self.save_object(savedata, open_references)
        max_rounds = 10
        c = 0
        while open_references and c < max_rounds:
            c += 1
            # print(len(savedata))
            # print('---------------------------')
            for obj in list(open_references.values()):
                if hasattr(obj, 'uid'):
                    obj.save_object(savedata, open_references)
                else:
                    print('cannot save open reference object ', obj)
        assert (c < max_rounds)
        print('total savedata: %s chars in %s items.' % (len(str(savedata)), len(savedata)))
        # print(savedata)
        return savedata

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    forests = SavedField("forests")
    current_index = SavedField("current_index")
    forest = SavedField("forest")
    lexicon = SavedField("lexicon")
