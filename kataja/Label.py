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
from kataja.singletons import ctrl, prefs
from kataja.utils import combine_dicts, combine_lists, time_me, open_symbol_data
from kataja.parser.INodes import ITextNode
import difflib

differ = difflib.Differ()


class Label(QtWidgets.QGraphicsTextItem):
    """ Labels are names of nodes. Node itself handles all the logic of
    deciding what to show in label, label only calls nodes method to ask for
    text. """
    max_width = 400

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
        self.resizable = False
        self.text_align = CENTER_ALIGN
        self.char_width = 0
        self.line_length = 0
        self._font = None
        self.html = ''
        self.editable_html = ''
        self._quick_editing = False
        self._recursion_block = False
        self._last_blockpos = ()
        self.display_styles = {}
        self.visible_in_label = []
        self.visible_parts = []
        self.editable = {}
        self.editable_in_label = []
        self.editable_parts = []
        self.prepare_template()
        self.doc = LabelDocument()

        self.setDocument(self.doc)
        # not acceptin hover events is important, editing focus gets lost if other labels take
        # hover events. It is unclear why.
        self.setAcceptDrops(False)
        self.setAcceptHoverEvents(False)
        self.doc.contentsChanged.connect(self.doc_changed)
        self.setTextWidth(-1)
        self.set_font(self._host.font)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65554

    def set_font(self, font):
        self.setFont(font)
        self._font = font
        fm = QtGui.QFontMetrics(font)
        self.char_width = fm.maxWidth()

    def update_label(self):
        """ Asks for node/host to give text and update if changed
        :param font: provide font to use for label document
        """
        self.has_been_initialized = True
        align = QtCore.Qt.AlignHCenter
        if self.text_align == LEFT_ALIGN:
            align = QtCore.Qt.AlignLeft
        elif self.text_align == RIGHT_ALIGN:
            align = QtCore.Qt.AlignRight
        self.doc.setDefaultTextOption(QtGui.QTextOption(align))

        old_html = self.html
        self.compose_html_for_viewing()
        if old_html != self.html:
            self.prepareGeometryChange()
            self.doc.setTextWidth(-1)
            self.setHtml(self.html)
            self.text = self.toPlainText()
        proposed_width = self.doc.idealWidth()
        self.setTextWidth(min(proposed_width, Label.max_width))

        if self.line_length and self.line_length * self.char_width < proposed_width:
            self.setTextWidth(self.line_length * self.char_width)
        elif proposed_width < Label.max_width:
            self.setTextWidth(proposed_width)
        else:
            self.setTextWidth(Label.max_width)
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

    def compose_html_for_viewing(self):
        """ Use 'visible_in_label' and 'display_styles' and the item attributes to compose the
        document html. Also stores information about the composition to 'viewable_parts'
        Actual parts is list of tuples where:
        (field_name, position in html string, line in displayed html, html_snippet)
        :return:
        """

        styles = self.display_styles
        h = self._host
        row = 0
        visible_parts = []
        html = []
        waiting = None
        bones_mode = prefs.bones_mode
        delimiter = ''
        for field_name in self.visible_in_label:
            s = styles.get(field_name, {})
            syntactic = s.get('syntactic', False)
            if bones_mode and not syntactic:
                continue
            end_tag = ''
            if 'getter' in s:
                getter = getattr(h, s.get('getter'), None)
                if callable(getter):
                    field_value = getter()
                else:
                    field_value = getter
            else:
                field_value = getattr(h, field_name, '')
            if not h.check_conditions(s):
                continue
            if 'delimiter' in s:
                delimiter = s['delimiter']

            if 'special' in s:
                special = s['special']
                if special == 'triangle':
                    if h.triangle:
                        html.append('<br/><br/>')
                        visible_parts.append(('triangle', row, '<br/><br/>'))
                        row += 2
                    continue
            if field_value:
                if isinstance(field_value, ITextNode):
                    field_value = field_value.as_html()
                field_value = str(field_value).replace('\n', '<br/>')
                start_tag = s.get('start_tag', '')
                if start_tag:
                    end_tag = s.get('end_tag', '')
                    field_value = start_tag + field_value + end_tag
                align = s.get('align', '')
                if align == 'line-end':
                    if visible_parts and visible_parts[-1][0] != 'triangle':
                        if html[-1] == '<br/>':
                            html.pop()
                        html.append(field_value)
                        visible_parts.append((field_name, row, field_value))
                        html.append('<br/>')
                        row += 1
                    else:
                        waiting = (field_value, field_name)
                    continue
                elif align == 'continue' or align == 'append':
                    print('align continue: ', field_value)
                    html.append(field_value)
                    visible_parts.append((field_name, row, field_value))
                    if delimiter:
                        html.append(delimiter)
                else:
                    html.append(field_value)
                    visible_parts.append((field_name, row, field_value))
                    if waiting:
                        html.append(waiting[0])
                        visible_parts.append((waiting[0], row, waiting[1]))
                        waiting = None
                    html.append('<br/>')
                    row += 1
        if html and html[-1] == '<br/>' or (delimiter and html[-1] == delimiter):
            html.pop()
        self.html = ''.join(html)
        self.visible_parts = visible_parts

    def compose_html_for_editing(self):
        """ Use 'visible_in_label' and 'display_styles' and the item attributes to compose the
        document html. Also stores information about the composition to 'viewable_parts'
        Actual parts is list of tuples where:
        (field_name, position in html string, line in displayed html, html_snippet)
        :return:
        """
        styles = self.display_styles
        edit_styles = self.editable
        h = self._host
        editable_parts = []
        editable = []
        bones_mode = prefs.bones_mode
        for field_name in self.visible_in_label:
            s = styles.get(field_name, {})
            e = edit_styles.get(field_name, {})
            syntactic = s.get('syntactic', False)
            if bones_mode and not syntactic:
                continue

            if 'getter' in e:
                getter = getattr(h, e.get('getter'), None)
                if callable(getter):
                    field_value = getter()
                else:
                    field_value = getter
            else:
                field_value = getattr(h, field_name, '')
            if 'special' in s:
                if s['special'] == 'triangle':
                    continue
            if field_value:
                if isinstance(field_value, ITextNode):
                    field_value = field_value.as_html()
                editable_parts.append((field_name,
                                       field_value,
                                       len(field_value.splitlines(keepends=False))))
                editable.append(field_value)
                editable.append('\n')
        if editable and editable[-1] == '\n':
            editable.pop()
        self.editable_html = ''.join(editable)

        # if there are no previous value to compare with, use the field defined as *focus* in
        # class.editable -dict
        if not editable_parts:
            for key, value in self.editable.items():
                if value.get('focus', False):
                    editable_parts = [(key, '', 1)]
                    break

        # if there was no focus declared, use the first field from class.editable_in_label
        if not editable_parts:
            if self.editable_in_label:
                editable_parts = [(self.editable_in_label[0], '', 1)]

        self.editable_parts = editable_parts

    def should_draw_triangle(self):
        return self.triangle_is_present and not self._quick_editing

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

    def is_quick_editing(self):
        return self._quick_editing

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
            self.compose_html_for_editing()
            self.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))
            self.setPlainText(self.editable_html)
            #opt = QtGui.QTextOption()
            #opt.setFlags(QtGui.QTextOption.ShowLineAndParagraphSeparators |
            #             QtGui.QTextOption.AddSpaceForLineAndParagraphSeparators)
            #self.doc.setDefaultTextOption(opt)
            proposed_width = self.doc.idealWidth()
            self.setTextWidth(min(proposed_width, Label.max_width))
            self.resize_label()
            self.setAcceptDrops(True)
            ctrl.graph_view.setFocus()
            self.setFocus()
        elif self._quick_editing:
            fields = []
            if self.doc.isModified():
                fields = self.analyze_changes()
                self.doc.setModified(False)
            ctrl.text_editor_focus = None
            self._quick_editing = False
            self.html = ''
            self._host.update_label()
            self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.setAcceptDrops(False)
            self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
            self.clearFocus()
            if len(fields) == 0:
                ctrl.main.action_finished("Finished editing %s, no changes." % self._host,
                                          undoable=False)
            elif len(fields) == 1:
                ctrl.main.action_finished("Edited field %s in %s" % (fields[0], self._host))
            else:
                ctrl.main.action_finished("Edited fields %s in %s" % (str(fields), self._host))

    def analyze_changes(self):
        """ Use difflib to get a robust idea on what has changed
        :return:
        """
        if not self.editable_parts:
            return []

        def safe_field_name(c):
            if len(field_names) > c:
                return field_names[c]
            else:
                return field_names[-1]

        def do_replacements(fname):
            # print('replacements:', replacements)
            # print('replace_these:', replace_these)
            for fname in replace_these:
                if replacements:
                    new_d.append((fname, replacements.pop(0)))
                else:
                    new_d.append((fname, ''))
            for fvalue in replacements:
                new_d.append((fname, fvalue))
            replace_these.clear()
            replacements.clear()

        al = self.editable_html.splitlines(keepends=False)
        bl = self.doc.toPlainText().splitlines(keepends=False)
        replacements = []
        replace_these = []
        new_d = []
        field_names = []
        old_fields = {}

        # Prepare a list that has equal length to old html split into lines. Each item in the list
        # is name of the field at that point in the old html. This list is a schema for recognizing
        # where changed lines belong to.
        for field_name, old_part, linespan in self.editable_parts:
            field_names += [field_name] * linespan
            old_fields[field_name] = old_part
        # print('field_names: ', field_names)
        if not field_names:
            return []

        # Use diff to find out which lines have been (- ) deleted and which have been (+ )added. If
        # there are deleted lines followed by added lines, these lines should replace each other.
        # So every time a deleted line is found, the field name for that line is stored, and when
        # the continuous series of deleted and added lines is finished, replace deleted lines with
        # the corresponding added lines.
        # Lists of deleted and added lines can have different lengths. If there are more
        # additions, the additions continue to the last available field, or the first, if starting
        # with an added line.
        c = 0
        for comp in differ.compare(al, bl):
            # print('comp: "%s"' % comp)
            word = comp[2:]
            op = comp[0]
            if op == ' ':
                do_replacements(safe_field_name(c))
                new_d.append((safe_field_name(c), word))
                c += 1
            elif op == '+':
                replacements.append(word)
            elif op == '-':
                replace_these.append(safe_field_name(c))
                c += 1
        if field_names:
            do_replacements(field_names[-1])
        # print('new_d:', new_d)

        # Merge all lines that belong to same field into one string and save it to new_fields
        current_field = ''
        current_stack = []
        new_fields = {}

        for field_name, value in new_d:
            if field_name and current_field and current_field != field_name:
                new_fields[current_field] = '\n'.join(current_stack).rstrip()
                current_stack = []
            current_field = field_name
            if value:
                current_stack.append(value)
        if current_field:
            new_fields[current_field] = '\n'.join(current_stack).rstrip()

        # Write changed values to label's host object and return list of changed field names
        changed = []
        for field_name, new_value in new_fields.items():
            if new_value != old_fields.get(field_name, ''):
                changed.append(field_name)
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
        return changed

    def doc_changed(self):
        if not self._recursion_block: # self._quick_editing and
            self._recursion_block = True
            self.prepareGeometryChange()
            w = self.width
            proposed_width = self.doc.idealWidth()
            self.setTextWidth(min(proposed_width, Label.max_width))
            self.resize_label()
            self._host.update_bounding_rect()
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
        for field_name, row, html in self.visible_parts:
            if row > last_row:
                last_row = row
            if field_name == 'triangle':
                self.triangle_is_present = True
                triangle_row = row
            elif not second_row and row > second_row:
                second_row = row
        if last_row < 0:
            last_row = 0
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

    def paint(self, painter, option, widget):
        """ Painting is sensitive to mouse/selection issues, but usually with
        nodes it is the label of the node that needs complex painting
        :param painter:
        :param option:
        :param widget:
        """
        self.setDefaultTextColor(self._host.contextual_color)
        QtWidgets.QGraphicsTextItem.paint(self, painter, option, widget)
