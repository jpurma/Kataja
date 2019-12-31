from PyQt5 import QtCore

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.buttons.OverlayButton import OverlayButton, NodeOverlayButton, GroupButton


class CutEdgeButton(OverlayButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key='accent3',
                         pixmap=qt_prefs.cut_icon, action='disconnect_edge')
        self.priority = 50

    @classmethod
    def condition(cls, edge):
        return edge.start and edge.end

    def update_position(self):
        """ Put button left and below the starting point of edge.
        """
        if self.host:
            p = self.host.path.get_point_at(0.7)
            if abs(self.host.start_point[0] - self.host.end_point[0]) < 10:
                p.setX(p.x() + 15)
            p.setY(p.y() - 30)
            pos = ctrl.main.graph_view.mapFromScene(p)
            self.avoid_overlaps(pos, 0, -8)
            self.move(pos)


class RemoveMergerButton(NodeOverlayButton):
    """ Button to delete unnecessary node between grandparent and child"""

    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, pixmap='delete_icon',
                         action='remove_merger')
        self.priority = 99

    @classmethod
    def condition(cls, host):
        return host.node_type == g.CONSTITUENT_NODE and host.is_unnecessary_merger()


class RemoveNodeButton(NodeOverlayButton):
    """ Button to delete node """

    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key='accent3',
                         pixmap='delete_icon', action='remove_node')
        self.priority = 100

    @classmethod
    def condition(cls, host):
        return (host.node_type == g.CONSTITUENT_NODE and not host.is_unnecessary_merger()) \
               or host.node_type != g.CONSTITUENT_NODE


class DeleteGroupButton(GroupButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key='accent3',
                         pixmap=qt_prefs.delete_icon, action='delete_group_items')
        self.priority = 24


class RotateButton(NodeOverlayButton):
    """ Button to rotate node """

    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16,
                         pixmap=qt_prefs.h_refresh_small_icon, action='rotate_children')
        self.priority = 100

    def update_position(self):
        """ """
        adjust = QtCore.QPointF(9, 16)
        x, y = self.host.centered_scene_position
        p = QtCore.QPointF(x + (self.host.width / 2), y)
        p = ctrl.main.graph_view.mapFromScene(p) + adjust
        p = p.toPoint()
        p = self.avoid_overlaps(p, 8, 0)
        self.move(p)

    @classmethod
    def condition(cls, host):
        return host.node_type == g.CONSTITUENT_NODE and not host.triangle_stack and len(host.get_children()) > 1
