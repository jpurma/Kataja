import math
import random

from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.singletons import ctrl
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.KatajaCheckBox import KatajaCheckBox
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.panels.ColorThemePanel import color_theme_fragment
from kataja.utils import get_parent_panel
from kataja.utils import to_tuple

__author__ = 'purma'

FLAG = 999


def spinner(parent, layout, connect, label='', vmin=0, vmax=360, wrapping=False):
    spin = QtWidgets.QSpinBox(parent)
    spin.setRange(vmin, vmax)
    spin.valueChanged.connect(connect)
    spin.setAccelerated(True)
    spin.setWrapping(wrapping)
    if label:
        label = QtWidgets.QLabel(label, parent)
        label.setBuddy(spin)
        layout.addWidget(label)
    layout.addWidget(spin)
    return spin


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
        self.match_contrast = 65
        ctrl.main.palette_changed.connect(self.update_themes_and_colors)
        ctrl.main.color_themes_changed.connect(self.update_themes_and_colors)
        self.try_to_match = True
        self._updating = True
        # ### Color wheel
        layout = self.vlayout
        widget = self.widget()
        self.preferred_size = QtCore.QSize(220, 300)
        # From ColorThemePanel
        color_theme_fragment(self, widget, layout)

        the_rest = [f'accent{i}' for i in range(1, 9)] + [f'custom{i}' for i in range(1, 10)]

        self.editable_colors = ['content1', 'background1'] + the_rest
        self.all_colors = ['content1', 'content2', 'content3', 'background1', 'background2'] + \
                          the_rest

        self.selector_items = None
        self.role_label = QtWidgets.QLabel("Picking color for role: ")
        self.role_selector = QtWidgets.QComboBox(parent=widget)
        self.role_selector.addItems(self.editable_colors)
        # noinspection PyUnresolvedReferences
        self.role_selector.currentTextChanged.connect(self.set_color_role)
        hlayout = box_row(layout)
        hlayout.addWidget(self.role_label)
        hlayout.addWidget(self.role_selector)

        self.color_name = QtWidgets.QLabel(ctrl.cm.get_color_name(self.selected_hsv), widget)
        layout.addWidget(self.color_name)

        self.color_wheel = ColorWheelInner(widget)
        self.color_wheel.suggested_size = 200
        layout.addWidget(self.color_wheel)

        layout.addSpacing(8)
        hlayout = box_row(layout)
        self.h_spinner = spinner(self, hlayout, self.h_changed, label='H:', vmax=360, wrapping=True)
        self.s_spinner = spinner(self, hlayout, self.s_changed, label='S:', vmax=255)
        self.v_spinner = spinner(self, hlayout, self.v_changed, label='V:', vmax=255)
        hlayout = box_row(layout)
        self.r_spinner = spinner(self, hlayout, self.r_changed, label='R:', vmax=255)
        self.g_spinner = spinner(self, hlayout, self.g_changed, label='G:', vmax=255)
        self.b_spinner = spinner(self, hlayout, self.b_changed, label='B:', vmax=255)

        hlayout = box_row(layout)
        match_help = "When adjusting 'content1' or 'background1', try to find contrasting colors " \
                     "for other roles."
        self.match_l = QtWidgets.QLabel("Auto-match palette:")
        self.match_l.setToolTip(match_help)
        self.match_l.setParent(self.widget())
        self.match_cb = KatajaCheckBox()
        self.match_cb.setToolTip(match_help)
        self.match_cb.setParent(widget)
        self.match_cb.setChecked(self.try_to_match)
        # noinspection PyUnresolvedReferences
        self.match_cb.stateChanged.connect(self.set_palette_matching)
        self.match_l.setBuddy(self.match_cb)
        hlayout.addWidget(self.match_l)
        hlayout.addWidget(self.match_cb)
        chelp = "Contrast for auto-matched palettes"
        self.contrast_label = QtWidgets.QLabel("Contrast:")
        self.contrast_label.setToolTip(chelp)
        self.contrast_label.setParent(widget)
        hlayout.addWidget(self.contrast_label)
        self.contrast_spin = spinner(self, hlayout, self.contrast_changed, vmin=30, vmax=99)
        self.contrast_spin.setToolTip(chelp)
        self.contrast_spin.setValue(self.match_contrast)
        self._updating = False
        self.finish_init()

    def set_color_role(self, role, update_selector=False):
        self.selected_role = role
        self.update_colors()
        if update_selector:
            self.role_selector.blockSignals(True)
            self.role_selector.setCurrentText(self.selected_role)
            self.role_selector.blockSignals(False)
        self.update_matching()

    def update_matching(self):
        if self.selected_role == 'content1' or self.selected_role == 'background1':
            self.match_cb.setEnabled(True)
            self.match_l.setEnabled(True)
            if self.try_to_match:
                self.contrast_spin.setEnabled(True)
                self.contrast_label.setEnabled(True)
            else:
                self.contrast_spin.setEnabled(False)
                self.contrast_label.setEnabled(False)
        else:
            self.match_cb.setEnabled(False)
            self.match_l.setEnabled(False)
            self.contrast_spin.setEnabled(False)
            self.contrast_label.setEnabled(False)

    def set_palette_matching(self, value):
        self.try_to_match = value
        self.update_matching()

    def update_hsv(self):
        color = ctrl.cm.get(self.selected_role)
        if color:
            self.selected_hsv = color.getHsvF()[:3]
        else:
            # Create semi-random color to start with
            self.selected_hsv = random.random(), 0.6, 0.75
            self.send_color(*self.selected_hsv)

    def contrast_changed(self, value):
        if self._updating:
            return
        self.match_contrast = value
        self.send_color(*self.selected_hsv)

    def h_changed(self, value):
        if self._updating:
            return
        h, s, v = self.selected_hsv
        h = value / 360.0
        self.send_color(h, s, v)

    def s_changed(self, value):
        if self._updating:
            return
        h, s, v = self.selected_hsv
        s = value / 254.9
        self.send_color(h, s, v)

    def v_changed(self, value):
        if self._updating:
            return
        h, s, v = self.selected_hsv
        v = value / 255.0
        self.send_color(h, s, v)

    def r_changed(self, value):
        if self._updating:
            return
        color = QtGui.QColor.fromHsvF(*self.selected_hsv)
        self.send_color_rgb(value, color.green(), color.blue())

    def g_changed(self, value):
        if self._updating:
            return
        color = QtGui.QColor.fromHsvF(*self.selected_hsv)
        self.send_color_rgb(color.red(), value, color.blue())

    def b_changed(self, value):
        if self._updating:
            return
        color = QtGui.QColor.fromHsvF(*self.selected_hsv)
        self.send_color_rgb(color.red(), color.green(), value)

    def update_colors(self):
        """

        """
        self.update_hsv()
        h, s, v = self.selected_hsv
        self._updating = True
        self.h_spinner.setValue(h * 360)
        self.s_spinner.setValue(s * 255)
        self.v_spinner.setValue(v * 255)
        color = QtGui.QColor().fromHsvF(h, s, v)
        self.r_spinner.setValue(color.red())
        self.g_spinner.setValue(color.green())
        self.b_spinner.setValue(color.blue())
        self.color_name.setText(f'{ctrl.cm.get_color_name(self.selected_hsv)}, '
                                f'{color.name()}')
        self.contrast_spin.setValue(ctrl.cm.theme_contrast)
        self.color_wheel.update()
        self._updating = False

    def send_color(self, h, s, v):
        """ Replace color in palette with new color from hsvF (0.0-1.0)
        """
        color = QtGui.QColor().fromHsvF(h, s, v)
        ctrl.cm.set_color(self.selected_role, color, compute_companions=self.try_to_match,
                          contrast=self.match_contrast)

    def send_color_rgb(self, r, g, b):
        """ Replace color in palette with new color from rgb (0-255) """
        color = QtGui.QColor().fromRgb(r, g, b)
        ctrl.cm.set_color(self.selected_role, color, compute_companions=self.try_to_match,
                          contrast=self.match_contrast)

    def update_available_themes(self):
        themes = ctrl.cm.list_available_themes()
        key = ctrl.cm.theme_key
        if self.selector_items != themes:
            self.selector.blockSignals(True)
            self.selector_items = themes
            self.selector.clear()
            self.selector.add_items(self.selector_items)
            self.selector.select_by_data(key)
            self.selector.blockSignals(False)
        if key in ctrl.cm.custom_themes:
            self.randomise.hide()
            self.store_favorite.hide()
            self.remove_theme.show()
        else:
            self.remove_theme.hide()
            self.randomise.show()
            self.store_favorite.show()

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.update_themes_and_colors()
        super().showEvent(event)

    def update_themes_and_colors(self):
        self.update_available_themes()
        self.update_colors()


