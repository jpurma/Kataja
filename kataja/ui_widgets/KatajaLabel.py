from PyQt6 import QtWidgets

from kataja.singletons import ctrl


class KatajaBuddyLabel(QtWidgets.QLabel):
    """ KatajaBuddyLabels are supposed to be used with other fields. They expand the
    mouseover area of the field (for showing the tooltip) to the label and allow label to be
    disabled as the field is disabled.
    """

    def __init__(self, text, buddy):
        super().__init__()
        self.setParent(buddy.parentWidget())
        self.setText(text)
        self.setMouseTracking(True)
        self.setBuddy(buddy)

    def enterEvent(self, event):
        ctrl.ui.show_help(self.buddy(), event)

    def mouseMoveEvent(self, event):
        ctrl.ui.move_help(event)

    def leaveEvent(self, event):
        ctrl.ui.hide_help(self.buddy(), event)


class KatajaInfoLabel(QtWidgets.QLabel):
    """ KatajaInfoLabels are labels that can have their own tooltips that clarify or expand on the
    label text.
    """

    def __init__(self, text, tooltip='', parent=None):
        QtWidgets.QLabel.__init__(self)
        self.setParent(parent)
        self.setText(text)
        self.setMouseTracking(True)
        self.k_tooltip = tooltip

    def enterEvent(self, event):
        ctrl.ui.show_help(self, event)

    def mouseMoveEvent(self, event):
        ctrl.ui.move_help(event)

    def leaveEvent(self, event):
        ctrl.ui.hide_help(self, event)
