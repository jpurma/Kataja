from PyQt5 import QtWidgets

from kataja.singletons import ctrl
from kataja.utils import open_symbol_data


class EmbeddedLineEdit(QtWidgets.QLineEdit):
    """

    :param parent:
    :param tip:
    :param font:
    :param prefill:
    """

    def __init__(self, parent, tip='', font=None, prefill='', stretch=False, on_edit=None):
        QtWidgets.QLineEdit.__init__(self, parent)
        if tip:
            if ctrl.main.use_tooltips:
                self.setToolTip(tip)
                self.setToolTipDuration(2000)
            self.setStatusTip(tip)
        if font:
            self.setFont(font)
        if prefill:
            self.setPlaceholderText(prefill)
        self.stretch = stretch
        if stretch:
            self.textChanged.connect(self.check_for_resize)
        self.textEdited.connect(self.flag_as_changed)
        if on_edit:
            self.textChanged.connect(on_edit)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.changed = False
        self.original = ''

    def check_for_resize(self, *args, **kwargs):
        pass

    def set_original(self, text):
        """ This is the text to compare against for changes.
        :param text:
        :return:
        """
        self.original = text

    def dragEnterEvent(self, event):
        """ Announce support for regular ascii drops and drops of characters
        from symbolpanel.
        :param event: QDragEnterEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            return QtWidgets.QLineEdit.dragEnterEvent(self, event)

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
            return QtWidgets.QLineEdit.dropEvent(self, event)

    def update_visual(self, **kw):
        """

        :param kw:
        """
        if 'palette' in kw:
            self.setPalette(kw['palette'])
        if 'font' in kw:
            self.setFont(kw['font'])
        if 'text' in kw:
            self.setText(kw['text'])

    def flag_as_changed(self, text):
        self.changed = True
