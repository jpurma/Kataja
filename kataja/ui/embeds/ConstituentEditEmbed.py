__author__ = 'purma'

from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.ui.embeds.UIEmbed import UIEmbed, EmbeddedLineEdit
from kataja.singletons import qt_prefs, ctrl, prefs
from kataja.utils import print_transform
from kataja.ui.DrawnIconEngine import DrawnIconEngine
import kataja.globals as g

def make_label(text, parent=None, layout=None, tooltip='', buddy=None, palette=None):
    label = QtWidgets.QLabel(text, parent=parent)
    label.setPalette(palette)
    label.setFont(qt_prefs.font(g.UI_FONT))
    label.setBuddy(buddy)
    label.setStatusTip(tooltip)
    label.setToolTip(tooltip)
    layout.addWidget(label)
    return label




class ConstituentEditEmbed(UIEmbed):

    def __init__(self, parent, ui_manager, scenePos):
        UIEmbed.__init__(self, parent, ui_manager, scenePos)
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout)
        layout.addSpacing(12)
        self.node = None
        hlayout = QtWidgets.QHBoxLayout()
        ui_p = QtGui.QPalette()
        ui_p.setColor(QtGui.QPalette.Text, ctrl.cm.ui())

        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)
        tt = "non-functional readable label of the constituent"
        self.alias_edit = EmbeddedLineEdit(self, tip=tt, font=f)
        hlayout.addWidget(self.alias_edit)
        self.alias_label = make_label('Alias', self, hlayout, tt, self.alias_edit, ui_p)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        tt = "Label of the constituent (functional identifier)"
        self.input_line_edit = EmbeddedLineEdit(self, tip=tt, font=f)
        hlayout.addWidget(self.input_line_edit)
        self.label_label = make_label('Label', self, hlayout, tt, self.input_line_edit, ui_p)

        tt = "Index to recognize multiple occurences"
        self.index_edit = EmbeddedLineEdit(self, tip=tt, font=f)
        self.index_edit.setFixedWidth(20)
        hlayout.addWidget(self.index_edit)
        self.index_label = make_label('Index', self, hlayout, tt, self.index_edit, ui_p)

        layout.addLayout(hlayout)

        fg = QtGui.QFont(qt_prefs.font(g.ITALIC_FONT))
        fg.setPointSize(f.pointSize() * 2)
        hlayout = QtWidgets.QHBoxLayout()
        tt = "A translation of the word"
        self.gloss_edit = EmbeddedLineEdit(self, tip=tt, font=fg)
        hlayout.addWidget(self.gloss_edit)
        self.gloss_label = make_label('Gloss', self, hlayout, tt, self.gloss_edit, ui_p)
        layout.addLayout(hlayout)

        self.enter_button = QtWidgets.QPushButton("↩") # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        ui_manager.connect_element_to_action(self.enter_button, 'edit_constituent_finished')
        layout.addWidget(self.enter_button)
        self.setLayout(layout)
        self.assumed_width = 200
        self.assumed_height = 117


    def update_position(self):
        sx,sy,sz = self.node.current_position
        p = self.parent().mapFromScene(sx, sy)
        px, py = p.x(), p.y()
        py -= self.assumed_height/2
        self.move(px, py)

    def update_embed(self, scenePos=None, node=None):
        if node:
            self.node = node
        if self.node:
            scene_pos = self.node.pos()
            UIEmbed.update_embed(self, scenePos=scene_pos)
            p = QtGui.QPalette()
            p.setColor(QtGui.QPalette.Text, self.node.color)
            ui_p = QtGui.QPalette()
            ui_p.setColor(QtGui.QPalette.Text, ctrl.cm.ui())
            f = QtGui.QFont(self.node.font)
            f.setPointSize(f.pointSize() * 2)
            fg = QtGui.QFont(qt_prefs.font(g.ITALIC_FONT))
            fg.setPointSize(fg.pointSize() * 2)
            pg = QtGui.QPalette()
            gpc = ctrl.forest.settings.node_settings(g.GLOSS_NODE, 'color')
            pg.setColor(QtGui.QPalette.Text, ctrl.cm.get(gpc))

            self.alias_edit.update_visual(palette=p, font=f, text=self.node.alias)
            self.alias_label.setFont(qt_prefs.font(g.UI_FONT))
            self.alias_label.setPalette(ui_p)
            self.label_label.setFont(qt_prefs.font(g.UI_FONT))
            self.label_label.setPalette(ui_p)
            if self.node.syntactic_object:
                label = self.node.syntactic_object.label
            else:
                label = ''
            self.input_line_edit.update_visual(palette=p, font=f, text=label)
            self.index_edit.update_visual(palette=p, font=fg, text=self.node.index)

            self.index_label.setFont(qt_prefs.font(g.UI_FONT))
            self.index_label.setPalette(ui_p)

            self.gloss_edit.update_visual(palette=pg, font=fg, text=self.node.gloss)
            self.gloss_label.setFont(qt_prefs.font(g.UI_FONT))
            self.gloss_label.setPalette(ui_p)



    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)

    def focus_to_main(self):
        self.input_line_edit.setFocus()

    def close(self):
        self.input_line_edit.setText('')
        UIEmbed.close(self)
