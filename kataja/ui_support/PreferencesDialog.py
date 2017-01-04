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

import kataja.globals as g
from kataja.PaletteManager import color_modes
from kataja.singletons import prefs, qt_prefs, ctrl
from kataja.visualizations.available import VISUALIZATIONS
from kataja.ui_support.PluginSelector import PluginSelector

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

    def buddy_target(self):
        return self.slider

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


class CheckBox(QtWidgets.QHBoxLayout):
    """

    """

    def __init__(self, field_name, parent):
        QtWidgets.QHBoxLayout.__init__(self)
        self.checkbox = QtWidgets.QCheckBox(parent)
        self.field_name = field_name
        self.on_change_method = None
        value = getattr(prefs, self.field_name)
        self.checkbox.setChecked(value)
        self.checkbox.stateChanged.connect(self.checkbox_changed)
        self.addWidget(self.checkbox)

    def buddy_target(self):
        return self.checkbox

    def set_on_change_method(self, method):
        """

        :param method:
        """
        self.on_change_method = method

    def checkbox_changed(self, value):
        """

        :param value:
        :return:
        """
        setattr(prefs, self.field_name, bool(value))
        if self.on_change_method:
            self.on_change_method()


class Selector(QtWidgets.QComboBox):

    def __init__(self, field_name, parent, choices):
        QtWidgets.QComboBox.__init__(self, parent)
        self.field_name = field_name
        self.on_change_method = None
        if isinstance(choices[0], tuple):
            self.choice_values = [value for value, key in choices]
            self.choice_keys = [str(key) for value, key in choices]
        else:
            self.choice_values = choices
            self.choice_keys = [str(key) for key in choices]
        self.addItems(self.choice_keys)
        value = getattr(prefs, self.field_name)
        if value in self.choice_values:
            self.setCurrentIndex(self.choice_values.index(value))
        self.currentIndexChanged.connect(self.choice_changed)

    def buddy_target(self):
        return self

    def choice_changed(self, index):
        setattr(prefs, self.field_name, self.choice_values[index])
        if self.on_change_method:
            self.on_change_method()

    def set_on_change_method(self, method):
        """

        :param method:
        """
        self.on_change_method = method




class FileChooser(QtWidgets.QHBoxLayout):

    def __init__(self, field_name, parent=None, folders_only=False):
        QtWidgets.QHBoxLayout.__init__(self)
        self.parent_widget = parent
        self.folders_only = folders_only
        self.textbox = QtWidgets.QLineEdit()
        self.file_button = QtWidgets.QPushButton("Select Folder")
        self.addWidget(self.textbox)
        self.addWidget(self.file_button)
        self.field_name = field_name
        self.on_change_method = None
        value = getattr(prefs, self.field_name)
        self.textbox.setText(value)
        self.textbox.textChanged.connect(self.textbox_changed)
        self.file_button.clicked.connect(self.open_file_dialog)

    def open_file_dialog(self):
        dialog = QtWidgets.QFileDialog(self.parent_widget)
        if self.folders_only:
            dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if dialog.exec_():
            files = dialog.selectedFiles()
            if files:
                self.textbox.setText(files[0])

    def buddy_target(self):
        return self.textbox

    def set_on_change_method(self, method):
        """

        :param method:
        """
        self.on_change_method = method

    def textbox_changed(self):
        setattr(prefs, self.field_name, self.textbox.text())
        if self.on_change_method:
            self.on_change_method()


class TextInput(QtWidgets.QLineEdit):

    def __init__(self, field_name, parent=None, folders_only=False):
        QtWidgets.QLineEdit.__init__(self, parent)
        self.field_name = field_name
        self.on_change_method = None
        value = getattr(prefs, self.field_name)
        self.setText(value)
        self.textChanged.connect(self.textbox_changed)

    def buddy_target(self):
        return self

    def set_on_change_method(self, method):
        """

        :param method:
        """
        self.on_change_method = method

    def textbox_changed(self):
        setattr(prefs, self.field_name, self.text())
        if self.on_change_method:
            self.on_change_method()


class HelpLabel(QtWidgets.QLabel):

    def __init__(self, text, parent=None, buddy=None):
        QtWidgets.QLabel.__init__(self, text, parent)
        self.setIndent(10)
        self.setWordWrap(True)
        if buddy:
            self.setBuddy(buddy.buddy_target())


