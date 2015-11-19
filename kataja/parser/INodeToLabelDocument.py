__author__ = 'purma'

from PyQt5 import QtGui
from kataja.parser.INodes import ITextNode, ICommandNode, ITemplateNode
from kataja.LabelDocument import LabelDocument
import kataja.globals as g
from kataja.singletons import qt_prefs
from kataja.parser.latex_to_unicode import latex_to_unicode


def parse_inode(inode, document, options=None):
    """ Does what it says. Takes an existing LabelDocument to avoid problems
    with their garbage collection.
    :param inode: ITemplateNode, ICommandNode or ITextNode
    :param document: LabelDocument where to write
    :param options: flags to be delivered for actual parsing method
    """
    assert isinstance(document, LabelDocument)
    document.clear()
    if isinstance(inode, str):
        cursor = QtGui.QTextCursor(document)
        cursor.insertText(inode)
    elif isinstance(inode, ITemplateNode):
        parse_itemplatenode_for_viewing(inode, document, options)
    elif isinstance(inode, ITextNode):
        parse_itextnode(inode, document)
    else:
        print('what is inode?', type(inode))


def parse_itextnode(inode, document):
    cursor = QtGui.QTextCursor(document)
    write_node_to_document(inode, cursor)


def parse_itemplatenode_for_viewing(inode, document, options):
    """ Write inode to document, using the template stored with inode.
    :param inode: ITemplateNode
    :param document: LabelDocument
    """

    cursor = QtGui.QTextCursor(document)
    postponed = [None]
    has_text = False
    document.lines = []

    def write_subscript(index, cursor):
        old_format = QtGui.QTextCharFormat(cursor.charFormat())
        c = QtGui.QTextCharFormat()
        c.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)
        cursor.mergeCharFormat(c)
        write_node_to_document(index, cursor)
        cursor.setCharFormat(old_format)

    def write_field(field_name, cursor, has_text):
        d = inode.values[field_name]
        if not d.get('visible', True):
            return False
        v = d['value']
        if not v:
            return False
        align = d.get('align', 'newline')
        if align == 'newline':
            if has_text:
                cursor.insertBlock()
                document.lines.append(field_name)
        elif align == 'line-end':
            if not has_text:
                postponed[0] = field_name
                return False
        elif align == 'append':
            if has_text:
                cursor.insertText(' ')
        special = d.get('special', None)
        if special:
            if special == 'triangle':
                cursor.insertText('\n')
                return True
        style = d.get('style', 'normal')
        if style == 'normal':
            write_node_to_document(v, cursor)
        elif style == 'subscript':
            write_subscript(v, cursor)
        return True

    for field_name in inode.view_order:
        if postponed[0] and has_text:
            wrote_something = write_field(postponed[0], cursor, has_text)
            if wrote_something:
                postponed[0] = None
        wrote_something = write_field(field_name, cursor, has_text)
        if wrote_something and not has_text:
            has_text = True
            document.lines.append(field_name)


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


def write_node_to_document(n, cursor):
    """ Recursive node writer. Stores the current charformat, so when the end of formatting scope is reached,
    we can return to previous format.
    :param n: node or string
    :param cursor: cursor in document, this is the point where we write
    :return:
    """
    if not n:
        return
    if isinstance(n, ITextNode):
        old_format = None
        if isinstance(n, ICommandNode) and n.command:
            old_format = QtGui.QTextCharFormat(cursor.charFormat())
            run_command(n.command, cursor)
        for part in n.parts:
            if isinstance(part, ITextNode):  # ITextNode is parent class for
            # other INodes
                write_node_to_document(part, cursor)
            else:
                cursor.insertText(part)
        if old_format:
            cursor.setCharFormat(old_format)
    elif isinstance(n, list):
        for part in n:
            if isinstance(part, ITextNode):  # ITextNode is parent class for
            # other INodes
                write_node_to_document(part, cursor)
            else:
                cursor.insertText(part)
    else:
        cursor.insertText(n)

