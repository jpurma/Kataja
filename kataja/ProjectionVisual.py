__author__ = 'purma'
from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import ctrl
import kataja.globals as g

rotating_colors = [('accent%s' % i, 'accent%str' % i) for i in range(1, 9)]


class ProjectionData:
    """ Data structure for keeping track of projections. ProjectionVisual is
    used to draw these as separate graphicsitems, but these can be as well
    presented by modifying existing edges and nodes.
    """

    def __init__(self, head, rotator):
        super().__init__()
        self.color_id, self.color_tr_id = rotating_colors[rotator]
        self.head = head
        self.chain = [head]
        self.visual = None

    def __contains__(self, item):
        return item in self.chain

    def __len__(self):
        return len(self.chain)

    def add_to_chain(self, node):
        if node in self.chain:
            return
        for i, item in enumerate(self.chain):
            if node in item.get_children():
                self.chain.insert(i, node)
                return
        self.chain.append(node)

    def add_visual(self):
        self.visual = ProjectionVisual(self)

    def remove_from_chain(self, node):
        if node not in self.chain:
            return
        self.chain.remove(node)

    def get_edges(self):
        """ Return edges between nodes in this chain as a list
        :return:
        """
        if len(self.chain) < 2:
            return []
        child = None
        res = []
        for parent in self.chain:
            if child:
                edge = child.get_edge_to(parent, edge_type=g.CONSTITUENT_EDGE)
                if edge:
                    res.append(edge)
            child = parent
        return res

    def verify_chain(self):
        """ Verify that chain
        :return: True if chain is valid, False if the projection shouldn't exist
        anymore, if the head is no more its own head. Sort out the chain if
        it has ordering problems.
        """
        prev_node = None
        new_chain = []
        if self.head.scene() is None:
            return False
        if self.head != self.head.head:
            print('obsolete projection chain: ', self.head)
            return False
        order_problem = False
        for node in self.chain:
            if node.head is self.head and node is not self.head:
                new_chain.append(node)
            if prev_node and prev_node not in node.get_children():
                order_problem = True
            prev_node = node
        if order_problem and new_chain:
            lowest = self.head
            sorted_chain = [lowest]
            new_chain = set(new_chain)
            while new_chain:
                found = None
                for node in new_chain:
                    if lowest in node.get_children():
                        found = node
                        break
                if found:
                    sorted_chain.append(found)
                    new_chain.remove(found)
                    lowest = found
                else:
                    raise IndexError('broken projection chain: %s' % self.chain)
            self.chain = sorted_chain
        else:
            self.chain = [self.head] + new_chain
        return True


class ProjectionVisual(QtWidgets.QGraphicsItem):
    """ Transparent overlay to show which nodes belong to one projection
    """

    def __init__(self, data):
        super().__init__()
        self.d = data
        self.color = ctrl.cm.get(self.d.color_tr_id)
        self.show()

    def boundingRect(self):
        br = QtCore.QRectF()
        for node in self.d.chain:
            br.united(node.sceneBoundingRect())
        return br

    def paint(self, painter, style, QWidget_widget=None):
        vis_chain = [x for x in self.d.chain if x.is_visible()]
        if len(vis_chain) < 2:
            return
        painter.setBrush(self.color)
        painter.setPen(QtCore.Qt.NoPen)
        forward = []
        back = []
        sx = 0
        sy = 0
        if vis_chain:
            start_x, start_y, start_z = vis_chain[0].current_scene_position
            # shape will be one continous filled polygon, so when we iterate
            # through nodes it needs to go through we make list of positions for
            # polygon going there (forward) and for its return trip (back).
            for node in vis_chain:
                sx, sy, sz = node.current_scene_position
                # r = node.sceneBoundingRect()
                # p.addEllipse(r)
                forward.append((sx - 5, sy))
                back.append((sx + 5, sy))
            back.reverse()
            p = QtGui.QPainterPath(QtCore.QPointF(start_x, start_y + 5))
            for x, y in forward + [(sx, sy - 5)] + back:
                p.lineTo(x, y)
            painter.fillPath(p, self.color)

#
# def blob_path(start_point=None, end_point=None, curve_adjustment=None,
#               alignment=LEFT, thickness=4, start=None, end=None,
#               inner_only=False, **kwargs):
#     """ Surround the node with circular shape that stretches to other node
#     :param inner_only:
#     :param start_point:
#     :param end_point:
#     :param curve_adjustment:
#     :param alignment:
#     :param thickness:
#     :param start:
#     :param end:
#     :param kwargs:
#     """
#     if start:
#         scx, scy, scz = start.current_position
#     else:
#         scx, scy, scz = start_point
#     if end:
#         ecx, ecy, ecz = end.current_position
#     else:
#         ecx, ecy, ecz = end_point
#     t2 = thickness * 2
#
#     sx, sy, sz = start_point
#     ex, ey, dummy = end_point
#
#     inner_path = QtGui.QPainterPath(Pf(sx, sy))
#     inner_path.lineTo(ex, ey)
#
#     if inner_only:
#         return None, inner_path, []
#
#     if start:
#         sx1, sy1, sw, sh = start.boundingRect().getRect()
#     else:
#         sx1 = -10
#         sy1 = -10
#         sw = 20
#         sh = 20
#     if end:
#         ex1, ey1, ew, eh = end.boundingRect().getRect()
#     else:
#         ex1 = -10
#         ey1 = -10
#         ew = 20
#         eh = 20
#
#     sx1 += scx
#     sy1 += scy
#     ex1 += ecx
#     ey1 += ecy
#     c1x = (scx + ecx) / 2
#     c1y = (scy + ecy) / 2
#     path1 = QtGui.QPainterPath()
#     path1.addEllipse(sx1 - thickness, sy1 - thickness, sw + t2, sh + t2)
#     path1neg = QtGui.QPainterPath()
#     path1neg.addEllipse(sx1, sy1, sw, sh)
#
#     path2 = QtGui.QPainterPath()
#     path2.addEllipse(ex1 - thickness, ey1 - thickness, ew + t2, eh + t2)
#     path2neg = QtGui.QPainterPath()
#     path2neg.addEllipse(ex1, ey1, ew, eh)
#     path3 = QtGui.QPainterPath()
#     path3.moveTo(sx1, scy)
#     path3.quadTo(c1x, c1y, ex1, ecy)
#     path3.lineTo(ex1 + ew, ecy)
#     path3.quadTo(c1x, c1y, sx1 + sw, scy)
#     path = path1.united(path2)
#     path = path.united(path3)
#     path = path.subtracted(path1neg)
#     path = path.subtracted(path2neg)
#     return path.simplified(), inner_path, []
#
#
