# -*- coding: UTF-8 -*-
""" UndoManager is an object in a forest to store the previous states of the forest and to restore these states.
"""
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
import pprint

from kataja.utils import time_me
from kataja.singletons import ctrl


class UndoManager:
    """ Holds the undo stack and manages the undo- and redo-activities. """

    def __init__(self, forest):
        self.save_key = forest.save_key + '_undo_manager'
        self.forest = forest
        self.full_state = {}
        self._stack = []
        self._current = 0

    @time_me
    def init_if_empty(self):
        """ Not sure if we need this, but keep it for now.
        :return: None """
        pass
        # if not self.full_state:
        #     self.record_full_state()
        # print('full state: ', len(self.full_state))

    @time_me
    def take_snapshot(self, msg=''):
        """ Store changes from ctrl.undo_pile and put them here into undo_stack.
        :param msg: str = msg to
        :return: None
        """
        print('--- taking snapshot:%s ' % msg)
        # save objects in undo pile
        snapshot = {}
        for obj in ctrl.undo_pile:
            snapshot[obj.save_key] = (obj, obj.model.changes())
        # ...
        self._stack = self._stack[:self._current + 1]
        self._stack.append((msg, snapshot))
        self._current = len(self._stack) - 1
        print('snapshot: %s items in stack of %s snapshots' % (len(snapshot), len(self._stack)))
        ctrl.undo_pile = set()

    # def record_full_state(self):
    #     """ Iterates through all items in forest and puts them to the full_state -dict.
    #     This needs to be done before undo, in order to get the objects that may be affected into one place.
    #     :return: None
    #     """
    #     self.full_state = {'stack_index': self._current}
    #     open_refs = {}
    #     self.forest.model.save_object(self.full_state, open_refs)
    #     self.full_state['start_key'] = self.forest.save_key
    #     c = 0
    #     while open_refs and c < 10:
    #         c += 1
    #         for obj in list(open_refs.values()):
    #             obj.model.save_object(self.full_state, open_refs)

    def undo(self):
        """ Move backward in the undo stack
        :return: None
        """
        msg, snapshot = self._stack[self._current]
        for obj, changes in snapshot.values():
            obj.model.revert_to_earlier(changes)
        for obj, changes in snapshot.values():
            obj.model.update(changes)
        ctrl.add_message('undo [%s]: %s' % (self._current, msg))
        if self._current > 0:
            self._current -= 1

    def redo(self):
        """ Move forward in the undo stack
        :return: None
        """
        msg, snapshot = self._stack[self._current]
        for obj, changes in snapshot.values():
            obj.model.move_to_later(changes)
        for obj, changes in snapshot.values():
            obj.model.update(changes)
        ctrl.add_message('redo [%s]: %s' % (self._current, msg))
        if self._current < len(self._stack) - 1:
            self._current += 1

    @staticmethod
    def dump_dict_to_file(undo_dict, filename='undo_dump'):
        """ Debug method, does what it says.
        :param undo_dict: can be any dict
        :param filename: default is 'undo_dump'
        """
        f = open(filename, 'w')
        pp = pprint.PrettyPrinter(indent=4, stream=f)
        pp.pprint(undo_dict)
        f.close()
