import itertools


class ProjectionManager:
    def __init__(self, forest):
        self.forest = forest
        self.projections = {}
        self.projection_rotator = itertools.cycle(range(3, 8))

    @property
    def projection_visuals(self):
        return (p.visual for p in self.projections.values() if p.visual)

    def remove_projection(self, head):
        projection = self.projections.get(head, None)
        if projection:
            projection.set_visuals(0)
            del self.projections[head]

    def update_projection_display(self):
        """ Don't change the projection data structures, but just draw them according to current
        drawing settings. It is quite expensive since the new settings may draw less than
        previous settings and this would mean removing projection visuals from nodes and edges.
        This is done by removing all projection displays before drawing them.
        :return:
        """
        highlight = self.forest.settings.get('highlight_projections')
        # for projection in self.projections.values():
        #    projection.set_visuals(projection_style)
