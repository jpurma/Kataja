from PyQt5 import QtWidgets
from PyQt5.QtGui import QColor

from kataja.singletons import ctrl


class MyColorDialog(QtWidgets.QColorDialog):
    """

    :param parent:
    :param role:
    :param initial_color:
    """

    def __init__(self, parent, role, initial_color):
        super().__init__(parent)
        self.setOption(QtWidgets.QColorDialog.NoButtons)
        # self.setOption(QtWidgets.QColorDialog.DontUseNativeDialog)
        self.setOption(QtWidgets.QColorDialog.ShowAlphaChannel)
        for i, key in enumerate(ctrl.cm.color_keys):
            self.setStandardColor(i, ctrl.cm.get(key))
        self.role = role
        color = ctrl.cm.get(initial_color) or ctrl.cm.get('content1')
        self.setCurrentColor(color)
        self.currentColorChanged.connect(self.color_adjusted)
        self.show()

    def color_adjusted(self, color):
        """

        :param color:
        """
        panel = self.parent()
        if panel:
            panel.receive_color_from_color_dialog(self.role, color)