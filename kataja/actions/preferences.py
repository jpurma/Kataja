# coding=utf-8

from kataja.singletons import ctrl, prefs
from kataja.KatajaAction import KatajaAction


class SetPluginsPath(KatajaAction):
    k_action_uid = 'change_plugins_path'
    k_command = 'Change plugins path'
    k_undoable = False
    k_tooltip = 'Look for plugins in this folder'

    def method(self, path):
        prefs.plugins_path = path
        return "Plugin path set to %s" % path


class TogglePlugin(KatajaAction):
    k_action_uid = 'toggle_plugin'
    k_command = 'Enable/disable plugin'
    k_undoable = False
    k_tooltip = "Plugins can drastically change how Kataja operates and what it tries to do. " \
                "Be sure you trust the code before enabling a plugin. "

    def method(self, key=None):
        """ Enable or disable plugins, either by giving a plugin key or by assuming that there is a
        sender widget that knows the key. """
        value = self.state_arg
        sender = self.sender()
        if not (sender or key):
            return
        elif not key:
            key = sender.plugin_key
        print('toggle plugin, key: %s, value %s' % (key, value))
        if value:
            prefs.active_plugins[key] = ctrl.main.available_plugins[key].copy()
            ctrl.main.enable_plugin(key)
            m = "Enabled plugin '%s'" % key
        elif key in prefs.active_plugins:
            del prefs.active_plugins[key]
            ctrl.main.disable_plugin(key)
            m = "Disabled plugin '%s'" % key
        else:
            m = ""
        if sender:
            parent = sender.parentWidget()
            while parent and not hasattr(parent, 'refresh_plugin_selection'):
                parent = parent.parentWidget()
            if hasattr(parent, 'refresh_plugin_selection'):
                parent.refresh_plugin_selection()
        return m

