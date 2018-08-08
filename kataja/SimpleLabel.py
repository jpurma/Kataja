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
from kataja.globals import LEFT_ALIGN, \
    CENTER_ALIGN, RIGHT_ALIGN
from kataja.singletons import ctrl
from kataja.utils import combine_dicts, time_me, open_symbol_data
from kataja.uniqueness_generator import next_available_type_id

style_sheet = """
b {font-family: StixGeneral Bold; font-weight: 900; font-style: bold}
sub sub {font-size: 8pt; vertical-align: sub}
sup sub {font-size: 8pt; vertical-align: sub}
sub sup {font-size: 8pt; vertical-align: sup}
sup sup {font-size: 8pt; vertical-align: sup}
"""


class MyGraphicsTextItem(QtWidgets.QGraphicsTextItem):
    def __init__(self, parent, host):
        QtWidgets.QGraphicsTextItem.__init__(self, parent)
        self._host = host

    def hoverMoveEvent(self, event):
        if not self._host._is_moving:
            ctrl.ui.move_help(event)


class QuickEditTextItem(QtWidgets.QGraphicsTextItem):
    def mousePressEvent(self, event):
        # something in mousePressEvent causes it to ignore further mouse events.
        p = self.parent()
        if p._quick_editing:
            QtWidgets.QGraphicsTextItem.mousePressEvent(self, event)
        else:
            # otherwise let the node handle mousePress logic.
            p._host.mousePressEvent(event)

    def mouseMoveEvent(self, event):
        p = self.parent()
        if p._quick_editing:
            QtWidgets.QGraphicsTextItem.mouseMoveEvent(self, event)
        else:
            p._host.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        p = self.parent()
        if p._quick_editing:
            p.cursor_position_changed(self.textCursor())
            QtWidgets.QGraphicsTextItem.mouseReleaseEvent(event)
        else:
            p._host.mouseReleaseEvent(event)

    def keyReleaseEvent(self, keyevent):
        """ keyReleaseEvent is received after the keypress is registered by editor, so if we
        check cursor position here we receive the situation after normal cursor movement. So
        moving 'up' to first line would also register here as being in first line and moving up.
        Which is one up too many. So instead we store the last cursor pos and use that to decide
        if we are eg. in first line and moving up.
        :param keyevent:
        :return:
        """
        p = self.parent()
        c = self.textCursor()
        print('label keyreleaseevent')
        p.cursor_position_changed(c)
        next_sel = None
        if p._fresh_focus:
            p._fresh_focus = False
        elif p._last_blockpos:
            print('previous block pos: ', p._last_blockpos)
            first, last, first_line, last_line = p._last_blockpos
            if first and keyevent.matches(QtGui.QKeySequence.MoveToPreviousChar):
                next_sel = ctrl.graph_scene.next_selectable_from_node(p._host, 'left')
            elif last and keyevent.matches(QtGui.QKeySequence.MoveToNextChar):
                next_sel = ctrl.graph_scene.next_selectable_from_node(p._host, 'right')
            elif first_line and keyevent.matches(QtGui.QKeySequence.MoveToPreviousLine):
                next_sel = ctrl.graph_scene.next_selectable_from_node(p._host, 'up')
            elif last_line and keyevent.matches(QtGui.QKeySequence.MoveToNextLine):
                next_sel = ctrl.graph_scene.next_selectable_from_node(p._host, 'down')
            if next_sel and next_sel != p._host:
                self.clearFocus()
                ctrl.select(next_sel)
                next_sel.setFocus()
        p._last_blockpos = (c.atStart(), c.atEnd(), c.blockNumber() == 0,
                            c.blockNumber() == p.editable_doc.blockCount() - 1)


