from PyQt5 import QtWidgets, QtGui

from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.singletons import qt_prefs
import kataja.globals as g
from kataja.ui.OverlayButton import OverlayButton
from kataja.ui.panels.field_utils import EmbeddedLineEdit

__author__ = 'purma'


class EdgeLabelEmbed(UIEmbed):
    def __init__(self, parent, ui_manager, edge, ui_key):
        UIEmbed.__init__(self, parent, ui_manager, ui_key, edge, 'Edit edge text')
        self.marker = None
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout)  # close-button from UIEmbed
        tt = 'Label for arrow'
        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)
        self.input_line_edit = EmbeddedLineEdit(self, tip=tt, font=f, prefill='label')
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
            #self.input_line_edit.setFont(f)
        super().update_embed()

    def update_fields(self):
        self.input_line_edit.setText(self.host.label_text)
        super().update_fields()

    def update_position(self, focus_point=None):
        super().update_position(self.host.label_item.pos())

