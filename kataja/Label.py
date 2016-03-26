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
from kataja.utils import combine_dicts, combine_lists
from kataja.parser.INodes import ITextNode


class FocusKeeper(QtCore.QObject):

    def eventFilter(self, obj, event):

        if event.type() == QtCore.QEvent.FocusOut:
            print('ate focusout', event, event.reason())
            return True
        elif event.type() == QtCore.QEvent.FocusIn:
            print('ate focusin', event, event.reason())
            return True
        elif event.type() == QtCore.QEvent.FocusAboutToChange:
            print('ate focus about to change')
            return True
        elif event.type() == QtCore.QEvent.GrabMouse:
            print('ate mouse grab', event)
            return True
        elif event.type() == QtCore.QEvent.UngrabMouse:
            print('ate mouse ungrab', event)
            return True
        else:
            #print(event.type(), event)
            return QtCore.QObject.eventFilter(self, obj, event)


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
        self.top_row_y = 0
        self.bottom_row_y = 0
        self.bottom_y = 0
        self.triangle_is_present = False
        self.triangle_height = 0
        self.triangle_y = 0
        self.width = 0
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

        #self.focuskeeper = FocusKeeper(self)
        #self.installEventFilter(self.focuskeeper)
        self.setDocument(self.doc)
        # not acceptin hover events is important, editing focus gets lost if other labels take
        # hover events. It is unclear why.
        self.setAcceptHoverEvents(False)
        self.doc.contentsChange.connect(self.doc_changed)
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

    def update_label(self, font):
        """ Asks for node/host to give text and update if changed
        :param font: provide font to use for label document
        :param inode: provide inode to parse to label document
        """
        self.has_been_initialized = True
        if font != self._font:
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

        self.prepareGeometryChange()
        self.doc.setTextWidth(-1)
        self.parse_to_document()
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

        def add_part(parts_list, html, count, new_part, field_name):
            parts_list.append((field_name, count, new_part))
            html.append(new_part)
            return count + len(new_part)

        def add_html(html, count, new_html):
            html.append(new_html)
            return count + len(new_html)

        styles = self.display_styles
        h = self._host
        parts_list = []
        html = []
        count = 0
        waiting = None
        for field_name in self.visible_in_label:
            s = styles.get(field_name, {})
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
                        count = add_part(parts_list, html, count, '<br/>', 'triangle')
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
                    waiting = field_value
                    continue
                elif align == 'continue' or align == 'append':
                    count = add_part(parts_list, html, count, field_value, field_name)
                else:
                    count = add_part(parts_list, html, count, field_value, field_name)
                    if waiting:
                        count = add_part(parts_list, html, count, waiting, field_name)
                        waiting = None
                    count = add_html(html, count, '<br/>')
        self.html = ''.join(html)
        self.actual_parts = parts_list
        print(self.actual_parts)
        self.doc.setHtml(self.html)

    def is_empty(self):
        """ Turning this node into label would result in an empty label.
        :return: bool
        """
        return not self.html

    def has_content(self):
        return bool(self.html)

    def get_top_row_y(self):
        return self.top_row_y

    def get_bottom_row_y(self):
        return self.bottom_row_y

    def set_quick_editing(self, value):
        print('setting quick editing ', value)
        if value:
            self._quick_editing = True
            self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
            #w = ctrl.main.app.focusWidget()
            #if w:
            #    w.clearFocus()
            ctrl.graph_view.setFocus()
            self.setFocus()
        else:
            self._quick_editing = False
            self.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
            self.clearFocus()

    def doc_changed(self, position, chars_removed, chars_added):
        if self._quick_editing and not self._recursion_block:
            self._recursion_block = True
            self.prepareGeometryChange()
            lines = self.doc.interpret_changes(self.html,
                                               position,
                                               chars_removed,
                                               chars_added)
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
        l = self.doc.lineCount()
        inner_size = self.doc.size()
        ih = inner_size.height()
        iw = inner_size.width()
        h2 = ih / 2.0
        self.top_y = -h2
        self.bottom_y = h2
        self.width = iw
        if l <= 1:
            self.top_row_y = 0
            self.bottom_row_y = 0
        for part in enumerate(self.actual_parts):
            pass
        else:
            avg_line_height = (ih - 3) / float(l)
            half_height = avg_line_height / 2
            if 'triangle' in self.doc.lines:
                top_row_found = False
                triangle_found = False
                for i, line in enumerate(self.doc.lines):
                    if (not top_row_found) and line == 'triangle':
                        if i < 2:
                            self.top_row_y = self.top_y + half_height
                        else:
                            self.top_row_y = self.top_y + (i * avg_line_height) + half_height
                        top_row_found = True
                    if (not triangle_found) and line == 'triangle':
                        self.triangle_y = self.top_y + (i * avg_line_height) + 2
                        triangle_found = True
                    elif triangle_found and line != 'triangle':
                        self.bottom_row_y = self.top_y + (i * avg_line_height) + half_height
                        break
                self.triangle_height = (avg_line_height * 2) - 4
                self.triangle_is_present = True
            else:
                top_row = self.doc.lines[0]
                self.top_row_y = self.top_y + half_height + 3
                bottom_row_found = False
                for i, line in enumerate(self.doc.lines):
                    if line != top_row:
                        self.bottom_row_y = self.top_y + (i * avg_line_height) + half_height
                        bottom_row_found = True
                        break
                if not bottom_row_found:
                    self.bottom_row_y = self.top_row_y
                self.triangle_is_present = False
        self.setPos(iw / -2.0, self.top_y)

    def kfocusInEvent(self, event):
        print('focus in')
        #self.grabKeyboard()
        return QtWidgets.QGraphicsTextItem.focusInEvent(self, event)

    def focusOutEvent(self, event):
        print('focus out ', event.reason())
        #self.ungrabKeyboard()
        return QtWidgets.QGraphicsTextItem.focusOutEvent(self, event)

    def paint(self, painter, option, widget):
        """ Painting is sensitive to mouse/selection issues, but usually with
        nodes it is the label of the node that needs complex painting
        :param painter:
        :param option:
        :param widget:
        """
        self.setDefaultTextColor(self._host.contextual_color)
        QtWidgets.QGraphicsTextItem.paint(self, painter, option, widget)
