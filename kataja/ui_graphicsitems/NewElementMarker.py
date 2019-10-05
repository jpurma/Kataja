# coding=utf-8

from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.UIItem import UIGraphicsItem
from kataja.singletons import prefs, ctrl
from kataja.uniqueness_generator import next_available_type_id


class MarkerStartPoint(QtWidgets.QGraphicsItem):
    __qt_type_id__ = next_available_type_id()

    def __init__(self, parent):
        QtWidgets.QGraphicsItem.__init__(self, parent)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setAcceptHoverEvents(True)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def paint(self, painter, options, QWidget_widget=None):
        if prefs.touch:
            p = QtGui.QPen(ctrl.cm.ui_tr())
            p.setWidth(2)
            painter.setPen(p)
            painter.drawEllipse(-6, -6, 12, 12)
        else:
            p = QtGui.QPen(ctrl.cm.ui())
            p.setWidthF(0.5)
            painter.setPen(p)
            painter.drawRect(-2, -2, 4, 4)

    def boundingRect(self):
        if prefs.touch:
            return QtCore.QRectF(-6, -6, 12, 12)
        else:
            return QtCore.QRectF(-2, -2, 4, 4)

    def mouseMoveEvent(self, event):
        if ctrl.pressed is self:
            if ctrl.dragged_set or (event.buttonDownScenePos(
                    QtCore.Qt.LeftButton) - event.scenePos()).manhattanLength() > 6:
                self.drag(event)
                ctrl.graph_scene.dragging_over(event.scenePos())

    def mouseReleaseEvent(self, event):
        if ctrl.pressed is self:
            ctrl.release(self)
            if ctrl.dragged_set:
                ctrl.graph_scene.kill_dragging()
            return None  # this mouseRelease is now consumed
        super().mouseReleaseEvent(event)

    def drag(self, event):
        pi = self.parentItem()
        if pi:
            pi.update_position(event.scenePos())

    def drop_to(self, x, y, recipient=None, shift_down=False):
        pass


class NewElementMarker(UIGraphicsItem, QtWidgets.QGraphicsItem):
    __qt_type_id__ = next_available_type_id()
    unique = True

    def __init__(self, scene_pos, embed):
        UIGraphicsItem.__init__(self)
        QtWidgets.QGraphicsItem.__init__(self)
        self.start_point = None
        self.end_point = None
        self.embed = embed
        self.update_position(scene_pos=scene_pos)
        self.start_point_cp = MarkerStartPoint(self)
        self.start_point_cp.show()

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def paint(self, painter, options, QWidget_widget=None):
        b = ctrl.cm.ui()
        p = QtGui.QPen(b)
        p.setWidthF(0.5)
        painter.setPen(p)
        painter.drawLine(QtCore.QPoint(0, 0), self.end_point)

    def boundingRect(self):
        return QtCore.QRectF(self.start_point, self.end_point)

    def update_position(self, scene_pos=None):
        self.prepareGeometryChange()
        if scene_pos:
            self.start_point = scene_pos
        magnet, type = self.embed.magnet()
        end_pos = self.embed.pos() + magnet
        if type in [6, 8]:
            end_pos -= QtCore.QPoint(0, 20)
        elif type in [1, 3, 4, 5]:
            end_pos += QtCore.QPoint(0, 20)
        elif type in [2, 7]:
            end_pos += QtCore.QPoint(20, 0)
        v = self.embed.parentWidget()
        self.setPos(self.start_point)
        self.end_point = self.mapFromScene(v.mapToScene(end_pos)).toPoint()
