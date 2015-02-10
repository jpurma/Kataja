
__author__ = 'purma'

from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.singletons import qt_prefs, ctrl, prefs
from kataja.LabelDocument import LabelDocument
from kataja.ui.panels.SymbolPanel import open_symbol_data
from kataja.parser import INodeToLabelDocument
from kataja.parser import LabelDocumentToINode
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



class EmbeddedTextEdit(QtWidgets.QTextEdit):

    def __init__(self, parent):
        QtWidgets.QTextEdit.__init__(self, parent)
        self._old_size = self.new_size_hint()
        self.setAcceptDrops(True)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setAutoFillBackground(True)
        self.textChanged.connect(self.resize_as_needed)

    def canInsertFromMimeData(self, mimedata):
        if mimedata.hasFormat("application/x-qabstractitemmodeldatalist"):
            return True
        else:
            return QtWidgets.QTextEdit.canInsertFromMimeData(self, mimedata)

    def insertFromMimeData(self, mimedata):
        if mimedata.hasFormat("application/x-qabstractitemmodeldatalist"):
            data = open_symbol_data(mimedata)
            self.textCursor().insertText(data['char'])
        else:
            QtWidgets.QTextEdit.insertFromMimeData(self, mimedata)

    def sizeHint(self):
        return self._old_size

    def new_size_hint(self):
        w = max((100, self.document().idealWidth()))
        h = self.document().size().height()
        return QtCore.QSize(w, h)

    def resize_as_needed(self):
        sh = self.new_size_hint()
        if sh != self._old_size:
            self._old_size = sh
            self.setMinimumSize(sh)
            self.setMaximumSize(sh)
            self.updateGeometry()
            self.parent().resize(self.parent().sizeHint())

# todo: show latex source -button
class ConstituentEditEmbed(UIEmbed):

    def __init__(self, parent, ui_manager, node, scenePos):
        UIEmbed.__init__(self, parent, ui_manager, scenePos)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.raw_button = QtWidgets.QPushButton('LaTeX')
        self.raw_button.setCheckable(True)
        self.raw_button.setMaximumWidth(40)
        ui_manager.connect_element_to_action(self.raw_button, 'raw_editing_toggle')
        self.top_row_layout.addWidget(self.raw_button, 0, QtCore.Qt.AlignRight)

        layout.addLayout(self.top_row_layout)
        layout.addSpacing(4)
        self.node = node
        ui_p = QtGui.QPalette()
        ui_p.setColor(QtGui.QPalette.Text, ctrl.cm.ui())

        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)
        self.master_edit = EmbeddedTextEdit(self)
        self.master_edit.setDocument(LabelDocument(edit=True))
        self.master_edit.setFont(f)
        self.master_edit.setTextColor(ctrl.cm.text())
        self.update_document()
        layout.addWidget(self.master_edit)

        #
        # tt = "non-functional readable label of the constituent"
        # self.alias_edit = EmbeddedLineEdit(self, tip=tt, font=f)
        # hlayout.addWidget(self.alias_edit)
        # self.alias_label = make_label('Alias', self, hlayout, tt, self.alias_edit, ui_p)
        # layout.addLayout(hlayout)
        #
        # hlayout = QtWidgets.QHBoxLayout()
        # tt = "Label of the constituent (functional identifier)"
        # self.input_line_edit = EmbeddedLineEdit(self, tip=tt, font=f)
        # hlayout.addWidget(self.input_line_edit)
        # self.label_label = make_label('Label', self, hlayout, tt, self.input_line_edit, ui_p)
        #
        # tt = "Index to recognize multiple occurences"
        # self.index_edit = EmbeddedLineEdit(self, tip=tt, font=f)
        # self.index_edit.setFixedWidth(20)
        # hlayout.addWidget(self.index_edit)
        # self.index_label = make_label('Index', self, hlayout, tt, self.index_edit, ui_p)
        #
        # layout.addLayout(hlayout)
        #
        # fg = QtGui.QFont(qt_prefs.font(g.ITALIC_FONT))
        # fg.setPointSize(f.pointSize() * 2)
        # hlayout = QtWidgets.QHBoxLayout()
        # tt = "A translation of the word"
        # self.gloss_edit = EmbeddedLineEdit(self, tip=tt, font=fg)
        # hlayout.addWidget(self.gloss_edit)
        # self.gloss_label = make_label('Gloss', self, hlayout, tt, self.gloss_edit, ui_p)
        # layout.addLayout(hlayout)

        self.enter_button = QtWidgets.QPushButton("↩") # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        self.enter_button.setParent(self)
        ui_manager.connect_element_to_action(self.enter_button, 'edit_constituent_finished')

        layout.addWidget(self.enter_button)

    def toggle_raw_edit(self, value):
        d = self.master_edit.document()
        inode = LabelDocumentToINode.parse_labeldocument(d)
        d.raw_mode = value
        INodeToLabelDocument.parse_inode(inode, d)
        self.master_edit.setMinimumSize(self.master_edit.sizeHint())
        self.master_edit.updateGeometry()

    def update_document(self):
        d = self.master_edit.document()
        INodeToLabelDocument.parse_inode(self.node.as_inode, d)
        #d.blocks_to_strings()
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
        self.master_edit.viewport().update()


    def update_position(self):
        sx, sy, sz = self.node.current_position
        p = self.parent().mapFromScene(sx, sy)
        px, py = p.x(), p.y()
        py -= self.assumed_height/2
        self.move(px, py)

    def push_values_back(self):
        inode = LabelDocumentToINode.parse_labeldocument(self.master_edit.document())
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
            #     label = self.node.syntactic_object.label
            # else:
            #     label = ''
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
            h2 = r.height()/2
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
        #self.input_line_edit.setText('')
        UIEmbed.close(self)
