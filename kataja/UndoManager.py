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
    """

    """

    def __init__(self, forest):
        #self.save_key = forest.save_key + '_undo_manager'
        self.forest = forest
        self.full_state = {}
        self._stack = []
        self._msg_stack = []
        self._current = 0

    @time_me
    def init_if_empty(self):
        """ Not sure if we need this, but keep it for now.
        """
        if not self.full_state:
            self.record_full_state()
        print('full state: ', len(self.full_state))

    @time_me
    def take_snapshot(self, msg=''):
        """ Store changes from ctrl.undo_pile and put them here into undo_stack.
        :return: None
        """
        print('--- taking snapshot:%s ' % msg)
        #print('undo pile:', ctrl.undo_pile)
        print('undo pile len:', len(ctrl.undo_pile))
        # save objects in undo pile
        snapshot = {}
        for obj in ctrl.undo_pile:
            snapshot[obj.save_key] = obj.model.changes()
        # ...
        print('snapshot: %s items' % len(snapshot))
        ctrl.undo_pile = set()

    def record_full_state(self):
        """ Iterates through all items in forest and puts them to the full_state -dict.
        This needs to be done before undo, in order to get the objects that may be affected into one place.
        :return: None
        """
        self.full_state = {}
        self.full_state['stack_index'] = self._current
        open_refs = {}
        self.forest.model.save_object(self.full_state, open_refs)
        self.full_state['start_key'] = self.forest.save_key
        c = 0
        while open_refs and c < 10:
            c += 1
            for obj in list(open_refs.values()):
                obj.model.save_object(self.full_state, open_refs)


    # def record(self, msg=''):
    #     """
    #                        /------\
    #     self.full_state =  |  XXX |
    #                        \------/
    #
    #
    #
    #     :param msg:
    #     self._stack =  [, i-1: +- diff of previous state-1 and full_state ,   i: +- diff of previous_state and full_state)]
    #     """
    #     saved_objects = self.take_snapshot()
    #
    #     # Undo stack is cut
    #     self._stack = self._stack[:self._current]
    #     self._msg_stack = self._msg_stack[:self._current]
    #     if self.full_state:
    #         diff = self.compare_saved_dicts(self.full_state, saved_objects)
    #         self._stack.append(diff)
    #         self._msg_stack.append(msg)
    #         # self.dump_dict_to_file(diff)
    #
    #     self._current = len(self._stack)
    #     saved_objects['stack_index'] = self._current
    #     self.full_state = saved_objects
    #
    # def compare_saved_dicts(self, d1, d2):
    #     """
    #
    #     :param d1:
    #     :param d2:
    #     :return:
    #     """
    #     d2_missing = {}
    #     d2_has_more = dict(d2)
    #     diffs = {}
    #     for key, i1 in d1.items():
    #         if key not in d2:
    #             d2_missing[key] = i1
    #             continue
    #         else:
    #             del d2_has_more[key]
    #         i2 = d2[key]
    #         if isinstance(i1, dict):
    #             diff = self.compare_saved_dicts(i1, i2)
    #             if diff:
    #                 diffs[key] = diff
    #         elif i1 != i2:
    #             diffs[key] = {'old': i1, 'new': i2}
    #     if d2_missing or d2_has_more:
    #         if d2_missing:
    #             diffs['--'] = d2_missing
    #         if d2_has_more:
    #             diffs['++'] = d2_has_more
    #     return diffs

    def undo(self):
        """ Move backward in the undo stack
        :return: None
        """
        to_be_deleted = {}

        def _restore_older(state, diff):
            # fixme: this is not how changes are stored
            for key, item in diff.items():
                if isinstance(item, dict) and len(item) == 2 and 'old' in item and 'new' in item:
                    # restore older value
                    if item['new'] != state[key]:
                        print("weird, state should have the 'new' value of diff: %s %s" % (item['new'], state[key]))
                        raise Exception("Weird state to restore")
                    else:
                        # print 'replaced %s (%s) with %s' % (key, state[key], item['old'])
                        state[key] = item['old']
                elif key == '++':
                    # remove these objects from state
                    for dkey in item.keys():
                        to_be_deleted[dkey] = state[dkey]
                        del state[dkey]
                elif key == '--':
                    # restore these objects to state
                    for akey, aitem in item.items():
                        state[akey] = aitem
                elif key in state:
                    _restore_older(state[key], item)

        if self._current > 0:
            self._current -= 1
            ctrl.add_message('undo - %s (%s)' % (self._msg_stack[self._current], self._current))

            _restore_older(self.full_state, self._stack[self._current])

            self.full_state['stack_index'] = self._current
            self.forest.load_objects(self.full_state, ctrl.main)
            self.forest.main.graph_scene.draw(self.forest)
        else:
            ctrl.add_message('cannot undo')

    def redo(self):
        """ Move forward in the undo stack.
        :return: None
        """
        to_be_deleted = {}

        def _restore_newer(state, diff):
            for key, item in diff.items():
                # fixme: this is not how changes are stored
                if isinstance(item, dict) and len(item) == 2 and 'old' in item and 'new' in item:
                    # restore older value
                    if item['old'] != state[key]:
                        print("weird, state should have the 'old' value of diff: %s %s" % (item['old'], state[key]))
                        raise Exception("Weird state to restore")
                    else:
                        # print 'replaced %s (%s) with %s' % (key, state[key], item['new'])
                        state[key] = item['new']
                elif key == '++':
                    # restore these objects to state
                    for akey, aitem in item.items():
                        state[akey] = aitem
                elif key == '--':
                    # remove these objects from state
                    for dkey in item.keys():
                        to_be_deleted[dkey] = state[dkey]
                        del state[dkey]
                elif key in state:
                    _restore_newer(state[key], item)

        if self._current < len(self._stack) - 1:
            self._current += 1
            ctrl.add_message('redo - %s (%s)' % (self._msg_stack[self._current - 1], self._current))

            _restore_newer(self.full_state, self._stack[self._current - 1])

            self.full_state['stack_index'] = self._current
            self.forest.load_objects(self.full_state, ctrl.main)
            self.forest.main.graph_scene.draw(self.forest)
        else:
            ctrl.add_message('cannot redo')

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
