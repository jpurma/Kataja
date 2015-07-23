from PyQt5 import QtWidgets, QtGui

from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.singletons import qt_prefs
import kataja.globals as g
from kataja.ui.OverlayButton import OverlayButton


__author__ = 'purma'


class EdgeLabelEmbed(UIEmbed):
    def __init__(self, parent, ui_manager, edge, ui_key):
        UIEmbed.__init__(self, parent, ui_manager, ui_key, edge)
        self.marker = None
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout)  # close-button from UIEmbed
        self.input_line_edit = QtWidgets.QLineEdit(self)
        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)
        self.input_line_edit.setFont(f)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.input_line_edit)
        self.enter_button = QtWidgets.QPushButton("↩")  # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        ui_manager.connect_element_to_action(self.enter_button, 'edit_edge_label_enter_text')

        hlayout.addWidget(self.enter_button)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.assumed_width = 200
        self.assumed_height = 37

    def focus_to_main(self):
        self.input_line_edit.setFocus()

    def update_embed(self, focus_point=None):
        if self.host:
            p = QtGui.QPalette()
            p.setColor(QtGui.QPalette.Text, self.host.color)
            self.input_line_edit.setPalette(p)
            f = QtGui.QFont(self.host.font)
            f.setPointSize(f.pointSize() * 2)
            self.input_line_edit.setFont(f)
            self.input_line_edit.setText(self.host.label_text)
        UIEmbed.update_embed(focus_point=focus_point)

    def update_position(self):
        UIEmbed.update_embed(focus_point=self.host.label_item.pos())

