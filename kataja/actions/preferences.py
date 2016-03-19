# coding=utf-8

from kataja.singletons import ctrl, prefs

a = {}


def set_plugins_path(path):
    prefs.plugins_path = path
    return "Plugin path set to %s" % path

a['change_plugins_path'] = {'command': 'Change plugins path', 'method': set_plugins_path,
                               'trigger_args': True, 'undoable': False,
                               'tooltip': 'Look for plugins in this folder'}


def toggle_plugin(value, key=None, sender=None):
    """ Enable or disable plugins, either by giving a plugin key or by assuming that there is a
    sender widget that knows the key. """
    if not (sender or key):
        return
    elif not key:
        key = sender.plugin_key
    if value:
        prefs.active_plugins[key] = ctrl.main.available_plugins[key].copy()
        ctrl.main.enable_plugin(key)
        m = "Enabled plugin '%s'" % key
    elif key in prefs.active_plugins:
        del prefs.active_plugins[key]
        ctrl.main.disable_plugin(key)
        m = "Disabled plugin '%s'" % key
    if sender:
        parent = sender.parentWidget()
        while parent and not hasattr(parent, 'refresh_plugin_selection'):
            parent = parent.parentWidget()
        if hasattr(parent, 'refresh_plugin_selection'):
            parent.refresh_plugin_selection()
    return m

a['toggle_plugin'] = {'command': 'Enable/disable plugin', 'method': toggle_plugin,
                      'sender_arg': True, 'trigger_args': True, 'undoable': False,
                      'tooltip': 'Modify Kataja behavior as defined in the plugin, or return to '
                                 'default'}

