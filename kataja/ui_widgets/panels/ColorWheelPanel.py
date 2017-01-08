import math

from PyQt5 import QtWidgets, QtGui, QtCore

import kataja.globals as g
from kataja.singletons import ctrl
from kataja.utils import to_tuple
from kataja.ui_widgets.Panel import FLAG, CIRCLE, Panel


__author__ = 'purma'


class ColorWheelPanel(Panel):
    """

    """

    def __init__(self, name, default_position='right', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        self.selected_role = 'content1'
        self.selected_hsv = ctrl.cm.get(self.selected_role).getHsvF()[:3]
        self.watchlist = ['palette_changed', 'color_theme_changed']
        self.try_to_match = True
        self.draw_all_colors = True
        # ### Color wheel
        layout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget(self)
        # color_wheel_layout.setContentsMargins(4, 4, 4, 4)
        #widget.setMinimumHeight(150)
        #widget.setMaximumHeight(220)
        widget.preferred_size = QtCore.QSize(220, 300)
        the_rest = [f'accent{i}' for i in range(1, 9)] + [f'custom{i}' for i in range(1, 10)]

        self.editable_colors = ['content1', 'background1'] + the_rest
        self.all_colors = ['content1', 'content2', 'content3', 'background1', 'background2'] + \
                          the_rest

        self.role_label = QtWidgets.QLabel("Editing color")
        self.role_selector = QtWidgets.QComboBox(parent=self)
        self.role_selector.addItems(self.editable_colors)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.role_label)
        hlayout.addWidget(self.role_selector)
        layout.addLayout(hlayout)
        self.color_name = QtWidgets.QLabel(ctrl.cm.get_color_name(self.selected_hsv), self)
        layout.addWidget(self.color_name)

        self.color_wheel = ColorWheelInner(widget)
        self.color_wheel.suggested_size = 200
        layout.addWidget(self.color_wheel)

        layout.addSpacing(8)
        h_spinner = QtWidgets.QSpinBox(self)
        h_spinner.setRange(0, 255)
        h_spinner.valueChanged.connect(self.h_changed)
        h_spinner.setAccelerated(True)
        h_spinner.setWrapping(True)
        self.h_spinner = h_spinner
        h_label = QtWidgets.QLabel('&H:', self)
        h_label.setBuddy(h_spinner)
        s_spinner = QtWidgets.QSpinBox(self)
        s_spinner.setRange(0, 255)
        s_spinner.valueChanged.connect(self.s_changed)
        s_label = QtWidgets.QLabel('&S:', self)
        s_label.setBuddy(s_spinner)
        s_spinner.setAccelerated(True)
        self.s_spinner = s_spinner
        v_spinner = QtWidgets.QSpinBox(self)
        v_spinner.setRange(0, 255)
        v_spinner.valueChanged.connect(self.v_changed)
        v_label = QtWidgets.QLabel('&V:', self)
        v_label.setBuddy(v_spinner)
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
        widget.setLayout(layout)
        self.setWidget(widget)
        self.finish_init()

    def set_color_role(self, role):
        self.selected_role = role
        self.update_colors()
        self.role_selector.setCurrentText(self.selected_role)

    def update_hsv(self):
        color = ctrl.cm.get(self.selected_role)
        if color:
            self.selected_hsv = color.getHsvF()[:3]
        else:
            self.selected_hsv = 0, 0, 0

    def h_changed(self, value):
        """

        :param value:
        :return:
        """
        if self._updating:
            return
        h, s, v = self.selected_hsv
        h = value / 255.0
        self.send_color(h, s, v)

    def s_changed(self, value):
        """

        :param value:
        :return:
        """
        if self._updating:
            return
        h, s, v = self.selected_hsv
        s = value / 254.9
        self.send_color(h, s, v)

    def v_changed(self, value):
        """

        :param value:
        :return:
        """
        if self._updating:
            return
        h, s, v = self.selected_hsv
        v = value / 255.0
        self.send_color(h, s, v)

    def update_colors(self):
        """

        """
        self.update_hsv()
        h, s, v = self.selected_hsv
        self._updating = True
        self.h_spinner.setValue(h * 255)
        self.s_spinner.setValue(s * 255)
        self.v_spinner.setValue(v * 255)
        self.color_name.setText(ctrl.cm.get_color_name(self.selected_hsv))
        #self.update()
        self.color_wheel.update()
        self._updating = False

    def send_color(self, h, s, v):
        """ Replace color in palette with new color
        :param color:
        :return:
        """
        color = QtGui.QColor.fromHsvF(h, s, v)
        color_key = self.selected_role
        #if (not color_key.startswith('custom')) and ctrl.cm.theme_key in ctrl.cm.default_themes:
        #    ctrl.cm.create_custom_theme_from_modification(color_key, color)

        ctrl.cm.set_color(color_key, color)
        self.update_colors()
        #if self.role == 'node':
        #    ctrl.main.trigger_but_suppress_undo('change_node_color')
        #elif self.role == 'edge':
        #    ctrl.main.trigger_but_suppress_undo('change_edge_color')
        #elif self.role == 'group':
        #    ctrl.main.trigger_but_suppress_undo('change_group_color')
        ctrl.call_watchers(self, 'palette_changed')

    #def resizeEvent(self, rs):
    #    self.color_wheel.update_measurements(self.width() - 20)

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        if signal == 'palette_changed' or signal == 'color_theme_changed':
            self.update_colors()


