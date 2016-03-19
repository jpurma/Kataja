# coding=utf-8
from PyQt5 import QtWidgets, QtGui
from kataja.singletons import prefs, running_environment, ctrl


class PluginSelector(QtWidgets.QWidget):
    """ Enable and disable plugins, assumed to be used in preferences panel. Actions are
    hardcoded, not using KatajaActions at this point. """

    def __init__(self, field_name, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        layout = QtWidgets.QVBoxLayout()
        self.preferred_width = 360
        if prefs.large_ui_text:
            self.preferred_width = 460
        self.scroll_area = QtWidgets.QScrollArea(self)
        self.inner_widget = self.prepare_plugins_selection_widget()
        self.scroll_area.setWidget(self.inner_widget)
        self.scroll_area.setMinimumWidth(self.preferred_width)
        self.scroll_area.setMaximumWidth(self.preferred_width)
        layout.addWidget(self.scroll_area)
        layout.addStretch(10)
        hlayout = QtWidgets.QHBoxLayout()
        self.plugin_path = QtWidgets.QLabel('Plugin path: %s' % (prefs.plugins_path or
                                       running_environment.plugins_path),
                                       self)
        self.plugin_path.setMaximumWidth(self.preferred_width - 80)
        self.plugin_path.setWordWrap(True)
        self.plugin_path.setMinimumHeight(self.plugin_path.sizeHint().height() + 20)
        hlayout.addWidget(self.plugin_path)
        plugin_path_select = QtWidgets.QPushButton("Select folder")
        plugin_path_select.setMaximumWidth(72)
        plugin_path_select.clicked.connect(self.open_plugin_path_dialog)
        hlayout.addWidget(plugin_path_select)
        layout.addLayout(hlayout)
        refresh = QtWidgets.QPushButton('Refresh list', self)
        refresh.setMaximumWidth(80)
        refresh.clicked.connect(self.refresh_plugin_selection)
        layout.addWidget(refresh)
        self.setLayout(layout)
        self.field_name = field_name
        self.on_change_method = None

    def prepare_plugins_selection_widget(self):
        """ Draw or redraw the plugin info and their buttons based on available plugins dict """
        inner_widget = QtWidgets.QWidget(self.scroll_area)
        inner_layout = QtWidgets.QVBoxLayout()
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_widget.setLayout(inner_layout)
        height_sum = 0
        enabled_palette = ctrl.cm.get_accent_palette('accent1')
        inner_widget.setMinimumWidth(self.preferred_width - 20)
        inner_widget.setMaximumWidth(self.preferred_width - 20)
        inner_widget.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                   QtWidgets.QSizePolicy.MinimumExpanding)

        for key in sorted(ctrl.main.available_plugins.keys()):
            item = ctrl.main.available_plugins[key]
            activated = key in prefs.active_plugins
            plugin_frame = QtWidgets.QFrame(inner_widget)
            if activated:
                plugin_frame.setPalette(enabled_palette)
            else:
                plugin_frame.setBackgroundRole(QtGui.QPalette.AlternateBase)
            plugin_frame.setAutoFillBackground(True)
            hlayout = QtWidgets.QHBoxLayout()
            vlayout = QtWidgets.QVBoxLayout()
            name = QtWidgets.QLabel(item['name'])
            vlayout.addWidget(name)
            text = '%s\n v. %s by %s' % (item['description'], item['version'], item['author'])
            info = QtWidgets.QLabel(text, plugin_frame)
            info.setContentsMargins(0, 0, 0, 0)
            info.setWordWrap(True)
            plugin_frame.setMinimumWidth(self.preferred_width - 20)
            plugin_frame.setMaximumWidth(self.preferred_width - 20)
            info.setMinimumWidth(self.preferred_width - 100)
            info.setMaximumWidth(self.preferred_width - 100)
            info.setMinimumHeight(info.sizeHint().height() + 20)
            info.setSizePolicy(QtWidgets.QSizePolicy.Maximum,
                               QtWidgets.QSizePolicy.MinimumExpanding)
            vlayout.addWidget(info)
            hlayout.addLayout(vlayout)
            vlayout = QtWidgets.QVBoxLayout()
            enabled = QtWidgets.QPushButton('enable', plugin_frame)
            if activated:
                enabled.setText('enabled')
            enabled.setCheckable(True)
            enabled.setMaximumWidth(48)
            enabled.setChecked(activated)
            enabled.plugin_key = key
            ctrl.ui.connect_element_to_action(enabled, 'toggle_plugin')
            vlayout.addWidget(enabled)
            reapply = QtWidgets.QPushButton('refresh')
            reapply.setMaximumWidth(48)
            reapply.setEnabled(activated)
            vlayout.addWidget(reapply)
            hlayout.addLayout(vlayout)
            plugin_frame.setLayout(hlayout)
            height_sum += plugin_frame.sizeHint().height()
            inner_layout.addWidget(plugin_frame)
        inner_widget.setFixedHeight(height_sum)
        return inner_widget

    def open_plugin_path_dialog(self):
        dialog = QtWidgets.QFileDialog(self.parentWidget())
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if dialog.exec_():
            files = dialog.selectedFiles()
            if files:
                p = files[0]
                ctrl.main.trigger_action('change_plugins_path', p)
                self.plugin_path.setText('Plugin path: %s' % p)
                self.refresh_plugin_selection()

    def set_on_change_method(self, method):
        self.on_change_method = method

    def refresh_plugin_selection(self):
        ctrl.main.find_plugins(prefs.plugins_path or running_environment.plugins_path)
        self.inner_widget = self.prepare_plugins_selection_widget()
        self.inner_widget.show()
        self.scroll_area.setWidget(self.inner_widget)
        self.inner_widget.updateGeometry()
        self.updateGeometry()