class ColorWheelInner(QtWidgets.QWidget):
    def __init__(self, parent):
        self.preferred_size = QtCore.QSize(160, 160)
        # noinspection PyArgumentList
        QtWidgets.QWidget.__init__(self, parent=parent)
        self._pressed = 0
        self._flag_area = 0, 0, 0, 0
        self.setAutoFillBackground(True)
        self.show()
        self.suggested_size = 0
        self.outer = get_parent_panel(self)
        self._radius = 0
        self._top_corner = 0
        self._lum_box_width = 0
        self._lum_box_height = 0
        self._origin_x = 0
        self._origin_y = 0
        self._lum_box_x = 0
        self._lum_box_y = 0
        self._color_spot_max = 0
        self._color_spot_min = 0
        self._crosshair = 0
        self._flag_width = 0
        self._flag_height = 0
        self._gradient = None
        self.clickable_areas = []
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
        self._lum_box_y = x * 0.07
        self._color_spot_max = x * 0.15
        self._color_spot_min = x * 0.02
        self._crosshair = x * 0.05
        self._flag_width = x * 0.08
        self._flag_height = x * 0.04
        self._gradient = QtGui.QLinearGradient(0, self._lum_box_y, 0, self._lum_box_y +
                                               self._lum_box_height)

    def paintEvent(self, event):
        """

        :param event:
        :return:
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing)  # | QtGui.QPainter.TextAntialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        r = self._radius
        v = self.outer.selected_hsv[2] * 255
        con_grad = QtGui.QConicalGradient(self._top_corner + r, self._top_corner + r, 0)
        color = QtGui.QColor()
        con_grad.setColorAt(0, color.fromHsv(359, 255, v))
        con_grad.setColorAt(0.25, color.fromHsv(270, 255, v))
        con_grad.setColorAt(0.5, color.fromHsv(180, 255, v))
        con_grad.setColorAt(0.75, color.fromHsv(90, 255, v))
        con_grad.setColorAt(1.0, color.fromHsv(0, 255, v))
        painter.setBrush(con_grad)
        painter.drawEllipse(self._top_corner - 4, self._top_corner - 4, r + r + 8, r + r + 8)
        painter.setBrush(ctrl.cm.paper())

        painter.drawEllipse(self._top_corner, self._top_corner, r + r, r + r)
        cm = ctrl.cm

        def draw_as_circle(color, key, selected=False):
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
                painter.setPen(cm.ui())
                painter.drawLine(x, y - size2 - self._crosshair, x, y + size2 + self._crosshair)
                painter.drawLine(x - size2 - self._crosshair, y, x + size2 + self._crosshair, y)
                self._flag_area = (self._lum_box_x - ((self._flag_width - self._lum_box_width) / 2),
                                   self._lum_box_y + self._lum_box_height * (1 - v),
                                   self._flag_width, self._flag_height)
            if color_key.startswith('background'):
                painter.setPen(cm.drawing())
                painter.setBrush(color)
            else:
                painter.setBrush(color)
                painter.setPen(color)
            painter.drawEllipse(x - size2, y - size2, size, size)
            self.clickable_areas.append(QtCore.QRectF(x - size2 - 1, y - size2 - 1, size + 2,
                                                      size + 2))

        self.clickable_areas = []

        for color_key in self.outer.all_colors:
            color = ctrl.cm.get(color_key, allow_none=True)
            if color:
                draw_as_circle(color, color_key, selected=False)
            else:
                self.clickable_areas.append(QtCore.QRectF())
        color = ctrl.cm.get(self.outer.selected_role)
        if color:
            draw_as_circle(color, self.outer.selected_role, selected=True)
            self.clickable_areas.pop()  # dont want this to be twice there

        painter.setPen(ctrl.cm.ui())
        light = QtGui.QColor().fromHsvF(self.outer.selected_hsv[0], self.outer.selected_hsv[1], 1.0)
        self._gradient.setColorAt(0, light)
        dark = QtGui.QColor().fromHsvF(self.outer.selected_hsv[0], self.outer.selected_hsv[1], 0)
        self._gradient.setColorAt(1, dark)
        painter.setBrush(self._gradient)

        painter.drawRect(self._lum_box_x, self._lum_box_y, self._lum_box_width,
                         self._lum_box_height + self._flag_height)

        painter.setBrush(color or ctrl.cm.get('accent1'))
        painter.drawRect(self._flag_area[0], self._flag_area[1], self._flag_area[2], self._flag_area[3])
        # QtWidgets.QWidget.paintEvent(self, event)

    def wheelEvent(self, event):
        """

        :param event:
        """
        h, s, v = self.outer.selected_hsv
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
        lp = event.localPos()
        x, y = to_tuple(lp)
        f_x, f_y, f_w, f_h = self._flag_area
        if f_x <= x <= f_x + f_w and f_y <= y <= f_y + f_h:
            self._pressed = FLAG
            return

        found = -1
        for i, rect in enumerate(self.clickable_areas):
            if rect.contains(x, y):
                found = i
                if self.outer.all_colors[i] == self.outer.selected_role:
                    break
        if found >= 0:
            self._pressed = self.outer.all_colors[found]
            if self.outer.selected_role != self._pressed:
                if self._pressed in self.outer.editable_colors:
                    self.outer.set_color_role(self._pressed, update_selector=True)
                else:
                    if self._pressed.startswith('content'):
                        self.outer.set_color_role('content1', update_selector=True)
                    elif self._pressed.startswith('background'):
                        self.outer.set_color_role('background1', update_selector=True)
                    self._pressed = None  # prevent dragging weirdness

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
        elif self._pressed:
            x, y = to_tuple(event.localPos())
            h, s = get_color_from_position(x, y)
            self.outer.send_color(h, s, v)
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """

        :param event:
        """
        self._pressed = 0
