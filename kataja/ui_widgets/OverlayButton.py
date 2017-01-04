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


class PanelButton(QtWidgets.QPushButton):
    """ Buttons that change their color according to widget where they are.
        Currently this is not doing anything special that can't be done by
        setting
        TwoColorIconEngine for normal button, but let's keep this in case we
        need to deliver
        palette updates to icon engines.
        PanelButtons are to be contained in panels or other widgets,
        they cannot be targeted
        individually.
     """

    def __init__(self, pixmap=None, text=None, parent=None, size=16,
                 color_key='accent8', draw_method=None, tooltip=None):
        QtWidgets.QPushButton.__init__(self, parent)
        self.draw_method = draw_method
        self.color_key = color_key
        self.base_image = None
        self.normal_icon = None
        self.hover_icon = None
        if isinstance(size, QtCore.QSize):
            width = size.width()
            height = size.height()
        elif isinstance(size, tuple):
            width = size[0]
            height = size[1]
        else:
            width = size
            height = size
        size = QtCore.QSize(width, height)
        self.setIconSize(size)
        if isinstance(pixmap, str):
            pixmap = getattr(qt_prefs, pixmap)
        if isinstance(pixmap, QtGui.QIcon):
            self.pixmap = pixmap.pixmap(size)
        else:
            self.pixmap = pixmap
        if self.pixmap:
            self.base_image = self.pixmap.toImage()
        elif self.draw_method:
            isize = QtCore.QSize(size.width() * 2, size.height() * 2)
            self.base_image = QtGui.QImage(
                isize, QtGui.QImage.Format_ARGB32_Premultiplied)
            self.base_image.fill(QtCore.Qt.transparent)
        self.compose_icon()

        if text:
            self.setText(text)
        if tooltip:
            if ctrl.main.use_tooltips:
                self.setToolTip(text)
            self.setStatusTip(text)
        else:
            self.setStatusTip(text)
        self.w2 = self.iconSize().width() / 2
        self.h2 = self.iconSize().height() / 2
        self.setContentsMargins(0, 0, 0, 0)
        self.setFlat(True)
        self.update_colors()

    def contextual_color(self):
        if self.isDown():
            return ctrl.cm.get(self.color_key).lighter()
        else:
            return ctrl.cm.get(self.color_key)

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        c = ctrl.cm.get(self.color_key)
        if self.pixmap:
            image = QtGui.QImage(self.base_image)
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(image.rect(), c)
            painter.end()
            image2 = QtGui.QImage(self.base_image)
            painter = QtGui.QPainter(image2)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(image2.rect(), c.lighter())
            painter.end()

        elif self.draw_method:

            image = QtGui.QImage(self.base_image)
            image2 = QtGui.QImage(self.base_image)

            painter = QtGui.QPainter(image)
            #painter.setDevicePixelRatio(2.0)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(c)
            self.draw_method(painter, image.rect(), c)
            painter.end()
            painter = QtGui.QPainter(image2)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            cl = c.lighter()
            painter.setPen(cl)
            self.draw_method(painter, image2.rect(), cl)
            painter.end()
        else:
            return
        self.normal_icon = QtGui.QIcon(QtGui.QPixmap().fromImage(image))
        self.hover_icon = QtGui.QIcon(QtGui.QPixmap().fromImage(image2))
        self.setIcon(self.normal_icon)

    def update_style_sheet(self):
        paper = ctrl.cm.paper()
        c = ctrl.cm.get(self.color_key)
        ss = """ :hover {border-color: %s;}
:pressed {border-color: %s; background-color: %s;}
:checked {border-color: %s;}
""" % (c.name(), c.lighter().name(), paper.name(), c.name()) # paper2.name()
        self.setStyleSheet(ss) # background-color: %s;

    def update_colors(self):
        self.update_style_sheet()
        self.compose_icon()

    def event(self, e):
        if e.type() == QtCore.QEvent.PaletteChange:
            self.update_colors()
        return QtWidgets.QPushButton.event(self, e)


