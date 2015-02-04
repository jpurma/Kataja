from kataja.parser.INodes import ICommandNode, ITextNode

__author__ = 'purma'

#todo: special characters, escapes and one character commands

def parse_inode_for_field(inode):
    """ Turn INodes into LaTeX strings. This method is limited to handle only ITextNodes and ICommandNodes.
    :param inode:
    :return:
    """
    def parse(jnode):
        r = []
        if isinstance(jnode, ICommandNode):
            r.append(jnode.prefix)
            r.append(jnode.command)
            if not jnode.parts:
                return ''.join(r)
            r.append('{')
            for part in jnode.parts:
                r.append(parse(part))
            r.append('}')
        elif isinstance(jnode, ITextNode):
            for part in jnode.parts:
                r.append(parse(part))
        else:
            r.append(jnode)
        return ''.join(r)

    s = parse(inode)
    return s

def parse_inode(inode):
    """ General INode parser, parses IConstituentNodes all the way to LaTeX QTrees
    :param inode:
    :return:
    """
    s = ''
    return s