__author__ = 'purma'

from PyQt5 import QtGui, QtCore
from kataja.parser.LatexToINode import ITextNode, ICommandNode

from kataja.parser.latex_to_unicode import latex_to_unicode


class LabelDocument(QtGui.QTextDocument):
    """ This extends QTextDocument with ability to read INodes (intermediary nodes) and turn them into QTextDocuments
     RTF presentation """

    def __init__(self, edit=True):
        QtGui.QTextDocument.__init__(self)
        self.setDefaultTextOption(QtGui.QTextOption(QtCore.Qt.AlignHCenter))
        self.block_mapping = {0:'alias', 1: 'label', 2: 'index', 3: 'gloss', 4: 'features'}
        self.edit_mode = edit

    def run_command(self, command, cursor):
        """
        :param command: latex command that may be translated to rtf formatting commands.
        :param cursor: here we write.
        :param doc: document, required for fetching e.g. font info.
        :return:
        """
        if command == 'emph':
            c = QtGui.QTextCharFormat()
            c.setFontItalic(True)
            cursor.mergeCharFormat(c)
        elif command == '^':
            #c = QtGui.QTextCharFormat()
            c = QtGui.QTextCharFormat()
            c.setVerticalAlignment(QtGui.QTextCharFormat.AlignSuperScript)
            cursor.mergeCharFormat(c)
        elif command == '_':
            c = QtGui.QTextCharFormat()
            c.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)
            c.setFontItalic(True)
            cursor.mergeCharFormat(c)
        elif command in latex_to_unicode:
            cursor.insertText(latex_to_unicode[command][0])
        #print('got command: %s' % command)


    def write_node_to_document(self, n, cursor):
        """ Recursive node writer. Stores the current charformat, so when the end of formatting scope is reached,
        we can return to previous format.
        :param n: node
        :param cursor: cursor in document, this is the point where we write
        :return:
        """
        if not n:
            return
        old_format = None
        if isinstance(n, ICommandNode) and n.command:
            old_format = QtGui.QTextCharFormat(cursor.charFormat())
            self.run_command(n.command, cursor)
        for part in n.parts:
            if isinstance(part, ITextNode): # ITextNode includes also ICommandNodes and IConstituentNodes
                self.write_node_to_document(part, cursor)
            else:
                cursor.insertText(part)
        if old_format:
            cursor.setCharFormat(old_format)

    def blocks_to_strings(self):
        """ Parse LabelDocument back to alias, label, index, gloss and features
        :return:
        """
        c = self.blockCount()
        #print("blockCount = ", c)
        #print("document = ", self.toPlainText())
        r = []
        for i in range(0, c):
            block = self.findBlockByNumber(i)
            print('---- block %s ----' % block.blockNumber())
            print(block.text())
            print(block.textFormats())
            r.append(block.text())
            #print(i, block, block.layout(), block.layout().boundingRect())
            #print(self.documentLayout(), self.documentLayout().blockBoundingRect(block))
        return r


    def parse_inodes(self, inodes):
        """ Does what it says.
        :param inodes: Node or nodes to be translated. If there are several, linebreak is added between them """
        self.clear()
        cursor = QtGui.QTextCursor(self)
        if isinstance(inodes, tuple) or isinstance(inodes, list):
            first = True
            for node in inodes:
                if (not self.edit_mode) and ((not node) or node.is_empty()):
                    continue
                if not first:
                    cursor.insertText('\n')
                self.write_node_to_document(node, cursor)
                first = False
        else:
            self.write_node_to_document(inodes, cursor)

    def push_values_to(self, node):
        values = self.blocks_to_strings()

