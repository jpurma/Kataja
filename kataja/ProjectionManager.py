import itertools

from collections import defaultdict

from kataja.Projection import Projection
from kataja.singletons import ctrl
from kataja.globals import CONSTITUENT_NODE
from kataja.utils import time_me


class ProjectionManager:
    def __init__(self, forest):
        self.forest = forest
        self.projections = {}
        self.projection_rotator = itertools.cycle(range(3, 8))

    @property
    def projection_visuals(self):
        return (p.visual for p in self.projections.values() if p.visual)

    def guess_heads(self, root):
        """ Guess projecting heads for a structure parsed from bracket notation which doesn't
        have any markup for this task. This can be good enough, just to set some default values
        for 'heads'-variable in each node.

        ! note that you can assume that there is no multidomination yet. Or can you?
        :param root: topmost node of structure
        :return:
        """
        if (not root) or root.node_type != CONSTITUENT_NODE:
            return
        originals = {}
        done = set()

        def _collect_originals(node):
            if node.index and not node.is_trace:
                originals[node.index] = node
            for child in node.get_children(visible=False, similar=True):
                _collect_originals(child)

        _collect_originals(root)

        def _guess_head(node):
            # The original, not trace projects
            done.add(node)
            head_part = Projection.get_base_label(node)
            children = node.get_children(visible=False, similar=True)
            heads = []
            n = len(children)
            if n == 0:
                heads.append(node)
            elif n == 1:
                child = children[0]
                if child.is_trace and child.index in originals:
                    child = originals[child.index]
                    if child not in done:
                        _guess_head(child)
                else:
                    _guess_head(child)
                heads += child.heads
            else:
                for child in children:
                    if child.is_trace and child.index in originals:
                        child = originals[child.index]
                        if child in done:
                            head_part_of_child = Projection.get_base_label(child)
                        else:
                            head_part_of_child = _guess_head(child)
                    else:
                        head_part_of_child = _guess_head(child)
                    if head_part_of_child:
                        if head_part_of_child == head_part:
                            heads += child.heads
            node.set_heads(heads)
            return head_part

        _guess_head(root)

    def remove_projection(self, head):
        projection = self.projections.get(head, None)
        if projection:
            projection.set_visuals(0)
            del self.projections[head]

    def update_projections(self):

        old_heads = set(self.projections.keys())
        new_heads = set()

        for node in self.forest.nodes.values():
            if node.node_type == CONSTITUENT_NODE:
                if node in node.heads:
                    new_heads.add(node)
                node.in_projections = []
                node.autolabel = ''

        for edge in self.forest.edges.values():
            edge.in_projections = []

        for head in new_heads:
            ordered_chains = []

            # there are many possible 'routes' that a chain can take
            # for each we know the starting point and we start building upwards.
            # if there is a branch, a new chain makes a copy of existing and starts another
            # branch. Result may be many chains repeating parts. Chains shouldn't make circles.

            def _add_into_chain(_chain, _node, head):
                found_one = False
                for parent in _node.get_parents(similar=True, visible=False):
                    if head in parent.heads:
                        if found_one:  # make a copy and start another branch
                            l = list(_chain)
                            l.append(parent)
                            _add_into_chain(l, parent, head)
                        else:
                            _chain.append(parent)
                            _add_into_chain(_chain, parent, head)
                            found_one = True
                if not found_one:
                    ordered_chains.append(_chain)

            _add_into_chain([head], head, head)
            projection = self.projections.get(head, None)
            # We want to keep using existing projection objects as much as possible so they won't
            #  change colors on each update
            if projection:
                projection.update_chains(ordered_chains)
            else:
                projection = Projection(head, ordered_chains, next(self.projection_rotator))
                self.projections[head] = projection

        for head in old_heads - new_heads:
            self.remove_projection(head)
        self.update_projection_display()

    def update_projection_display(self):
        """ Don't change the projection data structures, but just draw them according to current
        drawing settings. It is quite expensive since the new settings may draw less than
        previous settings and this would mean removing projection visuals from nodes and edges.
        This is done by removing all projection displays before drawing them.
        :return:
        """
        projection_style = ctrl.settings.get('projection_style')
        for projection in self.projections.values():
            projection.set_visuals(projection_style)
