from PyQt5 import QtWidgets

from kataja.singletons import ctrl
from kataja.utils import open_symbol_data
from kataja.UIItem import UIWidget


class KatajaLineEdit(QtWidgets.QLineEdit, UIWidget):
    """

    :param parent:
    :param tip:
    :param font:
    :param prefill:
    """

    def __init__(self, parent, tooltip='', font=None, prefill='', stretch=False, on_edit=None,
                 on_finish=None, on_return=None):
        QtWidgets.QLineEdit.__init__(self, parent)
        UIWidget.__init__(self, tooltip=tooltip)
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
        if on_finish:
            self.editingFinished.connect(on_finish)
        if on_return:
            self.returnPressed.connect(on_return)
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

    def flag_as_changed(self, text):
        self.changed = True
