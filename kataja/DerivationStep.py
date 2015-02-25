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


from kataja.singletons import ctrl
from kataja.Saved import Savable

# Thinking about undo system. It should be a common class Undoable inherited by everyone. It contains few methods: start_undoable_operation, add_undoable_field, finish_undoable_operation.
# these all should operate on global dict, where each add_undoable_field would announce the item and the field.


class DerivationStep(Savable):
    """ Packed state of forest for undo -operations and for stepwise animation of tree growth. 

    Needs to be checked and tested, also what to do with saving and loading.
     """

    def __init__(self, msg=None, roots=None, chains=None, data=None):
        Savable.__init__(self)
        if not roots:
            roots = []
        if not chains:
            chains = {}
        if data:
            self.load(data)
        else:
            self.saved.msg = msg
            self.saved.roots = [self.snapshot_of_tree(root) for root in roots]
            self.saved.chains = self.snapshot_of_chains(chains)

    @property
    def msg(self):
        """
        :return:
        """
        return self.saved.msg

    @msg.setter
    def msg(self, value):
        """
        :param value:
        """
        self.saved.msg = value

    @property
    def roots(self):
        """
        :return:
        """
        return self.saved.roots

    @roots.setter
    def roots(self, value):
        """
        :param value:
        """
        self.saved.roots = value

    @property
    def chains(self):
        """
        :return:
        """
        return self.saved.chains

    @chains.setter
    def chains(self, value):
        """
        :param value:
        """
        self.saved.chains = value

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
                ctrl.forest.connect_node(parent=node, child=child, edge_type=edge_down.edge_type)
            node.edges_up = []
            for edge_up in data['edges_up']:
                parent = edge_up.start
                ctrl.forest.connect_node(parent=parent, child=node, edge_type=edge_up.edge_type)
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


class DerivationStepManager(Savable):
    """

    """
    saved_fields = ['_derivation_steps', '_derivation_step_index', 'forest', 'save_key']


    def __init__(self):
        Savable.__init__(self, unique=False)
        self.saved.derivation_steps = []
        self.saved.derivation_step_index = 0
        self.saved.forest = ctrl.forest

    @property
    def derivation_steps(self):
        return self.saved.derivation_steps

    @derivation_steps.setter
    def derivation_steps(self, value):
        self.saved.derivation_steps = value

    @property
    def derivation_step_index(self):
        return self.saved.derivation_step_index

    @derivation_step_index.setter
    def derivation_step_index(self, value):
        self.saved.derivation_step_index = value

    @property
    def forest(self):
        return self.saved.forest

    @forest.setter
    def forest(self, value):
        self.saved.forest = value


    def save_and_create_derivation_step(self, msg=''):

        # print 'saving derivation_step %s' % self._derivation_step_index
        # needs to be reimplemented, make every operation bidirectional and undoable.
        """

        :param msg:
        """
        roots = self.forest.roots
        chains = self.forest.chain_manager.chains
        derivation_step = DerivationStep(msg, roots, chains)
        self.derivation_step_index += 1
        self.derivation_steps.append(derivation_step)

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
        self.forest.main.add_message('Derivation step %s: %s' % (self.derivation_step_index, ds.msg))

    def previous_derivation_step(self):
        """


        :return:
        """
        if self.derivation_step_index == 0:
            return
        self.derivation_step_index -= 1
        ds = self.derivation_steps[self.derivation_step_index]
        self.restore_derivation_step(ds)
        self.forest.main.add_message('Derivation step %s: %s' % (self.derivation_step_index, ds.msg))


