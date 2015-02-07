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


def find_format_diff(new_format, old_format):
    diffs = []
    for command, qmethod in formats.items():
        new = getattr(new_format, qmethod)()
        old = getattr(old_format, qmethod)()
        if new != old:
            diffs.append((command, new, old))
    return diffs



def parse_fragment(frag, old_format, node_stack, open_tags):
    current_node = node_stack[-1]
    new_format = frag.charFormat()
    if new_format != old_format:
        diffs = find_format_diff(new_format, old_format)
        print('found diffs: ', diffs)
        # diffs have to be analyzed if they tell about closing a tag or opening one
        # problem is that format change between two fragments can be because of several commands applied at once
        openings = []
        closings = []
        # close those tags that need to be closed before starting new ones
        # (otherwise the new tag may immediately get closed)
        previous_size = len(open_tags) + 1
        while 0 < len(open_tags) < previous_size:
            print('finding tags to close')
            previous_size = len(open_tags)
            for command, new_value, old_value in diffs:
                previous_command, previous_value = open_tags[-1]
                if command == previous_command and new_value == previous_value:
                    # effectively we are closing a tag -- forgetting about current tag and moving to tag below it
                    node_stack.pop()
                    closings.append((command, new_value))
                    current_node = node_stack[-1]
                    open_tags.remove((command, new_value))
        for command, new_value in openings:
            if (command, new_value) in closings:
                continue
            open_tags.append((command, new_value))
            nnode = ICommandNode()
            nnode.command = command
            current_node.add_part(nnode)
            node_stack.append(nnode)
            current_node = nnode
    text = frag.text().strip()
    if text:
        current_node.add_part(text)
    return node_stack


def parse_block(block):
    it = block.begin()
    cformat = block.charFormat()
    default_format = {}
    for key, value in formats.items():
        default_format[key] = getattr(cformat, value)()
    print('Block: ', block.text())
    node_stack = []
    node = ITextNode()
    node_stack.append(node)
    open_tags = []
    while True:
        frag = it.fragment()
        print('Frag: ', frag.text())
        if frag.isValid():
            node_stack = parse_fragment(frag, cformat, node_stack, open_tags)
        if it.atEnd():
            break
        else:
            it += 1
    print('parsed block: ', node_stack[0])
    return node_stack[0]

def parse_labeldocument(doc):
    """

    :param doc: label
    :return:
    """
    node = IConstituentNode()
    bl = doc.block_order

    for i in range(0, doc.blockCount()):
        block = doc.findBlockByNumber(i)
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
    print('Parsed LabelDocument into IConstituentNode: ', node.__repr__())
    return node
