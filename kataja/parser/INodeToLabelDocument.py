__author__ = 'purma'

from PyQt5 import QtGui, QtCore
from kataja.parser.LatexToINode import ITextNode, ICommandNode, IConstituentNode

from kataja.parser.latex_to_unicode import latex_to_unicode


def parse_inode(inode, document):
    """ Does what it says. Takes an existing LabelDocument to avoid problems with their garbage collection.
    :param inode: Node or nodes to be translated. If there are several, linebreak is added between them
    :param document: LabelDocument where to write
    """
    document.clear()
    edit = getattr(document, 'edit_mode', False) # now it is compatible with QTextDocument too
    cursor = QtGui.QTextCursor(document)
    if isinstance(inode, IConstituentNode):
        if inode.alias:
            write_node_to_document(inode.alias, cursor)
        if inode.label:
            cursor.insertText('\n')
            write_node_to_document(inode.label, cursor)
        elif edit:
            cursor.insertText('\n')
        if inode.index:
            cursor.insertText('\n')
            cursor.insertText(inode.index)
        elif edit:
            cursor.insertText('\n')
        if inode.gloss:
            cursor.insertText('\n')
            write_node_to_document(inode.gloss, cursor)
        elif edit:
            cursor.insertText('\n')
        #todo:implement features


def run_command(command, cursor):
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
    # print('got command: %s' % command)


def write_node_to_document(n, cursor):
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
        run_command(n.command, cursor)
    for part in n.parts:
        if isinstance(part, ITextNode): # ITextNode includes also ICommandNodes and IConstituentNodes
            write_node_to_document(part, cursor)
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

