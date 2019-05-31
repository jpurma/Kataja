# -*- coding: UTF-8 -*-
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2019 Jukka Purma
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
from kataja.saved.DerivationStep import DerivationStepManager, DerivationStep
from kataja.syntax.SyntaxState import SyntaxState


class ParseTree(SavedObject):
    """ ParseTree holds the data for a specific parse. This data is stored as derivation steps. Conversion of parse
    tree to actual displayed nodes is done by Forest object containing ParseTrees."""

    def __init__(self, forest):
        """ Create an empty forest. Gloss_text and comments are metadata
        about trees that doesn't belong to syntax implementation, so its kept here. Syntax
        implementations may still use it.

        By default, a new Forest doesn't create its nodes -- it doesn't do the derivation yet.
        This is to save speed and memory with large structures. If the is_parsed -flag is False
        when created, but once Forest is displayed, the derivation has to run and after that
        is_parsed is True.
        """
        super().__init__()
        self.derivation_steps = DerivationStepManager(forest)

    def add_step(self, syn_state: SyntaxState or DerivationStep):
        """ Store given syntactic state as a derivation step. Forest can switch which derivation
        state it is currently displaying.
        :param syn_state: SyntaxState object
        :return:
        """
        if isinstance(syn_state, DerivationStep):
            self.derivation_steps.save_derivation_step(syn_state)
        else:
            self.derivation_steps.save_and_create_derivation_step(syn_state)

    def jump_to_starting_derivation(self):
        ds = self.derivation_steps
        if ds.derivation_step_index is None:
            ds.derivation_step_index = len(ds.derivation_steps) - 1
        ds.jump_to_derivation_step(ds.derivation_step_index)

    def remove_iterations(self, iterations):
        """
        :param iterations: list of iteration indices to remove from steps
        :return:
        """
        self.derivation_steps.remove_iterations(iterations)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    derivation_steps = SavedField("derivation_steps")
