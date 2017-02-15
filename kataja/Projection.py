import string

import kataja.globals as g
from kataja.ProjectionVisual import rotating_colors, ProjectionVisual
from kataja.singletons import ctrl
from kataja.parser.INodes import as_text
from kataja.utils import time_me


class Projection:
    """ Data structure for keeping track of projections. ProjectionVisual is
    used to draw these as separate graphicsitems, but these can be as well
    presented by modifying existing edges and nodes.
    """

    @staticmethod
    def get_base_label(node):
        head_part = as_text(node.label, omit_triangle=True, omit_index=True)
        if head_part:
            head_part = head_part.splitlines()[0].strip()
            last_char = head_part[-1]
            if len(head_part) > 1 and last_char in ('P', "'", "´"):
                head_part = head_part[:-1]
        return head_part

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
        self.base_label = ''
        self.update_autolabels()

    def update_chains(self, chains):
        self.chains = chains
        self.update_autolabels()

    def update_color(self):
        if self.base_label:
            code = sum([ord(c) for c in self.base_label])
        else:
            code = 0
        self.color_id, self.color_tr_id = rotating_colors[code % 8]

    def add_visual(self):
        self.visual = ProjectionVisual(self)

    def get_edges(self):
        """ Return edges between nodes in this chain as a list
        :return:
        """
        res = set()
        for chain in self.chains:
            if len(chain) < 2:
                return []
            child = chain[0]
            for parent in chain[1:]:
                edge = child.get_edge_to(parent, edge_type=g.CONSTITUENT_EDGE)
                if edge:
                    res.add(edge)
                child = parent
        return res

    def set_visuals(self, strong_lines, colorized, highlighter):
        self.colorized = colorized
        self.strong_lines = strong_lines
        for edge in self.get_edges():
            if self not in edge.in_projections:
                edge.in_projections.append(self)
        for chain in self.chains:
            if len(chain) > 1:
                for node in chain:
                    if self not in node.in_projections:
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

    def update_autolabels(self):
        """ Compute x-bar labels and put them to node.autolabel
        :return:
        """
        xbar = ctrl.settings.get('use_xbar_aliases') or True
        self.base_label = Projection.get_base_label(self.head)
        if xbar:
            for chain in self.chains:
                if len(chain) > 1 and len(chain[1].get_children(visible=False, similar=True)) == 1:
                    chain[0].autolabel = Projection.get_base_label(self.head)
                    self.base_label = Projection.get_base_label(chain[1])
                    chain = chain[1:]
                last = len(chain) - 1
                for i, node in enumerate(chain):
                    if i == last:
                        node.autolabel = self.base_label + 'P'
                    elif i == 0:
                        node.autolabel = node.label # self.base_label

                    else:
                        node.autolabel = self.base_label + '´'
                    node.update_label()
        else:
            for chain in self.chains:
                for i, node in enumerate(chain):
                    node.autolabel = self.base_label
                    node.update_label()
        self.update_color()
