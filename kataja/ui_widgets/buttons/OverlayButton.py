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
from PyQt6 import QtWidgets, QtGui, QtCore

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.utils import colored_image


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
            image = colored_image(c, self.base_image)
            image2 = colored_image(c.lighter(), self.base_image)
        elif self.draw_method:
            image = self.colored_image_from_drawing(c)
            image2 = self.colored_image_from_drawing(c.lighter())
        else:
            return
        # noinspection PyArgumentList
        self.normal_icon = QtGui.QIcon(QtGui.QPixmap().fromImage(image))
        # noinspection PyArgumentList
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

    def update_colors(self, color_key=None):
        pass


class CutEdgeButton(OverlayButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key='accent3',
                         pixmap=qt_prefs.cut_icon, action='disconnect_edge')
        self.priority = 50

    @classmethod
    def condition(cls, edge):
        return edge.start and edge.end and edge.edge_type in [g.GLOSS_EDGE, g.COMMENT_EDGE]

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


class CutArrowButton(CutEdgeButton):

    @classmethod
    def condition(cls, edge):
        return edge.start or edge.end


class RemoveArrowButton(OverlayButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, pixmap='delete_icon',
                         action='remove_arrow')
        self.priority = 50

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


class NodeOverlayButton(OverlayButton):

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


class NodeUnlockButton(NodeOverlayButton):

    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key=host.get_color_key(),
                         pixmap='unlock_icon', action='reset_adjustment')
        self.priority = 101

    @classmethod
    def condition(cls, host):
        return host.use_adjustment or host.locked


class GroupButton(OverlayButton):
    """ Button that is positioned around a group selection. It relies on methods provided by the
    group object to find its position. """

    def update_position(self):
        """ Tries to find an unoccupied position in the radius of the group """
        if self not in self.host.buttons:
            self.host.add_button(self)
        p = ctrl.main.graph_view.mapFromScene(self.host.position_for_buttons())
        i, total = self.host.index_for_button(self)
        w = self.width()
        spacing = 4
        total_width = (total * w) + ((total - 1) * spacing)
        if i > 0:
            my_x = i * w + ((i - 1) * spacing)
        else:
            my_x = 0
        my_x -= total_width / 2
        self.move(p.x() + my_x, p.y())


class GroupPersistenceButton(GroupButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key=host.color_key,
                         pixmap=qt_prefs.pin_drop_icon, action='make_selection_group_persistent')
        self.priority = 26

    @classmethod
    def condition(cls, host):
        return not host.persistent


class RemoveGroupPersistenceButton(GroupButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key=host.color_key,
                         pixmap=qt_prefs.close_icon, action='remove_group_persistence')
        self.priority = 26

    @classmethod
    def condition(cls, host):
        return host.persistent


class GroupOptionsButton(GroupButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key=host.color_key,
                         pixmap=qt_prefs.info_icon, action='toggle_group_options')
        self.priority = 25

    @classmethod
    def condition(cls, host):
        return host.persistent


class NodeEditorButton(OverlayButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key=host.get_color_key(),
                         pixmap=qt_prefs.info_icon, action='start_editing_node')
        self.priority = 25

    def update_position(self):
        """ """
        adjust = QtCore.QPoint(9, -8)
        x, y = self.host.centered_scene_position
        p = QtCore.QPointF(x + (self.host.width / 2), y)
        p = ctrl.main.graph_view.mapFromScene(p) + adjust
        p = self.avoid_overlaps(p, 8, 0)
        self.move(p)

    def enterEvent(self, event):
        self.host.hovering = True
        OverlayButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.host.hovering = False
        OverlayButton.leaveEvent(self, event)


class LockButton(OverlayButton):
    def __init__(self, host, parent):
        super().__init__(host=host, parent=parent, size=16, color_key=host.get_color_key(),
                         pixmap=qt_prefs.lock_icon, action='')
        self.priority = 25

    def update_position(self):
        """ """
        adjust = QtCore.QPoint(9, -8)
        x, y = self.host.centered_scene_position
        p = QtCore.QPointF(x + (self.host.width / 2), y + (self.host.height / 2))
        p = (ctrl.main.graph_view.mapFromScene(p) + adjust)
        p = self.avoid_overlaps(p, 8, 0)
        self.move(p)

    def enterEvent(self, event):
        self.host.hovering = True
        OverlayButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.host.hovering = False
        OverlayButton.leaveEvent(self, event)

    def fade_out(self, s=600):
        super().fade_out(s=s)
