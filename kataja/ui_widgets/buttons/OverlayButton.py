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

import kataja.globals as g
from kataja.UIItem import UIWidget
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_graphicsitems.TouchArea import TouchArea
from kataja.ui_widgets.buttons.PanelButton import PanelButton


class OverlayButton(PanelButton):
    """ A floating button on top of main canvas. These are individual UI
    elements each. """

    def mousePressEvent(self, event):
        if self.hover_icon:
            self.setIcon(self.hover_icon)
        PanelButton.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.normal_icon:
            self.setIcon(self.normal_icon)
        PanelButton.mouseReleaseEvent(self, event)

    @classmethod
    def condition(cls, host):
        """ Buttons may set conditions that have to apply (often related to the 'host' item) or the
        button is omitted. These conditions are checked before the button instances are created.
        Also because there are often one action related to many buttons (the host is given as a
        parameter when the action is activated), the condition to enable or disable the action is no
         help for this purpose.
        :param host: usually node, can also be edge. Condition check may evaluate if host has
        certain qualities or use some more general state/mode.
        :return:
        """
        # implement in subclasses
        return True

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        c = ctrl.cm.get(self.color_key)
        if self.pixmap:
            image = self.colored_image_from_base(c)
            image2 = self.colored_image_from_base(c.lighter())
        elif self.draw_method:
            image = self.colored_image_from_drawing(c)
            image2 = self.colored_image_from_drawing(c.lighter())
        else:
            return
        self.normal_icon = QtGui.QIcon(QtGui.QPixmap().fromImage(image))
        self.hover_icon = QtGui.QIcon(QtGui.QPixmap().fromImage(image2))
        self.setIcon(self.normal_icon)

    def avoid_overlaps(self, pos, step_x, step_y):
        if not self.host:
            return
        items = list(ctrl.ui.get_uis_for(self.host))
        if hasattr(self.host, 'edges_up'):
            for edge in self.host.edges_up:
                items += ctrl.ui.get_uis_for(edge)
        my_ge = self.geometry()
        my_ge.moveTopLeft(pos)
        step = QtCore.QPoint(step_x, step_y)
        for item in items:
            if item.priority < self.priority:
                if isinstance(item, QtWidgets.QGraphicsItem):
                    br = item.sceneBoundingRect()
                    ge = ctrl.graph_view.mapFromScene(br).boundingRect()
                elif isinstance(item, QtWidgets.QWidget):
                    ge = item.geometry()
                else:
                    continue
                while my_ge.intersects(ge):
                    pos += step
                    my_ge.moveTopLeft(pos)
        return pos


class TopRowButton(OverlayButton):
    permanent_ui = True

    def __init__(self, size=24, **kwargs):
        super().__init__(size=size, **kwargs)
        if isinstance(size, tuple):
            self.setMinimumSize(size[0] + 2, size[1])
            self.setMaximumSize(size[0] + 2, size[1])
        else:
            self.setMinimumSize(size + 2, size)
            self.setMaximumSize(size + 2, size)


class VisButton(OverlayButton):
    """ These are untypical buttons because these don't directly connect to actions and so they
    cannot get shortcuts, tooltips etc. from them. They are however connected to QButtonGroup,
    which takes care of signals.
    """

    permanent_ui = True

    def __init__(self, size=24, shortcut='', subtype=None, **kwargs):
        super().__init__(size=size, **kwargs)
        self.setCheckable(True)
        self.setShortcut(shortcut)
        if isinstance(size, tuple):
            self.setMinimumSize(size[0], size[1])
            self.setMaximumSize(size[0], size[1])
        else:
            self.setMinimumSize(size, size)
            self.setMaximumSize(size, size)
        self.sub_type = subtype

    def update_colors(self):
        pass


class CutFromStartButton(OverlayButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, pixmap=qt_prefs.cut_icon,
                         action='disconnect_edge_start')
        self.priority = 54

    @classmethod
    def condition(cls, edge):
        return edge.start and (not edge.end) and (
            ctrl.free_drawing_mode or edge.edge_type in [g.GLOSS_EDGE, g.COMMENT_EDGE, g.ARROW])

    def update_position(self):
        """ Put button left and below the starting point of edge.
        """
        if self.host and self.host.start:
            x, y = self.host.start_point
            x += self.w2
            y -= self.h2
            pos = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x, y))
            pos = self.avoid_overlaps(pos, 8, -8)
            self.move(pos)


class CutFromEndButton(OverlayButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, pixmap=qt_prefs.cut_icon,
                         action='disconnect_edge_end')
        self.priority = 55

    @classmethod
    def condition(cls, edge):
        return edge.end and (not edge.start) and (
            ctrl.free_drawing_mode or edge.edge_type in [g.GLOSS_EDGE, g.COMMENT_EDGE, g.ARROW])

    def update_position(self):
        """ Put button left and below the starting point of edge.
        """
        if self.host and self.host.end:
            x, y = self.host.end_point
            if self.host.direction() == g.LEFT:
                x += self.width()
            else:
                x -= self.width()
            y -= self.h2
            pos = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x, y))
            pos = self.avoid_overlaps(pos, -8, 0)
            self.move(pos)


