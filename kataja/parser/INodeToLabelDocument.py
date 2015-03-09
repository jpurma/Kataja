__author__ = 'purma'

from PyQt5 import QtGui, QtCore
from kataja.parser.INodes import ITextNode, ICommandNode, IConstituentNode, IFeatureNode, IGenericNode
from kataja.LabelDocument import LabelDocument
import kataja.globals as g
from kataja.singletons import qt_prefs, prefs
from kataja.parser.latex_to_unicode import latex_to_unicode
from kataja.parser.INodeToLatex import parse_inode_for_field


def parse_inode(inode, document, gloss_in_view=True, features_in_view=True):
    """ Does what it says. Takes an existing LabelDocument to avoid problems with their garbage collection.
    :param inode: IConstituentNode or IFeatureNode
    :param document: LabelDocument where to write
    :param gloss_in_view:
    :param features_in_view:
    """
    assert (isinstance(document, LabelDocument))
    document.clear()
    if isinstance(inode, IFeatureNode):
        parse_ifeaturenode(inode, document)
    elif isinstance(inode, IConstituentNode):
        if document.edit_mode:
            parse_iconstituentnode_for_editing(inode, document)
        else:
            parse_iconstituentnode_for_viewing(inode, document, gloss_in_view, features_in_view)
    elif isinstance(inode, ITextNode):
        parse_itextnode(inode, document)
    else:
        print('skipping parse_inode, ', inode, type(inode))


def parse_itextnode(inode, document):
    cursor = QtGui.QTextCursor(document)
    write_node_to_document(inode, cursor, document.raw_mode)


def parse_iconstituentnode_for_viewing(inode, document, gloss_in_view=True, features_in_view=True):
    """ Show only those fields that have values and add index as subscript to either alias or label
    :param inode: IConstituentNode
    :param document: LabelDocument
    :param gloss_in_view: include gloss in label complex (alternative is to have it as free floating node)
    :param features_in_view: include features in label complex (alternative is to have them as free floating nodes)
    :return:
    """

    def write_index(index, cursor):
        old_format = QtGui.QTextCharFormat(cursor.charFormat())
        c = QtGui.QTextCharFormat()
        c.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)
        cursor.mergeCharFormat(c)
        write_node_to_document(index, cursor)
        cursor.setCharFormat(old_format)

    cursor = QtGui.QTextCursor(document)
    actual_block_order = []
    first = True
    index_row = -1
    if inode.index:
        if inode.alias:
            index_row = 0
        elif inode.label:
            index_row = 1
        else:
            index_row = 0
    for block_id in document.block_order:
        if block_id == 'alias':
            if inode.alias:
                if not first:
                    cursor.insertBlock()
                write_node_to_document(inode.alias, cursor)
                actual_block_order.append(block_id)
                first = False
            if index_row == 0:
                write_index(inode.index, cursor)
        elif block_id == 'label':
            if inode.label:
                if not first:
                    cursor.insertBlock()
                write_node_to_document(inode.label, cursor)
                actual_block_order.append(block_id)
                first = False
            if index_row == 1:
                write_index(inode.index, cursor)
        elif block_id == 'gloss' and not prefs.gloss_nodes:
            if inode.gloss and gloss_in_view:
                if not first:
                    cursor.insertBlock()
                write_node_to_document(inode.gloss, cursor)
                actual_block_order.append(block_id)
                first = False
        elif block_id == 'features' and not prefs.feature_nodes:
            if inode.features and features_in_view:
                if not first:
                    cursor.insertBlock()

                print(inode.features)
                for item in inode.features.values():
                    write_node_to_document(item, cursor)
                    write_node_to_document(' ', cursor)
                actual_block_order.append(block_id)
                first = False
    document.block_order = actual_block_order


