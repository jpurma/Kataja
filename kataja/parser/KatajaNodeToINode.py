from kataja.parser.INodes import IFeatureNode, IConstituentNode
import kataja.globals as g

__author__ = 'purma'


def node_to_inode(node, children=False):
    """ Turn Kataja Node (generic Node, not ConstituentNode) into INodes, including Label
    :param node: Node to turned into INodes
    :param children: recursively turn children too (don't overdo this)
    :return: INode
    """
    inode = IFeatureNode(label=node.label)
    if children:
        for child in node.children():
            if child.__class__.type == g.CONSTITUENT_NODE:
                # well this shouldn't happen, but let's be agnostic here
                ichild = constituentnode_to_iconstituentnode(child, children=True)
            else:
                ichild = node_to_inode(child, children=True)
            inode.append(ichild)
    return inode


def constituentnode_to_iconstituentnode(node, children=False):
    """ Turn Kataja Node into IConstituentNodes, including Alias, Label, Gloss, Features, Index etc...
    :param node: ConstituentNode to turned into IConstituentNodes
    :param children: recursively turn children too (don't overdo this)
    :return: IConstituentNode
    """
    inode = IConstituentNode(alias=node.alias,
                             label=node.label,
                             index=node.index,
                             gloss=node.gloss,
                             features=node.features)
    # todo: features need to be reimplemented / thought out
    if children:
        for child in node.children():
            if child.__class__.type == g.CONSTITUENT_NODE:
                ichild = constituentnode_to_iconstituentnode(child, children=True)
            else:
                ichild = node_to_inode(child, children=True)
            inode.append(ichild)
    return inode
