from PyQt5 import QtWidgets

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
        self.setCurrentColor(ctrl.cm.get(initial_color))
        self.currentColorChanged.connect(self.color_adjusted)
        self.role = role
        self.show()

    def color_adjusted(self, color):
        """

        :param color:
        """
        panel = self.parent()
        if panel:
            panel.update_color_for_role(self.role, color)
        ctrl.main.action_finished()