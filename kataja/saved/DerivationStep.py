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

from kataja.singletons import ctrl
from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField


# Thinking about undo system. It should be a common class Undoable inherited
# by everyone. It contains few methods: start_undoable_operation,
# add_undoable_field, finish_undoable_operation.
# these all should operate on global dict, where each add_undoable_field
# would announce the item and the field.


class DerivationStep(SavedObject):
    """ Packed state of syntactic objects for stepwise animation of trees growth.
     """

    def __init__(self, synobjs, numeration, other, msg):
        super().__init__()
        self.synobjs = synobjs
        self.numeration = numeration
        self.other = other
        self.msg = msg

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    synobjs = SavedField("synobjs")
    numeration = SavedField("numeration")
    other = SavedField("other")
    msg = SavedField("msg")


class DerivationStepManager(SavedObject):
    """ Stores derivation steps for one forest and takes care of related
    logic """

    def __init__(self, forest=None):
        super().__init__()
        self.forest = forest
        self.current = None
        self.derivation_steps = []
        self.derivation_step_index = 0

    def save_and_create_derivation_step(self, synobjs, numeration=None, other=None, msg=''):
        """ Ok, new idea: derivation steps only include syntactic objects. Nodes etc. will be
        created in the fly. No problems from visualisations misbehaving, chains etc.
        :param synobjs: list of syntactic objects present in this snapshot
        :param numeration: optional list of items
        :param other: optional arbitrary data to store (must be Saveable or primitive data
        structures!)
        :param msg: optional message about derivation, to float when switching between derivations
        :return:
        """
        d_step = DerivationStep(synobjs, numeration, other, msg)
        # Use Kataja's save system to freeze objects into form where they can be stored and restored
        # without further changes affecting them.
        savedata = {}
        open_references = {}
        d_step.save_object(savedata, open_references)
        c = 0
        while open_references and c < 10:
            c += 1
            for obj in list(open_references.values()):
                if hasattr(obj, 'uid'):
                    obj.save_object(savedata, open_references)
                else:
                    print('cannot save open reference object ', obj)
        print('total savedata: %s chars in %s items.' % (len(str(savedata)), len(savedata)))
        self.derivation_steps.append((d_step.uid, savedata, msg))

    def restore_derivation_step(self, uid, frozen_data):
        """
        :param uid:
        :param frozen_data:
        """
        d_step = DerivationStep([])
        d_step.uid = uid
        d_step.load_objects(frozen_data, ctrl.main)
        self.current = d_step
        self.forest.mirror_the_syntax(d_step.synobjs, d_step.numeration, d_step.other)

    def next_derivation_step(self):
        """
        :return:
        """
        if self.derivation_step_index + 1 >= len(self.derivation_steps):
            return
        self.derivation_step_index += 1
        uid, ds, msg = self.derivation_steps[self.derivation_step_index]
        self.restore_derivation_step(uid, ds)
        ctrl.add_message(
            'Derivation step %s: %s' % (self.derivation_step_index, msg))

    def previous_derivation_step(self):
        """
        :return:
        """
        if self.derivation_step_index == 0:
            return
        self.derivation_step_index -= 1
        ds = self.derivation_steps[self.derivation_step_index]
        self.restore_derivation_step(ds)
        ctrl.add_message(
            'Derivation step %s: %s' % (self.derivation_step_index, ds.msg))

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    derivation_steps = SavedField("derivation_steps")
    derivation_step_index = SavedField("derivation_step_index")
    forest = SavedField("forest")
