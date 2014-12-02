# coding=utf-8
from collections import Counter
import string
from kataja.Saved import Savable
from kataja.debug import forest

from kataja.utils import time_me
from kataja.ConstituentNode import ConstituentNode
from kataja.singletons import ctrl





# ### Chains #######################################################################

# # chains should hold tuples of (node, parent), where node can be either real node or trace, and the parent provides the reliable/restorable identity/location for the trace.


class ChainManager(Savable):
    """

    """

    def __init__(self):
        Savable.__init__(self, unique=True)
        self.saved.chains = {}
        self.saved.forest = ctrl.forest

    @property
    def chains(self):
        return self.saved.chains

    @chains.setter
    def chains(self, value):
        self.saved.chains = value

    @property
    def forest(self):
        return self.saved.forest

    @forest.setter
    def forest(self, value):
        self.saved.forest = value

    def get_chain_head(self, chain_key):
        """

        :param chain_key:
        :return: :raise 'F broken chain':
        """
        chain = self.chains[chain_key]
        # assert chain[0].is_chain_head()
        for node, parent in chain:
            if node.is_chain_head():
                return node
        raise Exception('F broken chain')

    def dump_chains(self):
        """


        """
        r = []
        forest('---- chains -----')
        for key, chain in self.chains.items():
            forest('%s :' % key)
            for (item, parent) in chain:
                if item.is_trace:
                    forest('trace ')
                else:
                    forest('head ')
            forest('')

    # @time_me
    def rebuild_chains(self):
        """ Strategy for rebuilding chains depends on if the tree was saved in multidomination or with traces enabled. """
        self.chains = {}
        f = self.forest
        multidomination = False
        # decide if there is multidomination present and build dictionary of nodes with index.
        for node in list(f.nodes.values()):
            if isinstance(node, ConstituentNode):
                index = node.index
                if index:
                    if index in self.chains:
                        chain = self.chains[index]
                    else:
                        chain = []
                    parents = node.get_parents()
                    if len(parents) > 1:
                        orig_parent = f.nodes[node.original_parent]
                        for parent in parents:
                            if orig_parent == parent:
                                chain.append((node, orig_parent))
                            else:
                                chain.append((f.create_trace_for(node), parent))  # <----- modifies node dict
                    else:
                        chain.append((node, parents[0]))

                    self.chains[index] = chain

    @time_me
    def group_traces_to_chain_head(self):
        """


        """
        forest('group traces to chain head')
        # ## Move traces to their multidominant originals, purely visual thing ###
        self.rebuild_chains()
        y_adjust = {}
        for key, chain in self.chains.items():
            head = self.get_chain_head(key)
            for node, parent in chain:
                if node != head:
                    if key not in y_adjust:
                        y_adjust[key] = head.boundingRect().height(), head.boundingRect().height()
                    dx, dy = y_adjust[key]
                    if head.bind_x and head.bind_y:
                        node.bind_x = True
                        node.bind_y = True
                        x, y, z = head.computed_position
                        node.adjustment = head.adjustment
                        y += dy
                        x -= dx
                        node.computed_position = (x, y, z)
                    else:
                        x, y, z = head.current_position
                        y += dy
                        x -= dx
                        node.current_position = (x, y, z)
                    y_adjust[key] = (dx + node.boundingRect().width(), dy + node.boundingRect().height())

    @time_me
    def traces_to_multidomination(self):
        # ## Switch traces to multidominant originals, also mirror changes in syntax ###
        """


        """
        forest('traces to multidomination')
        # if not self._chains:
        self.rebuild_chains()
        self.dump_chains()
        # self._validate_chains()
        order_dict = {}
        for t, root in enumerate(self.forest.roots):
            for i, node in enumerate(self.forest.list_nodes(root)):
                if hasattr(node, 'index') and node.index:
                    order_dict[node.save_key] = (t, i, node)
        ordered = list(order_dict.values())
        ordered.sort(reverse=True)
        for t, i, node in ordered:
            if not node.is_trace:
                node.original_parent = node.get_parents()[0].save_key
        for t, i, node in ordered:
            if node.is_trace:
                forest('replacing trace ', node)
                original = self.get_chain_head(node.index)
                self.forest._replace_node(node, original)
                self.forest.delete_node(node)

    @time_me
    def multidomination_to_traces(self):
        # ## Switch multidominated elements to use traces instead ###
        """


        """
        forest('multidomination to traces')
        self.rebuild_chains()
        for key, chain in self.chains.items():
            head = self.get_chain_head(key)
            for node, parent in chain:
                if node != head:
                    self.forest._replace_node(head, node, only_for_parent=parent)
        self.rebuild_chains()

    def next_free_index(self):
        """


        :return:
        """
        max_found = 7  # 'h'
        for node in self.forest.nodes.values():
            index = node.index
            if index and len(index) == 1 and index[0].isalpha():
                pos = string.ascii_letters.find(index[0])
                if pos > max_found:
                    max_found = pos
        max_found += 1
        if max_found == len(string.ascii_letters):
            assert False
        return string.ascii_letters[max_found]

