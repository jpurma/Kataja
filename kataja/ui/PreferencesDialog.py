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
        setattr(prefs, self.field_name, value)
        if self.on_change_method:
            self.on_change_method()


class PreferencesDialog(QtWidgets.QDialog):
    """

    """

    def __init__(self, main):
        QtWidgets.QDialog.__init__(self, parent=None)  # separate window
        self.main = main
        self.tabwidget = QtWidgets.QTabWidget(parent=self)
        lo = QtWidgets.QVBoxLayout()
        lo.addWidget(self.tabwidget)
        self.setLayout(lo)
        self.fields = {}
        self.tabs = {}


        for key, value in vars(prefs).items():
            if not key.startswith('_'):
                d = getattr(prefs, '_%s_ui' % key, {})
                #if d:
                #    print(d)
                field_type = d.get('type', '')
                if not field_type:
                    if isinstance(value, float):
                        field_type = 'float_slider'
                    elif isinstance(value, bool):
                        field_type = 'checkbox'
                    elif isinstance(value, int):
                        field_type = 'int_slider'
                    elif isinstance(value, dict):
                        continue
                #print('creating field for ', key, value)
                label = d.get('label', '')
                tab_key = d.get('tab', 'General')
                widget, layout = self.get_tab(tab_key)
                if not label:
                    label = key.replace('_', ' ').capitalize()
                if field_type == 'int_slider':
                    if 'range' in d:
                        minv, maxv = d['range']
                    elif value < -10 or value > 10:
                        minv, maxv = -200, 200
                    else:
                        minv, maxv = -10, 10
                    f = DoubleSlider(key, self, decimals=False)
                    self.fields[key] = f
                    f.setRange(minv, maxv)
                    f.set_on_change_method(self.main.redraw)
                    layout.addRow(label, f)
                elif field_type == 'float_slider':
                    if 'range' in d:
                        minv, maxv = d['range']
                    elif value < -10 or value > 10:
                        minv, maxv = -200, 200
                    else:
                        minv, maxv = -10, 10
                    f = DoubleSlider(key, self, decimals=True)
                    self.fields[key] = f
                    f.setRange(minv, maxv)
                    f.set_on_change_method(self.main.redraw)
                    layout.addRow(label, f)
                elif field_type == 'checkbox':
                    f = CheckBox(key, self)
                    self.fields[key] = f
                    f.set_on_change_method(self.main.redraw)
                    layout.addRow(label, f)




    def get_tab(self, key):
        if key in self.tabs:
            return self.tabs[key], self.tabs[key].layout()
        new_tab = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout()
        self.tabwidget.addTab(new_tab, key)
        self.tabs[key] = new_tab
        new_tab.setLayout(layout)
        return new_tab, layout


    def update_pens(self):
        """


        """
        self.main.redraw()

    def dpi_changed(self, index):
        """

        :param index:
        """
        prefs.dpi = int(self.dpi_choices[index])
