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
from PyQt5 import QtGui, QtCore

import kataja.globals as g
from kataja.singletons import ctrl
from kataja.saved.movables.Node import Node


class CommentNode(Node):
    """ Node to display comments, annotations etc. syntactically inert information """
    width = 20
    height = 20
    node_type = g.COMMENT_NODE
    name = ('Comment', 'Comments')
    short_name = "ComNode"
    display = True
    is_syntactic = False
    can_be_in_groups = False
    visible_in_label = ['text']
    editable_in_label = ['text']
    display_styles = {'text': {'resizable': True,
                               'line_length': 24,
                               'text_align': g.LEFT_ALIGN}}
    editable = {'text': dict(name='',
                             prefill='comment',
                             tooltip='freeform text, invisible for processing',
                             input_type='textarea')}

    default_style = {'color': 'accent4',
                     'font': g.MAIN_FONT,
                     'font-size': 14}

    default_edge = {'id': g.COMMENT_EDGE,
                    'shape_name': 'linear',
                    'color': 'accent4',
                    'pull': 0,
                    'visible': True,
                    'arrowhead_at_start': True,
                    'arrowhead_at_end': False,
                    'labeled': False,
                    'name_pl': 'Comment arrows'}

    touch_areas_when_dragging = {g.DELETE_ARROW: {'condition': 'dragging_my_arrow'}}

    touch_areas_when_selected = {g.DELETE_ARROW: {'condition': 'has_arrow'}}

    def __init__(self, text='comment'):
        Node.__init__(self)
        if not text:
            text = 'comment'
        self.label = text
        self.physics_x = False
        self.physics_y = False
        self.pos_relative_to_host = -50, -50
        self.preferred_host = None

    @property
    def hosts(self):
        """ A comment can be associated with nodes. The association uses the general connect/disconnect mechanism, but
        'hosts' is a shortcut to get the nodes.
        :return: list of Nodes
        """
        return self.get_parents(edge_type=g.COMMENT_EDGE)


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

    def has_arrow(self):
        return bool(self.edges_down)

    def update_selection_status(self, selected):
        """

        :param selected:
        :return:
        """
        super().update_selection_status(selected)

    def dragging_my_arrow(self, dragged_type, dragged_item):
        return True

    def __str__(self):
        return 'comment: %s' % self.text

    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        if self.triangle:
            p = QtGui.QPen(self.contextual_color)
            p.setWidth(1)
            painter.setPen(p)
            self.paint_triangle(painter)
        if self.drag_data:
            p = QtGui.QPen(self.contextual_color)
            #b = QtGui.QBrush(ctrl.cm.paper())
            #p.setColor(ctrl.cm.hover())
            p.setWidth(1)
            painter.setPen(p)
            #painter.setBrush(self.drag_data.background)
            painter.drawRect(self.inner_rect)
            painter.setBrush(QtCore.Qt.NoBrush)


        elif self._hovering:
            p = QtGui.QPen(self.contextual_color)
            #p.setColor(ctrl.cm.hover())
            p.setWidth(1)
            painter.setPen(p)
            painter.drawRect(self.inner_rect)
        elif ctrl.pressed is self or ctrl.is_selected(self):
            p = QtGui.QPen(self.contextual_color)
            p.setWidth(1)
            painter.setPen(p)
            painter.drawRect(self.inner_rect)
        elif self.has_empty_label() and self.node_alone():
            p = QtGui.QPen(self.contextual_color)
            p.setStyle(QtCore.Qt.DotLine)
            p.setWidth(1)
            painter.setPen(p)
            painter.drawRect(self.inner_rect)

    def move(self, md):
        """ Override usual movement if comment is connected to some node. If so, try to keep the
        given position relative to that node.
        :return:
        """
        if self.preferred_host:
            x, y = self.preferred_host.current_scene_position
            dx, dy = self.pos_relative_to_host
            self.current_position = self.scene_position_to_tree_position((x + dx, y + dy))
            return False, False
        else:
            return super().move(md)

    def drop_to(self, x, y, recipient=None):
        """

        :param recipient:
        :param x:
        :param y:
        :return: action finished -message (str)
        """
        message = super().drop_to(x, y, recipient=recipient)
        if self.preferred_host:
            x, y = self.preferred_host.current_scene_position
            mx, my = self.current_scene_position
            self.pos_relative_to_host = mx - x, my - y
            message = "Adjusted comment to be at %s, %s relative to '%s'" % (mx - x, my - y,
                                                                             self.preferred_host)
        return message

    def on_connect(self, other):
        print('on_connect called, hosts:', self.hosts)
        if other in self.hosts:
            self.preferred_host = other
            x, y = other.current_scene_position
            mx, my = self.current_scene_position
            self.pos_relative_to_host = mx - x, my - y

    def on_disconnect(self, other):
        print('on_disconnect called')
        if other is self.preferred_host:
            for item in self.hosts:
                if item != other:
                    self.preferred_host = item
                    x, y = item.current_scene_position
                    mx, my = self.current_scene_position
                    self.pos_relative_to_host = mx - x, my - y
                    return
            self.preferred_host = None

    def can_connect_with(self, other):
        return other not in self.hosts

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # all same as Node
