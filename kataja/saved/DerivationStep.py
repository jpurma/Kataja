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

### NEED TO RETHINK DERIVATION STEP SYSTEM  -- PEN AND PAPER TIME ###

from kataja.singletons import ctrl, log
from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from kataja.utils import time_me


# Thinking about undo system. It should be a common class Undoable inherited
# by everyone. It contains few methods: start_undoable_operation,
# add_undoable_field, finish_undoable_operation.
# these all should operate on global dict, where each add_undoable_field
# would announce the item and the field.
from kataja.syntactic_state_to_nodes import syntactic_state_to_nodes


class DerivationStep(SavedObject):
    """ Packed state of syntactic objects for stepwise animation of trees growth.
     """

    def __init__(self, synobjs=None, numeration=None, other=None, msg=None, gloss=None,
                 transferred=None, mover=None, uid=None):
        super().__init__(uid=uid)
        self.synobjs = synobjs or []
        self.numeration = numeration
        self.other = other
        self.msg = msg
        self.gloss = gloss
        self.transferred = transferred
        self.mover = mover

    def __str__(self):
        return "DS(" + str(self.synobjs) + ", " + str(self.numeration) + ", " + str(self.other) \
               + ", '" + str(self.msg) + "')"


    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    synobjs = SavedField("synobjs")
    numeration = SavedField("numeration")
    other = SavedField("other")
    msg = SavedField("msg")
    gloss = SavedField("gloss")
    transferred = SavedField("transferred")
    mover = SavedField("mover")


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

    def save_and_create_derivation_step(self, synobjs, numeration=None, other=None, msg='',
                                        gloss='', transferred=None, mover=None):
        """ Ok, new idea: derivation steps only include syntactic objects. Nodes etc. will be
        created in the fly. No problems from visualisations misbehaving, chains etc.
        :param synobjs: list of syntactic objects present in this snapshot
        :param numeration: optional list of items
        :param other: optional arbitrary data to store (must be Saveable or primitive data
        structures!)
        :param msg: optional message about derivation, to float when switching between derivations
        :param gloss: optional gloss for derivation
        :param transferred: items that have been transferred/spelt out
        :return:
        """
        d_step = DerivationStep(synobjs, numeration, other, msg, gloss, transferred, mover)
        # Use Kataja's save system to freeze objects into form where they can be stored and restored
        # without further changes affecting them.
        savedata = {}
        open_references = {}
        d_step.save_object(savedata, open_references)
        c = 0
        max_depth = 100 # constituent trees can be surprisingly deep, and we don't have any
        # general dict about them.
        while open_references and c < max_depth:
            c += 1
            for obj in list(open_references.values()):
                if hasattr(obj, 'uid'):
                    #print('saving obj ', obj.uid)
                    obj.save_object(savedata, open_references)
                else:
                    print('cannot save open reference object ', obj)
        assert(c < max_depth) # please raise the max depth if this is reached
        self.derivation_steps.append((d_step.uid, savedata, msg))

#    @time_me
    def restore_derivation_step(self):
        if self.derivation_steps:
            uid, frozen_data, msg = self.derivation_steps[self.derivation_step_index]
            d_step = DerivationStep(uid=uid)
            d_step.load_objects(frozen_data, ctrl.main)
            self.activated = True
            self.current = d_step

            syntactic_state_to_nodes(self.forest, d_step.synobjs, msg)
            if msg:
                log.info(msg)

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
        return self.derivation_step_index == 0

    def is_last(self):
        return self.derivation_step_index == len(self.derivation_steps) - 1

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    derivation_steps = SavedField("derivation_steps")
    derivation_step_index = SavedField("derivation_step_index", watcher="forest_changed")
    forest = SavedField("forest")
