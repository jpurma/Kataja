# -*- coding: UTF-8 -*-
#############################################################################
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
#############################################################################


from kataja.utils import time_me, save_object, load_objects
from Controller import ctrl


class UndoManager:
    # if _stack is saved, the save files can become really large, but undo works beyond load point.
    #saved_fields = ['forest', '_stack', '_current']
    saved_fields = ['forest']

    def __init__(self, forest):
        self.save_key = forest.save_key + '_undo_manager'
        self.forest = forest
        self.full_state = {}
        self._stack = []
        self._msg_stack = []
        self._current = 0

    def init_if_empty(self):
        if not self.full_state:
            self.record('starting undo')

    @time_me
    def take_snapshot(self):
        saved_objects = {}
        open_refs = {}
        save_object(self.forest, saved_objects, open_refs, ignore=['undo_manager'])
        saved_objects['start_key'] = self.forest.save_key
        c = 0
        while open_refs and c < 10:
            c += 1
            for obj in open_refs.values():
                save_object(obj, saved_objects, open_refs)
        print 'total savedata: %s chars.' % len(str(saved_objects))
        return saved_objects


    def record(self, msg=''):
        """
                           /------\
        self.full_state =  |  XXX |
                           \------/



        self._stack =  [, i-1: +- diff of previous state-1 and full_state ,   i: +- diff of previous_state and full_state)]
        """
        print '*** undo manager: recording %s' % msg
        saved_objects = self.take_snapshot()

        # Undo stack is cut 
        print 'pre-cut stack size: %s, current index %s' % (len(self._stack), self._current)
        self._stack = self._stack[:self._current]
        self._msg_stack = self._msg_stack[:self._current]
        print 'cut stack size: %s, current index %s' % (len(self._stack), self._current)
        if self.full_state:
            diff = self.compare_saved_dicts(self.full_state, saved_objects)
            print 'diff size: ', len(str(diff))
            self._stack.append(diff)
            self._msg_stack.append(msg)
        self._current = len(self._stack)
        saved_objects['stack_index'] = self._current
        self.full_state = saved_objects
        print 'recorded stack and updated full state. stack size & current index: %s' % len(self._stack)

    def compare_saved_dicts(self, d1, d2):
        d2_missing = {}
        d2_has_more = dict(d2)
        diffs = {}
        for key, i1 in d1.items():
            if key not in d2:
                d2_missing[key] = i1
                continue
            else:
                del d2_has_more[key]
            i2 = d2[key]
            if isinstance(i1, dict):
                diff = self.compare_saved_dicts(i1, i2)
                if diff:
                    diffs[key] = diff
            elif i1 != i2:
                diffs[key] = {'old': i1, 'new': i2}
        if d2_missing or d2_has_more:
            if d2_missing:
                diffs['--'] = d2_missing
            if d2_has_more:
                diffs['++'] = d2_has_more
        return diffs

    @time_me
    def restore(self):
        if not self._stack:
            return
        to_be_deleted = {}

        def _restore_older(state, diff):
            for key, item in diff.items():
                if isinstance(item, dict) and len(item) == 2 and 'old' in item and 'new' in item:
                    # restore older value 
                    if item['new'] != state[key]:
                        print "weird, state should have the 'new' value of diff: %s %s" % (item['new'], state[key])
                        raise
                    else:
                        #print 'replaced %s (%s) with %s' % (key, state[key], item['old'])
                        state[key] = item['old']
                elif key == '++':
                    # remove these objects from state
                    for dkey in item.keys():
                        print 'del ', dkey
                        to_be_deleted[dkey] = state[dkey]
                        del state[dkey]
                elif key == '--':
                    # restore these objects to state
                    for akey, aitem in item.items():
                        state[akey] = aitem
                elif key in state:
                    _restore_older(state[key], item)

        def _restore_newer(state, diff):
            for key, item in diff.items():
                if isinstance(item, dict) and len(item) == 2 and 'old' in item and 'new' in item:
                    # restore older value 
                    if item['old'] != state[key]:
                        print "weird, state should have the 'old' value of diff: %s %s" % (item['old'], state[key])
                        raise
                    else:
                        #print 'replaced %s (%s) with %s' % (key, state[key], item['new'])
                        state[key] = item['new']
                elif key == '++':
                    # restore these objects to state
                    for akey, aitem in item.items():
                        state[akey] = aitem
                elif key == '--':
                    # remove these objects from state
                    for dkey in item.keys():
                        print 'del ', dkey
                        to_be_deleted[dkey] = state[dkey]
                        del state[dkey]
                elif key in state:
                    _restore_newer(state[key], item)


        print "full state's stack index: ", self.full_state['stack_index']
        if self._current < self.full_state['stack_index']:
            _restore_older(self.full_state, self._stack[self._current])
        elif self._current > self.full_state['stack_index']:
            _restore_newer(self.full_state, self._stack[self._current - 1])
        elif self._current == self.full_state['stack_index']:
            print 'shouldnt restore to the current full state'

        self.full_state['stack_index'] = self._current
        print 'modified the state, next we should restore forest to that state'
        print 'current stack index and state: %s' % self._current
        print 'to be deleted: ', to_be_deleted
        #forest_data = self.full_state[self.full_state['start_key']]
        load_objects(self.forest, self.full_state)
        self.forest.main.graph_scene.draw_forest(self.forest)


    def undo(self):
        self._current -= 1
        if self._current < 0:
            self._current = 0
            ctrl.add_message('cannot undo')
        else:
            ctrl.add_message('undo - %s (%s)' % (self._msg_stack[self._current], self._current))
            print 'undoing to stack index %s' % self._current
            self.restore()


    def redo(self):
        self._current += 1
        if self._current > len(self._stack):
            self._current = len(self._stack)
            ctrl.add_message('cannot redo')
        else:
            ctrl.add_message('redo - %s (%s)' % (self._msg_stack[self._current - 1], self._current))
            print 'redoing to stack index %s' % (self._current - 1)
            self.restore()

            # def repair_later(self, item):
            #     self._repair_list.append(item)
