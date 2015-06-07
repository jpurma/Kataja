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
from kataja.BaseModel import BaseModel, Saved

# Thinking about undo system. It should be a common class Undoable inherited by everyone. It contains few methods: start_undoable_operation, add_undoable_field, finish_undoable_operation.
# these all should operate on global dict, where each add_undoable_field would announce the item and the field.


class DerivationStep(BaseModel):
    """ Packed state of forest for undo -operations and for stepwise animation of tree growth. 

    Needs to be checked and tested, also what to do with saving and loading.
     """
    short_name = "DStep"



    def __init__(self, msg=None, roots=None, chains=None):
        super().__init__()
        if not roots:
            roots = []
        if not chains:
            chains = {}
        self.msg = msg
        self.roots = [self.snapshot_of_tree(root) for root in roots]
        self.chains = self.snapshot_of_chains(chains)

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
        1st wave creates the objects and calls __init__, and then iterates through and sets the values.
        2nd wave calls after_inits for all created objects. Now they can properly refer to each other and know their
        values.
        :return: None
        """
        self.announce_creation()

    def snapshot_of_chains(self, chains):
        """ shallow copy of chains is not enough -- it refers to original lists -- and deepCopy is too much. 
        :param chains:
        This copies the dict and the lists """
        snapshot = {}
        for key, item in chains.items():
            snapshot[key] = list(item)
        return snapshot

    def snapshot_of_tree(self, root_node):
        """ create a version of root with shallow copy for each node and a simple structure for rebuilding/restoring
        :param root_node:
         them """
        snapshot = []
        done = set()
        for node in ctrl.forest.list_nodes_once(root_node):
            if node not in done:
                data = {'node': node, 'edges_up': list(node.edges_up), 'edges_down': list(node.edges_down)}
                # these are the undoable changes, add data when necessary
                if hasattr(node, 'index'):
                    data['index'] = node.index
                else:
                    data['index'] = None
                snapshot.append(data)
                done.add(node)
        return {'root': snapshot}

    def rebuild_tree_from_snapshot(self, snapshot):
        """ Restores each node to use those connections it had when stored. Notice that this is rebuilding in a very limited sense. Probably we'll need something deeper soon.
        :param snapshot:
        :param forest:
        """
        root = snapshot['root']
        if root:
            root = root[0]['node']
        for data in root:
            node = data['node']
            node.edges_down = []
            for edge_down in data['edges_down']:
                child = edge_down.end
                ctrl.forest.connect_node(parent=node, child=child)
            node.edges_up = []
            for edge_up in data['edges_up']:
                parent = edge_up.start
                ctrl.forest.connect_node(parent=parent, child=node)
            node.index = data['index']
            ctrl.forest.store(node)
        return root

    def restore_from_snapshot(self):
        """ Puts the given forest back to state described in this derivation step
        :param forest:
        """
        ctrl.forest.roots = []
        for root_data in self.roots:
            root = self.rebuild_tree_from_snapshot(root_data)
            ctrl.forest.update_root_status(root)
        ctrl.forest.chain_manager.chains = self.chains

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    msg = Saved("msg")
    roots = Saved("roots")
    chains = Saved("chains")

class DerivationStepManager(BaseModel):
    """ Stores derivation steps for one forest and takes care of related logic """

    short_name = "DStepManager"

    def __init__(self):
        super().__init__(unique=False)
        self.derivation_steps = []
        self.derivation_step_index = 0

    def save_and_create_derivation_step(self, msg=''):

        # print 'saving derivation_step %s' % self._derivation_step_index
        # fixme: needs to be reimplemented, make every operation bidirectional and undoable.
        """

        :param msg:
        """
        # print('save_and_create_derivation_step called')
        roots = ctrl.forest.roots
        chains = ctrl.forest.chain_manager.chains
        if chains:
            print('saving chains into derivation step: ', chains)
        # derivation_step = DerivationStep(msg, roots, chains)
        # self.derivation_step_index += 1
        # self.derivation_steps.append(derivation_step)

    def restore_derivation_step(self, derivation_step):
        """
        :param derivation_step:
        """
        derivation_step.restore_from_snapshot()

    def next_derivation_step(self):
        """
        :return:
        """
        if self.derivation_step_index + 1 >= len(self.derivation_steps):
            return
        self.derivation_step_index += 1
        ds = self.derivation_steps[self.derivation_step_index]
        self.restore_derivation_step(ds)
        ctrl.add_message('Derivation step %s: %s' % (self.derivation_step_index, ds.msg))

    def previous_derivation_step(self):
        """
        :return:
        """
        if self.derivation_step_index == 0:
            return
        self.derivation_step_index -= 1
        ds = self.derivation_steps[self.derivation_step_index]
        self.restore_derivation_step(ds)
        ctrl.add_message('Derivation step %s: %s' % (self.derivation_step_index, ds.msg))

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    derivation_steps = Saved("derivation_steps")
    derivation_step_index = Saved("derivation_step_index")
