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


import pickle

from .Controller import ctrl
from .Forest import Forest


class ForestKeeper:
    """

    """
    saved_fields = ['main', '_forests', '_forests_dict', '_i', 'forest']
    singleton_key = 'ForestKeeper'

    def __init__(self, main, treelist=None, file_name=None):
        """

        :param MainWindow main:
        :param List treelist:
        :param StringType file_name:
        """
        if not treelist:
            treelist = []
        self.main = main
        self._forests = []
        self._forests_dict = {}
        self._i = 0
        self.forest = None
        if treelist:
            self.create_forests(treelist)
        elif file_name:
            self.create_forests_from_file(file_name)

    def get_forest(self, key):
        """
        Return one forest
        :param key:
        :param str key:
        """
        if key in self._forests_dict:
            return self._forests_dict[key]
        else:
            return None

    def all(self):
        """


        :return:
        """
        return self._forests

    def get_forests(self):
        """


        :return:
        """
        return self._forests

    def next_forest(self):
        """


        :return:
        """
        if not self._forests:
            return None
        if self._i < len(self._forests) - 1:
            self._i += 1
        else:
            self._i = 0
        self.forest = self._forests[self._i]
        return self._i, self.forest

    def prev_forest(self):
        """


        :return:
        """
        if not self._forests:
            return None
        if self._i > 0:
            self._i -= 1
        else:
            self._i = len(self._forests) - 1
        self.forest = self._forests[self._i]
        return self._i, self.forest

    def size(self):
        """


        :return:
        """
        return len(self._forests)

    def current_index(self):
        """


        :return:
        """
        return self._i

    def load(self, data):
        """


        :param data:
        :param dict data:
        """
        self._i = data['_i']
        self._forests = data['_forests']
        self._forests_dict = dict([(f.save_key, f) for f in self._forests])
        for key, item in list(ctrl.unassigned_objects.items()):
            forest = self.get_forest(item.forest_key)
            if not forest:
                assert False
            forest.store(item)
            item._finalize()
            del ctrl.unassigned_objects[key]
        # ## Second round, creating secondary items like brackets and chains
        for forest in self._forests:
            self.main.set_forest(forest)
            forest.rebuild_brackets()
            if not forest.settings.uses_multidomination():
                forest.rebuild_chains()
        for key, item in list(ctrl.unassigned_objects.items()):
            # print 'storing %s to %s' % (key, item.forest_key)
            forest = self.get_forest(item.forest_key)
            if not forest:
                assert False
            forest.store(item)
            del ctrl.unassigned_objects[key]

        # ctrl.set_forest(forest)
        #     print forest.info_dump()
        #     forest.undo_manager.finalize_objects()
        #     for node in forest.nodes.values():
        #         if not node._label_complex:
        #             print 'missing label for ', node, node.save_key
        #     #pass # finalize forest
        self.forest = self._forests[self._i]
        self.main.set_forest(self.forest)

    def save(self):
        """


        :return:
        """
        data = {'_i': self._i, '_forests': self._forests}
        return data

    def save_safe(self):
        """


        """
        savedata = {'_i': self._i, '_forests_pickled': []}
        for forest in self._forests:
            self.main.set_forest(forest)
            dump = pickle.dumps(forest, 0)
            savedata['forest_keeper'].append(dump)


    def create_forests_from_file(self, filename):
        """


        :param filename:
        :param StringType filename:
        """
        # f = codecs.open(filename, 'rb', encoding = 'utf-8')
        f = open(filename, 'rb')
        treelist = f.readlines()
        f.close()
        self.create_forests(treelist)

    def create_forests(self, treelist):
        """


        :param treelist:
        :param list treelist:
        """
        self._forests = []
        self._forests_dict = {}
        forest = None
        buildstring = ''
        for line in treelist:
            line = line.strip()
            parts = line.split('=', 1)
            if line.startswith('#'):
                if forest:
                    forest.add_comment(line[1:])
                else:
                    pass
            elif len(parts) > 1:
                if not forest:
                    forest = Forest(self.main)
                    self.main.set_forest(forest)
                word = parts[0].strip()
                values = parts[1]
                forest._parser.add_definition(word, values)
                # if key== '\gll':
                # forest.setGloss(line)
            elif line.startswith("'"):
                if forest:
                    if line.endswith("'"):
                        line = line[:-1]
                    forest.set_gloss_text(line[1:])
            elif forest and not line:  # finalize this forest
                forest.build(buildstring)
                self._forests.append(forest)
                self._forests_dict[forest.save_key] = forest
                forest = None
            elif line and not forest:  # start a new forest
                buildstring = line
                forest = Forest(self.main)
                self.main.set_forest(forest)
        if forest:  # make sure that the last forest is also added
            forest.build(buildstring)
            self._forests.append(forest)
            self._forests_dict[forest.save_key] = forest
        self._i = 0
        if self._forests:
            if self.forest:
                self.forest.clear_scene()
            self.forest = self._forests[0]
            self.forest.undo_manager.init_if_empty()
            # self.save()



