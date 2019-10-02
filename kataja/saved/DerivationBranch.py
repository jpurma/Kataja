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

from kataja.singletons import log
from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from kataja.syntactic_state_to_nodes import syntactic_state_to_nodes
from kataja.syntax.SyntaxState import SyntaxState
from kataja.saved.DerivationStep import DerivationStep


class DerivationBranch(SavedObject):
    """ Stores derivation steps for one forest and takes care of related
    logic """

    def __init__(self, forest=None):
        super().__init__()
        self.forest = forest
        self.activated = False
        self.current = None
        self.derivation_steps = []
        self.derivation_step_index = None

    def save_and_create_derivation_step(self, syn_state: SyntaxState):
        """ Derivation steps store syntax states. Nodes etc. will be
        then updated and created as necessary the fly.
        :param syn_state: SyntaxState-instance
        :return:
        """
        d_step = DerivationStep(syn_state)
        # Use Kataja's save system to freeze objects into form where they can be stored and restored
        # without further changes affecting them.
        d_step.freeze()
        self.derivation_steps.append(d_step.frozen)

    def save_derivation_step(self, derivation_step: DerivationStep):
        if not derivation_step.frozen:
            derivation_step.freeze()
        self.derivation_steps.append(derivation_step.frozen)

    def remove_iterations(self, iterations):
        """ There may be derivation steps that have been created during the parse but are
        found redundant or not interesting and that they should be removed. They can be
        removed by their iteration index
        :param iterations: list of iterations, all of these will be removed if found.
        :return:
        """
        print(f'removing {len(iterations)} iterations.')
        self.derivation_steps = [(uid, data, msg, i, parent_uid) for uid, data, msg, i, parent_uid
                                 in self.derivation_steps
                                 if i not in iterations]

    #    @time_me
    def restore_derivation_step(self):
        if self.derivation_steps:
            uid, frozen_data, msg, i, parent_uid = self.derivation_steps[self.derivation_step_index]
            d_step = DerivationStep(None, uid=uid, parent_uid=parent_uid)
            d_step.load_objects(frozen_data)
            self.activated = True
            self.current = d_step
            syntactic_state_to_nodes(self.forest, d_step.to_syn_state())
            if d_step.msg:
                log.info(f'<b>msg: {d_step.msg}</b>')
            for log_msg in d_step.log:
                if log_msg.strip():
                    log_msg = log_msg.replace("\t", "&nbsp;&nbsp;")
                    log.info(f'<font color="#859900">{log_msg}</font>')

    def get_derivation_step(self, index):
        if self.derivation_steps:
            uid, frozen_data, msg, i, parent_uid = self.derivation_steps[index]
            d_step = DerivationStep(None, uid=uid, parent_uid=parent_uid)
            d_step.load_objects(frozen_data)
            return d_step

    def next_derivation_step(self):
        """
        :return:
        """
        if self.derivation_step_index is None or self.derivation_step_index + 1 >= len(self.derivation_steps):
            self.derivation_step_index = 0
        else:
            self.derivation_step_index += 1
        self.restore_derivation_step()

    def previous_derivation_step(self):
        """
        :return:
        """
        if self.derivation_step_index is None or self.derivation_step_index == 0:
            self.derivation_step_index = len(self.derivation_steps) - 1
        else:
            self.derivation_step_index -= 1
        self.restore_derivation_step()

    def jump_to_derivation_step(self, i):
        """
        :return:
        """
        self.derivation_step_index = i
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


    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    derivation_steps = SavedField("derivation_steps")
    derivation_step_index = SavedField("derivation_step_index")  # , watcher=ctrl.main.forest_changed)
    forest = SavedField("forest")
