# coding=utf-8
# ############################################################################
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
# ############################################################################

from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.FadeInOut import FadeInOut
from kataja.Shapes import SHAPE_PRESETS
from kataja.singletons import ctrl, prefs
import kataja.globals as g


class Triangle(QtWidgets.QGraphicsItem, FadeInOut):
    def __init__(self, host, width, height):
        QtWidgets.QGraphicsItem.__init__(self, parent=host)
        FadeInOut.__init__(self)
        self.setParentItem(host)
        self._host = host
        self.width = width
        self.height = height

    def get_color(self):
        return self._host.color

    def boundingRect(self):
        return QtCore.QRectF(-self.width / 2, 0, self.width, self.height)

    def set_width(self, width):
        self.width = width
        self.update()

    def set_height(self, height):
        self.height = height
        self.update()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        c = self.get_color()
        center = 0
        w2 = self.width / 2
        left = -w2
        right = w2
        top = 0
        bottom = self.height
        simple = False
        painter.setPen(c)
        if simple:
            triangle = QtGui.QPainterPath()
            triangle.moveTo(center, top)
            triangle.lineTo(right, bottom)
            triangle.lineTo(left, bottom)
            triangle.lineTo(center, top)
            painter.drawPath(triangle)
        else:
            # We want node's shape class and its properties so that the triangle can be drawn in similar style.
            edge_type = self._host.edge_type()
            shape_name = ctrl.settings.get_edge_setting('shape_name', edge_type=edge_type)
            path_class = SHAPE_PRESETS[shape_name]
            path, lpath, foo, bar = path_class.path((center, top), (right, bottom), [], g.BOTTOM, g.TOP)
            fill = path_class.fillable and ctrl.settings.get_shape_setting('fill', edge_type=edge_type)
            if fill:
                painter.fillPath(path, c)
            else:
                painter.drawPath(path)
            painter.drawLine(left, bottom, right, bottom)
            path, lpath, foo, bar = path_class.path((center, top), (left, bottom), [], g.BOTTOM, g.TOP)

            if fill:
                painter.fillPath(path, c)
            else:
                painter.drawPath(path)

    @staticmethod
    def add_or_update_triangle_for(root):

        def fold_into_me(host, nodes):
            to_do = []
            x = 0
            for node in nodes:
                node.lock_to_node(host)
                br = node.boundingRect()
                to_do.append((node, x, br.left()))
                if not node.hidden_in_triangle():
                    x += br.width()
            xt = x / 2
            host.label_object.triangle_width = x
            host.update_label()
            bottom = host.boundingRect().bottom()
            y = bottom + prefs.edge_height
            for node, my_x, my_l in to_do:
                node.move_to(my_x - my_l - xt, y, can_adjust=False, valign=g.TOP)
                node.update_label()
                node.update_visibility()
            draw_triangle(host, bottom, x, prefs.edge_height)

        def draw_triangle(host, top, width, height):
            triangle = Triangle(host=host, width=width, height=height)
            triangle.setY(top)

        def remove_children(bad_mother):
            for child in bad_mother.get_children(similar=False, visible=False):
                if child in folded:
                    folded.remove(child)
                    remove_children(child)

        if root not in root.triangle_stack:
            root.poke('triangle_stack')
            root.triangle_stack.append(root)
        fold_scope = root.list_descendants_once()
        folded = []
        bad_mothers = set()

        # triangle_stack for node holds the ground truth of triangles. Folding and graphicsitem
        # parent relation are surface stuff.

        for node in fold_scope:
            if root not in node.triangle_stack:
                node.poke('triangle_stack')
                node.triangle_stack.append(root)
            # multidominated nodes can be folded if all parents are in scope of fold
            parents = node.get_parents()
            if len(parents) > 1:
                can_fold = True
                for parent in parents:
                    if parent not in fold_scope:
                        bad_mothers.add(node)
                        can_fold = False
                        break
                if can_fold:
                    folded.append(node)
            else:
                folded.append(node)

        # remember that the branch that couldn't be folded won't allow any of its children to be folded either.
        for bm in bad_mothers:
            remove_children(bm)

        fold_into_me(root, folded)

    @staticmethod
    def remove_triangle_from(root):

        def remove_triangle(host):
            for item in host.childItems():
                if isinstance(item, Triangle):
                    item.setParentItem(None)
                    item.hide()

        root.poke('triangle_stack')
        root.triangle_stack.pop()
        remove_triangle(root)
        fold_scope = root.list_descendants_once()
        for node in fold_scope:
            if node.triangle_stack and node.triangle_stack[-1] is root:
                node.poke('triangle_stack')
                node.triangle_stack.pop()
            if node.parentItem() == root:
                node.release_from_locked_position()
                if not node.isVisible():
                    node.current_position = root.current_position
            node.update_visibility()  # with triangle_stack reduced, hidden nodes may become
            # visible again. movement back to visualisation positions is handled by visualisation redraw
        # when unfolding a triangle you may unfold previous triangles. Their leaf nodes are now
        # in wrong positions and have to be redrawn. Update all contained triangles:
        for n in fold_scope:
            if n.is_triangle_host():
                Triangle.add_or_update_triangle_for(n)
