
__author__ = 'purma'

from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.parser.LatexToINode import parse_field
from kataja.ui.embeds.UIEmbed import UIEmbed, EmbeddedLineEdit
from kataja.singletons import qt_prefs, ctrl
from kataja.parser import INodeToLabelDocument
from kataja.parser import INodeToLatex
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
    def __init__(self, parent, ui_manager, node, scenePos):
        UIEmbed.__init__(self, parent, ui_manager, scenePos)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        #self.latex_button = QtWidgets.QPushButton('LaTeX')
        #self.latex_button.setCheckable(True)
        #self.latex_button.setMaximumWidth(40)
        #ui_manager.connect_element_to_action(self.latex_button, 'latex_editing_toggle')
        #self.top_row_layout.addWidget(self.raw_button, 0, QtCore.Qt.AlignRight)
        layout.addLayout(self.top_row_layout)
        layout.addSpacing(4)
        self.node = node
        ui_p = QtGui.QPalette()
        ui_p.setColor(QtGui.QPalette.Text, ctrl.cm.ui())

        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)

        tt = "non-functional readable label of the constituent"
        hlayout = QtWidgets.QHBoxLayout()
        self.alias_edit = EmbeddedLineEdit(self, tip=tt, font=f, prefill="alias")
        self.alias_edit.setMaximumWidth(140)
        hlayout.addWidget(self.alias_edit)
        self.alias_label = make_label('Alias', self, hlayout, tt, self.alias_edit, ui_p)
        tt = "Index to recognize multiple occurences"
        self.index_edit = EmbeddedLineEdit(self, tip=tt, font=f, prefill="i")
        self.index_edit.setFixedWidth(20)
        hlayout.addWidget(self.index_edit)
        self.index_label = make_label('Index', self, hlayout, tt, self.index_edit, ui_p)
        hlayout.addWidget(self.index_label)
        layout.addLayout(hlayout)

        tt = "Label of the constituent (functional identifier)"
        hlayout = QtWidgets.QHBoxLayout()
        self.label_edit = EmbeddedLineEdit(self, tip=tt, font=f, prefill="label")
        self.label_edit.setMaximumWidth(200)
        hlayout.addWidget(self.label_edit)
        self.label_label = make_label('Label', self, hlayout, tt, self.label_edit, ui_p)
        layout.addLayout(hlayout)

        self.enter_button = QtWidgets.QPushButton("↩")  # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        self.enter_button.setParent(self)
        ui_manager.connect_element_to_action(self.enter_button, 'edit_constituent_finished')
        layout.addWidget(self.enter_button)
        self.update_fields()

    def update_fields(self):
        self.index_edit.setText(self.node.index)
        self.alias_edit.setText(INodeToLatex.parse_inode_for_field(self.node.alias))
        self.label_edit.setText(INodeToLatex.parse_inode_for_field(self.node.label))


    def update_document(self):
        d = self.master_edit.document()
        INodeToLabelDocument.parse_inode(self.node.as_inode, d)
        # d.blocks_to_strings()
        self.master_edit.setMinimumSize(self.master_edit.sizeHint())
        self.master_edit.updateGeometry()
        cursor = self.master_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.Start)
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock)
        self.master_edit.setTextCursor(cursor)

    def sizeHint(self):
        base = QtWidgets.QWidget.sizeHint(self)
        return base + QtCore.QSize(40, 0)

    def after_appear(self):
        """ Customizable calls for refreshing widgets that have drawing problems recovering from blur effect.
        :return:
        """
        pass

    def update_position(self):
        sx, sy, sz = self.node.current_position
        p = self.parent().mapFromScene(sx, sy)
        px, py = p.x(), p.y()
        py -= self.assumed_height / 2
        self.move(px, py)

    def push_values_back(self):
        self.node.label = parse_field(self.label_edit.text())
        self.node.alias = parse_field(self.alias_edit.text())
        self.node.index = self.index_edit.text()
        self.node.update_label()

    def update_embed(self, scenePos=None, node=None):
        if node:
            self.node = node
        if self.node:
            self.update_fields()
            scene_pos = self.node.pos()
            UIEmbed.update_embed(self, scenePos=scene_pos)
            # p = QtGui.QPalette()
            # p.setColor(QtGui.QPalette.Text, self.node.color)
            # ui_p = QtGui.QPalette()
            # ui_p.setColor(QtGui.QPalette.Text, ctrl.cm.ui())
            # f = QtGui.QFont(self.node.font)
            # f.setPointSize(f.pointSize() * 2)
            # fg = QtGui.QFont(qt_prefs.font(g.ITALIC_FONT))
            # fg.setPointSize(fg.pointSize() * 2)
            # pg = QtGui.QPalette()
            # gpc = ctrl.forest.settings.node_settings(g.GLOSS_NODE, 'color')
            # pg.setColor(QtGui.QPalette.Text, ctrl.cm.get(gpc))
            #
            # self.alias_edit.update_visual(palette=p, font=f, text=self.node.alias)
            # self.alias_label.setFont(qt_prefs.font(g.UI_FONT))
            # self.alias_label.setPalette(ui_p)
            # self.label_label.setFont(qt_prefs.font(g.UI_FONT))
            # self.label_label.setPalette(ui_p)
            # if self.node.syntactic_object:
            # label = self.node.syntactic_object.label
            # else:
            # label = ''
            # self.input_line_edit.update_visual(palette=p, font=f, text=label)
            # self.index_edit.update_visual(palette=p, font=fg, text=self.node.index)
            #
            # self.index_label.setFont(qt_prefs.font(g.UI_FONT))
            # self.index_label.setPalette(ui_p)
            #
            # self.gloss_edit.update_visual(palette=pg, font=fg, text=self.node.gloss)
            # self.gloss_label.setFont(qt_prefs.font(g.UI_FONT))
            # self.gloss_label.setPalette(ui_p)


    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)

    def focus_to_main(self):
        self.label_edit.setFocus()

    def close(self):
        # self.input_line_edit.setText('')
        UIEmbed.close(self)
