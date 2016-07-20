from PyQt5 import QtWidgets

from kataja.singletons import ctrl
from kataja.utils import open_symbol_data


class EmbeddedTextarea(QtWidgets.QPlainTextEdit):
    """

    :param parent:
    :param tip:
    :param font:
    :param prefill:
    """

    def __init__(self, parent, tip='', font=None, prefill=''):
        QtWidgets.QPlainTextEdit.__init__(self, parent)
        if tip:
            if ctrl.main.use_tooltips:
                self.setToolTip(tip)
                self.setToolTipDuration(2000)
            self.setStatusTip(tip)
        if font:
            self.setFont(font)
        if prefill:
            self.setPlaceholderText(prefill)
        self.setAcceptDrops(True)
        self.setSizeAdjustPolicy(QtWidgets.QTextEdit.AdjustToContents)
        self.changed = False
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

    # currently not used
    def text_area_check_for_resize(self):
        text = self.text_area.toPlainText()
        max_height = 400
        min_width = 400
        fh = self.text_area.fontMetrics().height()
        rows = self.text_area.document().size().height()
        tot = min(fh * rows + 5, max_height)
        if self.text_area.height() < tot:
            if self.text_area.width() < min_width:
                self.setFixedWidth(min_width)
            self.setFixedHeight(tot)
            self.parentWidget().update_size()
        if self.on_edit:
            self.on_edit(text)

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

    def changeEvent(self, ev):
        self.changed = True
        print('textarea text changed')
        return QtWidgets.QPlainTextEdit.changeEvent(self, ev)