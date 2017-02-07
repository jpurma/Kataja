
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
                    #print('head_part_of_child: %r , head_part: %r' % (head_part_of_child,
                    # head_part))
                    if head_part_of_child:
                        if head_part_of_child == head_part:
                            #print('match')
                            heads += child.heads
                            #print(heads)
            node.set_heads(heads)
            return head_part

        _guess_head(root)

    @time_me
    def remove_projection(self, head):
        projection = self.projections.get(head, None)
        if projection:
            projection.set_visuals(False, False, False)
            del self.projections[head]

    @time_me
    def update_projections(self):

        chains = defaultdict(list)
        old_heads = set(self.projections.keys())

        for node in self.forest.nodes.values():
            if node.node_type == CONSTITUENT_NODE:
                for head in node.heads:
                    chains[head].append(node)
                node.in_projections = []
                node.autolabel = ''

        for head, chain in list(chains.items()):
            if head not in chain:
                print('head %s not in chain: %s' % (str(head), str(chain)))
                for node in chain:
                    if head in node.heads:
                        node.poke('heads')
                        node.heads.remove(head)
                del chains[head]
                continue
            chain.remove(head)
            ordered_chains = [[head]]
            progress = True
            while chain and progress:
                progress = False
                for oc in list(ordered_chains):
                    last = oc[-1]
                    found = False
                    for i, node in enumerate(list(chain)):
                        if last in node.get_children(visible=False, similar=True):
                            chain.pop(i)
                            progress = True
                            if found:
                                oc = list(oc)
                                ordered_chains.append(oc)
                            found = True
                            oc.append(node)
            projection = self.projections.get(head, None)
            # We want to keep using existing projection objects as much as possible so they won't
            #  change colors on each update
            if projection:
                projection.update_chains(ordered_chains)
            else:
                projection = Projection(head, ordered_chains, next(self.projection_rotator))
                self.projections[head] = projection

        new_heads = set(chains.keys())
        for head in old_heads - new_heads:
            print('remove projection starting with ', head)
            self.remove_projection(head)
        for edge in self.forest.edges.values():
            edge.in_projections = []
        self.update_projection_display()

    def update_projection_display(self):
        """ Don't change the projection data structures, but just draw them according to current
        drawing settings. It is quite expensive since the new settings may draw less than
        previous settings and this would mean removing projection visuals from nodes and edges.
        This is done by removing all projection displays before drawing them.
        :return:
        """
        strong_lines = ctrl.settings.get('projection_strong_lines')
        colorized = ctrl.settings.get('projection_colorized')
        highlighter = ctrl.settings.get('projection_highlighter')
        for projection in self.projections.values():
            projection.set_visuals(strong_lines, colorized, highlighter)
