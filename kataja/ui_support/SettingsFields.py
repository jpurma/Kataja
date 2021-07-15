from PyQt6 import QtCore, QtWidgets

from kataja.PaletteManager import color_themes
from kataja.singletons import prefs, ctrl
from kataja.ui_widgets.selection_boxes.PluginSelector import PluginSelector
from kataja.visualizations.available import VISUALIZATIONS


class DoubleSlider(QtWidgets.QHBoxLayout):
    continuous_action_slot = 'valueChanged'
    action_slot = 'sliderReleased'

    def __init__(self, field_name, parent, decimals=True, range=None):
        QtWidgets.QHBoxLayout.__init__(self)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, parent)
        self.decimals = decimals
        self.min, self.max = range or (-10, 10)
        self.field_name = field_name
        self.now_changing = False
        self.on_change_method = None
        value = getattr(prefs, self.field_name)
        if decimals:
            self.spinbox = QtWidgets.QDoubleSpinBox(parent)
            self.spinbox.setDecimals(1)
            self.slider.setRange(self.min * 10, self.max * 10)
            self.slider.setValue(value * 10)
        else:
            self.spinbox = QtWidgets.QSpinBox(parent)
            self.slider.setRange(self.min, self.max)
            self.slider.setValue(value)
        self.spinbox.setRange(self.min, self.max)
        self.spinbox.setValue(value)
        self.slider.setTickInterval(10)
        self.spinbox.setAccelerated(True)
        # noinspection PyUnresolvedReferences
        self.slider.valueChanged.connect(self.slider_changed)
        # noinspection PyUnresolvedReferences
        self.spinbox.valueChanged.connect(self.spinbox_changed)
        # noinspection PyArgumentList
        self.addWidget(self.slider)
        # noinspection PyArgumentList
        self.addWidget(self.spinbox)

    def buddy_target(self):
        return self.slider

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
        # noinspection PyUnresolvedReferences
        self.checkbox.stateChanged.connect(self.checkbox_changed)
        # noinspection PyArgumentList
        self.addWidget(self.checkbox)

    def buddy_target(self):
        return self.checkbox

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


class FileChooser(QtWidgets.QVBoxLayout):
    def __init__(self, field_name, parent=None, folders_only=False):
        QtWidgets.QVBoxLayout.__init__(self)
        self.parent_widget = parent
        self.folders_only = folders_only
        self.textbox = QtWidgets.QLineEdit()
        self.file_button = QtWidgets.QPushButton("Select Folder")
        # noinspection PyArgumentList
        self.addWidget(self.textbox)
        # noinspection PyArgumentList
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


class FieldBuilder:
    """ Class to hold static methods for building interaction widgets from preferences data.
    These widgets can go to PreferencesDialog or into some panel: each method takes 'widget' for
    this parent widget.
    """

    @staticmethod
    def build_field(key, d, widget, layout):
        f = None
        full_row = False
        value = d['value']
        label = d.get('label', '')
        if not label:
            label = key.replace('_', ' ').capitalize()
        special = d.get('special', '')
        if special:
            method = getattr(FieldBuilder, 'build_' + special, None)
            if method:
                f, full_row = method(key, d, widget)
            else:
                print('looking for method: build_' + special)

        else:
            field_type = d.get('type', '')
            f_range = d.get('range', None)
            if not field_type:
                if d.get('choices', ''):
                    field_type = 'selection'
                elif isinstance(value, float) or f_range and (isinstance(f_range[0], float) or
                                                              isinstance(f_range[1], float)):
                    field_type = 'float_slider'
                elif isinstance(value, bool):
                    field_type = 'checkbox'
                elif isinstance(value, int):
                    field_type = 'int_slider'
                elif isinstance(value, dict):
                    return
            if field_type == 'int_slider' or field_type == 'float_slider':
                if f_range:
                    minv, maxv = f_range
                elif value < -10 or value > 10:
                    minv, maxv = -200, 200
                else:
                    minv, maxv = -10, 10
                f = DoubleSlider(key, widget,
                                 decimals=field_type == 'float_slider',
                                 range=(minv, maxv))
            elif field_type == 'checkbox':
                f = CheckBox(key, widget)
            elif field_type == 'selection':
                f = Selector(key, widget, d['choices'])
            elif field_type == 'folder':
                f = FileChooser(key, widget, folders_only=True)
            elif field_type == 'text':
                f = TextInput(key, widget)

        if f:
            on_change = d.get('on_change', None)
            if on_change:
                on_change = getattr(ctrl.main, on_change, None)
                f.on_change_method = on_change
            else:
                f.on_change_method = ctrl.main.redraw
            if full_row:
                layout.addRow(QtWidgets.QLabel(label))
                layout.addRow(f)
            else:
                layout.addRow(label, f)
            help = d.get('help', None)
            if help:
                layout.addRow(HelpLabel(help, widget, f))
            return f
        return None

    @staticmethod
    def build_color_themes(key, d, widget):
        choices = [(key, data['name']) for key, data in color_themes.items()]
        return Selector(key, widget, choices), False

    @staticmethod
    def build_visualizations(key, d, widget):
        choices = list(VISUALIZATIONS.keys())
        return Selector(key, widget, choices), False

    @staticmethod
    def build_plugins(key, d, widget):
        return PluginSelector(key, widget), True