def parse_iconstituentnode_for_editing(inode, document):
    """ Write all fields into one document for easier editing -- if field is empty, leave a blank row as a placeholder
    :param inode: IConstituentNode
    :param document: LabelDocument
    :return:
    """
    # o = QtGui.QTextOption()
    # o.setFlags(QtGui.QTextOption.ShowLineAndParagraphSeparators |
    # QtGui.QTextOption.AddSpaceForLineAndParagraphSeparators)
    #document.setDefaultTextOption(o)
    cursor = QtGui.QTextCursor(document)
    first = document.block_order[0]
    raw = document.raw_mode
    for block_id in document.block_order:
        if block_id == 'alias':
            if block_id != first:
                cursor.insertBlock()
            if inode.alias:
                write_node_to_document(inode.alias, cursor, raw)
        elif block_id == 'label':
            if block_id != first:
                cursor.insertBlock()
            if inode.label:
                write_node_to_document(inode.label, cursor, raw)
        elif block_id == 'index':
            if block_id != first:
                cursor.insertBlock()
            if inode.index:
                write_node_to_document(inode.index, cursor, raw)
        elif block_id == 'gloss':
            if block_id != first:
                cursor.insertBlock()
            if inode.gloss:
                write_node_to_document(inode.gloss, cursor, raw)
        elif block_id == 'features':
            if block_id != first:
                cursor.insertBlock()
            if inode.features:
                write_node_to_document(inode.features, cursor, raw)


def parse_ifeaturenode(inode, document):
    """ Write feature into document. At this point it only has single field, label
    :param inode: IFeatureNode
    :param document: LabelDocument
    """
    cursor = QtGui.QTextCursor(document)
    if inode.family:
        write_node_to_document(inode.family, cursor)
        cursor.insertText(':')
    write_node_to_document(inode.key, cursor)
    if inode.value:
        cursor.insertText('=')
        write_node_to_document(inode.value, cursor)
    if inode.parts:
        cursor.insertText(' ')
        write_node_to_document(inode.parts, cursor)



def run_command(command, cursor):
    """
    :param command: latex command that may be translated to rtf formatting commands.
    :param cursor: here we write.
    :param doc: document, required for fetching e.g. font info.
    :return:
    """
    c = QtGui.QTextCharFormat()
    merge_format = True
    if command == 'emph' or command == 'textit':
        c.setFontItalic(True)
    elif command == 'textbf':
        c.setFont(qt_prefs.fonts[g.BOLD_FONT])
        c.setFontWeight(QtGui.QFont.Bold)
    elif command == '^':
        c.setVerticalAlignment(QtGui.QTextCharFormat.AlignSuperScript)
    elif command == '_':
        c.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)
        c.setFontItalic(True)
    elif command == '$':
        merge_format = False
    elif command == 'underline':
        c.setFontUnderline(True)
    elif command == 'strikeout':
        c.setFontStrikeOut(True)
    elif command == 'textsc':
        c.setFontCapitalization(QtGui.QFont.SmallCaps)
    elif command == 'overline':
        c.setFontOverline(True)
    elif command in latex_to_unicode:
        cursor.insertText(latex_to_unicode[command][0])
        merge_format = False
    if merge_format:
        cursor.mergeCharFormat(c)


def write_node_to_document(n, cursor, raw=False):
    """ Recursive node writer. Stores the current charformat, so when the end of formatting scope is reached,
    we can return to previous format.
    :param n: node or string
    :param cursor: cursor in document, this is the point where we write
    :param raw: write as latex instead of RTF
    :return:
    """
    if not n:
        return
    if raw:
        cursor.insertText(parse_inode_for_field(n))
        return
    if isinstance(n, ITextNode):
        old_format = None
        if isinstance(n, ICommandNode) and n.command:
            old_format = QtGui.QTextCharFormat(cursor.charFormat())
            run_command(n.command, cursor)
        for part in n.parts:
            if isinstance(part, ITextNode):  # ITextNode includes also ICommandNodes and IConstituentNodes
                write_node_to_document(part, cursor)
            else:
                cursor.insertText(part)
        if old_format:
            cursor.setCharFormat(old_format)
    elif isinstance(n, list):
        for part in n:
            if isinstance(part, ITextNode):  # ITextNode includes also ICommandNodes and IConstituentNodes
                write_node_to_document(part, cursor)
            else:
                cursor.insertText(part)
    else:
        cursor.insertText(n)

