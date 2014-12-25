# coding=utf-8
from collections import Counter
import string
from kataja.Saved import Savable
from kataja.debug import forest

from kataja.utils import time_me
from kataja.ConstituentNode import ConstituentNode
from kataja.singletons import ctrl

from collections import namedtuple



# ### Chains #######################################################################

# # chains should hold tuples of (node, parent), where node can be either real node or trace, and the parent provides the reliable/restorable identity/location for the trace.

ChainItem = namedtuple('ChainItem', ['node', 'parent', 'is_head'])


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
        for node, parent, is_head in chain:
            if is_head:
                return node
        raise Exception('F broken chain')

    def dump_chains(self):
        """


        """
        r = []
        forest('---- chains -----')
        for key, chain in self.chains.items():
            forest('%s :' % key)
            for (item, parent, is_head) in chain:
                if is_head:
                    forest('head ')
                else:
                    forest('trace ')
            forest('')


    def rebuild_chains_from_traces(self):
        """ Strategy for rebuilding chains depends on if the tree was saved in multidomination or with traces enabled. """

        f = self.forest
        self.chains = {}
        self.traces_from_bottom = []

        def _bottom_right_count_traces(node, parent):
            r = node.right()
            if r:
                _bottom_right_count_traces(r, node)
            l = node.left()
            if l:
                _bottom_right_count_traces(l, node)
            if node.index:
                if node.index in self.chains:
                    chain = self.chains[node.index]
                else:
                    chain = []
                chain.append(ChainItem(node, parent, not node.is_trace))
                self.traces_from_bottom.append(node)
                self.chains[node.index] = chain

        for r in f.roots:
            print('building chains from traces')
            # building chains from traces
            _bottom_right_count_traces(r, None)
        # Verify that each chain has one head
        for chain in self.chains.values():
            heads = [chain_item for chain_item in chain if chain_item.is_head]
            if len(heads) != 1:
                print('chain has %s heads, why so? ' % len(heads))
                print(chain)
            assert(len(heads) == 1)


    def rebuild_chains_from_multidomination(self):
        """ Strategy for rebuilding chains depends on if the tree was saved in multidomination or with traces enabled. """

        f = self.forest
        self.chains = {}
        self.traces_from_bottom = []

        def _bottom_right_count_parents(node, parent, c):
            r = node.right()
            if r:
                c = _bottom_right_count_parents(r, node, c)
            l = node.left()
            if l:
                c = _bottom_right_count_parents(l, node, c)
            if node.index:
                c += 1
                if node.index in self.chains:
                    chain = self.chains[node.index]
                else:
                    chain = []
                for d, item in chain:
                    if item.parent == parent:
                        return c
                chain.append((c, ChainItem(node, parent, not node.is_trace)))
                self.traces_from_bottom.append(node)
                self.chains[node.index] = chain
            return c

        c = 0
        for r in f.roots:
            print('building chains from multidominated nodes')
            # building chains from multidominated nodes
            c = _bottom_right_count_parents(r, None, c)

        # If chains are built from multidomination, they need to be sorted and indexes removed
        for key, values in list(self.chains.items()):
            values.sort(reverse=True)
            values = [v for i, v in values]
            new_values = [values.pop(0)]
            for node, parent, is_trace in values:
                new_values.append(ChainItem(node=f.create_trace_for(node), parent=parent, is_head=False))
            self.chains[key] = new_values
        # Verify that each chain has one head
        for chain in self.chains.values():
            heads = [chain_item for chain_item in chain if chain_item.is_head]
            if len(heads) != 1:
                print('chain has %s heads, why so? ' % len(heads))
                print(chain)
            assert(len(heads) == 1)


    @time_me
    def group_traces_to_chain_head(self):
        """


        """
        # ## Move traces to their multidominant originals, purely visual thing ###
        self.rebuild_chains_from_traces()
        y_adjust = {}
        for key, chain in self.chains.items():
            head = self.get_chain_head(key)
            for node, parent, is_head in chain:
                if not is_head:
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
        print('traces to multidomination called')
        self.rebuild_chains_from_traces()
        for trace in self.traces_from_bottom:
            if trace.is_trace:
                original = self.get_chain_head(trace.index)
                self.forest._replace_node(trace, original)

    @time_me
    def multidomination_to_traces(self):
        """ Switch multidominated elements to use traces instead  """
        self.rebuild_chains_from_multidomination()
        # each instance in chain that is not in head position is replaced with a trace
        print(self.forest.roots)
        for key, chain in self.chains.items():
            head = self.get_chain_head(key)
            for trace, parent, is_head in chain:
                if not is_head:
                    self.forest._replace_node(head, trace, only_for_parent=parent)
        print(self.forest.roots)

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

