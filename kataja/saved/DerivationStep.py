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

from kataja.singletons import ctrl, log
from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from kataja.utils import time_me
from kataja.syntactic_state_to_nodes import syntactic_state_to_nodes
from syntax.SyntaxState import SyntaxState


# Thinking about undo system. It should be a common class Undoable inherited
# by everyone. It contains few methods: start_undoable_operation,
# add_undoable_field, finish_undoable_operation.
# these all should operate on global dict, where each add_undoable_field
# would announce the item and the field.


class DerivationStep(SavedObject):
    """ Saveable SyntaxState.
     """

    def __init__(self, syn_state, uid=None):
        super().__init__(uid=uid)
        if syn_state:
            self.tree_roots = syn_state.tree_roots
            self.numeration = syn_state.numeration
            self.msg = syn_state.msg
            self.gloss = syn_state.gloss
            self.transferred = syn_state.transferred
            self.marked = syn_state.marked
            self.semantic_hierarchies = syn_state.semantic_hierarchies
            self.iteration = syn_state.iteration
        else:
            self.tree_roots = []
            self.numeration = []
            self.msg = ''
            self.gloss = ''
            self.transferred = []
            self.marked = []
            self.semantic_hierarchies = []
            self.iteration = 0

    def __str__(self):
        return "DS(" + str(self.synobjs) + ", " + str(self.numeration) + ", " + str(
            self.other) + ", '" + str(self.msg) + "')"

    def to_syn_state(self):
        return SyntaxState(tree_roots=self.tree_roots, numeration=self.numeration, msg=self.msg,
                           gloss=self.gloss, transferred=self.transferred, marked=self.marked,
                           semantic_hierarchies=self.semantic_hierarchies,
                           iteration=self.iteration)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    tree_roots = SavedField("tree_roots")
    numeration = SavedField("numeration")
    msg = SavedField("msg")
    gloss = SavedField("gloss")
    transferred = SavedField("transferred")
    marked = SavedField("marked")
    semantic_hierarchies = SavedField("semantic_hierarchies")
    iteration = SavedField("iteration")


class DerivationStepManager(SavedObject):
    """ Stores derivation steps for one forest and takes care of related
    logic """

    def __init__(self, forest=None):
        super().__init__()
        self.forest = forest
        self.activated = False
        self.current = None
        self.derivation_steps = []
        self.derivation_step_index = 0

    def save_and_create_derivation_step(self, syn_state: SyntaxState):
        """ Derivation steps store syntax states. Nodes etc. will be
        then updated and created as necessary the fly.
        :param syn_state: SyntaxState-instance
        :return:
        """
        d_step = DerivationStep(syn_state)
        # Use Kataja's save system to freeze objects into form where they can be stored and restored
        # without further changes affecting them.
        savedata = {}
        open_references = {}
        d_step.save_object(savedata, open_references)
        c = 0
        max_depth = 100  # constituent trees can be surprisingly deep, and we don't have any
        # general dict about them.
        while open_references and c < max_depth:
            c += 1
            for obj in list(open_references.values()):
                if hasattr(obj, 'uid'):
                    # print('saving obj ', obj.uid)
                    obj.save_object(savedata, open_references)
                else:
                    print('cannot save open reference object ', obj)
        assert (c < max_depth)  # please raise the max depth if this is reached
        self.derivation_steps.append((d_step.uid, savedata, d_step.msg, d_step.iteration))

    def remove_iterations(self, iterations):
        """ There may be derivation steps that have been created during the parse but are
        found redundant or not interesting and that they should be removed. They can be
        removed by their iteration index
        :param iterations: list of iterations, all of these will be removed if found.
        :return:
        """
        print('removing iterations ', iterations)
        self.derivation_steps = [(uid, data, msg, i) for uid, data, msg, i
                                 in self.derivation_steps
                                 if i not in iterations]

    #    @time_me
    def restore_derivation_step(self):
        if self.derivation_steps:
            uid, frozen_data, msg, i = self.derivation_steps[self.derivation_step_index]
            d_step = DerivationStep(None, uid=uid)
            d_step.load_objects(frozen_data, ctrl.main)
            self.activated = True
            self.current = d_step
            syntactic_state_to_nodes(self.forest, d_step.to_syn_state())
            if d_step.msg:
                log.info(d_step.msg)

    def next_derivation_step(self):
        """
        :return:
        """
        if self.derivation_step_index + 1 >= len(self.derivation_steps):
            return
        self.derivation_step_index += 1
        self.restore_derivation_step()

    def previous_derivation_step(self):
        """
        :return:
        """
        if self.derivation_step_index == 0:
            return
        self.derivation_step_index -= 1
        self.restore_derivation_step()

    def jump_to_derivation_step(self, i):
        """
        :return:
        """
        self.derivation_step_index = i
        self.restore_derivation_step()

    def is_first(self):
        return self.derivation_step_index == 0 or not self.derivation_steps

    def is_last(self):
        return (not self.derivation_steps) or (
            self.derivation_step_index == len(self.derivation_steps) - 1)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    derivation_steps = SavedField("derivation_steps")
    derivation_step_index = SavedField("derivation_step_index", watcher="forest_changed")
    forest = SavedField("forest")
