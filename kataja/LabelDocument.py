__author__ = 'purma'

from PyQt5 import QtGui, QtCore


class LabelDocument(QtGui.QTextDocument):
    """ This extends QTextDocument with ability to read INodes (intermediary nodes) and turn them into
    QTextDocuments RTF presentation """

    def __init__(self):
        QtGui.QTextDocument.__init__(self)
        self.lines = []
        self.setDefaultTextOption(QtGui.QTextOption(QtCore.Qt.AlignHCenter))

    def clear(self):
        QtGui.QTextDocument.clear(self)
        self.clearUndoRedoStacks()
