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

from kataja.nodes.Node import Node
from kataja.globals import ARROW, COMMENT_NODE
import kataja.globals as g


class CommentNode(Node):
    """ Node to display comments, annotations etc. syntactically inert information """
    width = 20
    height = 20
    default_edge_type = ARROW
    node_type = COMMENT_NODE
    name = ('Comment', 'Comments')
    short_name = "ComNode"
    display = True

    visible = {'text': {'order': 3}}
    editable = {'text': dict(name='Comment', order=3, prefill='comment',
                              tooltip='freeform text, invisible for '
                                      'processing')}


    default_style = {'color': 'accent4', 'font': g.MAIN_FONT, 'font-size': 14,
                     'edge': g.COMMENT_EDGE}

    default_edge = {'id': g.COMMENT_EDGE,'shape_name': 'linear', 'color': 'accent4', 'pull': 0,
                    'visible': True, 'arrowhead_at_start': True, 'arrowhead_at_end': False,
                    'labeled': False}


    def __init__(self, text=''):
        Node.__init__(self)
        self.label = text
        self.use_physics = False

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
        return self.label

    @text.setter
    def text(self, value):
        """ The text of the comment. Uses the generic node.label as storage.
        :param value: str or ITextNode
        """
        self.label = value


    def __str__(self):
        return 'comment: %s' % self.text

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # all same as Node
