from PyQt5 import QtWidgets

from kataja.UIItem import UIWidget


class KatajaButtonGroup(QtWidgets.QButtonGroup, UIWidget):
    action_slot = 'buttonClicked'

    def __init__(self, parent=None, **kwargs):
        QtWidgets.QButtonGroup.__init__(self, parent=parent)
        UIWidget.__init__(self, **kwargs)

    def set_displayed_value(self, value):
        pass
