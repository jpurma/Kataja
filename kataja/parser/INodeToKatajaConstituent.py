__author__ = 'purma'

import kataja.globals as g
from kataja.BaseConstituentNode import BaseConstituentNode
from kataja.parser.BaseParser import BaseParser
from kataja.parser.INodes import IParserNode, ITextNode
from kataja.parser.LatexToINode import parse
from kataja.singletons import ctrl, classes


class INodeToKatajaConstituent(BaseParser):
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
    # @time_me
    def parse_into_forest(self, string, simple_parse=False):
        """ Parse the text as new nodes in the current forest.

        :param string:
        :param simple_parse: If several words are given, merge them together
        """
        if not string:
            return None
        old_should_add = self.should_add_to_scene
        self.should_add_to_scene = True
        # the heavy work is done in LatexToINode ###
        parsernodes = parse(string)
        # done.
        if isinstance(parsernodes, list):
            if simple_parse:
                result = [self.parsernodes_to_constituentnodes(parsernode) for parsernode in
                          parsernodes]
                if len(result) > 1:
                    right = result.pop()
                    while result:
                        left = result.pop()
                        left.head = left
                        right = ctrl.forest.create_merger_node(left, right, new=left, head=left)
                    result = right
            else:
                result = [self.parsernodes_into_tree(parsernode) for parsernode in parsernodes]
        else:
            result = self.parsernodes_into_tree(parsernodes)
        self.should_add_to_scene = old_should_add
        return result

    def parsernodes_into_tree(self, parsernode):
        """ Parses inode into constituentnodes, but prepare a temporary trees that can be assigned
        for created nodes so they don't each end up creating their own trees or get lost.
        :param inode:
        :return:
        """
        self.forest.temp_tree = None
        result = self.parsernodes_to_constituentnodes(parsernode)
        if self.forest.temp_tree:
            self.forest.temp_tree.rebuild()
        return result

    def parsernodes_to_constituentnodes(self, parsernode):
        """ Recursively turn ITemplateNodes into Constituents supported by syntax
        and further into
         Kataja's ConstituentNodes.
        :param inode: should be ITemplateNode.
        :param forest: forest where ConstituentNodes will be added
        :return: the root ConstituentNode
        """
        f = self.forest
        if isinstance(parsernode, IParserNode):
            children = []
            if parsernode.parts:
                right_first = reversed(parsernode)
                for nnode in right_first:
                    child = self.parsernodes_to_constituentnodes(nnode)
                    if child and isinstance(child, BaseConstituentNode):
                        children.append(child)
            constituent = classes.Constituent(str(hash(parsernode)))
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
            f.derivation_steps.save_and_create_derivation_step()
            return cn
        elif isinstance(parsernode, ITextNode):
            constituent = classes.Constituent(str(hash(parsernode)))
            cn = f.create_node(synobj=constituent)
            cn.label = parsernode
            cn.update_label()
            return cn
        else:
            print('failing here: ', parsernode, type(parsernode))
