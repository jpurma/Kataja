__author__ = 'purma'

from PyQt5 import QtGui, QtCore


class LabelDocument(QtGui.QTextDocument):
    """ This extends QTextDocument with ability to read INodes (intermediary nodes) and turn them into
    QTextDocuments RTF presentation """

    def __init__(self):
        QtGui.QTextDocument.__init__(self)
        self.lines = []
        self.new_lines = {}
        self.align = QtCore.Qt.AlignHCenter
        dto = self.defaultTextOption()
        dto.setWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)
        dto.setAlignment(self.align)
        self.setDefaultTextOption(dto)

    def clear(self):
        QtGui.QTextDocument.clear(self)
        self.clearUndoRedoStacks()

    def set_align(self, align):
        if self.align != align:
            dto = self.defaultTextOption()
            dto.setAlignment(align)
            self.setDefaultTextOption(dto)
            self.align = align