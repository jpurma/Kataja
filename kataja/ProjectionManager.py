
import itertools

from kataja.Projection import Projection
from kataja.singletons import ctrl
from kataja.globals import CONSTITUENT_NODE


class ProjectionManager:

    def __init__(self, forest):
        self.forest = forest
        self.projections = {}
        self.guessed_projections = False
        self.projection_rotator = itertools.cycle(range(3, 8))


    @staticmethod
    def compute_projection_chains_for(head_node) -> list:
        """ Takes a node and looks at its parents trying to find if they are projections of this
        node. This doesn't rely on projection objects: this is the computation that builds
        chains necessary for creating projection objects.
        :param head_node:
        """
        chains = []

        def is_head_projecting_upwards(chain, node) -> None:
            chain.append(node)
            ends_here = True
            for parent in node.get_parents(similar=True, visible=False):
                if node in parent.heads:
                    ends_here = False
                    # create a copy of chain so that when the chain ends it will be added
                    # as separate chain to another projection branch
                    is_head_projecting_upwards(list(chain), parent)
            if ends_here and len(chain) > 1:
                chains.append(chain)
        is_head_projecting_upwards([], head_node)
        return chains

    def remove_projection(self, head_node):
        key = head_node.uid
        projection = self.projections.get(key, None)
        if projection:
            projection.set_visuals(False, False, False)
            del self.projections[key]

    def update_projections(self):
        """ Try to guess projections in the trees based on labels and aliases, and once this is
        done, create Projection objects that match all upward projections. Try to match
        Projection objects with existing visual markers for projections.
        :return:
        """
        # only do this the first time we load a new structure
        if ctrl.settings.get('guess_projections') and not self.guessed_projections:
            for tree in self.forest.trees:
                for node in tree.sorted_constituents:
                    node.guess_projection()
            self.guessed_projections = True

        # We want to keep using existing projection objects as much as possible so they won't change
        # colors randomly
        old_heads = set([x.head for x in self.projections.values()])

        new_heads = set()
        for node in self.forest.nodes.values():
            if node.node_type == CONSTITUENT_NODE:
                if not node.heads:
                    chains = ProjectionManager.compute_projection_chains_for(node)
                    if chains:
                        new_heads.add(node)
                        projection = self.projections.get(node.uid, None)
                        if projection:
                            projection.update_chains(chains)
                        else:
                            projection = Projection(node, chains, next(self.projection_rotator))
                            self.projections[node.uid] = projection
                node.in_projections = []
        for head in old_heads - new_heads:
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
