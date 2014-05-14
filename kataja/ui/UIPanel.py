# coding=utf-8
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

import math

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtCore import QPointF as Pf, QPoint as P, Qt
from kataja.Controller import ctrl, prefs, qt_prefs
from kataja.utils import to_tuple
from kataja.visualizations.available import VISUALIZATIONS
from kataja.ui.TwoColorButton import TwoColorButton
from kataja.Edge import SHAPE_PRESETS


class TwoColorIcon(QtGui.QIcon):
    """ Icons that change their color according to widget where they are """

    def paint(self, painter, **kwargs):
        """

        :param painter:
        :param kwargs:
        :return:
        """
        print 'using twocoloricon painter'
        return QtGui.QIcon.paint(self, painter, kwargs)


class DockPanel(QtWidgets.QDockWidget):
    """ Big panel where other dock panels are folded in"""

    def __init__(self, name, default_position=None, parent=None, ui_buttons=None):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'... -- not used here.
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added -- not really used here
        """
        QtWidgets.QDockWidget.__init__(self, name, parent=None)
        self.name = name
        self.setFloating(True)
        self.resize(200, 600)
        parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)


class UIPanel(QtWidgets.QDockWidget):
    """ UI windows that can be docked to main window or separated. Gives some extra control and helper methods on QDockWidget. """

    def __init__(self, name, default_position='bottom', parent=None):
        """

        :param name:
        :param default_position:
        :param parent:
        """
        QtWidgets.QDockWidget.__init__(self, name, parent=parent)
        self.name = name
        if default_position == 'bottom':
            parent.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self)
        elif default_position == 'top':
            parent.addDockWidget(QtCore.Qt.TopDockWidgetArea, self)
        elif default_position == 'left':
            parent.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)
        elif default_position == 'right':
            parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
        elif default_position == 'float':
            parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
            self.setFloating(True)
        self.dockLocationChanged.connect(self.report_dock_location)
        self.topLevelChanged.connect(self.report_top_level)

    #def dockLocationChanged(self, area):
    #    print 'UIPanel %s docked: %s' % (self, area)

    #def topLevelChanged(self, floating):
    #    print 'UIPanel %s floating: %s' % (self, floating)

    def report_dock_location(self, area):
        """

        :param area:
        """
        print 'UIPanel %s docked: %s' % (self, area)

    def report_top_level(self, floating):
        """

        :param floating:
        """
        if floating:
            w, h = self.preferred_size
            self.resize(w, h)
        print 'UIPanel %s floating: %s' % (self, floating)

    def update_field(self, field_key, field, value):
        """

        :param field_key:
        :param field:
        :param value:
        """
        field.setText(value)


class VisualizationPanel(UIPanel):
    """ Switch visualizations and their adjust their settings """

    def __init__(self, name, default_position='right', parent=None, ui_buttons=None):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, default_position, parent)
        label_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        button_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        inner = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()
        self.preferred_size = (300, 80)
        self.setMaximumSize(200, 80)

        #label = QtWidgets.QLabel('Use visualization', self)
        #label.setSizePolicy(label_policy)
        #layout.addWidget(label, 0, 0)

        selector = QtWidgets.QComboBox(self)
        #selector.setSizePolicy(label_policy)
        ui_buttons['visualization_selector'] = selector
        selector.addItems(['%s (%s)' % (key, item.shortcut) for key, item in VISUALIZATIONS.items()])
        selector.activated.connect(self.submit_action)
        selector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        layout.addWidget(selector, 1, 0)
        inner.setLayout(layout)
        inner.sizeHint = self.sizeHint
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.show()
        w, h = self.preferred_size
        self.resize(w, h)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def update_field(self, field_key, field, value):
        """

        :param field_key:
        :param field:
        :param value:
        """
        if field_key == 'visualization_selector':
            index = VISUALIZATIONS.keys().index(value)
            field.setCurrentIndex(index)


    def sizeHint(self):
        """


        :return:
        """
        print 'navigation panel asked for size hint'
        return QtCore.QSize(300, 80)

    def submit_action(self, index):
        """

        :param index:
        """
        action_key = VISUALIZATIONS.keys()[index]
        if action_key in self.parent()._actions:
            self.parent()._actions[action_key].trigger()


class NavigationPanel(UIPanel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, default_position='bottom', parent=None, ui_buttons=None):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, default_position, parent)
        label_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        button_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        inner = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()
        self.preferred_size = (200, 80)
        #self.setMaximumSize(200,120)
        #self.setFont(qt_prefs.menu_font)

        label = QtWidgets.QLabel('Tree set', self)
        label.setSizePolicy(label_policy)
        layout.addWidget(label, 0, 0, 1, 1)

        treeset_counter = QtWidgets.QLabel('0/0', self)
        treeset_counter.setSizePolicy(label_policy)
        layout.addWidget(treeset_counter, 0, 1, 1, 1)
        ui_buttons['treeset_counter'] = treeset_counter

        prev_tree = TwoColorButton(qt_prefs.left_arrow, 'Previous', inner)
        prev_tree.setSizePolicy(button_policy)
        layout.addWidget(prev_tree, 1, 0, 1, 1)
        ui_buttons['prev_tree'] = prev_tree

        next_tree = TwoColorButton(qt_prefs.right_arrow, 'Next', self)
        next_tree.setSizePolicy(button_policy)
        layout.addWidget(next_tree, 1, 1, 1, 1)
        ui_buttons['next_tree'] = next_tree

        label = QtWidgets.QLabel('Derivation step', self)
        label.setSizePolicy(label_policy)
        layout.addWidget(label, 2, 0, 1, 1)

        derivation_counter = QtWidgets.QLabel('0/0', self)
        derivation_counter.setSizePolicy(label_policy)
        layout.addWidget(derivation_counter, 2, 1, 1, 1)
        ui_buttons['derivation_counter'] = derivation_counter

        prev_der = TwoColorButton(qt_prefs.left_arrow, 'Previous', self)
        prev_der.setSizePolicy(label_policy)
        layout.addWidget(prev_der, 3, 0, 1, 1)
        ui_buttons['prev_der'] = prev_der

        next_der = TwoColorButton(qt_prefs.right_arrow, 'Next', self)
        next_der.setSizePolicy(label_policy)
        layout.addWidget(next_der, 3, 1, 1, 1)
        ui_buttons['next_der'] = next_der

        inner.setLayout(layout)
        inner.resize(303, 80)
        inner.setMaximumHeight(200)
        inner.setMinimumHeight(80)

        inner.sizeHint = self.sizeHint
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.show()
        w, h = self.preferred_size
        self.resize(w, h)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def sizeHint(self):
        """


        :return:
        """
        print 'navigation panel asked for size hint'
        return QtCore.QSize(200, 80)


class LogPanel(UIPanel):
    """ Dump window """

    def __init__(self, name, default_position='bottom', parent=None, ui_buttons=None):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, default_position, parent)
        x, y, w, h = parent.geometry().getRect()
        #self.setLayout(QtWidgets.QHBoxLayout())
        widget = QtWidgets.QTextBrowser()
        w = 640
        h = 80
        self.preferred_size = (w, h)
        print widget.sizePolicy().verticalPolicy()
        widget.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        widget.resize(w, h)
        widget.sizeHint = self.sizeHint
        self.resize(w, h)
        self.setWidget(widget)
        print widget.sizePolicy().verticalPolicy()
        print self.sizePolicy().verticalPolicy()
        #self.setMaximumSize(w,120)

        #self.resize(w, 80)
        #self.widget().resize(w, 80)
        #self.widget().setGeometry(x, y + h, w, 80)
        #self.setGeometry(x, y + h, w, 80)
        self.widget().setFont(qt_prefs.menu_font)  # @UndefinedVariable
        self.widget().setAutoFillBackground(True)
        self.show()

        print '*** created log panel ***'

    def sizeHint(self):
        """


        :return:
        """
        return QtCore.QSize(640, 80)


NONE = 0
FLAG = 1
CIRCLE = 2


class ColorWheelInner(QtWidgets.QWidget):
    def __init__(self, parent):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        QtWidgets.QWidget.__init__(self, parent=parent)
        self._pressed = 0
        self._color_spot_area = 0, 0, 0
        self._flag_area = 0, 0, 0, 0
        self.setAutoFillBackground(True)
        self.setMaximumSize(160, 148)
        self.setGeometry(0, 0, 160, 148)
        self.show()
        self._radius = 70
        self._origin_x = self._radius + 4
        self._origin_y = self._radius + 4
        self._lum_box_x = 8 + (self._radius * 2)
        self._lum_box_y = 4 + (self._radius / 2)


    def paintEvent(self, event):
        """

        :param event:
        :return:
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
        #painter.setBrush(colors.dark_gray)
        painter.setPen(ctrl.cm().ui())
        #painter.drawRect(0, 0, 160, 160)
        #painter.setBrush(colors.paper)
        #painter.setPen(colors.paper)
        r = self._radius
        painter.drawEllipse(4, 4, r + r, r + r)
        painter.drawRect(self._lum_box_x, self._lum_box_y, 8, r)
        cm = ctrl.cm()

        def draw_as_circle(color):
            h, s, v, a = color.getHsvF()
            angle = math.radians(h * 360)
            depth = s * r
            y = math.sin(angle) * depth
            x = math.cos(angle) * depth
            x += self._origin_x
            y += self._origin_y
            size = (1 - v) * 20.0 + 5
            size2 = size / 2

            if color == cm.paper():
                painter.setPen(cm.drawing())
                painter.setBrush(color)
            else:
                painter.setBrush(color)
                painter.setPen(color)
            painter.drawEllipse(x - size2, y - size2, size, size)
            return x, y, v

        draw_these = [cm.paper(), cm.ui(), cm.secondary(), cm.drawing()]
        x, y, v = 0, 0, 0
        for color in draw_these:
            x, y, v = draw_as_circle(color)
        self._color_spot_area = x, y, v
        size = (1 - v) * 20.0 + 5
        size2 = size / 2
        painter.setPen(cm.ui())
        painter.drawLine(x, y - size2, x, y + size2)
        painter.drawLine(x - size2, y, x + size2, y)
        self._flag_area = self._lum_box_x, self._lum_box_y + r * (1 - v), 8, 8
        painter.setBrush(cm.drawing())
        painter.drawRect(self._flag_area[0], self._flag_area[1], self._flag_area[2], self._flag_area[3])
        #QtWidgets.QWidget.paintEvent(self, event)

    def wheelEvent(self, event):
        """

        :param event:
        """
        h, s, v = ctrl.main.forest.settings.hsv()  # @UndefinedVariable
        ov = v
        v += event.angleDelta().y() / 100.0
        if v < 0:
            v = 0
        elif v > 1:
            v = 1
        if ov != v:
            ctrl.main.adjust_colors((h, s, v))  # @UndefinedVariable
            self.update()


    def mousePressEvent(self, event):
        """

        :param event:
        """
        x, y = to_tuple(event.localPos())
        f_x, f_y, f_w, f_h = self._flag_area
        # print 'x:%s y:%s f_x1:%s f_y1:%s, f_x2:%s, f_y2:%s' % (x,y, f_x, f_y, f_x+f_w, f_y+f_h)
        c_x, c_y, c_r = self._color_spot_area
        if f_x <= x <= f_x + f_w and f_y <= y <= f_y + f_h:
            self._pressed = FLAG
        elif abs(x - c_x) + abs(y - c_y) < (1 - c_r) * 20 + 5:
            self._pressed = CIRCLE

    def mouseMoveEvent(self, event):
        """

        :param event:
        :return:
        """

        def get_value_from_flag_position(value, y):
            dv = (self._radius - (y - self._lum_box_y)) / self._radius
            if dv < 0:
                dv = 0
            if dv > 1:
                dv = 1
            return dv

        def get_color_from_position(x, y):
            dx = self._origin_x - x
            dy = self._origin_y - y
            hyp = math.sqrt(dx * dx + dy * dy)
            s = hyp / self._radius
            if s > 1:
                s = 1.0
            h = (math.atan2(dy, dx) + math.pi) / (math.pi * 2)
            return h, s

        cm = ctrl.cm()
        if self._pressed == FLAG:
            x, y = to_tuple(event.localPos())
            new_value = get_value_from_flag_position(cm.hsv[2], y)
            hsv = (cm.hsv[0], cm.hsv[1], new_value)
            ctrl.main.adjust_colors(hsv)  # @UndefinedVariable
            self.update()
        elif self._pressed == CIRCLE:
            x, y = to_tuple(event.localPos())
            h, s = get_color_from_position(x, y)
            hsv = (h, s, cm.hsv[2])
            ctrl.main.adjust_colors(hsv)  # @UndefinedVariable
            self.update()

    def mouseReleaseEvent(self, event):
        """

        :param event:
        """
        self._pressed = 0


