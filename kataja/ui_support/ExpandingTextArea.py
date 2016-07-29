from PyQt5 import QtWidgets, QtGui

from kataja.singletons import ctrl
from kataja.utils import open_symbol_data
from kataja.parser.INodes import ITextNode


class ExpandingTextArea(QtWidgets.QWidget):

    def __init__(self, parent, tip='', font=None, prefill='', on_edit=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.raw_text = ''
        self.parsed_text = ''
        layout = QtWidgets.QVBoxLayout()
        self.top_row_layout = QtWidgets.QHBoxLayout()
        self.input_parsing_modes = QtWidgets.QButtonGroup()
        self.tex_radio = QtWidgets.QRadioButton("TeX", self)
        self.html_radio = QtWidgets.QRadioButton("HTML", self)
        self.plain_radio = QtWidgets.QRadioButton("plain", self)
        self.plain_radio.setChecked(True)
        self.input_parsing_modes.buttonClicked.connect(self.change_text_field_mode)
        self.input_parsing_modes.addButton(self.tex_radio, 1)
        self.input_parsing_modes.addButton(self.html_radio, 2)
        self.input_parsing_modes.addButton(self.plain_radio, 3)
        self.top_row_layout.addWidget(self.tex_radio)
        self.top_row_layout.addWidget(self.html_radio)
        self.top_row_layout.addWidget(self.plain_radio)
        layout.addLayout(self.top_row_layout)
        self.text_area = QtWidgets.QPlainTextEdit(parent)
        self.text_area.setAutoFillBackground(True)
        self.text_area.setSizeAdjustPolicy(self.text_area.AdjustToContents)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)
        self.on_edit = on_edit
        self.text_area.setEnabled(True)
        self.cut_point = 24
        self.font_height = self.text_area.fontMetrics().height()
        self.input_parsing_modes.button(self.get_host().text_parse_mode).setChecked(True)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text_area)
        self.setLayout(layout)
        self.text_area.setMinimumHeight(40)
        if tip:
            if ctrl.main.use_tooltips:
                self.setToolTip(tip)
                self.setToolTipDuration(2000)
            self.setStatusTip(tip)
        if font:
            self.text_area.setFont(font)
        if prefill:
            self.text_area.setPlaceholderText(prefill)
        self.text_area.textChanged.connect(self.text_area_check_for_resize)
        self.setAcceptDrops(True)
        self.original_size = None
        self.changed = False

    def get_host(self):
        parent = self.parentWidget()
        if parent:
            return getattr(parent, 'host', None)

    def set_original(self, text):
        self.original_text = text

    def text(self):
        return self.text_area.toPlainText()

    def setText(self, text):
        self.raw_text = text
        parsing_mode = self.input_parsing_modes.checkedId()  # 1 = TeX,  2 = HTML, 3 = Plain
        if isinstance(text, list):
            rows = []
            if parsing_mode == 1:
                for row in text:
                    if isinstance(row, ITextNode):
                        rows.append(row.as_latex())
                    else:
                        rows.append(row)
            elif parsing_mode == 2:
                for row in text:
                    if isinstance(row, ITextNode):
                        rows.append(row.as_html())
                    else:
                        rows.append(row)
            elif parsing_mode == 2:
                for row in text:
                    if isinstance(row, ITextNode):
                        rows.append(str(row))
                    else:
                        rows.append(row)
            self.parsed_text = '\n'.join(rows)
        elif isinstance(text, ITextNode):
            if parsing_mode == 1:
                self.parsed_text = text.as_latex()
            elif parsing_mode == 2:
                self.parsed_text = text.as_html()
            elif parsing_mode == 3:
                self.parsed_text = text.as_plain()
            else:
                raise ValueError
        else:
            self.parsed_text = text
        return self.text_area.setPlainText(self.parsed_text)

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
        if not self.changed and text != self.parsed_text:
            self.changed = True
        max_height = 400
        min_width = 400

        rows = self.text_area.document().size().height()
        tot = min(self.font_height * rows + 5, max_height)
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
                self.text_area.insert(data['char'])
                event.acceptProposedAction()
        else:
            return QtWidgets.QWidget.dropEvent(self, event)

    def change_text_field_mode(self, button_clicked):
        """ Recompose displayed text as TeX, HTML or Plain
        :param button_clicked:
        :return:
        """
        old_parsing_mode = self.get_host().text_parse_mode
        new_parsing_mode = self.input_parsing_modes.id(button_clicked)  # 1 = TeX,  2 = HTML,
        # 3 = Plain
        if self.changed:
            if old_parsing_mode == 1:
                parser = ctrl.latex_field_parser
            elif old_parsing_mode == 2:
                parser = ctrl.html_field_parser
            elif old_parsing_mode == 3:
                parser = ctrl.plain_field_parser
            else:
                raise ValueError
            inode_rows = []
            old_lines = self.text().splitlines()
            for row in old_lines:
                inode_rows.append(parser.process(row))
            self.raw_text = inode_rows
        value = self.raw_text
        rows = []
        if new_parsing_mode == 1:
            for row in value:
                if isinstance(row, ITextNode):
                    rows.append(row.as_latex())
                else:
                    rows.append(row)
        elif new_parsing_mode == 2:
            for row in value:
                if isinstance(row, ITextNode):
                    rows.append(row.as_html())
                else:
                    rows.append(row)
        elif new_parsing_mode == 3:
            for row in value:
                if isinstance(row, ITextNode):
                    rows.append(row.as_plain())
                else:
                    rows.append(row)
        self.parsed_text = '\n'.join(rows)
        self.text_area.setPlainText(self.parsed_text)

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
