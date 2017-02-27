# coding=utf-8
import string
from collections import defaultdict

from kataja.globals import FOREST, CONSTITUENT_NODE
from kataja.singletons import ctrl
from kataja.utils import time_me


class ChainManager:
    """ Manages switching between trace views and multidomination views, and handles side-effect
    when forest operation should behave differently between the cases.

    Chain manager doesn't save its state, its structures are purely derivative from information
    already existing in the trees.
    """

    def __init__(self, forest):
        self.forest = forest

    @time_me
    def update(self):
        """ Checks and fixes current forest to follow multidominance or trace-based display for 
        nodes. The mode has already been set in ctrl.settings.
        :return: 
        """
        # First make sure that multidominated nodes have indices
        for node in self.forest.nodes.values():
            if node.node_type == CONSTITUENT_NODE and \
                    not node.index and \
                    len(node.get_parents(similar=True, visible=False)) > 1:
                node.index = self.next_free_index()
        # Then implement the rules
        md = ctrl.settings.get('uses_multidomination')
        traces_grouped = ctrl.settings.get('traces_are_grouped_together')
        if md:
            self.traces_to_multidomination()
        else:
            self.multidomination_to_traces()
            if traces_grouped:
                self.group_traces_to_chain_head()

    def traces_are_visible(self):
        """ Helper method for checking if we need to deal with chains
        :return:
        """
        return not ctrl.settings.get('uses_multidomination')

    def _get_heads_and_traces(self):
        heads = {}
        traces = defaultdict(list)
        for node in self.forest.nodes.values():
            if node.node_type != CONSTITUENT_NODE:
                continue
            if node.index:
                if node.is_trace:
                    traces[node.index].append(node)
                else:
                    heads[node.index] = node
        return heads, traces

    @time_me
    def group_traces_to_chain_head(self):
        """ Move traces to their multidominant originals, purely didactic thing """
        heads, traces = self._get_heads_and_traces()
        for index, traces in traces.items():
            if index in heads:
                original = heads[index]
                dx, dy = original.target_position
                dy += original.height / 2 + 4
                for trace in traces:
                    trace.use_adjustment = False
                    trace.adjustment = (0, 0)
                    trace.move_to(dx, dy, can_adjust=False)
                    dx += 10
                    dy += trace.height

    @time_me
    def traces_to_multidomination(self):
        """Switch traces to multidominant originals, as they are in syntax """

        heads, traces = self._get_heads_and_traces()
        for index, traces in traces.items():
            if index in heads:
                original = heads[index]
                for trace in traces:
                    self.forest.free_drawing.replace_node(trace, original)

    @time_me
    def multidomination_to_traces(self):
        def _find_paths_up(n, depth):
            pars = n.get_parents(similar=True, visible=False)
            if pars:
                for par in pars:
                    _find_paths_up(par, depth + 1)
            else:
                paths_up.append(depth)

        parents = defaultdict(list)
        originals = {}

        for node in self.forest.nodes.values():
            if node.node_type != CONSTITUENT_NODE:
                continue
            if node.index:
                originals[node.index] = node
                for parent in node.get_parents(similar=True, visible=False):
                    paths_up = []
                    _find_paths_up(parent, 0)
                    parents[node.index].append((max(paths_up), parent))
                # we leave open case [A A], it will get random order, but who cares
                parents[node.index].sort()
        # replace all but highest instance with traces
        for index, original in originals.items():
            my_parents = parents[index]
            if len(my_parents) > 1:
                for foo, parent in my_parents[1:]:
                    trace = self.forest.free_drawing.create_trace_for(original)
                    self.forest.free_drawing.replace_node(original, trace, only_for_parent=parent)

    def next_free_index(self):
        """ Return the next available letter suitable for indexes (i, j, k, l...)
        When lowercase alphabet run out, use integers instead. They wont run out too soon.
        :return:
        """
        max_letter = 'h'
        max_number = 0
        for node in self.forest.nodes.values():
            index = getattr(node, 'index', None)
            if index:
                if len(index) == 1 and index.isalpha() and index > max_letter:
                    max_letter = index
                elif index.isdigit() and int(index) > max_number:
                    max_number = int(index)
        if max_letter < 'z':
            return string.ascii_letters[string.ascii_letters.index(max_letter) + 1]
        else:
            return str(max_number + 1)

