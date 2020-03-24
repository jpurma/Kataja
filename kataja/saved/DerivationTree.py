# coding=utf-8
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

from kataja.SavedField import SavedField
from kataja.SavedObject import SavedObject
from kataja.saved.DerivationStep import DerivationStep
from kataja.singletons import log, ctrl
from kataja.syntactic_state_to_nodes import syntactic_state_to_nodes
from kataja.syntax.SyntaxState import SyntaxState

from collections import defaultdict


class DerivationTree(SavedObject):
    """ Stores derivation steps for one forest and takes care of related
    logic """

    def __init__(self, forest=None):
        super().__init__()
        self.forest = forest
        self.d = {}
        self.branches = []  # state_id:s, last step of the branch
        self.branch = []  # state_id:s
        self.current_step_index = 0
        self.current_step_id = 0
        self.current_branch_id = 0  # state_id
        self.current_branch_index = 0
        self.child_map = defaultdict(list)

    def add_step(self, d_step: SyntaxState or DerivationStep):
        """ Store given syntactic state as a derivation step. Forest can switch which derivation
        state it is currently displaying.
        :param d_step: SyntaxState or DerivationStep object
        :return:
        """
        if isinstance(d_step, SyntaxState):
            d_step = DerivationStep(d_step)
        self.save_derivation_step(d_step)

    def save_derivation_step(self, derivation_step: DerivationStep):
        if not derivation_step.frozen:
            derivation_step.freeze()
        self.d[derivation_step.state_id] = derivation_step.frozen

    def build_active_branch(self):
        self.branch = self.build_branch(self.current_branch_id)

    def build_branch(self, branch_id):
        print('building branch...', branch_id)
        b = []
        step = self.d.get(branch_id, None)
        done = set()
        while step:
            uid, data, msg, state_id, parent_id, state_type = step
            b.append(state_id)
            if parent_id in done:
                print('looping branch, at parent ', parent_id)
                break
            step = self.d.get(parent_id, None)
            done.add(parent_id)
        print('...done building branch')
        return list(reversed(b))

    def collect_states(self):
        states = {}
        for key, val in self.d.items():
            state_key = key.rsplit('_', 1)[-1]
            if state_key not in states:
                uid, data, msg, state_id, parent_id, state_type = val
                states[int(state_key)] = msg, state_type
        return states

    def build_branches(self):
        print('building branches...')
        nodes = set(self.d.keys())
        parents = {parent_id for uid, data, msg, state_id, parent_id, state_type in self.d.values()}
        self.branches = list(nodes - parents)
        print('...done building branches')

    def build_child_map(self):
        print('building child map...')
        self.child_map = defaultdict(list)
        for uid, data, msg, state_id, parent_id, state_type in self.d.values():
            if parent_id:
                self.child_map[parent_id].append(state_id)
        print('...done building child map')

    def iterate_branch(self, branch_id):
        step = self.d.get(branch_id, None)
        while step:
            uid, data, msg, state_id, parent_id, state_type = step
            yield state_id
            step = self.d.get(parent_id, None)

    def get_roots(self):
        return [state_id for uid, data, msg, state_id, parent_id, state_type in self.d.values() if not parent_id]

    def update_dimensions(self):
        self.build_branches()
        self.build_child_map()

    #    @time_me
    def restore_derivation_step(self):
        d_step = self.get_derivation_step_by_id(self.current_step_id)
        if d_step:
            syntactic_state_to_nodes(self.forest, d_step.to_syn_state())
            if d_step.msg:
                log.info(f'<b>msg: {d_step.msg}</b>')
            for log_msg in d_step.log:
                if log_msg.strip():
                    log_msg = log_msg.replace("\t", "&nbsp;&nbsp;")
                    log.info(f'<font color="#859900">{log_msg}</font>')
        ctrl.main.parse_changed.emit()

    def get_derivation_step_by_index(self, index):
        state_id = self.branch[index]
        return self.get_derivation_step_by_id(state_id)

    def get_derivation_step_by_id(self, state_id):
        uid, frozen_data, msg, state_id, parent_id, state_type = self.d[state_id]
        d_step = DerivationStep(None, uid=uid)
        d_step.load_objects(frozen_data)
        return d_step

    def _find_branch_for(self, state_id):
        for i, branch in enumerate(self.branches):
            for step_id in self.iterate_branch(branch):
                if step_id == state_id:
                    return branch
        return 0

    def jump_to_derivation_step_by_id(self, state_id):
        self.current_step_id = state_id
        if state_id in self.branch:
            self.current_step_index = self.branch.index(state_id)
        else:
            self.current_branch_id = self._find_branch_for(state_id)
            self.current_branch_index = self.branches.index(self.current_branch_id)
            self.build_active_branch()
            self.current_step_index = self.branch.index(state_id)
        self.restore_derivation_step()

    def next_derivation_step(self):
        """
        :return:
        """
        if self.current_step_index + 1 < len(self.branch):
            self.current_step_index += 1
        else:
            self.current_step_index = 0
        self.current_step_id = self.branch[self.current_step_index]
        self.restore_derivation_step()

    def previous_derivation_step(self):
        """
        :return:
        """
        if self.current_step_index > 0:
            self.current_step_index -= 1
        else:
            self.current_step_index = len(self.branch) - 1
        self.current_step_id = self.branch[self.current_step_index]
        self.restore_derivation_step()

    def jump_to_derivation_step(self, i):
        """
        :return:
        """
        self.current_step_index = i
        self.current_step_id = self.branch[self.current_step_index]
        self.restore_derivation_step()

    def jump_to_first_step(self):
        self.jump_to_derivation_step(0)

    def jump_to_last_step(self):
        self.jump_to_derivation_step(len(self.branch) - 1)

    def next_parse(self):
        if self.current_branch_index + 1 < len(self.branches):
            self.current_branch_index += 1
        else:
            self.current_branch_index = 0
        self.show_parse(self.current_branch_index)

    def previous_parse(self):
        if self.current_branch_index > 0:
            self.current_branch_index -= 1
        else:
            self.current_branch_index = len(self.branches) - 1
        self.show_parse(self.current_branch_index)

    def show_parse(self, parse_index):
        if self.branches:
            self.current_branch_id = self.branches[parse_index]
            self.build_active_branch()
            self.jump_to_last_step()
            ctrl.main.parse_changed.emit()

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    forest = SavedField("forest")
    d = SavedField("d")
    branches = SavedField("branches")
    branch = SavedField("branch")
    current_step_index = SavedField("current_step_index")
    current_step_id = SavedField("current_step_id")
    current_branch_index = SavedField("current_branch_index")
    current_branch_id = SavedField("current_branch_id")
