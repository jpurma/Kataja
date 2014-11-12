__author__ = 'purma'

from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.singletons import qt_prefs, ctrl, prefs
from kataja.utils import print_transform
from kataja.ui.DrawnIconEngine import DrawnIconEngine
import kataja.globals as g



class ConstituentEditEmbed(UIEmbed):

    def __init__(self, parent, ui_manager, scenePos):
        UIEmbed.__init__(self, parent, ui_manager, scenePos)
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout)
        layout.addSpacing(12)
        self.node = None
        self.input_line_edit = QtWidgets.QLineEdit(self)
        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)
        self.input_line_edit.setFont(f)
        layout.addWidget(self.input_line_edit)
        self.enter_button = QtWidgets.QPushButton("↩") # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        ui_manager.connect_element_to_action(self.enter_button, 'edit_constituent_finished')
        self.setLayout(layout)
        self.assumed_width = 200
        self.assumed_height = 117

    def update_position(self):
        self.move(self.node.pos().x(), self.node.pos().y())

    def update_embed(self, scenePos=None, node=None):
        if node:
            self.node = node
        if self.node:
            p = QtGui.QPalette()
            p.setColor(QtGui.QPalette.Text, self.node.color())
            self.input_line_edit.setPalette(p)
            f = QtGui.QFont(self.node.font())
            f.setPointSize(f.pointSize() * 2)
            self.input_line_edit.setFont(f)
            self.input_line_edit.setText(str(self.node))

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)

    def focus_to_main(self):
        self.input_line_edit.setFocus()

    def close(self):
        self.input_line_edit.setText('')
        UIEmbed.close(self)
