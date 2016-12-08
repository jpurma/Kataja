from utils import time_me

__author__ = 'purma'
import kataja.globals as g
from kataja.parser.INodes import IParserNode, ITextNode
from kataja.saved.movables.nodes.ConstituentNode import ConstituentNode
from kataja.singletons import ctrl
from kataja.parser.SuperParser import SuperParser
from kataja.utils import time_me


class INodeToKatajaConstituent:
    """ INodeParser relies on a chain of parser components where the strings
    are parsed into
     intermediary nodes (INodes) and these can be more easily turned into
     Constituents,
     ConstituentNodes and their various text elements (RTF documents, raw text,
     stripped text).
    The benefit of this approach is that parsing raw strings to INodes can be
    used as well
     with text elements that require parsing LaTeX to Rich Text Format or HTML.
     If the raw
     strings are stored with nodes, INodes can be easily recreated and
     translated when required.
    """

    def __init__(self, forest):
        """ Parsers have own lexicons to allow referencing to parsed objects """
        self.local_lexicon = {}
        self._definitions = {}
        self.forest = forest
        self.parser = None
        self.should_add_to_scene = True

    # @time_me

    def simple_parse(self, string):
        """ Parse the text as merged nodes in the current forest.
        :param string:
        """
        if not string:
            return None
        old_should_add = self.should_add_to_scene
        self.should_add_to_scene = True
        # the heavy work is done in SuperParser ###
        self.parser = SuperParser(string)
        result = [self.inode_to_constituentnode(inode) for inode in
                  self.parser.nodes]
        if len(result) > 1:
            right = result.pop()
            while result:
                left = result.pop()
                left.set_projection(None)
                right = ctrl.forest.create_merger_node(left, right, new=left, head=left)
            result = right
        elif result:
            result = result[0]
        self.should_add_to_scene = old_should_add
        return result

    def string_into_forest(self, string):
        """ Parse the text as new nodes in the current forest.

        :param string:
        """
        if not string:
            return None
        old_should_add = self.should_add_to_scene
        self.should_add_to_scene = True
        # the heavy work is done in SuperParser ###
        self.parser = SuperParser(string)
        result = [self.inode_into_tree(inode) for inode in self.parser.nodes]
        self.should_add_to_scene = old_should_add
        return result

    def inode_into_tree(self, inode):
        """ Parses inode into constituentnodes, but prepare a temporary trees that can be assigned
        for created nodes so they don't each end up creating their own trees or get lost.
        :param inode:
        :return:
        """
        self.forest.temp_tree = None
        result = self.inode_to_constituentnode(inode)
        if self.forest.temp_tree:
            self.forest.temp_tree.rebuild()
        return result

    def inode_to_constituentnode(self, inode):
        """

        :param inode:
        :return:
        """
        if isinstance(inode, IParserNode):
            return self.parsernodes_to_constituentnodes(inode)
        elif isinstance(inode, ITextNode):
            return self.textnode_to_constituentnode(inode)

    def textnode_to_constituentnode(self, tnode):
        """

        :param node:
        :return:
        """
        constituent = ctrl.syntax.Constituent(str(hash(tnode)))
        cn = self.forest.create_node(synobj=constituent)
        cn.label = tnode
        cn.update_label()
        return cn

    def parsernodes_to_constituentnodes(self, parsernode):
        """ Recursively turn IParserNodes into Constituents supported by syntax
        and further into Kataja's ConstituentNodes.
        :param inode: should be IParserNode.
        :return: the root ConstituentNode
        """
        f = self.forest
        children = []
        if parsernode.parts:
            right_first = reversed(parsernode)
            for nnode in right_first:
                child = self.parsernodes_to_constituentnodes(nnode)
                if child and isinstance(child, ConstituentNode):
                    children.append(child)
        constituent = ctrl.syntax.Constituent()
        cn = f.create_node(synobj=constituent)
        if not f.temp_tree:
            f.temp_tree = f.create_tree_for(cn)
        else:
            cn.add_to_tree(f.temp_tree)
        if parsernode.parts:
            f.add_merge_counter(cn)
        else:
            f.add_select_counter(cn)
        children.reverse()
        direction = g.LEFT
        if len(children) == 1:
            direction = g.NO_ALIGN
        for child in children:
            constituent.add_part(child.syntactic_object)
            f.connect_node(parent=cn, child=child, direction=direction)
            direction = g.RIGHT
        cn.load_values_from_parsernode(parsernode)
        cn.update_label()
        #f.derivation_steps.save_and_create_derivation_step([cn])
        return cn
