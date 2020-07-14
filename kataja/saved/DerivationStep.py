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
from kataja.syntax.SyntaxState import SyntaxState


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
            self.state_id = syn_state.state_id
            self.tree_roots = syn_state.tree_roots
            self.numeration = syn_state.numeration
            self.msg = syn_state.msg
            self.gloss = syn_state.gloss
            self.groups = syn_state.groups
            self.semantic_hierarchies = syn_state.semantic_hierarchies
            self.log = syn_state.log
            self.parent_id = syn_state.parent_id
            self.state_type = syn_state.state_type
            self.sort_order = syn_state.sort_order
        else:
            self.state_id = 0
            self.tree_roots = []
            self.numeration = []
            self.msg = ''
            self.gloss = ''
            self.groups = []
            self.semantic_hierarchies = []
            self.log = []
            self.parent_id = None
            self.state_type = 0
            self.sort_order = 0
        self.frozen = None

    def __str__(self):
        return f"DS({self.tree_roots}, {self.numeration}, '{self.msg}', {self.state_id}, {self.parent_id}, {self.state_type}, {self.sort_order})"

    def freeze(self):
        data = {}
        open_references = {}
        self.save_object(data, open_references)
        c = 0
        max_depth = 100  # constituent trees can be surprisingly deep, and we don't have any
        # general dict about them.
        while open_references and c < max_depth:
            c += 1
            for obj in list(open_references.values()):
                if hasattr(obj, 'uid'):
                    # print('saving obj ', obj.uid)
                    obj.save_object(data, open_references)
                else:
                    print('cannot save open reference object ', obj)
        assert (c < max_depth)  # please raise the max depth if this is reached
        self.frozen = (self.uid, data, self.msg, self.state_id, self.parent_id, self.state_type, self.sort_order)
        return self.frozen

    def to_syn_state(self):
        return SyntaxState(tree_roots=self.tree_roots, numeration=self.numeration, msg=self.msg,
                           gloss=self.gloss, groups=self.groups,
                           semantic_hierarchies=self.semantic_hierarchies,
                           state_id=self.state_id, parent_id=self.parent_id, log=self.log, state_type=self.state_type,
                           sort_order=self.sort_order)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    tree_roots = SavedField("tree_roots")
    numeration = SavedField("numeration")
    msg = SavedField("msg")
    gloss = SavedField("gloss")
    groups = SavedField("groups")
    semantic_hierarchies = SavedField("semantic_hierarchies")
    state_id = SavedField("state_id")
    parent_id = SavedField("parent_id")
    log = SavedField("log")
    sort_order = SavedField("sort_order")