class PreferencesDialog(QtWidgets.QDialog):
    """

    """

    def __init__(self, main):
        QtWidgets.QDialog.__init__(self, parent=None)  # separate window
        self.setWindowTitle('Preferences')
        self.main = main
        self.left_area = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout()
        self.listwidget = QtWidgets.QListWidget()
        self.listwidget.setMaximumWidth(150)
        left_layout.addWidget(self.listwidget)
        self.reset_button = QtWidgets.QPushButton('Reset to defaults')
        self.reset_button.clicked.connect(ctrl.main.reset_preferences)
        left_layout.addWidget(self.reset_button)
        self.left_area.setLayout(left_layout)

        self.stackwidget = QtWidgets.QStackedLayout()
        self.pages = {}

        for page in prefs._tab_order:
            self.listwidget.addItem(page)
            widget, layout = self.get_page(page)
            self.stackwidget.addWidget(widget)

        self.listwidget.currentRowChanged.connect(self.stackwidget.setCurrentIndex)
        self.listwidget.setCurrentRow(0)
        lo = QtWidgets.QHBoxLayout()
        lo.addWidget(self.left_area)
        lo.addLayout(self.stackwidget)
        self.setLayout(lo)
        self.fields = {}
        self.triggers = {}

        paged = {}
        for key, value in vars(prefs).items():
            if key.startswith('_'):
                continue
            d = getattr(prefs, '_%s_ui' % key, {})
            if not d:
                continue
            tab = d.get('tab', 'Advanced')
            order = d.get('order', 999)
            d['value'] = value
            if tab not in paged:
                paged[tab] = {'ordered':[]}
            paged[tab][key] = d
            ordered = paged[tab]['ordered']
            ordered.append((order, key))

        for tab, tabdata in paged.items():
            ordered = tabdata['ordered']
            ordered.sort()
            widget, layout = self.get_page(tab)
            for o, key in ordered:
                f = None
                full_row = False
                d = tabdata[key]
                value = d['value']
                label = d.get('label', '')
                if not label:
                    label = key.replace('_', ' ').capitalize()
                special = d.get('special', '')
                if special:
                    method = getattr(self, 'build_' + special, None)
                    if method:
                        f, full_row = method(key, d)
                    else:
                        print('looking for method: build_' + special)

                else:
                    field_type = d.get('type', '')
                    if not field_type:
                        if d.get('choices', ''):
                            field_type = 'selection'
                        elif isinstance(value, float):
                            field_type = 'float_slider'
                        elif isinstance(value, bool):
                            field_type = 'checkbox'
                        elif isinstance(value, int):
                            field_type = 'int_slider'
                        elif isinstance(value, dict):
                            continue
                    if field_type == 'int_slider':
                        if 'range' in d:
                            minv, maxv = d['range']
                        elif value < -10 or value > 10:
                            minv, maxv = -200, 200
                        else:
                            minv, maxv = -10, 10
                        f = DoubleSlider(key, self, decimals=False)
                        f.setRange(minv, maxv)
                    elif field_type == 'float_slider':
                        if 'range' in d:
                            minv, maxv = d['range']
                        elif value < -10 or value > 10:
                            minv, maxv = -200, 200
                        else:
                            minv, maxv = -10, 10
                        f = DoubleSlider(key, self, decimals=True)
                        f.setRange(minv, maxv)
                    elif field_type == 'checkbox':
                        f = CheckBox(key, self)
                    elif field_type == 'selection':
                        f = Selector(key, self, d['choices'])
                    elif field_type == 'folder':
                        f = FileChooser(key, self, folders_only=True)
                    elif field_type == 'text':
                        f = TextInput(key, self)

                if f:
                    self.fields[key] = f
                    on_change = d.get('on_change', None)
                    if isinstance(on_change, str):
                        on_change = getattr(self, on_change)
                    if on_change:
                        self.triggers[key] = on_change
                    else:
                        on_change = self.main.redraw
                    f.set_on_change_method(on_change)
                    if full_row:
                        layout.addRow(QtWidgets.QLabel(label))
                        layout.addRow(f)
                    else:
                        layout.addRow(label, f)
                    help = d.get('help', None)
                    if help:
                        layout.addRow(HelpLabel(help, self, f))
                else:
                    pass
                    #print('couldnt create ui_support for this: ', key, d)

    def trigger_all_updates(self):
        """ When reseting to defaults, on_change -updaters are not triggered. This method
        collects all of them and runs them. Good luck!
        :return:
        """
        for method in set(self.triggers.values()):
            method()
        self.main.redraw()

    def get_page(self, key):
        if key in self.pages:
            return self.pages[key], self.pages[key].layout()
        new_page = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout()
        self.pages[key] = new_page
        new_page.setLayout(layout)
        return new_page, layout

    def build_color_modes(self, key, d):
        choices = [(key, data['name']) for key, data in color_modes.items()]
        return Selector(key, self, choices), False

    def build_visualizations(self, key, d):
        choices = list(VISUALIZATIONS.keys())
        return Selector(key, self, choices), False

    def build_plugins(self, key, d):
        return PluginSelector(key, self), True

    def prepare_easing_curve(self):
        qt_prefs.prepare_easing_curve(prefs.curve, prefs.move_frames)

    def update_colors(self):
        ctrl.main.change_color_mode(prefs.color_mode, force=True)

    def update_visualization(self):
        ctrl.forest.set_visualization(prefs.visualization)
        self.main.redraw()

    def resize_ui_font(self):

        qt_prefs.toggle_large_ui_font(prefs.large_ui_text, prefs.fonts)
        ctrl.call_watchers(self, 'ui_font_changed')
        ctrl.ui.redraw_panels()

    def update_pens(self):
        """


        """
        self.main.redraw()

    def dpi_changed(self, index):
        """

        :param index:
        """
        prefs.dpi = int(self.dpi_choices[index])
