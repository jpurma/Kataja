from kataja.utils import time_me

__author__ = 'purma'

from kataja.parser.BaseParser import BaseParser
from kataja.parser.LatexToINode import parse
from kataja.parser.INodes import IConstituentNode, ITextNode, ICommandNode
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
        trans_nodes = parse(string)
        # done.
        if isinstance(trans_nodes, list):
            result = [self.node_to_constituentnodes(x) for x in trans_nodes]
        else:
            result = self.node_to_constituentnodes(trans_nodes)
        self.should_add_to_scene = old_should_add
        return result

    #@time_me
    def node_to_constituentnodes(self, node):
        """ Recursively turn IConstituentNodes into Constituents supported by syntax and further into
         Kataja's ConstituentNodes.
        :param node: should be IConstituentNode.
        :return: the root ConstituentNode
        """
        if isinstance(node, IConstituentNode):
            children = []
            if node.parts:
                right_first = list(node.parts)
                right_first.reverse()
                for nnode in right_first:
                    child = self.node_to_constituentnodes(nnode)
                    if child and isinstance(child, ConstituentNode):
                        children.append(child)
            if isinstance(node.label, ITextNode):
                label = node.label.raw_string
            else:
                label = node.label
            if isinstance(node.alias, ITextNode):
                alias = node.alias.raw_string
            else:
                alias = node.alias
            if isinstance(node.gloss, ITextNode):
                gloss = node.gloss.raw_string
            else:
                gloss = node.gloss
            if node.features:
                print('Needs to create features from:', node.features)
            index = node.index
            constituent = ctrl.Constituent(label)
            constituent.index = index
            constituent.alias = alias
            if node.parts:
                result_of_merge = True
                result_of_select = False
            else:
                result_of_merge = False
                result_of_select = True
            cn = self.forest.create_node_from_constituent(constituent,
                                                          result_of_merge=result_of_merge,
                                                          result_of_select=result_of_select)
            cn.gloss = gloss

            if len(children) == 2:
                left = children[1]
                right = children[0]
                self.forest._connect_node(parent=cn, child=left, direction=g.LEFT)
                self.forest._connect_node(parent=cn, child=right, direction=g.RIGHT)

            elif len(children) == 1:
                self.forest._connect_node(parent=cn, child=children[0], direction=g.LEFT)

            cn.update_label()
            self.forest.derivation_steps.save_and_create_derivation_step()

            return cn







