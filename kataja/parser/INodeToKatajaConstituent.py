from kataja.utils import time_me

__author__ = 'purma'

from kataja.parser.BaseParser import BaseParser
from kataja.parser.LatexToINode import parse
from kataja.parser.INodes import IConstituentNode, ITextNode, ICommandNode
from kataja.parser import INodeToLatex
from kataja.singletons import ctrl
from kataja.ConstituentNode import ConstituentNode
import kataja.globals as g


class INodeToKatajaConstituent(BaseParser):
    """ INodeParser relies on a chain of parser components where the strings are parsed into intermediary nodes (INodes)
    and these can be more easily turned into Constituents, ConstituentNodes and their various text fields
    (RTF documents, raw text, stripped text).
    The benefit of this approach is that parsing raw strings to INodes can be used as well with text fields that
    require parsing LaTeX to Rich Text Format or HTML. If the raw strings are stored with nodes, INodes can be easily
    recreated and translated when required.
    """
    #@time_me
    def parse_into_forest(self, string):
        """ Parse the text as new nodes in the current forest.

        :param string:
        """
        if not string:
            return None
        old_should_add = self.should_add_to_scene
        self.should_add_to_scene = True
        # the heavy work is done in LatexToINode ###
        inodes = parse(string)
        # done.
        if isinstance(inodes, list):
            result = [inode_to_constituentnodes(x, self.forest) for x in inodes]
        else:
            result = inode_to_constituentnodes(inodes, self.forest)
        self.should_add_to_scene = old_should_add
        return result

#@time_me
def inode_to_constituentnodes(inode, forest):
    """ Recursively turn IConstituentNodes into Constituents supported by syntax and further into
     Kataja's ConstituentNodes.
    :param inode: should be IConstituentNode.
    :param forest: forest where ConstituentNodes will be added
    :return: the root ConstituentNode
    """
    if isinstance(inode, IConstituentNode):
        children = []
        if inode.parts:
            right_first = reversed(inode)
            for nnode in right_first:
                child = inode_to_constituentnodes(nnode, forest)
                if child and isinstance(child, ConstituentNode):
                    children.append(child)
        if inode.features:
            # todo: features here
            print('Needs to create features from:', inode.features)
        constituent = ctrl.Constituent(inode.label)
        constituent.index = inode.index
        constituent.alias = inode.alias
        if inode.parts:
            result_of_merge = True
            result_of_select = False
        else:
            result_of_merge = False
            result_of_select = True
        cn = forest.create_node_from_constituent(constituent,
                                                      result_of_merge=result_of_merge,
                                                      result_of_select=result_of_select)
        cn.gloss = inode.gloss
        cn.features = inode.features

        if len(children) == 2:
            left = children[1]
            right = children[0]
            constituent.left = left.syntactic_object
            constituent.right = right.syntactic_object
            forest._connect_node(parent=cn, child=left, direction=g.LEFT)
            forest._connect_node(parent=cn, child=right, direction=g.RIGHT)

        # fixme: monochild
        elif len(children) == 1:
            left = children[0]
            constituent.left = left.syntactic_object
            forest._connect_node(parent=cn, child=left, direction=g.LEFT)

        cn.update_label()
        forest.derivation_steps.save_and_create_derivation_step()
        print([constituent])
        return cn


def update_constituentnode_fields(constituentnode, inode):
    if not inode:
        print("Updating constituent node %s, but no inode to update with" % constituentnode)
        return
    if constituentnode.alias != inode.alias:
        constituentnode.alias = inode.alias
    if constituentnode.label != inode.label:
        constituentnode.label = inode.label
    if constituentnode.gloss != inode.gloss:
        constituentnode.gloss = inode.gloss
    constituentnode.update_label()
    #todo: handling of features




