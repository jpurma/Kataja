
import kataja.globals as g
from kataja.ProjectionVisual import rotating_colors, ProjectionVisual
from kataja.singletons import ctrl
from kataja.saved.movables.nodes.ConstituentNode import strip_xbars


class Projection:
    """ Data structure for keeping track of projections. ProjectionVisual is
    used to draw these as separate graphicsitems, but these can be as well
    presented by modifying existing edges and nodes.
    """

    def __init__(self, head, chains, rotator):
        super().__init__()
        self.color_id, self.color_tr_id = rotating_colors[rotator]
        self.colorized = False
        self.strong_lines = False
        self.highlighter = False
        self.head = head # head in a projection is head node, not syntactic object
        self.chains = chains or []
        self.visual = None
        self._changes = False
        if head and chains:
            self.fix_labels()

    def update_chains(self, chains):
        changes = chains != self.chains
        self.chains = chains
        if changes:
            self._changes = True
            self.fix_labels()

    def add_visual(self):
        self.visual = ProjectionVisual(self)

    def get_edges(self):
        """ Return edges between nodes in this chain as a list
        :return:
        """
        res = []
        for chain in self.chains:
            if len(chain) < 2:
                return []
            child = chain[0]
            for parent in chain[1:]:
                edge = child.get_edge_to(parent, edge_type=g.CONSTITUENT_EDGE)
                if edge:
                    res.append(edge)
                child = parent
        return res

    def set_visuals(self, strong_lines, colorized, highlighter):
        self.colorized = colorized
        self.strong_lines = strong_lines
        if colorized:
            color_id = self.color_id
        else:
            color_id = None
        for edge in self.get_edges():
            edge.in_projections.append(self)
        for chain in self.chains:
            if len(chain) > 1:
                for node in chain:
                    node.in_projections.append(self)
        self.highlighter = highlighter
        if highlighter:
            if not self.visual:
                self.add_visual()
                ctrl.forest.add_to_scene(self.visual)
            elif self.visual.scene() != ctrl.graph_scene:
                ctrl.forest.add_to_scene(self.visual)
            else:
                self.visual.update()
        elif self.visual:
            ctrl.forest.remove_from_scene(self.visual)
            self.visual = None

    def fix_labels(self):
        """ If node has head, then start from this node, and
        move upwards labeling the nodes that also use the same head.

        If head is None, then remove label.
        :return:
        """
        xbar = ctrl.settings.get('use_xbar_aliases')
        label = self.head.label
        if not xbar:
            for chain in self.chains:
                for node in chain[1:]:
                    if node.label != label:
                        node.label = label
                        node.update_label()
            return
        head_base = strip_xbars(str(self.head.label or self.head.get_syn_label()))
        if head_base != str(self.head.label):
            self.head.label = head_base
        for chain in self.chains:
            new_label = head_base + '´'
            for node in chain[1:-1]:
                if str(node.label) != new_label:
                    node.label = new_label
                    node.update_label()
            node = chain[-1]
            new_label = head_base + 'P'
            if str(node.display_label) != new_label:
                node.label = new_label
                node.update_label()