class SimpleLabel(QtWidgets.QGraphicsItem):
    """ Labels are names of nodes. Node itself provides a template for what to show in label,
    label composes its document (html layout) for its contents based on that. """
    max_width = 400
    __qt_type_id__ = next_available_type_id()

    def __init__(self, parent=None):
        """ Give node as parent. Label asks it to produce text to show here """
        QtWidgets.QGraphicsItem.__init__(self, parent)
        self.editable_part = MyGraphicsTextItem(self, parent)
        self._host = parent
        self.has_been_initialized = False
        self.top_y = 0
        self.upper_part_y = 0
        self.bottom_y = 0
        self.width = 0
        self.height = 0
        self.template_width = 0
        self.x_offset = 0
        self.y_offset = 0
        self.text_align = CENTER_ALIGN
        self._font = None
        self._font_metrics = None
        self.editable_html = ''
        self.edited_field = ''
        self._quick_editing = False
        self._recursion_block = False
        self._last_blockpos = ()
        self.editable = {}
        self.prepare_template()  # !<----
        self.editable_doc = LabelDocument()
        self._fresh_focus = False
        self.editable_part.setDocument(self.editable_doc)
        self.setZValue(20)  # ZValue amongst the childItems of Node
        # not acceptin hover events is important, editing focus gets lost if other labels take
        # hover events. It is unclear why.
        self.setAcceptDrops(False)
        self.setAcceptHoverEvents(False)
        self.editable_doc.contentsChanged.connect(self.editable_doc_changed)
        self.editable_part.setTextWidth(-1)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def keep_visible(self):
        return self.has_content() or self.is_quick_editing()

    def hoverMoveEvent(self, event):
        # print('L sending hoverMoveEvent')
        ctrl.ui.move_help(event)
        QtWidgets.QGraphicsItem.hoverMoveEvent(self, event)

    def __str__(self):
        return 'Label:' + self.editable_html

    def set_font(self, font):
        self.editable_part.setFont(font)
        self._font = font
        self._font_metrics = QtGui.QFontMetrics(font)

    def update_font(self):
        self.set_font(self._host.get_font())

    def update_label(self, force_update=False):
        """ Asks for node/host to give text and update if changed """
        force_update = True
        self.has_been_initialized = True
        if self.text_align == LEFT_ALIGN:
            self.editable_doc.set_align(QtCore.Qt.AlignLeft)
        elif self.text_align == RIGHT_ALIGN:
            self.editable_doc.set_align(QtCore.Qt.AlignRight)
        else:
            self.editable_doc.set_align(QtCore.Qt.AlignHCenter)
        html = self._host.label_as_html()
        if force_update or html != self.editable_html:
            if self.editable_html != html:
                self.editable_doc.blockSignals(True)
                self.editable_doc.setTextWidth(-1)
                self.editable_html = html
                self.editable_part.setHtml(html)
                self.editable_doc.blockSignals(False)

            ctrl.qdocument_parser.process(self.editable_doc)
        self.resize_label()

    def string_width(self, string):
        return self._font_metrics.width(string)

    def prepare_template(self):
        my_class = self._host.__class__
        if self._host.syntactic_object:
            synclass = self._host.syntactic_object.__class__
            syn_editable = getattr(synclass, 'editable', {})
            self.editable = combine_dicts(syn_editable, my_class.editable)
        else:
            self.editable = my_class.editable

    def is_empty(self) -> bool:
        """ Turning this node into label would result in an empty label.
        :return: bool
        """
        return not self.editable_html

    def cursor(self):
        return self.editable_part.textCursor()

    def char_format(self) -> QtGui.QTextCharFormat:
        return self.editable_part.textCursor().charFormat()

    def has_content(self) -> bool:
        return bool(self.editable_html)

    def get_top_y(self) -> int:
        return self.y_offset

    def release_editor_focus(self):
        self.set_quick_editing(False)

    def is_quick_editing(self) -> bool:
        return self._quick_editing

    def _get_editing_width(self) -> int:
        return -1

    def set_quick_editing(self, value):
        """  Toggle quick editing on and off for this label. Quick editing is toggled on when
        the label is clicked or navigated into with the keyboard. The label and its editor takes
        focus and many things behave differently while editing, so please keep make sure that
        quick editing is switched off properly, using this method.
        :param value:
        :return:
        """
        if value:
            if self._quick_editing:
                return
            self.setAcceptHoverEvents(True)
            self._quick_editing = True
            self._host.update_label_visibility()
            if ctrl.text_editor_focus:
                ctrl.release_editor_focus()
            ctrl.text_editor_focus = self
            self.editable_part.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
            self.prepareGeometryChange()
            self.editable_doc.setTextWidth(self._get_editing_width())
            self.edited_field, self.editable_html = self._host.label_as_editable_html()
            self.setCursor(QtGui.QCursor(QtCore.Qt.IBeamCursor))

            ctrl.ui.add_quick_edit_buttons_for(self._host, self.editable_doc)
            self.editable_part.setHtml(self.editable_html)
            self.editable_doc.cursorPositionChanged.connect(self.cursor_position_changed)

            self.resize_label()
            self.editable_part.setAcceptDrops(True)
            ctrl.graph_view.setFocus()
            self.editable_part.setFocus()
            self._fresh_focus = True

        elif self._quick_editing:
            if self.editable_doc.isModified():
                self.parse_document_to_field()
                self.editable_doc.setModified(False)
            self.setAcceptHoverEvents(False)
            ctrl.text_editor_focus = None
            self._quick_editing = False
            ctrl.ui.remove_quick_edit_buttons()
            self._host.update_label()
            self.editable_part.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.editable_part.setAcceptDrops(False)
            self.editable_part.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
            self.editable_part.clearFocus()
            self._fresh_focus = False

    def cursor_position_changed(self, cursor):
        if self._quick_editing:
            ctrl.ui.quick_edit_buttons.update_formats(cursor.charFormat())

    def parse_document_to_field(self):
        """ Parse edited QDocument into rows of INodes and into receptable
        field in host object

        :return:
        """
        parsed_parts = ctrl.qdocument_parser.process(self.editable_doc)
        # Parser should return INode or str, if there is nothing that needs INode in it.
        print('parsed_parts:', repr(parsed_parts))
        self._host.parse_edited_label(self.edited_field, parsed_parts)

    def editable_doc_changed(self):
        if self._recursion_block or not (ctrl.forest.in_display and ctrl.forest.is_parsed):
            return
        w = self.width
        self._recursion_block = True
        self.resize_label()
        self._host.update_bounding_rect()
        if self.width != w and self.scene() == ctrl.graph_scene:
            ctrl.forest.draw()
        self._recursion_block = False

    def get_max_size_from_host(self):
        if self._host.resizable and self._host.user_size is not None:
            return self._host.user_size
        else:
            return 0, 0

    def resize_label(self):
        self.prepareGeometryChange()

        user_width, user_height = self.get_max_size_from_host()
        # ------------------- Width -------------------
        self.editable_part.setTextWidth(-1)
        ideal_width = self.editable_doc.idealWidth()
        if user_width and user_width < ideal_width:
            width = user_width
        elif self.template_width:
            width = self.template_width
        else:
            width = ideal_width
        if width < 20:
            width = 20
        elif width > SimpleLabel.max_width:
            width = SimpleLabel.max_width
        self.editable_part.setTextWidth(width)

        # ------------------- Height -------------------
        total_height = self.editable_doc.size().height()
        half_height = total_height / 2.0
        self.top_y = -half_height
        self.bottom_y = half_height
        self.width = width
        self.height = total_height
        self.upper_part_y = 0
        self.x_offset = width / -2.0
        self.y_offset = -half_height
        self.setPos(self.x_offset, self.y_offset)
        self.editable_part.setPos(0, self.upper_part_y)

        # Update ui items around the label (or node hosting the label)
        ctrl.ui.update_position_for(self._host)

    def dropEvent(self, event):
        mim = event.mimeData()
        if mim.hasFormat("application/x-qabstractitemmodeldatalist"):
            print('label dropEvent application/x-qabstractitemmodeldatalist')
            event.accept()
            data = open_symbol_data(event.mimeData())
            if data and 'char' in data:
                self.editable_part.textCursor().insertText(data['char'])
                event.acceptProposedAction()
        elif mim.hasFormat("text/plain"):
            print('label dropEvent text/plain')
            event.accept()
            event.acceptProposedAction()
            self.editable_part.dropEvent(event)
        else:
            print('label dropEvent something')
            self.editable_part.dropEvent(event)

    def boundingRect(self):
        return QtCore.QRectF(self.x_offset, self.y_offset, self.width, self.height)

    def dragEnterEvent(self, event):
        """ Support dragging of items from their panel containers, e.g. symbols from symbol panel
        or new nodes from nodes panel.
        :param event:
        """
        data = event.mimeData()
        print('label dragEnterEvent ', data)
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
        if self._host.invert_colors:
            c = ctrl.cm.paper()
        else:
            c = self._host.contextual_color()
        self.editable_part.setDefaultTextColor(c)
