from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.singletons import qt_prefs, ctrl
import kataja.globals as g
from kataja.ui.OverlayButton import OverlayButton

__author__ = 'purma'


class EdgeLabelEmbed(UIEmbed):

    def __init__(self, parent, ui_manager, scenePos):
        UIEmbed.__init__(self, parent, ui_manager, scenePos)
        self.marker = None
        self.edge = None
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout) # close-button from UIEmbed
        self.input_line_edit = QtWidgets.QLineEdit(self)
        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize()*2)
        self.input_line_edit.setFont(f)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.input_line_edit)
        self.enter_button = QtWidgets.QPushButton("↩") # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        ui_manager.connect_element_to_action(self.enter_button, 'edit_edge_label_enter_text')

        hlayout.addWidget(self.enter_button)
        self.unlock_button = OverlayButton(qt_prefs.lock_icon, 'unlock', self)
        hlayout.addWidget(self.unlock_button)

        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.assumed_width = 200
        self.assumed_height = 37

    def focus_to_main(self):
        self.input_line_edit.setFocus()

    def update_embed(self, scenePos=None, edge=None):
        if edge:
            self.edge = edge
        if self.edge:
            p = QtGui.QPalette()
            p.setColor(QtGui.QPalette.Text, self.edge.color())
            self.input_line_edit.setPalette(p)
            f = QtGui.QFont(self.edge.font())
            f.setPointSize(f.pointSize() * 2)
            self.input_line_edit.setFont(f)
            self.input_line_edit.setText(self.edge.label_text())

        UIEmbed.update_embed(self, scenePos=scenePos)