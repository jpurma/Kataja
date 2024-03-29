from PyQt6 import QtWidgets, QtGui

from kataja.UIItem import UIWidget
from kataja.utils import open_symbol_data


class ExpandingLineEdit(QtWidgets.QWidget, UIWidget):

    def __init__(self, parent, tooltip='', big_font=None, smaller_font=None, prefill='',
                 on_edit=None):
        # noinspection PyArgumentList
        QtWidgets.QWidget.__init__(self, parent)
        UIWidget.__init__(self, tooltip=tooltip)
        self.line_mode = True
        self.original_text = ''
        layout = QtWidgets.QVBoxLayout()
        self.line_edit = QtWidgets.QLineEdit(parent)
        # self.command_prompt.setClearButtonEnabled(True)
        self.text_area = QtWidgets.QPlainTextEdit(parent)
        self.text_area.setAutoFillBackground(True)
        self.text_area.setSizeAdjustPolicy(self.text_area.SizeAdjustPolicy.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        self.on_edit = on_edit
        self.line_edit.show()
        self.text_area.hide()
        self.text_area.setEnabled(False)
        self.line_edit.setEnabled(True)
        self.cut_point = 24
        layout.setContentsMargins(0, 0, 0, 0)
        # noinspection PyArgumentList
        layout.addWidget(self.line_edit)
        # noinspection PyArgumentList
        layout.addWidget(self.text_area)
        self.setLayout(layout)
        self.line_edit.setMinimumHeight(26)
        self.text_area.setMinimumHeight(40)
        self.k_tooltip = tooltip
        if big_font:
            self.line_edit.setFont(big_font)
        if smaller_font:
            self.text_area.setFont(smaller_font)
        if prefill:
            self.line_edit.setPlaceholderText(prefill)
            self.text_area.setPlaceholderText(prefill)
        self.line_edit.textChanged.connect(self.line_edit_check_for_resize)
        self.text_area.textChanged.connect(self.text_area_check_for_resize)
        self.setAcceptDrops(True)
        self.line_edit.setDragEnabled(True)
        self.original_size = None
        self.changed = False

    def set_original(self, text):
        self.original_text = text

    def text(self):
        if self.line_mode:
            return self.line_edit.text()
        else:
            return self.text_area.toPlainText()

    def setText(self, text):
        if len(text) > self.cut_point:
            if self.line_mode:
                self.toggle_area_mode()
            return self.text_area.setPlainText(text)
        if not self.line_mode:
            self.toggle_line_mode()
        return self.line_edit.setText(text)

    def setFocus(self, *args):
        if self.line_mode:
            self.line_edit.setFocus(*args)
        else:
            self.text_area.setFocus(*args)

    def toggle_line_mode(self):
        if not self.line_mode:
            pos = self.text_area.textCursor().position()
            self.line_edit.setCursorPosition(pos)
        self.line_mode = True
        self.line_edit.show()
        self.text_area.setEnabled(False)
        self.line_edit.setEnabled(True)
        self.text_area.hide()
        self.line_edit.setFocus()

    def reset(self):
        self.line_edit.setText('')
        self.text_area.setPlainText('')
        self.toggle_line_mode()
        if self.original_size:
            self.setFixedSize(self.original_size)
        self.parentWidget().update_size()

    def toggle_area_mode(self):
        pos = self.line_edit.cursorPosition()
        self.line_mode = False
        self.line_edit.hide()
        self.text_area.show()
        self.text_area.setEnabled(True)
        self.line_edit.setEnabled(False)
        self.text_area.setFocus()
        cursor = self.text_area.textCursor()
        cursor.setPosition(pos, QtGui.QTextCursor.MoveAnchor)
        self.text_area.setTextCursor(cursor)

    def line_edit_check_for_resize(self, text):
        if not self.changed and text != self.original_text:
            self.changed = True
        if self.original_size is None:
            self.original_size = self.size()
        if len(text) > self.cut_point:
            self.text_area.setPlainText(text)
            self.toggle_area_mode()
        else:
            tw = self.line_edit.fontMetrics().horizontalAdvance(text)
            if tw > self.line_edit.width():
                self.setFixedWidth(tw)
                self.parentWidget().update_size()
        if self.on_edit:
            self.on_edit(text)

    def text_area_check_for_resize(self):
        text = self.text_area.toPlainText()
        if not self.changed and text != self.original_text:
            self.changed = True
        if len(text) < self.cut_point:
            self.toggle_line_mode()
            return
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

    def dragEnterEvent(self, event):
        """ Announce support for regular ascii drops and drops of characters
        from symbolpanel.
        :param event: QDragEnterEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            return QtWidgets.QWidget.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """ Support regular ascii drops and drops of characters from
        symbolpanel.
        :param event: QDropEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            data = open_symbol_data(event.mimeData())
            if data and 'char' in data:
                if self.line_mode:
                    self.line_edit.insert(data['char'])
                else:
                    self.text_area.insert(data['char'])
                event.acceptProposedAction()
        else:
            return QtWidgets.QWidget.dropEvent(self, event)
