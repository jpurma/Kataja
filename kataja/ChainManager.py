# coding=utf-8
import string
from collections import defaultdict

from kataja.globals import FOREST, CONSTITUENT_NODE
from kataja.singletons import ctrl



class ChainManager:
    """ Manages switching between trace views and multidomination views, and handles side-effect
    when forest operation should behave differently between the cases.

    Chain manager doesn't save its state, its structures are purely derivative from information
    already existing in the trees.
    """

    def __init__(self, forest):
        self.forest = forest

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
        ctrl.settings.set('traces_are_grouped_together', True, level=FOREST)
        ctrl.settings.set('uses_multidomination', False, level=FOREST)

    def traces_to_multidomination(self):
        """Switch traces to multidominant originals, as they are in syntax """
        heads, traces = self._get_heads_and_traces()
        for index, traces in traces.items():
            if index in heads:
                original = heads[index]
                for trace in traces:
                    self.forest.free_drawing.replace_node(trace, original)
        ctrl.settings.set('uses_multidomination', True, level=FOREST)
        self.forest.forest_edited()

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
            if len(parents) > 1:
                for foo, parent in parents[index][1:]:
                    trace = self.forest.free_drawing.create_trace_for(original)
                    self.forest.free_drawing.replace_node(original, trace, only_for_parent=parent)
        ctrl.settings.set('traces_are_grouped_together', False, level=FOREST)
        ctrl.settings.set('uses_multidomination', False, level=FOREST)
        self.forest.forest_edited()

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

