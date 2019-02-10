
from kataja.ui_support.ErrorDialog import ErrorDialog
from kataja.singletons import ctrl, prefs, log, classes
import os
import sys
import json
import importlib
import traceback

# Plugins ################################

class PluginManager:
    def __init__(self):
        self.available_plugins = {}
        self.active_plugin_setup = {}
        self.active_plugin_path = ''

    def find_plugins(self, plugins_path):
        """ Find the plugins dir for the running configuration and read the metadata of plugins.
        Don't try to load actual python code yet
        :return: None
        """
        if not plugins_path:
            return
        self.available_plugins = {}
        plugins_path = os.path.normpath(plugins_path)
        os.makedirs(plugins_path, exist_ok=True)
        sys.path.append(plugins_path)
        base_ends = len(plugins_path.split(os.sep))
        for root, dirs, files in os.walk(plugins_path, followlinks=True):
            path_parts = root.split(os.sep)
            if len(path_parts) == base_ends + 1 and not path_parts[base_ends].startswith(
                    '__') and 'plugin.json' in files:
                success = False
                try:
                    plugin_file = open(os.path.join(root, 'plugin.json'), 'r')
                    data = json.load(plugin_file)
                    plugin_file.close()
                    success = True
                except:
                    log.error(sys.exc_info())
                    print(sys.exc_info())
                if success:
                    mod_name = path_parts[base_ends]
                    data['module_name'] = mod_name
                    data['module_path'] = root
                    self.available_plugins[mod_name] = data

    def set_active_plugin(self, plugin_key, enable):
        if enable:
            if prefs.active_plugin_name:
                self.disable_current_plugin()
            self.enable_plugin(plugin_key)
            ctrl.document.load_default_forests()
            return "Enabled plugin '%s'" % plugin_key
        elif plugin_key == prefs.active_plugin_name:
            self.disable_current_plugin()
            ctrl.document.load_default_forests()
            return "Disabled plugin '%s'" % plugin_key
            return ""
        pass

    def enable_plugin(self, plugin_key, reload=False):
        """ Start one plugin: save data, replace required classes with plugin classes, load data.

        """
        ctrl.plugin_settings = {}
        self.active_plugin_setup = self.load_plugin(plugin_key)
        if not self.active_plugin_setup:
            return

        ctrl.main.disable_signaling()

        ctrl.main.clear_document()

        if reload:
            available = []
            for key in sys.modules:
                if key.startswith(plugin_key):
                    available.append(key)
            if getattr(self.active_plugin_setup, 'reload_order', None):
                to_reload = [x for x in self.active_plugin_setup.reload_order if x in available]
            else:
                to_reload = sorted(available)
            for mod_name in to_reload:
                importlib.reload(sys.modules[mod_name])
                log.info('reloaded module %s' % mod_name)

        if hasattr(self.active_plugin_setup, 'plugin_classes'):
            for classobj in self.active_plugin_setup.plugin_classes:
                base_class = classes.find_base_model(classobj)
                if base_class:
                    classes.add_mapping(base_class, classobj)
                    m = "replacing %s with %s " % (base_class.__name__, classobj.__name__)
                else:
                    m = "adding %s " % classobj.__name__
                log.info(m)
        actions_module = getattr(self.active_plugin_setup, 'plugin_actions', None)
        if actions_module:
            classes.replaced_actions = {}
            classes.added_actions = []
            ctrl.ui.load_actions_from_module(actions_module,
                                             added=classes.added_actions,
                                             replaced=classes.replaced_actions)
        dir_path = os.path.dirname(os.path.realpath(self.active_plugin_setup.__file__))
        if hasattr(self.active_plugin_setup, 'help_file'):

            ctrl.ui.set_help_source(dir_path, self.active_plugin_setup.help_file)
        if hasattr(self.active_plugin_setup, 'start_plugin'):
            self.active_plugin_setup.start_plugin(self, ctrl, prefs)
        ctrl.main.create_default_document()
        ctrl.main.enable_signaling()
        self.active_plugin_path = dir_path
        prefs.active_plugin_name = plugin_key
        ctrl.ui.update_plugin_menu()

    def disable_current_plugin(self):
        """ Disable the current plugin and load the default trees instead.
        :param clear: if True, have empty treeset, if False, try to load default kataja treeset."""
        if not self.active_plugin_setup:
            print('bailing out disable plugin: no active plugin recognised')
            return
        ctrl.main.disable_signaling()
        if hasattr(self.active_plugin_setup, 'tear_down_plugin'):
            self.active_plugin_setup.tear_down_plugin(self, ctrl, prefs)
        ctrl.plugin_settings = {}
        ctrl.main.clear_document()
        ctrl.ui.unload_actions_from_module(classes.added_actions, classes.replaced_actions)
        classes.added_actions = []
        classes.replaced_actions = {}
        classes.restore_default_classes()
        ctrl.main.create_default_document()
        ctrl.main.enable_signaling()
        prefs.active_plugin_name = ''

    def load_plugin(self, plugin_module):
        setup = None
        importlib.invalidate_caches()
        if plugin_module in self.available_plugins:
            retry = True
            while retry:
                try:
                    setup = importlib.import_module(plugin_module + ".setup")
                    retry = False
                except:
                    e = sys.exc_info()
                    error_dialog = ErrorDialog(ctrl.main)
                    error_dialog.set_error('%s, line %s\n%s: %s' % (
                        plugin_module + ".setup.py", e[2].tb_lineno, e[0].__name__, e[1]))
                    error_dialog.set_traceback(traceback.format_exc())
                    retry = error_dialog.exec_()
                    setup = None
        return setup
