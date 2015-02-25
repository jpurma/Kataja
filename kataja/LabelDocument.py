__author__ = 'purma'

from PyQt5 import QtGui, QtCore


class LabelDocument(QtGui.QTextDocument):
    """ This extends QTextDocument with ability to read INodes (intermediary nodes) and turn them into QTextDocuments
     RTF presentation """

    def __init__(self, edit=False, raw=False):
        QtGui.QTextDocument.__init__(self)
        self.setDefaultTextOption(QtGui.QTextOption(QtCore.Qt.AlignHCenter))
        self.edit_mode = edit
        self.raw_mode = raw
        self.block_order = []

    def default_block_order(self):
        return ['alias', 'label', 'index', 'gloss', 'features']

    def clear(self):
        self.block_order = self.default_block_order()
        QtGui.QTextDocument.clear(self)
        self.clearUndoRedoStacks()
