__author__ = 'purma'
from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import ctrl

rotating_colors = [('accent%s' % i, 'accent%str' % i) for i in range(1, 9)]


class ProjectionVisual(QtWidgets.QGraphicsItem):
    """ Transparent overlay to show which nodes belong to one projection
    """

    def __init__(self, data):
        super().__init__()
        self.d = data
        self.color = ctrl.cm.get(self.d.color_tr_id)
        self.show()

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65555

    def boundingRect(self):
        br = QtCore.QRectF()
        for chain in self.d.chains:
            for node in chain:
                br |= node.sceneBoundingRect()
        return br

    def paint(self, painter, style, QWidget_widget=None):
        painter.setBrush(self.color)
        painter.setPen(QtCore.Qt.NoPen)
        for chain in self.d.chains:
            vis_chain = [x for x in chain if x.is_visible()]
            if len(vis_chain) < 2:
                continue
            forward = []
            back = []
            sx = 0
            sy = 0
            start_x, start_y = vis_chain[0].current_scene_position
            # shape will be one continous filled polygon, so when we iterate
            # through nodes it needs to go through we make list of positions for
            # polygon going there (forward) and for its return trip (back).
            for node in vis_chain:
                sx, sy = node.current_scene_position
                # r = node.sceneBoundingRect()
                # p.addEllipse(r)
                forward.append((sx - 5, sy))
                back.append((sx + 5, sy))
            back.reverse()
            p = QtGui.QPainterPath(QtCore.QPointF(start_x, start_y + 5))
            for x, y in forward + [(sx, sy - 5)] + back:
                p.lineTo(x, y)
            painter.fillPath(p, self.color)
