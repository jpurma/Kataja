# coding=utf-8
"""
CommentNode is a non-functional node for freeform text
"""
#############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from kataja.Node import Node, NodeModel
from kataja.globals import ARROW, COMMENT_NODE
from kataja.singletons import ctrl
from kataja.parser.INodes import ITextNode
from kataja.parser.LatexToINode import parse_field


color_map = {'tense': 0, 'person': 2, 'number': 4, 'case': 6, 'unknown': 3}

class CommentNodeModel(NodeModel):

    def __init__(self, host):
        super().__init__(host)


class CommentNode(Node):
    """ Node to display comments, annotations etc. syntactically inert information """
    width = 20
    height = 20
    default_edge_type = ARROW
    node_type = COMMENT_NODE

    def __init__(self, text=''):
        if not hasattr(self, 'model'):
            self.model = CommentNodeModel(self)
        Node.__init__(self)
        self.label = text
        self.use_physics = False


    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
            1st wave creates the objects and calls __init__, and then iterates through and sets the values.
            2nd wave calls after_inits for all created objects. Now they can properly refer to each other and know their
                values.
        :return: None
        """
        print("CommentNode after_init called")
        self.update_label()
        self.update_bounding_rect()
        self.update_visibility()
        # !fixme: is there a good reason for storing the object only in after_init???
        self.model.announce_creation()
        ctrl.forest.store(self)

    @property
    def hosts(self):
        """ A comment can be associated with nodes. The association uses the general connect/disconnect mechanism, but
        'hosts' is a shortcut to get the nodes.
        :return: list of Nodes
        """
        return self.get_parents(edge_type=ARROW)


    @property
    def text(self):
        """ The text of the comment. Uses the generic node.label as storage.
        :return: str or ITextNode
        """
        return self.model.label

    @text.setter
    def text(self, value):
        """ The text of the comment. Uses the generic node.label as storage.
        :param value: str or ITextNode
        """
        self.label = value

    def update_colors(self):
        """
        Deprecated for now? Does nothing, overrides, but doesn't call Node's update_colors.
        """
        pass
        # self.color = colors.drawing2
        # if self._label_complex:
        # self._label_complex.setDefaultTextColor(colors.drawing2)

    def __str__(self):
        return 'comment: %s' % self.text

    @property
    def as_inode(self):
        """ INode representation of the whole CommentNode
        :return: INodes or str or tuple of them
        """
        if self._inode_changed:
            if isinstance(self.label, ITextNode):
                self._inode = self.label
            else:
                self._inode = parse_field(self.label)
            print('comment node inode is: ', self._inode)
            self._inode_changed = False
        return self._inode