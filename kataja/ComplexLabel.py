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

from kataja.Shapes import SHAPE_PRESETS
from kataja.LabelDocument import LabelDocument
from kataja.SimpleLabel import SimpleLabel
from kataja.globals import NORMAL, BRACKETED, SCOPEBOX, CARD, LEFT_ALIGN, RIGHT_ALIGN
from kataja.singletons import ctrl
from kataja.uniqueness_generator import next_available_type_id
import kataja.globals as g


inner_cards = False


class ComplexLabel(SimpleLabel):
    """ ComplexLabels are labels that can have two textareas and a triangle between them """
    max_width = 400
    __qt_type_id__ = next_available_type_id()
    card_size = (60, 90)

    def __init__(self, parent=None):
        """ Give node as parent. Label asks it to produce text to show here """
        self.lower_part = None
        SimpleLabel.__init__(self, parent)
        self.lower_part_y = 0
        self.draw_triangle = False
        self.triangle_height = 20
        self.triangle_width = 20
        self.triangle_y = 0
        self.node_shape = NORMAL
        self.lower_html = ''
        self._previous_values = None
        self.lower_doc = None

    def __str__(self):
        return 'Label:' + self.editable_html + self.lower_html

    def keep_visible(self):
        return self.is_card() or self.has_content() or self.is_quick_editing()

    def init_lower_part(self):
        self.lower_part = QtWidgets.QGraphicsTextItem(self)
        self.lower_doc = LabelDocument()
        self.lower_part.setDocument(self.lower_doc)
        self.lower_part.setTextWidth(-1)
        if self._font:
            self.lower_part.setFont(self._font)

    def remove_lower_part(self):
        self.lower_part.setParentItem(None)
        self.lower_part.setParent(None)
        self.lower_part = None
        self.lower_doc = None

    def set_font(self, font):
        super().set_font(font)
        if self.lower_part:
            self.lower_part.setFont(font)

    def update_label(self, force_update=False):
        """ Asks for node/host to give text and update if changed """
        force_update = True
        self.has_been_initialized = True
        is_card = self.is_card()
        if self.text_align == LEFT_ALIGN:
            self.editable_doc.set_align(QtCore.Qt.AlignLeft)
        elif self.text_align == RIGHT_ALIGN:
            self.editable_doc.set_align(QtCore.Qt.AlignRight)
        else:
            self.editable_doc.set_align(QtCore.Qt.AlignHCenter)
        html, lower_html = self._host.label_as_html()
        if html is None:
            print('problems ahead:')
            print(self._host, self._host.node_type, self._host.syntactic_object)

        if self.node_shape == SCOPEBOX:
            if not self._host.is_leaf(only_similar=True, only_visible=True):
                html = '<sub>' + html + '</sub>'
            if lower_html:
                html += lower_html.replace('<br/>', '')
        elif self.node_shape == BRACKETED:
            if not self._host.is_leaf(only_similar=True, only_visible=True):
                html = '[<sub>' + html + '</sub>'
            if lower_html:
                html += lower_html.replace('<br/>', '')

        if force_update or (self.node_shape, html, lower_html, is_card) != self._previous_values:
            if self.editable_html != html:
                self.editable_doc.blockSignals(True)
                if is_card:
                    self.editable_doc.setTextWidth(self.card_size[0])
                else:
                    self.editable_doc.setTextWidth(-1)
                self.editable_html = html
                self.editable_part.setHtml(html)
                self.editable_doc.blockSignals(False)

            ctrl.qdocument_parser.process(self.editable_doc)
            if lower_html and self.node_shape not in [g.SCOPEBOX, g.BRACKETED]:
                if not self.lower_part:
                    self.init_lower_part()
                if lower_html != self.lower_html:
                    self.lower_html = lower_html
                    if is_card:
                        self.lower_doc.setTextWidth(self.card_size[0])
                    else:
                        self.lower_doc.setTextWidth(-1)
                    self.lower_part.setHtml(self.lower_html)
                ctrl.qdocument_parser.process(self.lower_doc)
            else:
                self.lower_html = ''
                if self.lower_part:
                    self.remove_lower_part()
            self._previous_values = (self.node_shape, self.editable_html, self.lower_html, is_card)

        self.resize_label()

    def is_card(self):
        if self.node_shape != CARD:
            return False
        if inner_cards:
            return True
        elif self._host.is_triangle_host():
            return True
        elif self._host.is_leaf(only_similar=True, only_visible=True):
            return True
        return False

    def left_bracket_width(self):
        return self.width

    def right_bracket_width(self) -> int:
        if self.node_shape == BRACKETED:
            return 6
        elif self.node_shape == SCOPEBOX:
            return 2
        else:
            return 0

    def is_empty(self) -> bool:
        """ Turning this node into label would result in an empty label.
        :return: bool
        """
        return not (self.editable_html or self.lower_html)

    def has_content(self) -> bool:
        return bool(self.editable_html or self.lower_html)

    def get_lower_part_y(self) -> int:
        return self.y_offset + self.lower_part_y

    def _get_editing_width(self) -> int:
        return self.card_size[0] if self.is_card() else -1

    def resize_label(self):
        self.prepareGeometryChange()
        triangle_host = self._host.is_triangle_host()
        if triangle_host:
            label_text = self._host.allowed_label_text_mode()
            self.draw_triangle = ((label_text == g.NODE_LABELS or
                                   label_text == g.NODE_LABELS_FOR_LEAVES) and
                                   self.node_shape not in [g.SCOPEBOX, g.CARD, g.BRACKETED])
        else:
            self.draw_triangle = False

        # ------------------- Width -------------------
        user_width, user_height = self.get_max_size_from_host()
        if self.is_card():
            width = self.card_size[0]
        else:
            if self.lower_html:
                self.editable_part.setTextWidth(-1)
                self.lower_part.setTextWidth(-1)
                ideal_width = max((self.editable_doc.idealWidth(), self.lower_doc.idealWidth()))
            elif triangle_host:
                self.editable_part.setTextWidth(-1)
                ideal_width = max((self.editable_doc.idealWidth(), self.triangle_width))
            else:
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
            elif width > ComplexLabel.max_width:
                width = ComplexLabel.max_width
        self.editable_part.setTextWidth(width)
        if self.lower_html:
            self.lower_part.setTextWidth(width)

        # ------------------- Height -------------------
        if self.is_card():
            total_height = self.card_size[1]
        elif self.draw_triangle:
            if self.editable_html:
                eh = self.editable_doc.size().height()
            else:
                eh = 0
            if self.lower_html:
                lh = self.lower_doc.size().height()
            else:
                lh = 0
            total_height = eh + self.triangle_height + lh
        else:
            total_height = self.editable_doc.size().height()
        half_height = total_height / 2.0
        self.top_y = -half_height
        self.bottom_y = half_height
        self.width = width
        self.height = total_height
        # middle line is 0
        if self.draw_triangle:
            # if triangled is not leaf, editing should target the upper part and leave
            # the combination of leaves alone
            self.upper_part_y = 0
            if self.editable_html:
                self.triangle_y = self.editable_doc.size().height()
            else:
                self.triangle_y = 0
            self.lower_part_y = self.triangle_y + self.triangle_height
        elif self.node_shape == g.CARD:
            # no lower part, no triangle
            self.upper_part_y = 0
            self.triangle_y = 0
            self.lower_part_y = self.editable_doc.size().height()
            # reduce font size until it fits
            if self.lower_part and self.lower_html:
                font = self.lower_part.font()
                use_point_size = font.pointSize() != -1
                if use_point_size:
                    fsize = font.pointSize()
                else:
                    fsize = font.pixelSize()
                attempts = 0
                while fsize > 5 and attempts < 10 and self.lower_part_y + self.lower_doc.size(

                ).height() > total_height:
                    fsize -= 1
                    if use_point_size:
                        font.setPointSize(fsize)
                    else:
                        font.setPixelSize(fsize)
                    self.lower_part.setFont(font)
                    attempts += 1
        else:
            # no lower part, no triangle
            self.upper_part_y = 0
            self.triangle_y = 0
            self.lower_part_y = 0

        self.x_offset = width / -2.0
        if self.is_card():
            self.y_offset = self.upper_part_y
        else:
            self.y_offset = -half_height

        self.setPos(self.x_offset, self.y_offset)
        self.editable_part.setPos(0, self.upper_part_y)
        if self.lower_html:
            self.lower_part.setPos(0, self.lower_part_y)

        # Update ui items around the label (or node hosting the label)
        ctrl.ui.update_position_for(self._host)

    def boundingRect(self):
        if self.is_card():
            return QtCore.QRectF(0, 0, self.card_size[0], self.card_size[1])
        else:
            return QtCore.QRectF(self.x_offset, self.y_offset, self.width, self.height)

    def _paint_triangle(self, painter, c):
        left = 0
        center = self.width / 2
        right = self.width
        top = self.triangle_y
        bottom = top + self.triangle_height
        simple = False
        painter.setPen(c)
        if simple:
            triangle = QtGui.QPainterPath()
            triangle.moveTo(center, top)
            triangle.lineTo(right, bottom)
            triangle.lineTo(left, bottom)
            triangle.lineTo(center, top)
            painter.drawPath(triangle)
        else:
            # This looks complicated, but it is necessary. We want node's edge type's shape
            # class and its properties so that the triangle can be drawn in similar style.
            edge_type = self._host.edge_type()
            shape_name = ctrl.settings.get_edge_setting('shape_name', edge_type=edge_type)
            path_class = SHAPE_PRESETS[shape_name]
            path, lpath, foo, bar = path_class.path((center, top), (right, bottom), [],
                                                    g.BOTTOM, g.TOP)
            fill = path_class.fillable and ctrl.settings.get_shape_setting('fill',
                                                                           edge_type=edge_type)
            if fill:
                painter.fillPath(path, c)
            else:
                painter.drawPath(path)
            painter.drawLine(left, bottom, right, bottom)
            path, lpath, foo, bar = path_class.path((center, top), (left, bottom), [], g.BOTTOM,
                                                    g.TOP)

            if fill:
                painter.fillPath(path, c)
            else:
                painter.drawPath(path)

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
        if self.lower_part:
            self.lower_part.setDefaultTextColor(c)
        if self.draw_triangle:
            self._paint_triangle(painter, c)