class CutEdgeButton(OverlayButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key='accent3',
                         pixmap=qt_prefs.cut_icon, action='disconnect_edge')
        self.priority = 50

    @classmethod
    def condition(cls, edge):
        return edge.start and edge.end and (
            ctrl.free_drawing_mode or edge.edge_type in [g.GLOSS_EDGE, g.COMMENT_EDGE, g.ARROW])

    def update_position(self):
        """ Put button left and below the starting point of edge.
        """
        if self.host:
            p = self.host.path.get_point_at(0.7)
            if abs(self.host.start_point[0] - self.host.end_point[0]) < 10:
                p.setX(p.x() + 15)
            p.setY(p.y() - 30)
            pos = ctrl.main.graph_view.mapFromScene(p)
            self.avoid_overlaps(pos, 0, -8)
            self.move(pos)


class RemoveMergerButton(OverlayButton):
    """ Button to delete unnecessary node between grandparent and child"""

    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, pixmap='delete_icon',
                         action='remove_merger')
        self.priority = 99

    @classmethod
    def condition(cls, host):
        return ctrl.free_drawing_mode and host.node_type == g.CONSTITUENT_NODE and \
               host.is_unnecessary_merger()

    def update_position(self):
        """ """
        x, y = self.host.centered_scene_position
        p = ctrl.main.graph_view.mapFromScene(
            QtCore.QPointF(x + self.host.width / 2, y - self.host.height / 2))
        p += QtCore.QPoint(4, -self.height())
        p = self.avoid_overlaps(p, 16, 0)
        self.move(p)

    def enterEvent(self, event):
        self.host.hovering = True
        OverlayButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.host.hovering = False
        OverlayButton.leaveEvent(self, event)


class RemoveNodeButton(OverlayButton):
    """ Button to delete node """

    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key='accent3',
                         pixmap='delete_icon', action='remove_node')
        self.priority = 100

    @classmethod
    def condition(cls, host):
        return ctrl.free_drawing_mode and (
            (host.node_type == g.CONSTITUENT_NODE and not host.is_unnecessary_merger())
            or host.node_type != g.CONSTITUENT_NODE
        )

    def update_position(self):
        """ """

        x, y = self.host.centered_scene_position
        p = ctrl.main.graph_view.mapFromScene(
            QtCore.QPointF(x + self.host.width / 2, y - self.host.height / 2))
        p += QtCore.QPoint(4, -self.height())
        p = self.avoid_overlaps(p, 16, 0)
        self.move(p)

    def enterEvent(self, event):
        self.host.hovering = True
        OverlayButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.host.hovering = False
        OverlayButton.leaveEvent(self, event)


class GroupOptionsButton(OverlayButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key=host.color_key,
                         pixmap=qt_prefs.info_icon, action='toggle_group_options')
        self.priority = 25

    def update_position(self):
        """ Tries to find an unoccupied position in the radius of the group """
        candidates = self.host.clockwise_path_points(8)
        if not candidates:
            return
        scene_size = ctrl.main.graph_view.mapToScene(self.width() / 2,
                                                     self.height() / 2) - \
                     ctrl.main.graph_view.mapToScene(
            0, 0)
        w2 = scene_size.x()
        h2 = scene_size.y()
        for x, y in candidates:
            overlap = False
            items = ctrl.graph_scene.items(QtCore.QRectF(x - w2, y - h2, w2 + w2, h2 + h2))
            for item in items:
                if isinstance(item, TouchArea):
                    overlap = True
                    break
            if not overlap:
                break
        # noinspection PyUnboundLocalVariable
        p = ctrl.main.graph_view.mapFromScene(x - w2, y - h2)
        self.move(p)


class NodeEditorButton(OverlayButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key=host.get_color_id(),
                         pixmap=qt_prefs.info_icon, action='start_editing_node')
        self.priority = 25

    def update_position(self):
        """ """
        adjust = QtCore.QPointF(9, -8)
        x, y = self.host.centered_scene_position
        p = QtCore.QPointF(x + (self.host.width / 2), y)
        p = ctrl.main.graph_view.mapFromScene(p) + adjust
        p = p.toPoint()
        p = self.avoid_overlaps(p, 8, 0)
        self.move(p)

    def enterEvent(self, event):
        self.host.hovering = True
        OverlayButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.host.hovering = False
        OverlayButton.leaveEvent(self, event)


class OverlayLabel(UIWidget, QtWidgets.QLabel):
    """ A floating label on top of main canvas. These are individual UI
    elements each.
    """
    selection_independent = False
    permanent_ui = False

    def __init__(self, host, parent=None, ui_key=None, tooltip='', **kwargs):
        UIWidget.__init__(self, ui_key=ui_key or 'OverlayLabel', host=host, **kwargs)
        text = host.label_object.edited_field + "→"
        QtWidgets.QLabel.__init__(self, text, parent)
        self.k_tooltip = tooltip

    def update_edited_field(self):
        self.setText(self.host.label_object.edited_field + "→")

    def update_position(self):
        """ """
        adjust = QtCore.QPointF(-self.width() - 4, 8)
        x, y = self.host.current_scene_position
        y += self.host.get_top_y()
        p = QtCore.QPointF(x - (self.host.width / 2), y)
        p = ctrl.main.graph_view.mapFromScene(p) + adjust
        self.move(p.toPoint())