class OverlayButton(UIWidget, PanelButton):
    """ A floating button on top of main canvas. These are individual UI
    elements each.

    :param pixmap:
    :param host:
    :param ui_key:
    :param text:
    :param parent:
    :param size:
    :param color_key:
    """

    def __init__(self, host, ui_key=None, pixmap=None, text=None, parent=None,
                 size=16, color_key='accent8', draw_method=None, tooltip=None, **kwargs):
        UIWidget.__init__(self, ui_key=ui_key, host=host)
        PanelButton.__init__(self, pixmap=pixmap, text=text, parent=parent, size=size,
                             color_key=color_key, draw_method=draw_method, tooltip=tooltip)

    def mousePressEvent(self, event):
        self.setIcon(self.hover_icon)
        PanelButton.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        self.setIcon(self.normal_icon)
        PanelButton.mouseReleaseEvent(self, event)


class TopRowButton(OverlayButton):

    permanent_ui = True

    def __init__(self, ui_key, parent=None, pixmap=None, text=None, draw_method=None,
                 size=24, tooltip=None):
        super().__init__(None, ui_key=ui_key,
                         parent=parent,
                         pixmap=pixmap,
                         text=text,
                         draw_method=draw_method,
                         tooltip=tooltip,
                         size=size,
                         color_key='accent8')
        if isinstance(size, tuple):
            self.setMinimumSize(size[0]+2, size[1])
            self.setMaximumSize(size[0]+2, size[1])
        else:
            self.setMinimumSize(size+2, size)
            self.setMaximumSize(size+2, size)


class QuickEditButton(OverlayButton):

    permanent_ui = True

    def __init__(self, ui_key, parent=None, pixmap=None, text=None, draw_method=None,
                 size=24, tooltip=None):
        super().__init__(None, ui_key=ui_key,
                         parent=parent,
                         pixmap=pixmap,
                         text=text,
                         draw_method=draw_method,
                         tooltip=tooltip,
                         size=size,
                         color_key='accent3')
        if isinstance(size, tuple):
            self.setMinimumSize(size[0]+2, size[1])
            self.setMaximumSize(size[0]+2, size[1])
        else:
            self.setMinimumSize(size+2, size)
            self.setMaximumSize(size+2, size)


class CutFromStartButton(OverlayButton):

    def __init__(self, host, parent=None):
        super().__init__(host, pixmap=qt_prefs.cut_icon,
                         tooltip='Disconnect edge from the start',
                         parent=parent,
                         size=16,
                         color_key='accent8')

    def update_position(self):
        """ Put button left and below the starting point of edge.
        """
        if self.host and self.host.start:
            x, y = self.host.start_point
            x += self.w2
            y -= self.h2
            self.move(ctrl.main.graph_view.mapFromScene(
                QtCore.QPointF(x, y)))


class CutFromEndButton(OverlayButton):

    def __init__(self, host, parent=None):
        super().__init__(host, pixmap=qt_prefs.cut_icon,
                         tooltip='Disconnect edge from the end',
                         parent=parent,
                         size=16,
                         color_key='accent8')

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
            self.move(ctrl.main.graph_view.mapFromScene(
                QtCore.QPointF(x, y)))


class AddTriangleButton(OverlayButton):

    def __init__(self, host, parent=None):
        super().__init__(host, pixmap=qt_prefs.cut_icon,
                         tooltip='Disconnect edge from the end',
                         parent=parent,
                         size=16,
                         color_key='accent8')

    def update_position(self):
        """ Put button left and below the starting point of edge.
        """
        if self.host:
            x, y = self.host.centered_scene_position
            p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x, y + self.host.height / 2 +
                                                                 self.h2))
            print(y, y + self.host.height / 2, self.host.height)
            self.move(p - QtCore.QPoint(self.w2 + 4, 0))


class RemoveTriangleButton(OverlayButton):

    def __init__(self, host, parent=None):
        super().__init__(host, pixmap=qt_prefs.cut_icon,
                         tooltip='Disconnect edge from the end',
                         parent=parent,
                         size=16,
                         color_key='accent8')

    def update_position(self):
        """ Put button left and below the starting point of edge.
        """
        if self.host:
            x, y = self.host.centered_scene_position
            p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x, y + self.host.height / 2 + self.h2))
            self.move(p - QtCore.QPoint(self.w2 + 4, 0))


