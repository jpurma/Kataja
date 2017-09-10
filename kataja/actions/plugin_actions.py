# coding=utf-8

from kataja.singletons import ctrl, prefs
from kataja.KatajaAction import KatajaAction
from kataja.ui_support.PreferencesDialog import PreferencesDialog


# ==== Class variables for KatajaActions:
#
# k_action_uid : unique id for calling this action. required, other are optional
# k_command : text used for menu command and log feedback, unless the method returns a fdback string
# k_tooltip : tooltip text for ui element. If not given, uses k_command as tooltip.
# k_undoable : is the action undoable, default is True
# k_shortcut : keyboard shortcut given as string, e.g. 'Ctrl+x'
# k_shortcut_context : can be nothing or 'parent_and_children' if shortcut is active only when the
#                      parent widget is visible and active
# k_checkable : should the action be checkable, default False
#
# ==== Methods:
#
# method : gets called when action is triggered. If it returns a string, this is used as a command
#          feedback string, otherwise k_command is printed to log.
# getter : if there is an UI element that can show state or display value, this method returns the
#          value. These are called quite often, but with values that have to change e.g. when item
#          is dragged, you'll have to update manually.
# enabler : if enabler is defined, the action is active (also reflected into its UI elements) only
#           when enabler returns True
#


class SetPluginsPath(KatajaAction):
    k_action_uid = 'change_plugins_path'
    k_command = 'Change plugins path'
    k_undoable = False
    k_tooltip = 'Look for plugins in this folder'

    def method(self, path):
        prefs.plugins_path = path
        return "Plugin path set to %s" % path


class ManagePlugins(KatajaAction):
    k_action_uid = 'manage_plugins'
    k_command = 'Manage plugins...'
    k_undoable = False
    k_tooltip = 'View available plugins and enable or disable them'

    def method(self):
        """ Opens the large preferences dialog and switch to plugins tab, as it has the UI
        for managing plugins.
        :return: None
        """
        if not ctrl.ui.preferences_dialog:
            ctrl.ui.preferences_dialog = PreferencesDialog(ctrl.main)
        ctrl.ui.preferences_dialog.open()
        i = prefs._tab_order.index('Plugins')
        ctrl.ui.preferences_dialog.listwidget.setCurrentRow(i)
        ctrl.ui.preferences_dialog.stackwidget.setCurrentIndex(i)


class SwitchPlugin(KatajaAction):
    k_action_uid = 'switch_plugin'
    k_checkable = True
    k_undoable = False
    k_exclusive = True

    def method(self, index):
        """ Switch to another project. The action description is generated dynamically,
        not in code below.
        :param index:
        """
        pass
        # project = ctrl.main.switch_project(index)
        # log.info("Switched to project '%s'" % project.name)


class ReloadPlugin(KatajaAction):
    k_action_uid = 'reload_plugin'
    k_command = '&Reload plugins'
    k_shortcut = 'Ctrl+Shift+r'
    k_undoable = False

    def method(self):
        """ Reload currently active plugin
        :return: None
        """

        key = prefs.active_plugin_name
        if key:
            ctrl.main.disable_current_plugin()
            ctrl.main.enable_plugin(key, reload=True)
            ctrl.main.load_initial_treeset()

    def enabler(self):
        return prefs.active_plugin_name


class TogglePlugin(KatajaAction):
    k_action_uid = 'toggle_plugin'
    k_command = 'Enable plugin'
    k_command_alt = 'Disable plugin'
    k_undoable = False
    k_tooltip = "Plugins can drastically change how Kataja operates and what it tries to do. " \
                "Be sure you trust the code before enabling a plugin. "

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        return [sender.plugin_key, sender.isChecked()], kwargs

    def method(self, plugin_key, value):
        """ Enable or disable plugin identified by plugin_key
        :param plugin_key: str
        :param value: bool
        """
        if value:
            if prefs.active_plugin_name:
                ctrl.main.disable_current_plugin()
            ctrl.main.enable_plugin(plugin_key)
            ctrl.main.load_initial_treeset()
            m = "Enabled plugin '%s'" % plugin_key
        elif plugin_key == prefs.active_plugin_name:
            ctrl.main.disable_current_plugin()
            ctrl.main.load_initial_treeset()
            m = "Disabled plugin '%s'" % plugin_key
        else:
            m = ""
        if self.sender():
            parent = self.sender().parentWidget()
            while parent and not hasattr(parent, 'refresh_plugin_selection'):
                parent = parent.parentWidget()
            if hasattr(parent, 'refresh_plugin_selection'):
                parent.refresh_plugin_selection()
        return m
