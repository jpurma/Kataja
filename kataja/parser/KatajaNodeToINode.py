from kataja.parser.INodes import INode, IConstituentNode
from kataja.parser.LatexToINode import parse_field
import kataja.globals as g

__author__ = 'purma'


def node_to_inode(node, children=False):
    """ Turn Kataja Node into INodes, including Label
    :param node: Node to turned into INodes
    :param children: recursively turn children too (don't overdo this)
    :return: INode
    """
    inode = INode()
    label = parse_field(node.label)
    inode.add_label(label)
    if children:
        for child in node.children():
            if child.__class__.type == g.CONSTITUENT_NODE:
                ichild = constituentnode_to_iconstituentnode(child, children=True)
            else:
                ichild = node_to_inode(child, children=True)
            inode.add_part(ichild)
    return inode


def constituentnode_to_iconstituentnode(node, children=False):
    """ Turn Kataja Node into IConstituentNodes, including Alias, Label, Gloss, Features, Index etc...
    :param node: ConstituentNode to turned into IConstituentNodes
    :param children: recursively turn children too (don't overdo this)
    :return: IConstituentNode
    """
    inode = IConstituentNode()
    alias = parse_field(node.alias)
    inode.add_alias(alias)
    label = parse_field(node.label)
    inode.add_label(label)
    inode.add_index(node.index)
    gloss = parse_field(node.gloss)
    inode.add_gloss(gloss)
    # todo: features need to be reimplemented / thought out
    if children:
        for child in node.children():
            if child.__class__.type == g.CONSTITUENT_NODE:
                ichild = constituentnode_to_iconstituentnode(child, children=True)
            else:
                ichild = node_to_inode(child, children=True)
            inode.add_part(ichild)
    return inode
