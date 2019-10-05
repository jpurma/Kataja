from PyQt5 import QtWidgets

from kataja.UIItem import UIWidget
from kataja.singletons import ctrl
from kataja.utils import open_symbol_data


class KatajaTextarea(QtWidgets.QPlainTextEdit, UIWidget):
    def __init__(self, parent, tooltip='', font=None, prefill='', on_edit=None):
        UIWidget.__init__(self, tooltip=tooltip)
        QtWidgets.QPlainTextEdit.__init__(self, parent)
        if prefill:
            self.setPlaceholderText(prefill)
        self.setAcceptDrops(True)
        self.setSizeAdjustPolicy(QtWidgets.QTextEdit.AdjustToContents)
        self.setMinimumHeight(24)
        self.changed = False
        self.textChanged.connect(self.flag_as_changed)
        # if a font is provided here, it has to be updated manually. Default font (console) will get updated through
        # master stylesheet
        if font:
            self.setStyleSheet('font-family: "%s"; font-size: %spx;' % (
                font.family(), font.pointSize()))

        if on_edit:
            self.textChanged.connect(on_edit)
        self.updateGeometry()

    def dragEnterEvent(self, event):
        """ Announce support for regular ascii drops and drops of characters
        from symbolpanel.
        :param event: QDragEnterEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            return QtWidgets.QPlainTextEdit.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """ Support regular ascii drops and drops of characters from
        symbolpanel.
        :param event: QDropEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            data = open_symbol_data(event.mimeData())
            if data and 'char' in data:
                self.insert(data['char'])
                event.acceptProposedAction()
        else:
            return QtWidgets.QPlainTextEdit.dropEvent(self, event)

    def focusInEvent(self, event):
        self.grabKeyboard()
        ctrl.suppress_arrow_shortcuts()
        return QtWidgets.QPlainTextEdit.focusInEvent(self, event)

    def focusOutEvent(self, event):
        self.releaseKeyboard()
        ctrl.allow_arrow_shortcuts()
        return QtWidgets.QPlainTextEdit.focusOutEvent(self, event)

    def text(self):
        return self.toPlainText()

    def setText(self, text):
        self.setPlainText(text)

    def flag_as_changed(self):
        self.changed = True

    def enterEvent(self, event):
        UIWidget.enterEvent(self, event)
        return QtWidgets.QPlainTextEdit.enterEvent(self, event)

    def mouseMoveEvent(self, event):
        UIWidget.mouseMoveEvent(self, event)
        return QtWidgets.QPlainTextEdit.mouseMoveEvent(self, event)

    def leaveEvent(self, event):
        UIWidget.leaveEvent(self, event)
        return QtWidgets.QPlainTextEdit.leaveEvent(self, event)
