from PyQt6 import QtWidgets, QtGui, QtCore

from kataja.singletons import qt_prefs, ctrl
from kataja.uniqueness_generator import next_available_type_id


def color_for(ds_type, tr=False):
    return ctrl.cm.d[f'accent{ds_type % 8 + 1}{"tr" if tr else ""}']


class DTNode(QtWidgets.QGraphicsEllipseItem):
    __qt_type_id__ = next_available_type_id()

    def __init__(self, state_id, x, y, msg, ds_type=0):
        super().__init__(x - 3, y - 3, 6, 6)
        self.state_id = state_id
        self.setPen(qt_prefs.no_pen)
        self.k_tooltip = f'{state_id}: {msg}'
        self.ds_type = ds_type
        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsObject.GraphicsItemFlag.ItemIsSelectable)
        self.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.setBrush(color_for(ds_type))
        self.selected = False
        self.fog = False

    def set_selected(self, value):
        self.selected = value
        if value:
            pen = QtGui.QPen(ctrl.cm.lighter(color_for(self.ds_type)))
            pen.setWidth(3)
            self.setPen(pen)
        else:
            self.setPen(qt_prefs.no_pen)

    def set_fog(self, value):
        if value != self.fog:
            self.fog = value
            self.setBrush(color_for(self.ds_type, self.fog))

    def hoverEnterEvent(self, event):
        self.setBrush(ctrl.cm.lighter(color_for(self.ds_type)))
        ctrl.ui.show_help(self, event)

    def hoverMoveEvent(self, event):
        ctrl.ui.move_help(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(color_for(self.ds_type, self.fog))
        ctrl.ui.hide_help(self, event)

    def mouseReleaseEvent(self, event):
        ctrl.main.trigger_action('jump_to_derivation_by_id', self.state_id)
        super().mouseReleaseEvent(event)