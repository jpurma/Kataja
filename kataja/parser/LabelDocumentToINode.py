from kataja.parser.INodes import ITextNode, IConstituentNode, ICommandNode
from PyQt5 import QtGui

__author__ = 'purma'

formats = {'underline': 'fontUnderline',
           'emph': 'fontItalic',
           'textbf': 'fontWeight',
           'overline': 'fontOverline',
           'valign': 'verticalAlignment',
           'strikeout': 'fontStrikeOut',
           'font': 'fontFamily',
           'textsc': 'fontCapitalization'}


def find_command(new_format, old_format, text):
    inner = None
    outer = None
    for command, qmethod in formats.items():
        new = getattr(new_format, qmethod)()
        old = getattr(old_format, qmethod)()
        if new != old:
            outer = ICommandNode(command=command)
            if inner:
                outer.append(inner)
            else:
                outer.append(text)
            inner = outer
    return outer


def line_to_textnode(line, doc):
    def charFormat(n):
        return doc.allFormats()[n].toCharFormat()
    node = ITextNode()
    for (style, text) in line:
        if style != 0:
            icommandnode = find_command(charFormat(style), charFormat(0), text)
            print(repr(icommandnode))
            if icommandnode:
                node.append(icommandnode)
        else:
            node.append(text)
    return node


def parse_labeldocument(doc):

    block = doc.begin()
    lines = []
    while block != doc.end():
        it = block.begin()
        block_finished = False
        line = []
        while not block_finished:
            frag = it.fragment()
            format = frag.charFormatIndex()
            frags = frag.text().splitlines()
            f = frags[0].strip()
            if f:
                line.append((format, f))
            if it.atEnd():
                block_finished = True
                lines.append(line)
            else:
                it += 1
        block = block.next()

    bl = doc.block_order
    d = {'alias': '',
         'label': '',
         'index': '',
         'gloss': '',
         'features': []}

    for i, line in enumerate(lines):
        key = bl[i]
        if key == 'feature':
            d['features'].append(line_to_textnode(line, doc))
        else:
            d[key] = line_to_textnode(line, doc)

    node = IConstituentNode(**d)

    print('Parsed LabelDocument into IConstituentNode: ', node.__repr__())
    return node
