import math

from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.globals import COLOR_THEME
from kataja.singletons import ctrl
from kataja.utils import to_tuple
from ui_items.Panel import FLAG, CIRCLE, Panel


__author__ = 'purma'


class ColorWheelPanel(Panel):
    """

    """

    def __init__(self, name, key, default_position='right', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        # ### Color wheel
        layout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget(self)
        # color_wheel_layout.setContentsMargins(4, 4, 4, 4)
        widget.setMinimumHeight(150)
        widget.setMaximumHeight(220)
        widget.preferred_size = QtCore.QSize(220, 150)

        label_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        button_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        hlayout = QtWidgets.QHBoxLayout()
        color_name = QtWidgets.QLabel(ctrl.cm.get_color_name(ctrl.cm.hsv), self)
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

        color_wheel = ColorWheelInner(widget)
        color_wheel.setFixedSize(160, 148)
        layout.addWidget(color_wheel)
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
        #layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        layout.addLayout(hlayout)
        widget.setLayout(layout)
        # Color mapping


        self.setWidget(widget)
        self.finish_init()


    def h_changed(self, value):
        """

        :param value:
        :return:
        """
        if self._updating:
            return
        cm = ctrl.cm
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
        cm = ctrl.cm
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
        cm = ctrl.cm
        hsv = (cm.hsv[0], cm.hsv[1], value / 255.0)
        ctrl.main.adjust_colors(hsv)  # @UndefinedVariable
        self.update()

    def remember_color(self):
        """


        """
        cm = ctrl.cm
        panel = ctrl.ui.get_panel(COLOR_THEME)
        color_key = panel.create_theme_from_color(cm.hsv)
        ctrl.main.change_color_mode(color_key)

    def update_colors(self):
        """


        """
        cm = ctrl.cm
        h, s, v = cm.hsv
        self._updating = True
        self.h_spinner.setValue(h * 255)
        self.s_spinner.setValue(s * 255)
        self.v_spinner.setValue(v * 255)
        self.color_name.setText(cm.get_color_name(cm.hsv))
        self._updating = False


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
        # painter.setBrush(colors.dark_gray)
        painter.setPen(ctrl.cm.ui())
        # painter.drawRect(0, 0, 160, 160)
        # painter.setBrush(colors.paper)
        # painter.setPen(colors.paper)
        r = self._radius
        painter.drawEllipse(4, 4, r + r, r + r)
        painter.drawRect(self._lum_box_x, self._lum_box_y, 8, r)
        cm = ctrl.cm

        def draw_as_circle(color):
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
        # QtWidgets.QWidget.paintEvent(self, event)

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
            """

            :param value:
            :param y:
            :return:
            """
            dv = (self._radius - (y - self._lum_box_y)) / self._radius
            if dv < 0:
                dv = 0
            if dv > 1:
                dv = 1
            return dv

        def get_color_from_position(x, y):
            """

            :param x:
            :param y:
            :return:
            """
            dx = self._origin_x - x
            dy = self._origin_y - y
            hyp = math.sqrt(dx * dx + dy * dy)
            s = hyp / self._radius
            if s > 1:
                s = 1.0
            h = (math.atan2(dy, dx) + math.pi) / (math.pi * 2)
            return h, s

        cm = ctrl.cm
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
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """

        :param event:
        """
        self._pressed = 0