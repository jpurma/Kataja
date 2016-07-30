from PyQt5 import QtWidgets, QtGui

from kataja.singletons import ctrl, qt_prefs
from kataja.utils import open_symbol_data
from kataja.parser.INodes import ITextNode
import kataja.globals as g


def as_html(value):
    if isinstance(value, list):
        html_rows = []
        for row in value:
            if isinstance(row, ITextNode):
                html_rows.append(row.as_html())
            else:
                html_rows.append(row)
        return '\n'.join(html_rows)
    elif isinstance(value, ITextNode):
        return value.as_html()
    else:
        return value


def as_latex(value):
    if isinstance(value, list):
        latex_rows = []
        for row in value:
            if isinstance(row, ITextNode):
                latex_rows.append(row.as_latex())
            else:
                latex_rows.append(row)
        return '\n'.join(latex_rows)
    elif isinstance(value, ITextNode):
        return value.as_latex()
    else:
        return value


class ExpandingTextArea(QtWidgets.QWidget):

    def __init__(self, parent, tip='', font=None, prefill='', on_edit=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.raw_text = ''
        self.parsed_latex = ''
        self.parsed_html = ''
        self.parsing_mode = 1
        layout = QtWidgets.QVBoxLayout()
        self.top_row_layout = QtWidgets.QHBoxLayout()
        self.input_parsing_modes = QtWidgets.QButtonGroup()
        self.tex_radio = QtWidgets.QRadioButton("TeX", self)
        self.html_radio = QtWidgets.QRadioButton("HTML", self)
        self.input_parsing_modes.buttonClicked.connect(self.change_text_field_mode)
        self.input_parsing_modes.addButton(self.tex_radio, 1)
        self.input_parsing_modes.addButton(self.html_radio, 2)
        self.top_row_layout.addWidget(self.tex_radio)
        self.top_row_layout.addWidget(self.html_radio)
        layout.addLayout(self.top_row_layout)
        self.text_area = QtWidgets.QPlainTextEdit(parent)
        self.text_area.setAutoFillBackground(True)
        self.text_area.setSizeAdjustPolicy(self.text_area.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)
        self.text_preview = QtWidgets.QTextEdit(parent)
        self.text_preview.setAutoFillBackground(True)
        self.text_preview.setSizeAdjustPolicy(self.text_preview.AdjustToContents)
        self.text_preview.setReadOnly(True)

        self.on_edit = on_edit
        self.text_area.setEnabled(True)
        self.cut_point = 24
        self.input_parsing_modes.button(self.get_host().text_parse_mode).setChecked(True)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text_area)
        layout.addWidget(self.text_preview)
        self.setLayout(layout)
        self.text_area.setFont(qt_prefs.get_font(g.CONSOLE_FONT))
        self.text_area.setMinimumHeight(40)
        self.text_preview.setMinimumHeight(40)
        self.text_area.setMinimumWidth(200)
        self.text_preview.setMinimumWidth(200)
        if tip:
            if ctrl.main.use_tooltips:
                self.setToolTip(tip)
                self.setToolTipDuration(2000)
            self.setStatusTip(tip)
        if font:
            self.text_preview.setFont(font)
        if prefill:
            self.text_area.setPlaceholderText(prefill)
        self.font_height = self.text_preview.fontMetrics().height()
        self.text_area.textChanged.connect(self.text_area_check_for_resize)
        self.setAcceptDrops(True)
        self.original_size = None
        self.changed = False

    def get_host(self):
        parent = self.parentWidget()
        if parent:
            return getattr(parent, 'host', None)

    def text(self):
        return self.text_area.toPlainText()

    def setText(self, text):
        self.raw_text = text
        self.parsed_latex = as_latex(text)
        self.parsed_html = as_html(text)
        if self.parsing_mode == 1:
            self.text_area.setPlainText(self.parsed_latex)
        elif self.parsing_mode == 2:
            self.text_area.setPlainText(self.parsed_html)
        self.text_preview.setHtml(self.parsed_html)

    def setFocus(self, *args):
        self.text_area.setFocus(*args)

    def reset(self):
        self.text_area.setPlainText('')
        self.toggle_line_mode()
        if self.original_size:
            self.setFixedSize(self.original_size)
        self.parentWidget().update_size()

    def text_area_check_for_resize(self):
        text = self.text_area.toPlainText()
        if self.parsing_mode == 1:
            if not self.changed and text != self.parsed_latex:
                self.changed = True
        elif self.parsing_mode == 2:
            if not self.changed and text != self.parsed_html:
                self.changed = True
        max_height = 400
        min_width = 400
        if self.changed:
            inode_text = self.inode_text()
            self.text_preview.setHtml(as_html(inode_text))

        #rows = self.text_area.document().size().height()
        #tot = min(self.font_height * rows + 5, max_height)
        #if self.text_area.height() < tot:
        #    if self.text_area.width() < min_width:
        #        self.setFixedWidth(min_width)
        #    self.setFixedHeight(tot)
        #    self.parentWidget().update_size()
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
                self.text_area.insertPlainText(data['char'])
                event.acceptProposedAction()
        else:
            return QtWidgets.QWidget.dropEvent(self, event)

    def change_text_field_mode(self, button_clicked):
        """ Recompose displayed text as TeX, HTML or Plain
        :param button_clicked:
        :return:
        """
        value = self.inode_text()
        self.parsing_mode = self.input_parsing_modes.id(button_clicked)  # 1 = TeX,  2 = HTML,
        # 3 = Plain
        self.get_host().text_parse_mode = self.parsing_mode
        self.parsed_html = as_html(value)
        self.parsed_latex = as_latex(value)
        if self.parsing_mode == 1:
            self.text_area.setPlainText(self.parsed_latex)
        elif self.parsing_mode == 2:
            self.text_area.setPlainText(self.parsed_html)

    def inode_text(self):
        """
        :return:
        """

        if self.changed:
            if self.parsing_mode == 1:
                parser = ctrl.latex_field_parser
            elif self.parsing_mode == 2:
                parser = ctrl.html_field_parser
            else:
                raise ValueError
            inode_rows = []
            old_lines = self.text().splitlines()
            for row in old_lines:
                inode_rows.append(parser.process(row))
            return inode_rows
        else:
            return self.raw_text

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
