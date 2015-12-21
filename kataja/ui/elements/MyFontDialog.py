from PyQt5 import QtWidgets

from kataja.singletons import qt_prefs, ctrl


class MyFontDialog(QtWidgets.QFontDialog):
    """

    :param parent:
    :param role:
    :param initial_font:
    """

    def __init__(self, parent, role, initial_font):
        super().__init__(parent)
        self.setOption(QtWidgets.QFontDialog.NoButtons)
        self.setCurrentFont(qt_prefs.font(initial_font))
        self.currentFontChanged.connect(self.font_changed)
        self.role = role
        self.font_key = initial_font
        self.show()

    def font_changed(self, font):
        """

        :param font:
        """
        panel = self.parent()
        font_id = panel.cached_font_id
        font_id = ctrl.ui.create_or_set_font(font_id, font)
        panel.update_font_for_role(self.role, font_id)
        ctrl.main.action_finished()