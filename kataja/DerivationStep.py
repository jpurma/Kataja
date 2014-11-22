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

# Thinking about undo system. It should be a common class Undoable inherited by everyone. It contains few methods: start_undoable_operation, add_undoable_field, finish_undoable_operation.
# these all should operate on global dict, where each add_undoable_field would announce the item and the field.


class DerivationStep:
    """ Packed state of forest for undo -operations and for stepwise animation of tree growth. 

    Needs to be checked and tested, also what to do with saving and loading.
     """
    saved_fields = ['_msg', '_roots', '_chains']

    def __init__(self, msg=None, roots=None, chains=None, data=None):
        if not roots:
            roots = []
        if not chains:
            chains = {}
        if data:
            self.load(data)
        else:
            self._msg = msg
            self._roots = [self.snapshot_of_tree(root) for root in roots]
            self._chains = self.snapshot_of_chains(chains)
            self.save_key = 'Dstep%s' % id(self)

    def get_message(self):
        """


        :return:
        """
        return self._msg


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
                data = {'node': node}
                # these are the undoable changes, add data when necessary
                data['edges_up'] = list(node.edges_up)
                data['edges_down'] = list(node.edges_down)
                if hasattr(node, 'get_index'):
                    data['index'] = node.get_index()
                else:
                    data['index'] = None
                snapshot.append(data)
                done.add(node)
        return {'root': snapshot}

    def rebuild_tree_from_snapshot(self, snapshot, forest):
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
                node._connect_node(child=child, edge_type=edge_down.edge_type)
            node.edges_up = []
            for edge_up in data['edges_up']:
                parent = edge_up.start
                node._connect_node(parent=parent, edge_type=edge_up.edge_type)
            node.set_index(data['index'])
            forest.store(node)
        return root

    def restore_from_snapshot(self):
        """ Puts the given forest back to state described in this derivation step
        :param forest:
        """
        ctrl.forest.roots = []
        for root_data in self._roots:
            root = self.rebuild_tree_from_snapshot(root_data, ctrl.forest)
            ctrl.forest.roots.append(root)
        ctrl.forest._chains = self._chains


    def after_restore(self, values=None):
        """

        :param values:
        :return:
        """
        if not values:
            values = {}
        return


class DerivationStepManager:
    """

    """
    saved_fields = ['_derivation_steps', '_derivation_step_index', 'forest', 'save_key']


    def __init__(self, forest):
        self._derivation_steps = []
        self._derivation_step_index = 0
        self.forest = forest
        self.save_key = self.forest.save_key + '_derivation_step_manager'


    def save_and_create_derivation_step(self, msg=''):

        # print 'saving derivation_step %s' % self._derivation_step_index
        # needs to be reimplemented, make every operation bidirectional and undoable.
        """

        :param msg:
        """
        roots = self.forest.roots
        chains = self.forest.chain_manager.get_chains()
        derivation_step = DerivationStep(msg, roots, chains)
        self._derivation_step_index += 1
        self._derivation_steps.append(derivation_step)

    def restore_derivation_step(self, derivation_step):
        """

        :param derivation_step:
        """
        derivation_step.restore_from_snapshot()

    def next_derivation_step(self):
        """


        :return:
        """
        if self._derivation_step_index + 1 >= len(self._derivation_steps):
            return
        self._derivation_step_index += 1
        self.restore_derivation_step(self._derivation_steps[self._derivation_step_index])
        self.forest.main.add_message(self._derivation_steps[self._derivation_step_index].get_message())

    def previous_derivation_step(self):
        """


        :return:
        """
        if self._derivation_step_index == 0:
            return
        self._derivation_step_index -= 1
        self.restore_derivation_step(self._derivation_steps[self._derivation_step_index])
        self.forest.main.add_message(self._derivation_steps[self._derivation_step_index].get_message())

    def after_restore(self, values=None):
        """

        :param values:
        :return:
        """
        if not values:
            values = {}
        return

