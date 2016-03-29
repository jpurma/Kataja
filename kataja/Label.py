# coding=utf-8
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.LabelDocument import LabelDocument
from kataja.globals import LEFT_ALIGN, CENTER_ALIGN, RIGHT_ALIGN
from kataja.singletons import ctrl
from kataja.utils import combine_dicts, combine_lists, time_me, open_symbol_data
from kataja.parser.INodes import ITextNode
import difflib

differ = difflib.Differ()


class Label(QtWidgets.QGraphicsTextItem):
    """ Labels are names of nodes. Node itself handles all the logic of
    deciding what to show in label, label only calls nodes method to ask for
    text. """

    def __init__(self, parent=None):
        """ Give node as parent. Label asks it to produce text to show here """
        QtWidgets.QGraphicsTextItem.__init__(self, parent)
        self._host = parent
        self.has_been_initialized = False
        self.top_y = 0
        self.top_part_y = 0
        self.lowert_part_y = 0
        self.bottom_y = 0
        self.triangle_is_present = False
        self.triangle_height = 0
        self.triangle_y = 0
        self.width = 0
        self.html = ''
        self._quick_editing = False
        self._recursion_block = False
        self._last_blockpos = ()
        self.display_styles = {}
        self.visible_in_label = []
        self.editable = {}
        self.editable_in_label = []
        self.actual_parts = []
        self.prepare_template()
        self.doc = LabelDocument()

        self.setDocument(self.doc)
        # not acceptin hover events is important, editing focus gets lost if other labels take
        # hover events. It is unclear why.
        self.setAcceptDrops(False)
        self.setAcceptHoverEvents(False)
        self.doc.contentsChanged.connect(self.doc_changed)
        self.setTextWidth(-1)
        self.resizable = False
        self.text_align = CENTER_ALIGN
        self.char_width = 0
        self.line_length = 0
        self._font = None

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65554

    def update_label(self, font=None):
        """ Asks for node/host to give text and update if changed
        :param font: provide font to use for label document
        :param inode: provide inode to parse to label document
        """
        self.has_been_initialized = True
        if font and font != self._font:
            self.setFont(font)
            self._font = font
            fm = QtGui.QFontMetrics(font)
            self.char_width = fm.maxWidth()
        align = QtCore.Qt.AlignHCenter
        if self.text_align == LEFT_ALIGN:
            align = QtCore.Qt.AlignLeft
        elif self.text_align == RIGHT_ALIGN:
            align = QtCore.Qt.AlignRight
        self.doc.setDefaultTextOption(QtGui.QTextOption(align))

        old_html = self.html
        self.parse_to_document()
        if old_html != self.html:
            self.prepareGeometryChange()
            self.doc.setTextWidth(-1)
            self.setHtml(self.html)
            self.text = self.toPlainText()
        ideal_width = self.doc.idealWidth()

        if self.line_length and self.line_length * self.char_width < ideal_width:
            self.setTextWidth(self.line_length * self.char_width)
        else:
            self.setTextWidth(ideal_width)
        self.resize_label()

    def prepare_template(self):
        my_class = self._host.__class__
        if self._host.syntactic_object:
            synclass = self._host.syntactic_object.__class__
            syn_display_styles = getattr(synclass, 'display_styles', {})
            syn_visible_in_label = getattr(synclass, 'visible_in_label', [])
            syn_editable = getattr(synclass, 'editable', {})
            syn_editable_in_label = getattr(synclass, 'editable_in_label', [])
            self.display_styles = combine_dicts(syn_display_styles, my_class.display_styles)
            self.visible_in_label = combine_lists(my_class.visible_in_label, syn_visible_in_label)
            self.editable = combine_dicts(syn_editable, my_class.editable)
            self.editable_in_label = combine_lists(my_class.editable_in_label,
                                                   syn_editable_in_label)
        else:
            self.display_styles = my_class.display_styles
            self.visible_in_label = my_class.visible_in_label
            self.editable = my_class.editable
            self.editable_in_label = my_class.editable_in_label

        for style in self.display_styles.values():
            if 'resizable' in style:
                self.resizable = True
            if 'line_length' in style:
                ll = style['line_length']
                if ll > self.line_length:
                    self.line_length = ll
            if 'text_align' in style:
                self.text_align = style['text_align']

    def parse_to_document(self):
        """ Use 'visible_in_label' and 'display_styles' and the item attributes to compose the
        document html. Also stores information about the composition to 'actual_parts'.
        Actual parts is list of tuples where:
        (field_name, position in html string, line in displayed html, html_snippet)
        :return:
        """

        def add_part(parts_list, html, count, row, new_part, field_name):
            parts_list.append((field_name, count, row, new_part))
            html.append(new_part)
            return count + len(new_part)

        def add_html(html, count, new_html):
            html.append(new_html)
            return count + len(new_html)

        styles = self.display_styles
        h = self._host
        parts_list = []
        html = []
        position = 0
        row = 0
        waiting = None
        for field_name in self.visible_in_label:
            s = styles.get(field_name, {})
            end_tag = ''
            if 'getter' in s:
                getter = getattr(h, s.get('getter'), None)
                if callable(getter):
                    field_value = getter()
                else:
                    field_value = getter
            else:
                field_value = getattr(h, field_name, '')
            if 'condition' in s:
                condition = getattr(h, s.get('condition'), None)
                if callable(condition):
                    if not condition():
                        continue
                elif not condition:
                    continue
            if 'special' in s:
                special = s['special']
                if special == 'triangle':
                    if h.triangle:
                        position = add_part(parts_list, html, position, row, '<br/><br/>',
                                            'triangle')
                        row += 2
                    continue
            if field_value:
                if isinstance(field_value, ITextNode):
                    field_value = field_value.as_html()
                start_tag = s.get('start_tag', '')
                if start_tag:
                    end_tag = s.get('end_tag', '')
                    field_value = start_tag + field_value + end_tag
                align = s.get('align', '')
                if align == 'line-end':
                    waiting = (field_value, field_name)
                    continue
                elif align == 'continue' or align == 'append':
                    position = add_part(parts_list, html, position, row, field_value, field_name)
                else:
                    position = add_part(parts_list, html, position, row, field_value, field_name)
                    if waiting:
                        position = add_part(parts_list, html, position, row, waiting[0], waiting[1])
                        waiting = None
                    position = add_html(html, position, '<br/>')
                    row += 1
                if '<br/>' in end_tag:
                    row += 1
        if html and html[-1] == '<br/>':
            html.pop()
        self.html = ''.join(html)
        self.actual_parts = parts_list

    def is_empty(self):
        """ Turning this node into label would result in an empty label.
        :return: bool
        """
        return not self.html

    def has_content(self):
        return bool(self.html)

    def get_top_part_y(self):
        return self.top_part_y

    def get_lower_part_y(self):
        return self.lowert_part_y

    def release_editor_focus(self):
        self.set_quick_editing(False)

    def set_quick_editing(self, value):
        """  Toggle quick editing on and off for this label. Quick editing is toggled on when
        the label is clicked or navigated into with the keyboard. The label and its editor takes
        focus and many things behave differently while editing, so please keep make sure that
        quick editing is switched off properly, using this method.
        :param value:
        :return:
        """
        if value:
            self._quick_editing = True
            if ctrl.text_editor_focus:
                ctrl.text_editor_focus.release_editor_focus()
            ctrl.text_editor_focus = self
            self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
            self.prepareGeometryChange()
            self.doc.setTextWidth(-1)
            self.setPlainText(self.html.replace('<br/>', '\n'))
            self.setTextWidth(self.doc.idealWidth())
            self.resize_label()
            self.setAcceptDrops(True)
            ctrl.graph_view.setFocus()
            self.setFocus()
        elif self._quick_editing:
            if self.doc.isModified():
                self.analyze_changes()
                self.doc.setModified(False)
                self.update_label()
            else:
                self.setHtml(self.html)
            self._quick_editing = False
            self.setAcceptDrops(False)
            self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
            ctrl.text_editor_focus = None
            self.clearFocus()

    def analyze_changes(self):

        def do_replacements(replace_with, replace_these, c):
            if replace_with or replace_these:
                for item in replace_these:
                    if replace_with:
                        new_d.append(replace_with.pop(0))
                    else:
                        new_d.append('')
                    c += 1
                if replace_with:
                    new_d[c - 1] = '\n'.join([new_d[c - 1]] + replace_with)
                replace_with.clear()
                replace_these.clear()
            return c

        al = self.text.splitlines(keepends=False)
        bl = self.doc.toPlainText().splitlines(keepends=False)
        replace_with = []
        replace_these = []
        new_d = []
        i = 0

        for comp in differ.compare(al, bl):
            word = comp[2:]
            op = comp[0]
            if op == ' ':
                i = do_replacements(replace_with, replace_these, i)
                new_d.append(word)
                i += 1
            elif op == '+':
                replace_with.append(word)
            elif op == '-':
                replace_these.append(word)
        do_replacements(replace_with, replace_these, i)
        for i, item in enumerate(self.actual_parts):
            field_name, count, row, old_part = item
            new_value = new_d[i]
            if new_value != old_part:
                my_editable = self.editable.get(field_name, {})
                setter = my_editable.get('setter', None)
                if setter:
                    setter_method = getattr(self._host, setter, None)
                    if setter_method and callable(setter_method):
                        setter_method(new_value)
                    else:
                        print('missing setter!')
                else:
                    setattr(self._host, field_name, new_value)

    def doc_changed(self):
        if self._quick_editing and not self._recursion_block:
            self._recursion_block = True
            self.prepareGeometryChange()
            w = self.width
            self.setTextWidth(self.doc.idealWidth())
            self.resize_label()
            self._host.update_bounding_rect()
            if ctrl.ui.selection_amoeba:
                ctrl.ui.selection_amoeba.update_shape()
            if self.width != w and self.scene() == ctrl.graph_scene:
                ctrl.forest.draw()
            self._recursion_block = False

    def keyReleaseEvent(self, keyevent):
        """ keyReleaseEvent is received after the keypress is registered by editor, so if we
        check cursor position here we receive the situation after normal cursor movement. So
        moving 'up' to first line would also register here as being in first line and moving up.
        Which is one up too many. So instead we store the last cursor pos and use that to decide
        if we are eg. in first line and moving up.
        :param keyevent:
        :return:
        """
        c = self.textCursor()
        next_sel = None
        if self._last_blockpos:
            first, last, first_line, last_line = self._last_blockpos
            if first and keyevent.matches(QtGui.QKeySequence.MoveToPreviousChar):
                next_sel = ctrl.graph_scene.find_next_selection(self._host, 'left')
            elif last and keyevent.matches(QtGui.QKeySequence.MoveToNextChar):
                next_sel = ctrl.graph_scene.find_next_selection(self._host, 'right')
            elif first_line and keyevent.matches(QtGui.QKeySequence.MoveToPreviousLine):
                next_sel = ctrl.graph_scene.find_next_selection(self._host, 'up')
            elif last_line and keyevent.matches(QtGui.QKeySequence.MoveToNextLine):
                next_sel = ctrl.graph_scene.find_next_selection(self._host, 'down')
            if next_sel and next_sel != self._host:
                self.clearFocus()
                ctrl.select(next_sel)
                next_sel.setFocus()
        self._last_blockpos = (c.atStart(), c.atEnd(), c.blockNumber() == 0,
                               c.blockNumber() == self.doc.blockCount() - 1)

    def resize_label(self):
        #l = self.doc.lineCount()
        inner_size = self.doc.size()
        ih = inner_size.height()
        iw = inner_size.width()
        h2 = ih / 2.0
        self.top_y = -h2
        self.bottom_y = h2
        self.width = iw
        self.triangle_is_present = False
        second_row = 0
        triangle_row = 0
        last_row = 0
        for field_name, count, row, html in self.actual_parts:
            if row > last_row:
                last_row = row
            if field_name == 'triangle':
                self.triangle_is_present = True
                triangle_row = row
            elif not second_row and row > second_row:
                second_row = row

        row_count = last_row + 1
        if row_count == 1:
            self.top_part_y = 0
            self.lowert_part_y = 0
        else:
            avg_line_height = (ih - 3) / float(row_count)
            half_height = avg_line_height / 2
            if self.triangle_is_present:
                triangle_space = 0
                if triangle_row > 1:
                    triangle_space = triangle_row * avg_line_height
                self.top_part_y = self.top_y + triangle_space + half_height
                self.triangle_y = self.top_y + (triangle_row * avg_line_height) + 2
                self.lowert_part_y = self.top_y + (second_row * avg_line_height) + half_height
                self.triangle_height = (avg_line_height * 2) - 4
            else:
                self.top_part_y = self.top_y + half_height + 3
                self.lowert_part_y = self.top_y + (second_row * avg_line_height) + half_height
        self.setPos(iw / -2.0, self.top_y)

    def dropEvent(self, event):
        mim = event.mimeData()
        if mim.hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
            data = open_symbol_data(event.mimeData())
            if data and 'char' in data:
                self.textCursor().insertText(data['char'])
                event.acceptProposedAction()
        elif mim.hasFormat("text/plain"):
            event.accept()
            event.acceptProposedAction()
            QtWidgets.QGraphicsTextItem.dropEvent(self, event)
        else:
            QtWidgets.QGraphicsTextItem.dropEvent(self, event)

    def dragEnterEvent(self, event):
        """ Support dragging of items from their panel containers, e.g. symbols from symbol panel
        or new nodes from nodes panel.
        :param event:
        """
        data = event.mimeData()
        if data.hasFormat("application/x-qabstractitemmodeldatalist") or data.hasFormat(
                "text/plain"):
            event.acceptProposedAction()
            event.accept()
        else:
            QtWidgets.QGraphicsTextItem.dragEnterEvent(self, event)

    def dragfMoveEvent(self, event):
        """ Support dragging of items from their panel containers, e.g. symbols from symbol panel
        or new nodes from nodes panel.
        :param event:
        """
        data = event.mimeData()
        if data.hasFormat("application/x-qabstractitemmodeldatalist") or data.hasFormat(
                "text/plain"):
            event.accept()
            event.acceptProposedAction()
        else:
            QtWidgets.QGraphicsTextItem.dragMoveEvent(self, event)

    def paint(self, painter, option, widget):
        """ Painting is sensitive to mouse/selection issues, but usually with
        nodes it is the label of the node that needs complex painting
        :param painter:
        :param option:
        :param widget:
        """
        self.setDefaultTextColor(self._host.contextual_color)
        QtWidgets.QGraphicsTextItem.paint(self, painter, option, widget)
