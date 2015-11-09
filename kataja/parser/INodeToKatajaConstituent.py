__author__ = 'purma'

from kataja.parser.BaseParser import BaseParser
from kataja.parser.LatexToINode import parse
from kataja.parser.INodes import ITemplateNode
from kataja.singletons import ctrl
from kataja.nodes.BaseConstituentNode import BaseConstituentNode
import kataja.globals as g


class INodeToKatajaConstituent(BaseParser):
    """ INodeParser relies on a chain of parser components where the strings
    are parsed into
     intermediary nodes (INodes) and these can be more easily turned into
     Constituents,
     ConstituentNodes and their various text fields (RTF documents, raw text,
     stripped text).
    The benefit of this approach is that parsing raw strings to INodes can be
    used as well
     with text fields that require parsing LaTeX to Rich Text Format or HTML.
     If the raw
     strings are stored with nodes, INodes can be easily recreated and
     translated when required.
    """
    # @time_me
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
            result = [self.parse_inode_into_tree(inode) for inode in inodes]
        else:
            result = self.parse_inode_into_tree(inodes)
        self.should_add_to_scene = old_should_add
        return result

    def parse_inode_into_tree(self, inode):
        """ Parses inode into constituentnodes, but prepare a temporary trees that can be assigned
        for created nodes so they don't each end up creating their own trees or get lost.
        :param inode:
        :return:
        """
        self.forest.temp_tree = None
        result = self.inode_to_constituentnodes(inode)
        if self.forest.temp_tree:
            self.forest.temp_tree.rebuild()
        return result

    def inode_to_constituentnodes(self, inode):
        """ Recursively turn ITemplateNodes into Constituents supported by syntax
        and further into
         Kataja's ConstituentNodes.
        :param inode: should be ITemplateNode.
        :param forest: forest where ConstituentNodes will be added
        :return: the root ConstituentNode
        """
        if isinstance(inode, ITemplateNode):
            children = []
            if inode.parts:
                right_first = reversed(inode)
                for nnode in right_first:
                    child = self.inode_to_constituentnodes(nnode)
                    if child and isinstance(child, BaseConstituentNode):
                        children.append(child)
            f = self.forest
            constituent = ctrl.Constituent(str(hash(inode)))
            cn = f.create_node(synobj=constituent)
            if not f.temp_tree:
                f.temp_tree = f.create_tree_for(cn)
            else:
                cn.add_to_tree(f.temp_tree)
            if inode.parts:
                f.add_merge_counter(cn)
            else:
                f.add_select_counter(cn)
            cn._inode = inode
            children.reverse()
            direction = g.LEFT
            if len(children) == 1:
                direction = g.NO_ALIGN
            for child in children:
                constituent.add_part(child.syntactic_object)
                f.connect_node(parent=cn, child=child, direction=direction)
                direction = g.RIGHT
            cn.impose_order_to_inode()
            cn.update_values_from_inode()
            cn.update_label()
            f.derivation_steps.save_and_create_derivation_step()
            return cn
        else:
            print('failing here')