class RemoveMergerButton(OverlayButton):
    """ Button to delete unnecessary node between grandparent and child"""

    def __init__(self, host, parent=None):

        super().__init__(host,
                         pixmap='delete_icon',
                         tooltip='Remove this non-merging node',
                         parent=parent,
                         size=16,
                         color_key='accent8')

    def update_position(self):
        """ """
        x, y = self.host.centered_scene_position
        p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x + self.host.width / 2,
                                                             y - self.host.height / 2))
        p += QtCore.QPoint(4, -self.height())
        if ctrl.ui.quick_edit_buttons:  # avoid overlap with button bar
            qeb = ctrl.ui.quick_edit_buttons.geometry()
            while qeb.contains(p):
                p += QtCore.QPoint(0, 10)
        self.move(p)

    def enterEvent(self, event):
        self.host.hovering = True
        OverlayButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.host.hovering = False
        OverlayButton.leaveEvent(self, event)


class RemoveNodeButton(OverlayButton):
    """ Button to delete unnecessary node between grandparent and child"""

    def __init__(self, host, parent=None):
        super().__init__(host,
                         pixmap='delete_icon',
                         tooltip='Remove node',
                         parent=parent,
                         size=16,
                         color_key='accent3')

    def update_position(self):
        """ """
        x, y = self.host.centered_scene_position
        p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(x + self.host.width / 2,
                                                             y - self.host.height / 2))
        p += QtCore.QPoint(4, -self.height())
        if ctrl.ui.quick_edit_buttons:  # avoid overlap with button bar
            qeb = ctrl.ui.quick_edit_buttons.geometry()
            while qeb.contains(p):
                p += QtCore.QPoint(0, 10)
        # avoid overlap with node editor button
        ne_button = ctrl.ui.get_ui_by_type(host=self.host, ui_type=g.NODE_EDITOR_BUTTON)
        if ne_button:
            neb = ne_button.geometry()
            while neb.contains(p + QtCore.QPoint(8, 10)):
                p += QtCore.QPoint(16, 0)

        self.move(p)

    def enterEvent(self, event):
        self.host.hovering = True
        OverlayButton.enterEvent(self, event)

    def leaveEvent(self, event):
        self.host.hovering = False
        OverlayButton.leaveEvent(self, event)


class GroupOptionsButton(OverlayButton):

    def __init__(self, host, parent=None):
        super().__init__(host,
                         pixmap=qt_prefs.info_icon,
                         tooltip='Name this selection',
                         parent=parent,
                         size=16,
                         color_key=host.color_key)

    def update_position(self):
        """ Tries to find an unoccupied position in the radius of the group """
        candidates = self.host.clockwise_path_points(8)
        if not candidates:
            return
        scene_size = ctrl.main.graph_view.mapToScene(self.width() / 2, self.height() / 2) - \
                     ctrl.main.graph_view.mapToScene(0, 0)
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

    def __init__(self, host, parent=None):
        super().__init__(host,
                         pixmap=qt_prefs.info_icon,
                         tooltip='Edit this node',
                         parent=parent,
                         size=16,
                         color_key='accent8')

    def update_position(self):
        """ """
        adjust = QtCore.QPointF(9, -8)
        x, y = self.host.centered_scene_position
        p = QtCore.QPointF(x + (self.host.width / 2), y)
        p = ctrl.main.graph_view.mapFromScene(p) + adjust
        p = p.toPoint()
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
    selection_independent = True

    def __init__(self, host, parent=None, ui_key=None, text=None,
                 size=16, color_key='accent8', tooltip=None, **kwargs):
        UIWidget.__init__(self, ui_key=ui_key or 'OverlayLabel', host=host)
        text = host.label_object.edited_field + "→"
        QtWidgets.QLabel.__init__(self, text, parent)
        if tooltip:
            self.setToolTip(tooltip)

    def update_position(self):
        """ """
        adjust = QtCore.QPointF(-self.width() - 4, 8)
        x, y = self.host.current_scene_position
        y += self.host.get_top_y()
        p = QtCore.QPointF(x - (self.host.width / 2), y)
        p = ctrl.main.graph_view.mapFromScene(p) + adjust
        self.move(p.toPoint())
