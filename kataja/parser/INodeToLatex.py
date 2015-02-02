from kataja.parser.INodes import ICommandNode, ITextNode

__author__ = 'purma'

#todo: special characters, escapes and one character commands

def parse_inode_for_field(inode):
    """ Turn INodes into LaTeX strings. This method is limited to handle only ITextNodes and ICommandNodes.
    :param inode:
    :return:
    """
    s = []
    def parse(inode):
        if isinstance(inode, ICommandNode):
            s.append(inode.command)
            if not inode.parts:
                return
            s.append('{')
            for part in inode.parts:
                parse(part)
            s.append('}')
        elif isinstance(inode, ITextNode):
            for part in inode.parts:
                parse(part)
        else:
            s.append(inode)

    parse(inode)
    return ''.join(s)

def parse_inode(inode):
    """ General INode parser, parses IConstituentNodes all the way to LaTeX QTrees
    :param inode:
    :return:
    """
    s = ''
    return s