class ColorWheelInner(QtWidgets.QWidget):
    """

    """

    def __init__(self, parent):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        self.suggested_size = 160
        QtWidgets.QWidget.__init__(self, parent=parent)
        self._pressed = 0
        self._color_spot_area = 0, 0, 0
        self._flag_area = 0, 0, 0, 0
        self.setAutoFillBackground(True)
        self.show()
        self.outer = self.parentWidget().parentWidget()
        self._radius = 0
        self._lum_box_height = 0
        self._origin_x = 0
        self._origin_y = 0
        self._lum_box_x = 0
        self._lum_box_y = 0
        self._color_spot_max = 0
        self._gradient = None
        self.setMinimumSize(self.suggested_size, self.suggested_size)
        self.setMaximumSize(600, 600)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                           QtWidgets.QSizePolicy.MinimumExpanding)
        self.update_measurements(self.suggested_size)

    def resizeEvent(self, rs):
        self.update_measurements(rs.size().width())

    def update_measurements(self, x):
        self.suggested_size = x
        self._radius = x * 0.43
        self._top_corner = x * 0.02
        self._lum_box_width = x * 0.04
        self._lum_box_height = x * 0.75
        self._origin_x = x * 0.45
        self._origin_y = x * 0.45
        self._lum_box_x = x * 0.93
        self._lum_box_y = x * 0.1
        self._color_spot_max = x * 0.15
        self._color_spot_min = x * 0.02
        self._crosshair = x * 0.05
        self._flag_width = x * 0.08
        self._flag_height = x * 0.04
        #self.setMinimumSize(self.suggested_size, self.suggested_size)
        self._gradient = QtGui.QLinearGradient(0, self._lum_box_y, 0, self._lum_box_y +
                                               self._lum_box_height)

    def sizeHint(self):
        return QtCore.QSize(self.suggested_size, self.suggested_size)

    def paintEvent(self, event):
        """

        :param event:
        :return:
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
        painter.setPen(ctrl.cm.ui())
        r = self._radius
        painter.drawEllipse(self._top_corner, self._top_corner, r + r, r + r)
        cm = ctrl.cm

        def draw_as_circle(color, selected=False):
            """

            :param color:
            :return:
            """
            h, s, v, a = color.getHsvF()
            angle = math.radians(h * 360)
            depth = s * r
            y = math.sin(angle) * depth
            x = math.cos(angle) * depth
            x += self._origin_x
            y += self._origin_y
            size = (1 - v) * self._color_spot_max + self._color_spot_min
            size2 = size / 2
            if selected:
                painter.setPen(QtGui.QColor(255, 255, 255))
                painter.drawEllipse(x - size2 - 1, y - size2 - 1, size + 2, size + 2)
                self._color_spot_area = x, y, v
                painter.setPen(cm.ui())
                painter.drawLine(x, y - size2 - self._crosshair, x, y + size2 + self._crosshair)
                painter.drawLine(x - size2 - self._crosshair, y, x + size2 + self._crosshair, y)
                self._flag_area = (self._lum_box_x - ((self._flag_width - self._lum_box_width) / 2),
                                   self._lum_box_y + self._lum_box_height * (1 - v),
                                   self._flag_width, self._flag_height)
            if color == cm.paper():
                painter.setPen(cm.drawing())
                painter.setBrush(color)
            else:
                painter.setBrush(color)
                painter.setPen(color)
            painter.drawEllipse(x - size2, y - size2, size, size)

        if self.outer.draw_all_colors:
            draw_these = self.outer.all_colors
        else:
            draw_these = [self.outer.selected_role]
        for color_key in draw_these:
            if color_key != self.outer.selected_role:
                color = ctrl.cm.get(color_key)
                if color:
                    draw_as_circle(color, selected=False)

        color = ctrl.cm.get(self.outer.selected_role)
        if color:
            draw_as_circle(color, selected=True)

        painter.setPen(ctrl.cm.ui())
        light = QtGui.QColor.fromHsvF(self.outer.selected_hsv[0], self.outer.selected_hsv[1], 1.0)
        self._gradient.setColorAt(0, light)
        dark = QtGui.QColor.fromHsvF(self.outer.selected_hsv[0], self.outer.selected_hsv[1], 0)
        self._gradient.setColorAt(1, dark)
        painter.setBrush(self._gradient)

        painter.drawRect(self._lum_box_x, self._lum_box_y, self._lum_box_width,
                         self._lum_box_height + self._flag_height)

        painter.setBrush(cm.drawing())
        painter.drawRect(self._flag_area[0], self._flag_area[1], self._flag_area[2], self._flag_area[3])
        # QtWidgets.QWidget.paintEvent(self, event)

    def wheelEvent(self, event):
        """

        :param event:
        """
        h, s, v = ctrl.settings.get('hsv')  # @UndefinedVariable
        ov = v
        v += event.angleDelta().y() / 100.0
        if v < 0:
            v = 0
        elif v > 1:
            v = 1
        if ov != v:
            self.outer.send_color(h, s, v)


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
        elif abs(x - c_x) + abs(y - c_y) < (1 - c_r) * self._color_spot_max + self._color_spot_min:
            self._pressed = CIRCLE

    def mouseMoveEvent(self, event):
        """

        :param event:
        :return:
        """

        def get_value_from_flag_position(y):
            dv = (self._lum_box_y + self._lum_box_height - y) / self._lum_box_height
            if dv < 0:
                dv = 0
            if dv > 1:
                dv = 1
            return dv

        def get_color_from_position(x, y):
            dx = self._origin_x - x
            dy = self._origin_y - y
            hyp = math.sqrt(dx * dx + dy * dy)
            if self._radius == 0:
                s = 1.0
            else:
                s = hyp / self._radius
            if s > 1:
                s = 1.0
            h = (math.atan2(dy, dx) + math.pi) / (math.pi * 2)
            return h, s

        h, s, v = self.outer.selected_hsv
        if self._pressed == FLAG:
            x, y = to_tuple(event.localPos())
            v = get_value_from_flag_position(y)
            self.outer.send_color(h, s, v)
        elif self._pressed == CIRCLE:
            x, y = to_tuple(event.localPos())
            h, s = get_color_from_position(x, y)
            self.outer.send_color(h, s, v)
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """

        :param event:
        """
        self._pressed = 0