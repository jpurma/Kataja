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

from PyQt5 import QtCore, QtWidgets

from kataja.singletons import prefs


class DoubleSlider(QtWidgets.QHBoxLayout):
    """

    """

    def __init__(self, field_name, parent, decimals=True):
        QtWidgets.QHBoxLayout.__init__(self)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, parent)
        self.decimals = decimals
        self.field_name = field_name
        self.now_changing = False
        self.on_change_method = None
        value = getattr(prefs, self.field_name)
        if decimals:
            self.spinbox = QtWidgets.QDoubleSpinBox(parent)
            self.spinbox.setDecimals(1)
            self.slider.setValue(value * 10)
        else:
            self.spinbox = QtWidgets.QSpinBox(parent)
            self.slider.setValue(value)
        self.spinbox.setValue(value)
        self.slider.setTickInterval(10)
        self.spinbox.setAccelerated(True)
        self.slider.valueChanged.connect(self.slider_changed)
        self.spinbox.valueChanged.connect(self.spinbox_changed)
        self.addWidget(self.slider)
        self.addWidget(self.spinbox)

    def set_on_change_method(self, method):
        """

        :param method:
        """
        self.on_change_method = method

    def setRange(self, min, max):
        """

        :param min:
        :param max:
        """
        self.spinbox.setRange(min, max)
        if self.decimals:
            self.slider.setRange(min * 10, max * 10)
        else:
            self.slider.setRange(min, max)

    def slider_changed(self, value):
        """

        :param value:
        :return:
        """
        if self.now_changing:
            return
        else:
            self.now_changing = True
        if self.decimals:
            value /= 10.0
        self.spinbox.setValue(value)
        setattr(prefs, self.field_name, value)
        if self.on_change_method:
            self.on_change_method()
        self.now_changing = False


    def spinbox_changed(self, value):
        """

        :param value:
        :return:
        """
        if self.now_changing:
            return
        else:
            self.now_changing = True
        if self.decimals:
            self.spinbox.setValue(value * 10)
        else:
            self.spinbox.setValue(value)
        setattr(prefs, self.field_name, value)
        if self.on_change_method:
            self.on_change_method()
        self.now_changing = False


class PreferencesDialog(QtWidgets.QDialog):
    """

    """

    def __init__(self, main):
        QtWidgets.QDialog.__init__(self, parent=None)  # separate window
        self.main = main
        self.dpi_choices = [72, 150, 300, 450, 600]

        layout = QtWidgets.QFormLayout()


        # self.draw_width = .5
        draw_width = DoubleSlider('draw_width', self, decimals=True)
        draw_width.setRange(0.1, 5)
        draw_width.set_on_change_method(self.update_pens)
        layout.addRow('Base line thickness', draw_width)

        # self.selection_width = 0.8
        # -- No need for preferences

        # self.thickness_multiplier = 2
        thickness_multiplier = DoubleSlider('thickness_multiplier', self, decimals=True)
        thickness_multiplier.setRange(0.5, 5)
        thickness_multiplier.set_on_change_method(self.update_pens)
        layout.addRow('Thickness multiplier for right branches ', thickness_multiplier)

        # self.dpi = 300
        dpi = QtWidgets.QComboBox(self)
        dpi.addItems([str(x) for x in self.dpi_choices])
        dpi.activated.connect(self.dpi_changed)
        dpi.setCurrentIndex(self.dpi_choices.index(prefs.dpi))
        layout.addRow('Dots Per Inch (DPI) for exported trees ', dpi)

        # self.FPS = 30
        # self.fps_in_msec = 1000 / self.FPS
        FPS = DoubleSlider('FPS', self, decimals=False)
        FPS.setRange(10, 90)
        layout.addRow('Frames per second (FPS) ', FPS)

        # self.move_frames = 12
        move_frames = DoubleSlider('move_frames', self, decimals=False)
        move_frames.setRange(0, 30)
        layout.addRow('Frames in each move animation ', move_frames)

        # self.edge_width = 20  # 20
        edge_width = DoubleSlider('edge_width', self, decimals=False)
        edge_width.setRange(5, 100)
        edge_width.set_on_change_method(self.main.redraw)
        layout.addRow('Edge width ', edge_width)

        # self.edge_height = 20
        edge_height = DoubleSlider('edge_height', self, decimals=False)
        edge_height.setRange(5, 100)
        edge_height.set_on_change_method(self.main.redraw)
        layout.addRow('Edge height ', edge_height)

        # self.color_mode = 'random'
        # self.color_modes = color_modes
        # self.shared_palettes = {}

        # self.default_visualization = 'Left first tree'

        # self.blender_app_path = '/Applications/blender.app/Contents/MacOS/blender'
        # self.blender_env_path = '/Users/purma/Dropbox/bioling_blender'

        # self._curve = 'InQuad'

        # self.fonts = fonts
        # self.keep_vertical_order = False
        # self.default_binary_branching = False  # True
        # self.use_magnets = True
        # self.hanging_gloss = True
        # self.spacing_between_trees = 3
        # self.include_features_to_label = False
        # self.default_use_multidomination = True
        # self.constituency_edge_shape = 1
        # self.feature_edge_shape = 3
        # self.console_visible = False
        # self.traces_are_grouped_together_by_default = 0
        # self.ui_speed = 8
        # self.show_labels = 2
        # self.touch = False
        # self.app_path = self.solve_app_path()
        # self.debug_treeset = self.app_path + '/trees.txt'
        # self.file_name = 'savetest.kataja'
        # self.print_file_path = self.app_path
        # self.print_file_name = 'kataja_print'
        # self.include_gloss_to_print = True
        self.setLayout(layout)

    def update_pens(self):
        """


        """
        self.main.redraw()

    def dpi_changed(self, index):
        """

        :param index:
        """
        prefs.dpi = int(self.dpi_choices[index])
