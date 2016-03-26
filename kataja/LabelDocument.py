__author__ = 'purma'

from PyQt5 import QtGui, QtCore


class LabelDocument(QtGui.QTextDocument):
    """ This extends QTextDocument with ability to read INodes (intermediary nodes) and turn them into
    QTextDocuments RTF presentation """

    def __init__(self):
        QtGui.QTextDocument.__init__(self)
        self.lines = []
        self.new_lines = {}

    def clear(self):
        QtGui.QTextDocument.clear(self)
        self.clearUndoRedoStacks()

    def interpret_changes(self, old_inode, position, chars_removed, chars_added):
        #print('old_inode: ', old_inode, ' lines: ', self.lines, 'lineCount:', self.lineCount())
        #print(self.isModified(), position, chars_removed, chars_added)
        block = self.firstBlock()
        last = self.lastBlock()
        texts = []
        i = 0
        changed_line = 0
        changed = None
        while True:
            texts.append((block.text(), block.textFormats()))
            if block.contains(position):
                changed = block
                changed_line = i
            if block != last:
                block = block.next()
                changed_line += 1
            else:
                break
        #print(changed.text(), changed_line, chars_removed, chars_added)
        #field_starts = changed.position()
        field = changed_line
        self.new_lines[field] = changed.text()