class LinesPanel(UIPanel):
    """

    """

    def __init__(self, name, default_position='right', parent=None, ui_buttons=None):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, default_position, parent)
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        selector = QtWidgets.QComboBox(self)
        ui_buttons['line_type'] = selector
        selector.addItems([lt for lt in SHAPE_PRESETS.keys()])
        selector.activated.connect(self.change_main_line_type)
        layout.addWidget(selector)
        inner.setLayout(layout)
        self.setWidget(inner)

    def change_main_line_type(self, index):
        """

        :param index:
        """
        ctrl.main.change_node_edge_shape(SHAPE_PRESETS.keys()[index])


class ColorMappingPanel(UIPanel):
    """

    """

    def __init__(self, name, default_position='right', parent=None, ui_buttons=None):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, default_position, parent)
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)

        label_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        button_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        self.preferred_size = (200, 220)
        selector = QtWidgets.QComboBox(self)
        ui_buttons['color_mode'] = selector

        selector.addItems([c['name'] for c in prefs.color_modes.values()])
        selector.activated.connect(self.change_color_mode)
        self.mode_select = selector
        #selector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        layout.addWidget(selector)
        hlayout = QtWidgets.QHBoxLayout()
        color_name = QtWidgets.QLabel(ctrl.cm().get_color_name(ctrl.cm().hsv), self)
        color_name.setFixedWidth(120)
        color_name.setSizePolicy(label_policy)
        self.color_name = color_name
        hlayout.addWidget(color_name)
        add_color_button = QtWidgets.QPushButton('+', self)
        add_color_button.setFixedWidth(20)
        add_color_button.setSizePolicy(label_policy)
        add_color_button.clicked.connect(self.remember_color)
        hlayout.addWidget(add_color_button)
        layout.addLayout(hlayout)

        color_wheel = ColorWheelInner(inner)
        color_wheel.setFixedSize(160, 148)
        layout.addWidget(color_wheel)
        #layout.setRowMinimumHeight(0, color_wheel.height())
        h_spinner = QtWidgets.QSpinBox(self)
        h_spinner.setRange(0, 255)
        h_spinner.valueChanged.connect(self.h_changed)
        h_spinner.setAccelerated(True)
        h_spinner.setWrapping(True)
        self.h_spinner = h_spinner
        h_label = QtWidgets.QLabel('&H:', self)
        h_label.setBuddy(h_spinner)
        h_label.setSizePolicy(label_policy)
        s_spinner = QtWidgets.QSpinBox(self)
        s_spinner.setRange(0, 255)
        s_spinner.valueChanged.connect(self.s_changed)
        s_label = QtWidgets.QLabel('&S:', self)
        s_label.setBuddy(s_spinner)
        s_label.setSizePolicy(label_policy)
        s_spinner.setAccelerated(True)
        self.s_spinner = s_spinner
        v_spinner = QtWidgets.QSpinBox(self)
        v_spinner.setRange(0, 255)
        v_spinner.valueChanged.connect(self.v_changed)
        v_label = QtWidgets.QLabel('&V:', self)
        v_label.setBuddy(v_spinner)
        v_label.setSizePolicy(label_policy)
        v_spinner.setAccelerated(True)
        self.v_spinner = v_spinner
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(h_label)
        hlayout.addWidget(h_spinner)
        hlayout.addWidget(s_label)
        hlayout.addWidget(s_spinner)
        hlayout.addWidget(v_label)
        hlayout.addWidget(v_spinner)
        layout.addLayout(hlayout)
        inner.setLayout(layout)
        #inner.setMaximumSize(200, 228)

        #self.inner.addTab(ColorWheelInner(self.inner), 'Wheel')
        self.setWidget(inner)
        self.show()


