from PyQt5 import QtWidgets

from kataja.UIItem import UIWidget


class KatajaCheckBox(QtWidgets.QCheckBox, UIWidget):
    action_slot = 'stateChanged'

    def __init__(self, parent=None, **kwargs):
        QtWidgets.QCheckBox.__init__(self)
        self.setParent(parent)
        UIWidget.__init__(self, **kwargs)

    def set_displayed_value(self, value):
        self.setChecked(value)
