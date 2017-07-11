from PyQt5 import QtWidgets

from kataja.singletons import ctrl, qt_prefs
from kataja.utils import open_symbol_data
from kataja.UIItem import UIWidget


class EmbeddedTextarea(QtWidgets.QPlainTextEdit, UIWidget):
    """

    :param parent:
    :param tip:
    :param font:
    :param prefill:
    """

    def __init__(self, parent, tooltip='', font=None, prefill='', on_edit=None):
        UIWidget.__init__(self, tooltip=tooltip)
        QtWidgets.QPlainTextEdit.__init__(self, parent)
        if prefill:
            self.setPlaceholderText(prefill)
        self.setAcceptDrops(True)
        self.setSizeAdjustPolicy(QtWidgets.QTextEdit.AdjustToContents)
        self.changed = False
        self.textChanged.connect(self.flag_as_changed)
        if not font:
            font = qt_prefs.get_font(g.CONSOLE_FONT)
        self.setStyleSheet(
            'font-family: "%s"; font-size: %spx; background-color: %s' % (font.family(),
                                                                          font.pointSize(),
                                                                          ctrl.cm.paper().name()))

        if on_edit:
            self.textChanged.connect(on_edit)
        #self.setFixedSize(200, 100)
        #self.text_area.textChanged.connect(self.text_area_check_for_resize)
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


    def text(self):
        return self.toPlainText()

    def setText(self, text):
        self.setPlainText(text)

    def update_visual(self, **kw):
        """

        :param kw:
        """
        if 'palette' in kw:
            self.setPalette(kw['palette'])
        if 'font' in kw:
            self.setFont(kw['font'])
        if 'text' in kw:
            self.setPlainText(kw['text'])

    def flag_as_changed(self, text):
        self.changed = True
