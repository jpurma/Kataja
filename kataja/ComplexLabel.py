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

from PyQt5 import QtCore

from kataja.SimpleLabel import SimpleLabel
from kataja.globals import NORMAL, BRACKETED, SCOPEBOX, CARD, LEFT_ALIGN, RIGHT_ALIGN
from kataja.singletons import ctrl
from kataja.uniqueness_generator import next_available_type_id

inner_cards = False


class ComplexLabel(SimpleLabel):
    """ ComplexLabels are labels that can have two textareas and a triangle between them """
    max_width = 400
    __qt_type_id__ = next_available_type_id()
    card_size = (60, 90)

    def __init__(self, parent=None):
        """ Give node as parent. Label asks it to produce text to show here """
        SimpleLabel.__init__(self, parent)
        self.cn_shape = NORMAL
        self._previous_values = None

    def keep_visible(self):
        return self.is_card() or self.has_content() or self.is_quick_editing()

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
        html = self._host.label_as_html()
        if html is None:
            print('problems ahead:')
            print(self._host, self._host.node_type, self._host.syntactic_object)

        if self.cn_shape == SCOPEBOX:
            if not self._host.is_leaf(visible=True):
                html = '<sub>' + html + '</sub>'
        elif self.cn_shape == BRACKETED:
            if not self._host.is_leaf(visible=True):
                html = '[<sub>' + html + '</sub>'

        if force_update or (self.cn_shape, html, is_card) != self._previous_values:
            if self.editable_html != html:
                self.editable_doc.blockSignals(True)
                if is_card:
                    self.editable_doc.setTextWidth(self.card_size[0])
                else:
                    self.editable_doc.setTextWidth(-1)
                self.editable_html = html
                self.setHtml(html)
                self.editable_doc.blockSignals(False)

            ctrl.qdocument_parser.process(self.editable_doc)
            self._previous_values = (self.cn_shape, self.editable_html, is_card)

        self.resize_label()

    def is_card(self):
        if self.cn_shape != CARD:
            return False
        if inner_cards:
            return True
        elif self._host.is_triangle_host():
            return True
        elif self._host.is_leaf(visible=True):
            return True
        return False

    def left_bracket_width(self):
        return self.width

    def right_bracket_width(self) -> int:
        if self.cn_shape == BRACKETED:
            return 6
        elif self.cn_shape == SCOPEBOX:
            return 2
        else:
            return 0

    def _get_editing_width(self) -> int:
        return self.card_size[0] if self.is_card() else -1

    def resize_label(self):
        self.prepareGeometryChange()

        # ------------------- Width -------------------
        user_width, user_height = self.get_max_size_from_host()
        if self.is_card():
            width = self.card_size[0]
        else:
            self.setTextWidth(-1)
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
        self.setTextWidth(width)

        # ------------------- Height -------------------
        if self.is_card():
            total_height = self.card_size[1]
        else:
            total_height = self.editable_doc.size().height()
        half_height = total_height / 2.0
        self.top_y = -half_height
        self.bottom_y = half_height
        self.width = width
        self.height = total_height
        # middle line is 0
        self.x_offset = width / -2.0
        if self.is_card():
            self.y_offset = 0
        else:
            self.y_offset = -half_height

        self.setPos(self.x_offset, self.y_offset)
        # Update ui items around the label (or node hosting the label)
        ctrl.ui.update_position_for(self._host)

    def boundingRect(self):
        if self.is_card():
            return QtCore.QRectF(0, 0, self.card_size[0], self.card_size[1])
        else:
            return super().boundingRect()
