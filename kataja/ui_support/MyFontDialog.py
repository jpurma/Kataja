from PyQt5 import QtWidgets

from kataja.singletons import qt_prefs, ctrl


class MyFontDialog(QtWidgets.QFontDialog):
    """

    :param parent:
    :param role:
    :param initial_font:
    """

    def __init__(self, parent, initial_font):
        super().__init__(parent)
        self.setOption(QtWidgets.QFontDialog.NoButtons)
        self.setCurrentFont(qt_prefs.get_font(initial_font))
        self.currentFontChanged.connect(self.font_changed)
        self.font_key = initial_font
        self.show()

    def font_changed(self, font):
        """

        :param font:
        """
        parent = self.sender()
        while parent and not isinstance(parent, MyFontDialog):
            print(parent, parent.parent())
            parent = parent.parent()
        if parent:
            font_key = ctrl.ui.get_role_of_font_dialog(parent)
            panel = self.parent()
            if panel:
                panel.receive_font_from_selector(font_key, font)
        else:
            print('???')
