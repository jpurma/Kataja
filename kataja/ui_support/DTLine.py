from PyQt6 import QtWidgets, QtGui

from kataja.singletons import ctrl
from kataja.uniqueness_generator import next_available_type_id


def color_for(ds_type, tr=False):
    return ctrl.cm.d[f'accent{ds_type % 8 + 1}{"tr" if tr else ""}']


class DTLine(QtWidgets.QGraphicsLineItem):
    __qt_type_id__ = next_available_type_id()

    def __init__(self, state_id, parent_id, x1, y1, x2, y2, ds_type):
        super().__init__(x1, y1, x2, y2)
        self.state_id = state_id
        self.parent_id = parent_id
        self.selected = False
        self.ds_type = ds_type
        self.fog = False
        self.set_selected(False)

    def get_id(self):
        return self.state_id, self.parent_id

    def set_selected(self, value):
        self.selected = value
        if value:
            pen = QtGui.QPen(color_for(self.ds_type))
            pen.setWidth(3)
            self.setPen(pen)
        else:
            pen = QtGui.QPen(color_for(self.ds_type, self.fog))
            pen.setWidth(1)
            self.setPen(pen)

    def set_fog(self, value):
        if value != self.fog and not self.selected:
            pen = QtGui.QPen(color_for(self.ds_type, value))
            if value:
                pen.setWidth(0.5)
            else:
                pen.setWidth(1)
            self.setPen(pen)
        self.fog = value