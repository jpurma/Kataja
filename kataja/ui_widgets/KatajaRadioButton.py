from PyQt5 import QtWidgets
from kataja.UIItem import UIWidget


class KatajaRadioButton(QtWidgets.QRadioButton, UIWidget):
    action_slot = 'bgroup.buttonToggled'

    def __init__(self, parent=None, group=None, **kwargs):
        QtWidgets.QRadioButton.__init__(self, parent=parent)
        UIWidget.__init__(self, **kwargs)
        if group:
            group.addButton(self)

    def set_displayed_value(self, value):
        self.setChecked(value)
