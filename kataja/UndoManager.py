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

# Creation/Deletion flags
CREATED = 1
DELETED = 2

class UndoManager:
    """ Holds the undo stack and manages the undo- and redo-activities. """

    def __init__(self, forest):
        self.save_key = forest.save_key + '_undo_manager'
        self.forest = forest
        self.full_state = {}
        self._stack = []
        self._current = 0
        self.phase = 'new'

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
            transitions, transition_type = obj.model.transitions()
            snapshot[obj.save_key] = (obj, transitions, transition_type)
        # ...
        if snapshot:
            self._stack = self._stack[:self._current + 1]
            self._stack.append((msg, snapshot))
            self._current = len(self._stack) - 1
            print('snapshot: %s items in stack of %s snapshots' % (len(snapshot), len(self._stack)))
        ctrl.undo_pile = set()
        self.phase = 'new'

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
        if not self._stack:
            return
        if self.phase == 'old':
            if self._current > 0:
                self._current -= 1
                self.phase = 'new'
            else:
                ctrl.add_message('undo [%s]: Cannot undo further' % self._current)
                return
        ctrl.disable_undo = True
        msg, snapshot = self._stack[self._current]
        print('undo: ', msg, snapshot)
        for obj, transitions, transition_type in snapshot.values():
            obj.model.revert_to_earlier(transitions)
            if transition_type == CREATED:
                print('undo should undo creation of object (=>cancel) ', obj)
                ctrl.forest.delete_item(obj)
            elif transition_type == DELETED:
                print('undo should undo deletion of object (=>revive)', obj)
                ctrl.forest.add_to_scene(obj)
        for obj, transitions, transition_type in snapshot.values():
            obj.model.update(transitions.keys(), transition_type)
        self.phase = 'old'
        ctrl.add_message('undo [%s]: %s' % (self._current, msg))
        ctrl.disable_undo = False

    def redo(self):
        """ Move forward in the undo stack
        :return: None
        """
        if self.phase == 'new':
            if self._current < len(self._stack) - 1:
                self._current += 1
                self.phase = 'old'
            else:
                ctrl.add_message('redo [%s]: In last action' % self._current)
                return
        ctrl.disable_undo = True
        msg, snapshot = self._stack[self._current]
        print('redo: ', msg, snapshot)
        for obj, transitions, transition_type  in snapshot.values():
            obj.model.move_to_later(transitions)
            if transition_type == CREATED:
                print('redo should recreate object ', obj)
                ctrl.forest.add_to_scene(obj)
            elif transition_type == DELETED:
                print('redo should delete object', obj)
                ctrl.forest.delete_item(obj)
        for obj, transitions, transition_type  in snapshot.values():
            obj.model.update(transitions.keys(), transition_type)
        ctrl.add_message('redo [%s]: %s' % (self._current, msg))
        self.phase = 'new'
        ctrl.disable_undo = False

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
