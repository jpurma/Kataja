# coding=utf-8
from collections import Counter
import string

from kataja.utils import time_me
from kataja.ConstituentNode import ConstituentNode




# ### Chains #######################################################################

# # chains should hold tuples of (node, parent), where node can be either real node or trace, and the parent provides the reliable/restorable identity/location for the trace.


class ChainManager:
    """

    """
    saved_fields = "all"

    def __init__(self, forest):
        self.save_key = forest.save_key + '_chain_manager'
        self._chains = {}
        self.forest = forest

    def get_chains(self):
        """


        :return:
        """
        return self._chains

    def get_chain(self, key):
        """

        :param key:
        :return:
        """
        return self._chains[key]

    def set_chain(self, key, chain):
        """

        :param key:
        :param chain:
        """
        self._chains[key] = chain

    def remove_chain(self, key, delete_traces=True):
        """

        :param key:
        :param delete_traces:
        """
        if delete_traces:
            for item in self._chains[key][1:]:
                self.forest.delete_node(item)  # <<<<<<-------
        del self._chains[key]

    def remove_from_chain(self, node):
        """

        :param node:
        """
        chain = self._chains[node.save_key]
        for i, np in enumerate(list(chain)):
            n, p = np
            if n == node:
                chain.pop(i)
        self._chains[node.save_key] = chain


    def number_of_chains(self):
        """


        :return:
        """
        return len(self._chains)

    def items_in_chains(self):
        """


        """
        for chain in self._chains.values():
            for item in chain:
                yield item

    def chain_counter(self):
        """ Returns a counter object where values of dict are lengths of each chain """
        c = Counter()
        for key, item in self._chains.items():
            c[key] = len(item)
        return c

    def add_to_chain(self, key, node, parent):
        # print 'adding %r to chain %s' % (node, key)
        """

        :param key:
        :param node:
        :param parent:
        """
        if key in self._chains:
            self._chains[key].append((node, parent))
        else:
            self._chains[key] = [(node, parent)]

    def _insert_into_chain(self, key, trace, parent):
        if key in self._chains:
            self._chains[key].insert(1, (trace, parent))
        else:
            self._chains[key] = [trace]

    def get_chain_head(self, chain_key):
        """

        :param chain_key:
        :return: :raise 'F broken chain':
        """
        chain = self._chains[chain_key]
        # assert chain[0].is_chain_head()
        for node, parent in chain:
            if node.is_chain_head():
                return node
        raise Exception('F broken chain')

    def dump_chains(self):
        """


        """
        r = []
        print('---- chains -----')
        for key, chain in self._chains.items():
            print('%s :' % key)
            for (item, parent) in chain:
                if item.is_trace:
                    print('trace ')
                else:
                    print('head ')
            print('')

    # @time_me
    def rebuild_chains(self):
        """ Strategy for rebuilding chains depends on if the tree was saved in multidomination or with traces enabled. """
        self._chains = {}
        f = self.forest
        multidomination = False
        # decide if there is multidomination present and build dictionary of nodes with index.
        for node in f.nodes.values():
            if isinstance(node, ConstituentNode):
                index = node.get_index()
                if index:
                    if index in self._chains:
                        chain = self._chains[index]
                    else:
                        chain = []
                    parents = node.get_parents()
                    if len(parents) > 1:
                        orig_parent = f.nodes[node.original_parent]
                        for parent in parents:
                            if orig_parent == parent:
                                chain.append((node, orig_parent))
                            else:
                                chain.append((f.create_trace_for(node), parent))  # <<<<<<<<-----
                    else:
                        chain.append((node, parents[0]))

                    self._chains[index] = chain

    @time_me
    def group_traces_to_chain_head(self):
        """


        """
        print('group traces to chain head')
        # ## Move traces to their multidominant originals, purely visual thing ###
        self.rebuild_chains()
        y_adjust = {}
        for key, chain in self._chains.items():
            head = self.get_chain_head(key)
            for node, parent in chain:
                if node != head:
                    if not key in y_adjust:
                        y_adjust[key] = head.boundingRect().height(), head.boundingRect().height()
                    dx, dy = y_adjust[key]
                    if head.bind_x and head.bind_y:
                        node.bind_x = True
                        node.bind_y = True
                        x, y, z = head.get_computed_position()
                        node.set_adjustment(head.get_adjustment())
                        y += dy
                        x -= dx
                        node.set_computed_position((x, y, z))
                    else:
                        x, y, z = head.get_current_position()
                        y += dy
                        x -= dx
                        node.set_current_position((x, y, z))
                    y_adjust[key] = (dx + node.boundingRect().width(), dy + node.boundingRect().height())

    @time_me
    def traces_to_multidomination(self):
        # ## Switch traces to multidominant originals, also mirror changes in syntax ###
        """


        """
        print('traces to multidomination')
        # if not self._chains:
        self.rebuild_chains()
        self.dump_chains()
        # self._validate_chains()
        order_dict = {}
        for t, root in enumerate(self.forest.roots):
            for i, node in enumerate(self.forest.list_nodes(root)):
                if node.get_index():
                    order_dict[node.save_key] = (t, i, node)
        ordered = list(order_dict.values())
        ordered.sort(reverse=True)
        for t, i, node in ordered:
            if not node.is_trace:
                node.original_parent = node.get_parents()[0].save_key
        for t, i, node in ordered:
            if node.is_trace:
                print('replacing trace ', node)
                original = self.get_chain_head(node.get_index())
                self.forest._replace_node(node, original)
                self.forest.delete_node(node)
        self.forest.update_roots()

    @time_me
    def multidomination_to_traces(self):
        # ## Switch multidominated elements to use traces instead ###
        """


        """
        print('multidomination to traces')
        self.rebuild_chains()
        for key, chain in self._chains.items():
            head = self.get_chain_head(key)
            for node, parent in chain:
                if node != head:
                    self.forest._replace_node(head, node, only_for_parent=parent)
        self.rebuild_chains()
        self.forest.update_roots()

    def next_free_index(self):
        """


        :return:
        """
        max_found = 7  # 'h'
        for node in self.forest.nodes.values():
            index = node.get_index()
            if index and len(index) == 1 and index[0].isalpha():
                pos = string.ascii_letters.find(index[0])
                if pos > max_found:
                    max_found = pos
        max_found += 1
        if max_found == len(string.ascii_letters):
            assert False
        return string.ascii_letters[max_found]

    def after_restore(self, values=None):
        """

        :param values:
        :return:
        """
        if not values:
            values = {}
        return

