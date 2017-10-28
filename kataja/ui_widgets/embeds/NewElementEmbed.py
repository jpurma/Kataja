from PyQt5 import QtWidgets, QtGui, QtCore

import kataja.globals as g
from kataja.singletons import qt_prefs, ctrl, classes
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.PushButtonBase import PushButtonBase
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.UIEmbed import UIEmbed
from kataja.ui_widgets.buttons.OverlayButton import OverlayButton
from kataja.utils import guess_node_type
from kataja.ui_widgets.ExpandingLineEdit import ExpandingLineEdit

__author__ = 'purma'


class NewElementEmbed(UIEmbed):
    def __init__(self, parent):
        UIEmbed.__init__(self, parent, None, 'Create new node')
        self.marker = None
        self.guess_mode = True
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout)
        tt = 'Text for new node'
        smaller_font = qt_prefs.get_font(g.MAIN_FONT)
        big_font = QtGui.QFont(smaller_font)
        big_font.setPointSize(big_font.pointSize() * 2)
        self.input_line_edit = ExpandingLineEdit(self, tooltip=tt, big_font=big_font,
                                                 smaller_font=smaller_font, prefill='label',
                                                 on_edit=self.guess_type_for_input)
        layout.addWidget(self.input_line_edit)
        hlayout = QtWidgets.QHBoxLayout()
        self.node_type_selector = SelectionBox(self)
        self.node_type_selector.currentIndexChanged.connect(self.changed_node_type)

        self.node_types = [(g.GUESS_FROM_INPUT, 'Guess from input')]
        for key in classes.node_types_order:
            node_class = classes.nodes.get(key, None)
            if (not node_class) or node_class.is_syntactic and not ctrl.free_drawing_mode:
                continue
            self.node_types.append((key, 'New %s' % node_class.display_name[0].lower()))
        self.node_type_selector.add_items(self.node_types)
        hlayout.addWidget(self.node_type_selector)
        hlayout.addStretch(0)
        # U+21A9 &#8617;
        self.enter_button = PushButtonBase(parent=self, text="Create ↩",
                                           action='create_new_node_from_text'
                                           ).to_layout(hlayout)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.assumed_width = 200
        self.assumed_height = 117

    @property
    def graphic_item(self):
        return self.marker

    def mouseMoveEvent(self, event):
        if self._drag_diff:
            self.move(self.mapToParent(event.pos()) - self._drag_diff)
            if self.marker:
                self.marker.update_position()
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def guess_type_for_input(self, text):
        if not self.guess_mode:
            return
        key = guess_node_type(text)
        if key == 100:
            self.top_title.setText('Create new tree')
        else:
            self.top_title.setText('Create new ' + classes.node_info[key]['name'].lower())

    def changed_node_type(self, index=-1):
        if index == 0:
            self.guess_mode = True
        elif index > 0:
            title_text = self.node_type_selector.itemText(index)
            self.top_title.setText('Create ' + title_text.lower())
            self.guess_mode = False

    def focus_to_main(self):
        self.input_line_edit.setFocus(QtCore.Qt.PopupFocusReason)

    def get_marker_points(self):
        p1 = self.marker.pos()
        p2 = self.marker.mapToScene(self.marker.end_point)
        return p1, p2

    def set_node_type(self, value):
        self.node_type_selector.setCurrentIndex(self.node_type_selector.findData(value, role=256))

    def resizeEvent(self, event):
        self.limited_update_position()
        QtWidgets.QWidget.resizeEvent(self, event)

    def limited_update_position(self):
        """ Updates the position but tries to minimize the movement of left top
        corner. This is called on resize, to ensure that all of the embed is in visible area.
        :return:
        """
        view = self.parent()
        eg = self.geometry()
        ex, ey, ew, eh = eg.getRect()
        top_left = view.mapToScene(ex, ey)
        bottom_right = view.mapToScene(QtCore.QPoint(ex + ew, ey + eh))
        size_in_scene = bottom_right - top_left
        x = top_left.x()
        y = top_left.y()
        w = size_in_scene.x()
        h = size_in_scene.y()
        vr = view.mapToScene(view.geometry()).boundingRect()
        view_left, view_top, view_right, view_bottom = vr.getRect()
        view_right += view_left
        view_bottom += view_top

        w_overlap = (x + w) - view_right
        h_overlap = (y + h) - view_bottom

        move = False
        if w_overlap > 0:
            x = x - w_overlap - 12
            move = True
        if h_overlap > 0:
            y = y - h_overlap - 8
            move = True
        if move:
            new_pos = QtCore.QPoint(x, y)
            self.move(view.mapFromScene(new_pos))
            self.updateGeometry()
