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
from PyQt6 import QtGui, QtCore, QtWidgets

import kataja.globals as g
from kataja.SavedField import SavedField
from kataja.saved.movables.Node import Node
from kataja.singletons import ctrl
from kataja.uniqueness_generator import next_available_type_id


class CommentNode(Node):
    """ Node to display comments, annotations etc. syntactically inert information """
    __qt_type_id__ = next_available_type_id()
    width = 20
    height = 20
    node_type = g.COMMENT_NODE
    display_name = ('Comment', 'Comments')
    display = True
    is_syntactic = False
    can_be_in_groups = False
    resizable = True
    quick_editable = True
    editable_fields = {'label': dict(name='',
                                     prefill='comment',
                                     tooltip='freeform text, invisible for processing',
                                     input_type='expandingtext')}

    default_style = {'fancy': {'color_key': 'accent4',
                               'font_id': g.MAIN_FONT,
                               'font-size': 14,
                               'visible': True},
                     'plain': {'color_key': 'accent4',
                               'font_id': g.MAIN_FONT,
                               'font-size': 14,
                               'visible': True}
                     }

    default_edge = g.COMMENT_EDGE

    touch_areas_when_dragging = []
    touch_areas_when_selected = []

    def __init__(self, label='comment', forest=None):
        self.image_object = None
        Node.__init__(self, forest=forest)
        if not label:
            label = 'comment'
        self.label = label
        self.physics_x = False
        self.physics_y = False
        self.image_path = None
        self.image = None
        self.pos_relative_to_host = -50, -50
        self.preferred_host = None

    def after_init(self):
        Node.after_init(self)
        if self.user_size:
            w, h = self.user_size
            self.set_user_size(w, h)

    @property
    def hosts(self):
        """ A comment can be associated with nodes. The association uses the general connect/disconnect mechanism, but
        'hosts' is a shortcut to get the nodes.
        :return: list of Nodes
        """
        return self.get_parents(of_type=g.COMMENT_NODE)

    def label_as_editable_html(self):
        return 'label', as_html(self.label)

    def has_arrow(self):
        return bool(self.edges_down)

    def set_image_path(self, pixmap_path):
        if pixmap_path and (self.image_path != pixmap_path or not self.image):
            self.image_path = pixmap_path
            self.image = QtGui.QPixmap()
            # noinspection PyArgumentList
            success = self.image.load(pixmap_path)
            if success:
                if self.image_object:
                    print('removing old image object')
                    self.image_object.hide()
                    self.image_object.setParentItem(None)
                self.image_object = QtWidgets.QGraphicsPixmapItem(self.image, self)
                self.image_object.setPos(self.image.width() / -2, self.image.height() / -2)
                self.label = ''
                self.update_label_visibility()
                self.update_bounding_rect()
        else:
            self.image = None
            if self.image_object:
                print('removing old image object 2')
                self.image_object.hide()
                self.image_object.setParentItem(None)
            self.image_object = None

    def set_user_size(self, width, height):
        if width < 1 or height < 1:
            return
        self.user_size = (width, height)
        if self.image_object:
            scaled = self.image.scaled(width, height, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                       QtCore.Qt.TransformationMode.SmoothTransformation)
            self.image_object.prepareGeometryChange()
            self.image_object.setPixmap(scaled)
            self.image_object.setPos(-scaled.width() / 2, -scaled.height() / 2)
            # Update ui items around the label (or node hosting the label)
            ctrl.ui.update_position_for(self)

        self.label_object.resize_label()

    @staticmethod
    def dragging_my_arrow():
        return True

    def node_alone(self):
        return not (self.edges_down or self.edges_up)

    def __str__(self):
        return 'comment: %s' % self.label

    def _calculate_inner_rect(self, min_w=0, min_h=0):
        user_width, user_height = self.user_size if self.user_size is not None else (0, 0)
        label = self.image_object or self.label_object
        label_rect = label.boundingRect()
        label_w = label_rect.width()
        label_h = label_rect.height()
        self.label_rect = label_rect
        w = max((min_w, label_w, CommentNode.width, user_width))
        h = max((min_h, label_h, CommentNode.height, user_height))
        x = w / -2
        y = h / -2
        self.width = w
        self.height = h
        self._create_magnets(x, y, w, h)
        return QtCore.QRectF(x, y, w, h)

    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        p = QtGui.QPen(self.contextual_color())
        p.setWidth(1)
        if self.drag_data:
            painter.setPen(p)
            # painter.setBrush(self.drag_data.background)
            painter.drawRect(self.inner_rect)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)


        elif self.hovering:
            painter.setPen(p)
            painter.drawRect(self.inner_rect)
        elif ctrl.pressed is self or ctrl.is_selected(self):
            painter.setPen(p)
            painter.drawRect(self.inner_rect)
        elif self.has_empty_label() and self.node_alone():
            p.setStyle(QtCore.Qt.PenStyle.DotLine)
            painter.setPen(p)
            painter.drawRect(self.inner_rect)

    def move(self, other_nodes: list, heat: float) -> (int, int):
        """ Override usual movement if comment is connected to some node. If so, try to keep the
        given position relative to that node.
        :return: diff_x, diff_y, normalize, ban_normalization  -- announce how much we moved and if 
        the movement is such that it should be included in normalization calculations. 
        Any node can prevent normalization altogether, as it is harmful in cases where there is 
        a good reason for many free moving feature nodes to flock into one direction.  
        """
        if self.preferred_host:
            x, y = self.preferred_host.current_scene_position
            dx, dy = self.pos_relative_to_host
            self.current_position = x + dx, y + dy
            return 0, 0, False, False
        else:
            return super().move(other_nodes, heat)

    def drop_to(self, x, y, recipient=None, shift_down=False):
        super().drop_to(x, y, recipient=recipient, shift_down=shift_down)
        if self.preferred_host:
            x, y = self.preferred_host.current_scene_position
            mx, my = self.current_scene_position
            self.pos_relative_to_host = mx - x, my - y

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

    def dragging_comment(self):
        """ Check if the currently dragged item is comment and can connect with me
        :return:
        """
        return self.is_dragging_this_type(g.COMMENT_NODE)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    image_path = SavedField("image_path", if_changed=set_image_path)
    user_size = SavedField("user_size")
