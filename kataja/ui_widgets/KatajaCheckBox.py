from PyQt5 import QtWidgets
from kataja.UIItem import UIWidget


class KatajaCheckBox(QtWidgets.QCheckBox, UIWidget):

    def __init__(self, parent=None, **kwargs):
        QtWidgets.QCheckBox.__init__(self, parent=parent)
        UIWidget.__init__(self, **kwargs)