class TestPanel(UIPanel):
    """
        Panel for rapid testing of various UI elements that otherwise may be hidden behind complex screens or logic.
    """

    def __init__(self, name, default_position='right', parent=None, ui_buttons=None):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, default_position, parent)
        inner = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel("Test area")
        layout.addWidget(label)
        color_button = ColorBox()
        inner.setLayout(layout)
        self.setWidget(inner)


class ColorBox(QtWidgets.QPushButton):
    """
        Rectangular solid button for displaying a color. Clicking it should open system's color selector.
    """
    def __init__(self, color, color_name):
        """

        :param color:
        :param color_name:
        """
        QtWidgets.QPushButton.__init__(self)
        self.color = color
        self.color_name = color_name



class ColorPanel(UIPanel):
    """

    """

    def __init__(self, name, default_position='right', parent=None, ui_buttons=None):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, default_position, parent)
        #self.setMaximumSize(200,170)
        #self.preferred_size = (160, 170)
        #self.setAutoFillBackground(True)
        inner = QtWidgets.QToolBox()
        #### Color wheel
        color_wheel_inner = QtWidgets.QWidget(self)
        inner.addItem(color_wheel_inner, "Main color")
        color_wheel_layout = QtWidgets.QVBoxLayout()
        #color_wheel_layout.setContentsMargins(4, 4, 4, 4)

        label_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        button_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        self.preferred_size = (200, 220)
        selector = QtWidgets.QComboBox(self)
        #selector.setSizePolicy(label_policy)
        ui_buttons['color_mode'] = selector

        selector.addItems([c['name'] for c in prefs.color_modes.values()])
        selector.activated.connect(self.change_color_mode)
        self.mode_select = selector
        #selector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        color_wheel_layout.addWidget(selector)
        hlayout = QtWidgets.QHBoxLayout()
        color_name = QtWidgets.QLabel(ctrl.cm().get_color_name(ctrl.cm().hsv), self)
        color_name.setFixedWidth(120)
        color_name.setSizePolicy(label_policy)
        self.color_name = color_name
        hlayout.addWidget(color_name)
        add_color_button = QtWidgets.QPushButton('+', self)
        add_color_button.setFixedWidth(20)
        add_color_button.setSizePolicy(label_policy)
        add_color_button.clicked.connect(self.remember_color)
        hlayout.addWidget(add_color_button)
        color_wheel_layout.addLayout(hlayout)

        color_wheel = ColorWheelInner(color_wheel_inner)
        color_wheel.setFixedSize(160, 148)
        color_wheel_layout.addWidget(color_wheel)
        #layout.setRowMinimumHeight(0, color_wheel.height())
        h_spinner = QtWidgets.QSpinBox(self)
        h_spinner.setRange(0, 255)
        h_spinner.valueChanged.connect(self.h_changed)
        h_spinner.setAccelerated(True)
        h_spinner.setWrapping(True)
        self.h_spinner = h_spinner
        h_label = QtWidgets.QLabel('&H:', self)
        h_label.setBuddy(h_spinner)
        h_label.setSizePolicy(label_policy)
        s_spinner = QtWidgets.QSpinBox(self)
        s_spinner.setRange(0, 255)
        s_spinner.valueChanged.connect(self.s_changed)
        s_label = QtWidgets.QLabel('&S:', self)
        s_label.setBuddy(s_spinner)
        s_label.setSizePolicy(label_policy)
        s_spinner.setAccelerated(True)
        self.s_spinner = s_spinner
        v_spinner = QtWidgets.QSpinBox(self)
        v_spinner.setRange(0, 255)
        v_spinner.valueChanged.connect(self.v_changed)
        v_label = QtWidgets.QLabel('&V:', self)
        v_label.setBuddy(v_spinner)
        v_label.setSizePolicy(label_policy)
        v_spinner.setAccelerated(True)
        self.v_spinner = v_spinner
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(h_label)
        hlayout.addWidget(h_spinner)
        hlayout.addWidget(s_label)
        hlayout.addWidget(s_spinner)
        hlayout.addWidget(v_label)
        hlayout.addWidget(v_spinner)
        color_wheel_layout.addLayout(hlayout)
        color_wheel_inner.setLayout(color_wheel_layout)
        #inner.setMaximumSize(200, 228)
        # Color mapping

        color_mapping_inner = QtWidgets.QWidget(self)
        inner.addItem(color_mapping_inner, "Mappings")
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)


        #self.inner.addTab(ColorWheelInner(self.inner), 'Wheel')        
        self.setWidget(inner)
        self.show()

    def h_changed(self, value):
        """

        :param value:
        :return:
        """
        if self._updating:
            return
        cm = ctrl.cm()
        hsv = (value / 255.0, cm.hsv[1], cm.hsv[2])
        ctrl.main.adjust_colors(hsv)  # @UndefinedVariable
        self.update()

    def s_changed(self, value):
        """

        :param value:
        :return:
        """
        if self._updating:
            return
        cm = ctrl.cm()
        hsv = (cm.hsv[0], value / 254.9, cm.hsv[2])
        ctrl.main.adjust_colors(hsv)  # @UndefinedVariable
        self.update()

    def v_changed(self, value):
        """

        :param value:
        :return:
        """
        if self._updating:
            return
        cm = ctrl.cm()
        hsv = (cm.hsv[0], cm.hsv[1], value / 255.0)
        ctrl.main.adjust_colors(hsv)  # @UndefinedVariable
        self.update()

    def change_color_mode(self, mode):
        """

        :param mode:
        """
        mode_key = prefs.color_modes.keys()[mode]
        print 'changing color mode to:', mode, mode_key
        ctrl.main.change_color_mode(mode_key)

    def remember_color(self):
        """


        """
        cm = ctrl.cm()
        color_key = str(cm.hsv)
        if color_key not in prefs.color_modes:
            prefs.add_color_mode(color_key, cm.hsv, cm)
            color_item = prefs.color_modes[color_key]
            self.mode_select.addItem(color_item['name'])
            self.mode_select.setCurrentIndex(self.mode_select.count() - 1)
        ctrl.main.change_color_mode(color_key)

    def update_colors(self):
        """


        """
        cm = ctrl.cm()
        h, s, v = cm.hsv
        self._updating = True
        self.h_spinner.setValue(h * 255)
        self.s_spinner.setValue(s * 255)
        self.v_spinner.setValue(v * 255)
        self.color_name.setText(cm.get_color_name(cm.hsv))
        self._updating = False



