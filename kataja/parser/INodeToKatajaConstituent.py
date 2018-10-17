__author__ = 'purma'
import kataja.globals as g
from kataja.parser.INodes import IParserNode, ITextNode
from kataja.saved.movables.nodes.ConstituentNode import ConstituentNode
from kataja.singletons import ctrl
from kataja.parser.SuperParser import SuperParser


class INodeToKatajaConstituent:
    """ INodeParser relies on a chain of parser components where the strings are parsed into
     intermediary nodes (INodes) and these can be more easily turned into Constituents,
     ConstituentNodes and their various text elements (RTF documents, raw text, stripped text).
    The benefit of this approach is that parsing raw strings to INodes can be used as well
     with text elements that require parsing LaTeX to Rich Text Format or HTML.
     If the raw strings are stored with nodes, INodes can be easily recreated and translated when required.
    """

    def __init__(self, forest):
        """ Parsers have own lexicons to allow referencing to parsed objects """
        self.local_lexicon = {}
        self._definitions = {}
        self.forest = forest
        self.parser = None
        self.should_add_to_scene = True
        self.temp_tree = None

    # @time_me
    #IParserNode(parts=[
    #    IParserNode(parts=[IParserNode(parts=[IParserNode(label_rows=['Cynth']), IParserNode(label_rows=['Daff'])])],
    #                label_rows=['Boris'])], label_rows=['Adolf'])

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
        result = [self.inode_to_constituentnode(inode) for inode in self.parser.nodes]
        self.should_add_to_scene = old_should_add
        return result

    def get_root_word(self, inode):
        if not inode:
            return ''
        if isinstance(inode, ITextNode):
            for part in inode.parts:
                return str(part)
        else:
            return str(inode)

    def inode_to_constituentnode(self, inode):
        """

        :param inode:
        :return:
        """
        if isinstance(inode, IParserNode):
            cnode = self.parsernodes_to_constituentnodes(inode)
        elif isinstance(inode, ITextNode):
            cnode = self.textnode_to_constituentnode(inode)
        return cnode

    def textnode_to_constituentnode(self, tnode):
        """

        :param node:
        :return:
        """
        cn = self.forest.drawing.create_node(label=tnode, node_type=g.CONSTITUENT_NODE)
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
        cn = f.drawing.create_node()
        if parsernode.has_triangle:
            assert not children
            child = self.textnode_to_constituentnode(parsernode.has_triangle.to_text_node())
            children.append(child)
            child.triangle_stack = [cn]
            cn.triangle_stack = [cn]
        if children:
            children.reverse()
            direction = g.LEFT
            if len(children) == 1:
                direction = g.NO_ALIGN
            for child in children:
                f.drawing.connect_node(parent=cn, child=child, direction=direction)
                direction = g.RIGHT
        cn.load_values_from_parsernode(parsernode)
        cn.update_label()
        return cn
