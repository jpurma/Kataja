# coding=utf-8
from PyQt5 import QtWidgets, QtCore

from kataja.singletons import ctrl
from kataja.saved.movables.Node import Node


class ResizeHandle(QtWidgets.QSizeGrip):

    def __init__(self, parent, resizable):
        super().__init__(parent)
        self.resizable = resizable
        self.pressed = False
        self.adjust = None

    def mousePressEvent(self, e):
        self.pressed = True
        grandparent = self.resizable.parent()
        rrect = self.resizable.geometry()
        bottom_right = grandparent.mapToGlobal(rrect.bottomRight())
        self.adjust = bottom_right - e.globalPos()

    def mouseReleaseEvent(self, e):
        self.pressed = False
        self.adjust = None

    def mouseMoveEvent(self, e):
        if e.buttons() != QtCore.Qt.LeftButton:
            return
        if not self.pressed:
            return
        gp = e.globalPos()
        size = self.resizable.size()
        rrect = self.resizable.geometry()
        grandparent = self.resizable.parent()
        bottom_right = grandparent.mapToGlobal(rrect.bottomRight())
        size_diff = bottom_right - gp - self.adjust
        nw = max(16, size.width() - size_diff.x())
        nh = max(16, size.height() - size_diff.y())
        self.resizable.setMinimumSize(nw, nh)
        pw = self.parentWidget()
        if hasattr(pw, 'update_size'):
            pw.update_size()
        #self.resizable.resize(size.width() - size_diff.x(), size.height() - size_diff.y())

    def eventFilter(self, obj, event):
        """ Remove check for hiding size grip on full screen --
        widgets should be always resizable.
        :param obj:
        :param event:
        :return:
        """
        return False


class GraphicsResizeHandle(QtWidgets.QSizeGrip):

    def __init__(self, view, host):
        super().__init__(view)
        self.host = host
        self.pressed = False
        self.adjust = None
        self.update_position()
        self.ui_key = host.uid + '_resize_handle'
        self.show()

    def update_position(self):
        v = ctrl.graph_view
        br = self.host.sceneBoundingRect().bottomRight()
        bottom_right = v.mapFromScene(br)
        self.move(bottom_right)

    def mousePressEvent(self, e):
        self.pressed = True
        v = ctrl.graph_view
        br = self.host.sceneBoundingRect().bottomRight()
        global_bottom_right = v.mapToGlobal(v.mapFromScene(br))
        self.adjust = global_bottom_right - e.globalPos()

    def mouseReleaseEvent(self, e):
        self.pressed = False
        self.adjust = None

    def mouseMoveEvent(self, e):
        if e.buttons() != QtCore.Qt.LeftButton:
            return
        if not self.pressed:
            return
        gp = e.globalPos()
        w = self.host.width
        h = self.host.height
        v = ctrl.graph_view
        br = self.host.sceneBoundingRect().bottomRight()
        global_bottom_right = v.mapToGlobal(v.mapFromScene(br))
        size_diff = global_bottom_right - gp - self.adjust
        new_width = w - size_diff.x()
        if isinstance(self.host, Node):
            lc = self.host.label_object
            if lc.char_width:
                lc.line_length = max(1, new_width / lc.char_width)
                self.host.update_label()
                self.update_position()
            else:
                print('no char width for label, why?')


    def eventFilter(self, obj, event):
        """ Remove check for hiding size grip on full screen --
        widgets should be always resizable.
        :param obj:
        :param event:
        :return:
        """
        return False
