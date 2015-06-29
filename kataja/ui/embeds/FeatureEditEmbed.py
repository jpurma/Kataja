
__author__ = 'purma'

from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.ui.embeds.UIEmbed import UIEmbed, EmbeddedLineEdit
from kataja.singletons import qt_prefs, ctrl
from kataja.ui.panels.SymbolPanel import open_symbol_data
from kataja.LabelDocument import LabelDocument
from kataja.parser import INodeToLabelDocument
from kataja.parser import INodeToKatajaConstituent
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



class FeatureEditEmbed(UIEmbed):
    def __init__(self, parent, ui_manager, ui_key, node):
        UIEmbed.__init__(self, parent, ui_manager, ui_key, node)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        layout.addLayout(self.top_row_layout)
        layout.addSpacing(4)
        self.node = node
        ui_p = QtGui.QPalette()
        ui_p.setColor(QtGui.QPalette.Text, ctrl.cm.ui())

        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)
        tt = "Feature name. This is the key syntax uses when looking for feature value e.g. 'case', 'number', 'edge'"
        self.name_edit = EmbeddedLineEdit(self, tip=tt, font=f, prefill="feature name, e.g. 'case'")
        self.name_edit.setText(self.node.name)
        layout.addWidget(self.name_edit)

        tt = "Feature value. Value assigned for feature. Text, number or boolean ('t/True', 'f/False', 1, 0) "
        self.value_edit = EmbeddedLineEdit(self, tip=tt, font=f, prefill="feature value, e.g. 'nom'")
        self.value_edit.setText(self.node.value)
        layout.addWidget(self.name_value)

        tt = "Feature family. For collecting features of similar type, e.g. phi-features "
        self.family_edit = EmbeddedLineEdit(self, tip=tt, font=f, prefill="family, e.g. 'phi'")
        self.family_edit.setText(self.node.family)
        layout.addWidget(self.family_edit)

        self.enter_button = QtWidgets.QPushButton("↩")  # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        self.enter_button.setParent(self)
        ui_manager.connect_element_to_action(self.enter_button, 'edit_feature_finished')

        layout.addWidget(self.enter_button)


    def usizeHint(self):
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
        #inode = LabelDocumentToINode.parse_labeldocument(self.master_edit.document())
        INodeToKatajaConstituent.update_constituentnode_fields(self.node, inode)

    def update_embed(self, scenePos=None, node=None):
        if node:
            self.node = node
        if self.node:
            self.update_document()
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


    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(ctrl.cm.ui())
        d = self.master_edit.document()
        c = d.blockCount()
        for i in range(0, c):
            block = d.findBlockByNumber(i)
            r = d.documentLayout().blockBoundingRect(block)
            tr = self.master_edit.mapToParent(r.topRight().toPoint())
            tr_x, tr_y = tr.x(), tr.y()
            h = r.height()
            h2 = r.height() / 2
            painter.drawLine(tr_x, tr_y, tr_x, tr_y + h)
            painter.drawLine(tr_x, tr_y + h2, tr_x + 20, tr_y + h2)
            if i < len(d.block_order):
                text = d.block_order[i]
            else:
                text = d.block_order[-1]
            painter.drawText(tr_x + 24, tr_y + h2, text)
        UIEmbed.paintEvent(self, event)


    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)

    def focus_to_main(self):
        self.master_edit.setFocus()
        pass

    def close(self):
        # self.input_line_edit.setText('')
        UIEmbed.close(self)
