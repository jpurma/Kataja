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

from kataja.singletons import log, ctrl
from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from kataja.syntactic_state_to_nodes import syntactic_state_to_nodes
from kataja.syntax.SyntaxState import SyntaxState
from kataja.saved.DerivationStep import DerivationStep


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

    def save_and_create_derivation_step(self, syn_state: SyntaxState):
        """ Derivation steps store syntax states. Nodes etc. will be
        then updated and created as necessary the fly.
        :param syn_state: SyntaxState-instance
        :return:
        """
        d_step = DerivationStep(syn_state)
        self.save_derivation_step(d_step)

    def save_derivation_step(self, derivation_step: DerivationStep):
        if not derivation_step.frozen:
            derivation_step.freeze()
        self.d[derivation_step.state_id] = derivation_step.frozen

    def build_active_branch(self):
        b = []
        step = self.d.get(self.current_branch_id, None)
        while step:
            uid, data, msg, state_id, parent_id = step
            b.append(state_id)
            step = self.d.get(parent_id, None)
        self.branch = list(reversed(b))

    def build_branches(self):
        nodes = set(self.d.keys())
        parents = {parent_id for uid, data, msg, state_id, parent_id in self.d.values()}
        self.branches = list(nodes - parents)
        self.branches.sort()
        print('nodes: ', nodes)
        print('parents: ', parents)
        print('nodes - parents: ', nodes - parents)
        print('created branches:', self.branches)

    def update_dimensions(self):
        self.build_branches()

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

    def get_derivation_step_by_index(self, index):
        state_id = self.branch[index]
        return self.get_derivation_step_by_id(state_id)

    def get_derivation_step_by_id(self, state_id):
        uid, frozen_data, msg, state_id, parent_id = self.d[state_id]
        d_step = DerivationStep(None, uid=uid)
        d_step.load_objects(frozen_data)
        return d_step

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

    def add_step(self, syn_state: SyntaxState or DerivationStep):
        """ Store given syntactic state as a derivation step. Forest can switch which derivation
        state it is currently displaying.
        :param syn_state: SyntaxState object
        :return:
        """
        if isinstance(syn_state, DerivationStep):
            self.save_derivation_step(syn_state)
        else:
            self.save_and_create_derivation_step(syn_state)

    def jump_to_starting_derivation(self):
        if self.derivation_step_index is None:
            self.derivation_step_index = len(self.derivation_steps) - 1
        self.jump_to_derivation_step(self.derivation_step_index)

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
        self.current_branch_id = self.branches[parse_index]
        self.build_active_branch()
        self.jump_to_last_step()
        ctrl.main.parse_changed.emit()

    # def _find_matching_parse(self, reverse=False):
    #     tree_roots = [x.syntactic_object for x in self.trees if x.node_type == g.CONSTITUENT_NODE]
    #     if (not tree_roots) or not hasattr(tree_roots[0], 'eq'):
    #         return "Cannot compare trees. Either no tree or constituents don't have 'eq'-comparison method."
    #     if reverse:
    #         tree_indices = range(self.current_parse_index - 1, -1, -1)
    #     else:
    #         tree_indices = range(self.current_parse_index + 1, len(self.derivation_branches))
    #     for tree_index in tree_indices:
    #         parse_tree = self.derivation_branches[tree_index]
    #         ds = parse_tree.derivation_steps
    #         for i in range(0, len(ds.derivation_steps)):
    #             step_data = ds.get_derivation_step(i)
    #             if (len(step_data.tree_roots) == len(tree_roots) and
    #                     all([a.eq(b) for a, b in zip(step_data.tree_roots, tree_roots)])):
    #                 self.current_parse_index = tree_index
    #                 ds.derivation_step_index = i
    #                 ds.jump_to_derivation_step(i)
    #                 ctrl.main.parse_changed.emit()
    #                 return self.current_parse_index, ds.derivation_step_index
    #
    # def find_next_matching_parse(self):
    #     return self._find_matching_parse()
    #
    # def find_previous_matching_parse(self):
    #     return self._find_matching_parse(reverse=True)


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
