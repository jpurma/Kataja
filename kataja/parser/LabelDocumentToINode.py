from kataja.parser.INodes import ITextNode, IConstituentNode, ICommandNode
from PyQt5 import QtGui
from kataja.parser.LatexToINode import parse_field

__author__ = 'purma'


def find_command(cf, old_format, text):

    def add_command(inner, command, prefix='\\'):
        outer = ICommandNode(command=command, prefix=prefix)
        if inner:
            outer.append(inner)
        else:
            outer.append(text)
        return outer

    outer = None
    if cf.fontUnderline():
        outer = add_command(outer, 'underline')
    if cf.fontItalic():
        outer = add_command(outer, 'emph')
    if cf.fontWeight() == QtGui.QFont.Bold:
        outer = add_command(outer, 'textbf')
    if cf.fontStrikeOut():
        outer = add_command(outer, 'strikeout')
    if cf.fontCapitalization() == QtGui.QFont.SmallCaps:
        outer = add_command(outer, 'textsc')
    if cf.verticalAlignment() == QtGui.QTextCharFormat.AlignSubScript:
        outer = add_command(outer, '_', '')
    if cf.verticalAlignment() == QtGui.QTextCharFormat.AlignSuperScript:
        outer = add_command(outer, '^', '')
    if cf.fontOverline():
        outer = add_command(outer, 'overline')
    return outer


def rtf_line_to_textnode(line, doc):
    def charFormat(n):
        return doc.allFormats()[n].toCharFormat()
    node = ITextNode()
    for (style, text) in line:
        if style != 0:
            icommandnode = find_command(charFormat(style), charFormat(0), text)
            if icommandnode:
                node.append(icommandnode)
        else:
            node.append(text)
    return node

def latex_line_to_textnode(line, doc):
    return parse_field(''.join([text for cformat, text in line]))


def parse_labeldocument(doc):

    block = doc.begin()
    lines = []
    for i in range(0, doc.blockCount()):
        block = doc.findBlockByNumber(i)
        it = block.begin()
        block_finished = False
        line = []
        while not block_finished:
            frag = it.fragment()
            if not frag.isValid():
                print('invalid fragment')
                break
            format = frag.charFormatIndex()
            frags = frag.text().splitlines()
            # linebreaks create new blocks but they also extend the current fragment. So same piece of text can be
            # read several times. This can be avoided if we take only the first line of each fragment.
            f = frags[0].strip()
            if f:
                line.append((format, f))
            if it.atEnd():
                block_finished = True
                lines.append(line)
            else:
                it += 1

    bl = doc.block_order
    d = {'alias': '',
         'label': '',
         'index': '',
         'gloss': '',
         'features': []}

    if doc.raw_mode:
        line_parser = latex_line_to_textnode
    else:
        line_parser = rtf_line_to_textnode

    for i, line in enumerate(lines):
        if i < len(bl):
            key = bl[i]
        else:
            key = bl[-1]
        if key == 'feature':
            d['features'].append(line_parser(line, doc))
        else:
            d[key] = line_parser(line, doc)

    node = IConstituentNode(**d)

    print('Parsed LabelDocument into IConstituentNode: ', node.__repr__())
    return node
