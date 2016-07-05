# coding=utf-8
import string
from collections import namedtuple

from kataja.utils import time_me, caller, add_xy
from kataja.singletons import ctrl



# ### Chains #######################################################################

# chains should hold tuples of (node, parent), where node can be either real node or trace, and
# the parent provides the reliable/restorable identity/location for the trace.

ChainItem = namedtuple('ChainItem', ['node', 'parent', 'is_head'])


class ChainManager:
    """ Manages switching between trace views and multidomination views, and handles side-effect when forest operation
    should behave differently between the cases.

    Chain manager doesn't save its state, its structures are purely derivative from information already existing in
    the trees.
    """

    def __init__(self, forest):
        self.chains = {}
        self.forest = forest
        self.traces_from_bottom = []

    @property
    def fs(self):
        return self.forest.settings

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

    def rebuild_chains(self, stop_count=0):
        """ Process for building chains depends on if the trees currently is using multidomination or not.
        Chains shouldn't include elements that are not really in the trees right now.
        :param stop_count: to avoid infinite recursion if the trees is seriously broken
        :return:
        """
        if self.fs.uses_multidomination:
            self.rebuild_chains_from_multidomination()
        else:
            self.rebuild_chains_from_traces()
        # Verify that each chain has one head
        for key, chain in self.chains.items():
            heads = [chain_item for chain_item in chain if chain_item.is_head]
            if len(heads) > 1:
                for item in heads[1:]:
                    item.node.is_trace = True
                if stop_count < 5:
                    stop_count += 1
                    self.rebuild_chains(stop_count=stop_count)
            elif len(heads) == 0:
                chain[0].node.is_trace = False
                if stop_count < 5:
                    stop_count += 1
                    self.rebuild_chains(stop_count=stop_count)

    def rebuild_chains_from_traces(self):
        """ When building chains from traces, usually the first member is the head, but the trees may be given in a
         form where this isn't the case.
        :return:
        """

        #print('rebuild chains from traces called')
        f = self.forest
        self.chains = {}
        self.traces_from_bottom = []

        # recursive method for collecting usage of a trace/node, counted from bottom up.
        def _bottom_right_count_traces(node, parent):
            children = node.get_reversed_children() # right first for bottom-up!
            for child in children:
                _bottom_right_count_traces(child, node)
            # then this node:
            if getattr(node, 'index', None):
                if node.index in self.chains:
                    chain = self.chains[node.index]
                else:
                    chain = []
                chain.append(ChainItem(node, parent, not node.is_trace))
                self.traces_from_bottom.append(node)
                self.chains[node.index] = chain

        for tree in f.trees:
            if tree.top:
                _bottom_right_count_traces(tree.top, None)

        for key, values in self.chains.items():
            values.reverse()
            self.chains[key] = values
            # print('used trace-based rebuild, received chains: ', self.chains)
            # print(self.traces_from_bottom)

    def rebuild_chains_from_multidomination(self):
        """ When building chains from multidomination, the end result should consist of list of
        (node, parent, is_head)-tuples, where the first element is the head, and topmost instance in trees,
        and the rest are other appearances top down. The node remains the same, parent is different. """

        #print('rebuild chains from md called')
        f = self.forest
        self.chains = {}
        self.traces_from_bottom = []

        # recursive method for collecting usage of a node, counted from bottom up.
        def _bottom_right_count_parents(node, parent, c):
            for child in node.get_reversed_children():
                c = _bottom_right_count_parents(child, node, c)
            if hasattr(node, 'index') and node.index:
                c += 1
                if node.index in self.chains:
                    chain = self.chains[node.index]
                else:
                    chain = []
                for d, item in chain:
                    if item.parent is parent:
                        return c
                chain.append((c, ChainItem(node, parent, not node.is_trace)))
                self.traces_from_bottom.append(node)
                self.chains[node.index] = chain
            return c

        count = 0
        for tree in f.trees:
            if tree.top:
                count = _bottom_right_count_parents(tree.top, None, count)

        # If chains are built from multidomination, they need to be sorted and sorting indexes removed
        for key, values in list(self.chains.items()):
            values.sort(reverse=True)
            # print('after sorting:' ,values)
            values = [v for i, v in values]
            new_values = [values.pop(0)]
            for node, parent, is_trace in values:
                new_values.append(ChainItem(node=node, parent=parent, is_head=False))
            self.chains[key] = new_values
            # print('used multidomination-based rebuild, received chains: ', self.chains)

    def group_traces_to_chain_head(self):
        """ Move traces to their multidominant originals, purely didactic thing """
        self.rebuild_chains()
        y_adjust = {}
        for key, chain in self.chains.items():
            head = self.get_chain_head(key)
            for node, parent, is_head in chain:
                if not is_head:
                    if key not in y_adjust:
                        y_adjust[key] = head.boundingRect().height(), head.boundingRect().height()
                    dx, dy = y_adjust[key]
                    node.use_adjustment = False
                    node.adjustment = (0, 0)
                    node.move_to(*add_xy(head.current_position, (-dx, dy)), can_adjust=False)
                    y_adjust[key] = (dx + node.boundingRect().width(), dy + node.boundingRect().height())
        self.fs.traces_are_grouped_together = True
        self.fs.uses_multidomination = False

    def traces_to_multidomination(self):
        """Switch traces to multidominant originals, also mirror changes in syntax  """
        self.rebuild_chains()
        for trace in self.traces_from_bottom:
            if trace.is_trace:
                original = self.get_chain_head(trace.index)
                self.forest.replace_node(trace, original)
        self.fs.uses_multidomination = True

    def multidomination_to_traces(self):
        """ Switch multidominated elements to use traces instead  """
        self.rebuild_chains()
        # each instance in chain that is not in head position is replaced with a trace
        for key, chain in self.chains.items():
            head = self.get_chain_head(key)
            for node, parent, is_head in chain:
                if not is_head:
                    if node.is_trace:
                        trace = node
                    else:
                        trace = self.forest.create_trace_for(node)
                    self.forest.replace_node(head, trace, only_for_parent=parent)
        self.fs.uses_multidomination = False
        self.fs.traces_are_grouped_together = False

    def next_free_index(self):
        """ Return the next available letter suitable for indexes (i, j, k, l...)
        :return:
        """
        max_found = 7  # 'h'
        for node in self.forest.nodes.values():
            index = getattr(node, 'index', None)
            if index and len(index) == 1 and index[0].isalpha():
                pos = string.ascii_letters.find(index[0])
                if pos > max_found:
                    max_found = pos
        max_found += 1
        if max_found == len(string.ascii_letters):
            assert False
        return string.ascii_letters[max_found]

