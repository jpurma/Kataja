from kataja.parser.INodes import ITextNode, IConstituentNode
from PyQt5 import QtGui

__author__ = 'purma'


def parse_fragment(frag):
    print('Fragment: ', frag.text())
    return frag.text()

def parse_block(block):
    it = block.begin()
    print('Block: ', block.text())
    node = ITextNode()
    while not it.atEnd():
        it += 1
        frag = it.fragment()
        if frag.isValid():
            node.add_part(parse_fragment(frag))
    return node

def parse_labeldocument(doc):
    """

    :param doc: label
    :return:
    """
    node = IConstituentNode()
    bl = doc.block_order

    for i in range(0, doc.blockCount()):
        block = doc.findBlock(i)
        if i < len(bl):
            block_type = bl[i]
        else:
            block_type = bl[-1]
        print('block type: ', block_type)
        if block_type == 'alias':
            inode = parse_block(block)
            node.add_alias(inode)
        elif block_type == 'label':
            inode = parse_block(block)
            node.add_label(inode)
        elif block_type == 'index':
            node.add_index(block.text())
        elif block_type == 'gloss':
            inode = parse_block(block)
            node.add_gloss(inode)
        elif block_type == 'feature':
            inode = parse_block(block)
            node.add_feature(inode)
    print('Parsed LabelDocument into IConstituentNode: ', node)
    return node
