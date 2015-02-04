
__author__ = 'purma'

from PyQt5 import QtGui, QtCore
from kataja.parser.LatexToINode import ITextNode, ICommandNode, IConstituentNode
from kataja.LabelDocument import LabelDocument
from kataja.parser.latex_to_unicode import latex_to_unicode


def parse_inode(inode, document):
    """ Does what it says. Takes an existing LabelDocument to avoid problems with their garbage collection.
    :param inode: Node or nodes to be translated. If there are several, linebreak is added between them
    :param document: LabelDocument where to write
    """
    assert(isinstance(document, LabelDocument))
    document.clear()
    if not inode:
        return

    edit = document.edit_mode
    cursor = QtGui.QTextCursor(document)
    first = document.block_order[0]
    if edit:
        for block_id in document.block_order:
            if block_id == 'alias':
                if block_id != first:
                    cursor.insertBlock()
                if inode.alias:
                    write_node_to_document(inode.alias, cursor)
            elif block_id == 'label':
                if block_id != first:
                    cursor.insertBlock()
                if inode.label:
                    write_node_to_document(inode.label, cursor)
            elif block_id == 'index':
                if block_id != first:
                    cursor.insertBlock()
                if inode.index:
                    cursor.insertText(inode.index)
            elif block_id == 'gloss':
                if block_id != first:
                    cursor.insertBlock()
                if inode.gloss:
                    write_node_to_document(inode.gloss, cursor)
            elif block_id == 'features':
                if block_id != first:
                    cursor.insertBlock()
                if inode.features:
                    write_node_to_document(inode.features, cursor)
    else:
        actual_block_order = []
        first = True
        for block_id in document.block_order:
            if block_id == 'alias':
                if inode.alias:
                    if not first:
                        cursor.insertBlock()
                    write_node_to_document(inode.alias, cursor)
                    actual_block_order.append(block_id)
                    first = False
            elif block_id == 'label':
                if inode.label:
                    if not first:
                        cursor.insertBlock()
                    write_node_to_document(inode.label, cursor)
                    actual_block_order.append(block_id)
                    first = False
            elif block_id == 'index':
                if inode.index:
                    if not first:
                        cursor.insertBlock()
                    cursor.insertText(inode.index)
                    actual_block_order.append(block_id)
                    first = False
            elif block_id == 'gloss':
                if inode.gloss:
                    if not first:
                        cursor.insertBlock()
                    write_node_to_document(inode.gloss, cursor)
                    actual_block_order.append(block_id)
                    first = False
            elif block_id == 'features':
                if inode.features:
                    if not first:
                        cursor.insertBlock()
                    write_node_to_document(inode.features, cursor)
                    actual_block_order.append(block_id)
                    first = False
        document.block_order = actual_block_order

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

