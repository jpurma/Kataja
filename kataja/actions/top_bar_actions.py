# coding=utf-8
from PyQt5 import QtWidgets, QtGui

from kataja.KatajaAction import KatajaAction, TransmitAction
from kataja.globals import DOCUMENT, PREFS
from kataja.singletons import ctrl, log


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

# Undo and Redo are in edit.py


class PlayOrPause(KatajaAction):
    k_action_uid = 'play_or_pause'
    k_command = 'Play animations'
    k_command_alt = 'Pause animations'
    k_shortcut = 'Space'
    k_undoable = False
    k_tooltip = 'Let nodes to move to their computed places'
    k_tooltip_alt = 'Pause node movement and other animations'
    k_checkable = True

    def method(self, value=None):
        """ Switch between visualisation mode and free edit mode
        :param value: None to toggle between modes, True for play,
        False for pause
        :return:
        """
        if value is None:
            ctrl.set_play(not ctrl.play)
        else:
            ctrl.set_play(value)

    def getter(self):
        return ctrl.play


class SwitchEditMode(KatajaAction):
    k_action_uid = 'switch_edit_mode'
    k_command = 'Free editing mode'
    k_command_alt = 'Visualisation mode'
    k_shortcut = 'Ctrl+Shift+Space'
    k_undoable = False
    k_checkable = True
    k_tooltip = 'Trees can be created and edited in free editing mode.'
    k_tooltip_alt = 'In visualisation mode structures are built by syntax algorithms (e.g. in ' \
                    'plugins)  and only cosmetic changes are allowed.'

    def method(self, free_edit=None):
        """ Switch between visualisation mode and free edit mode
        :type free_edit: None to toggle between modes, True for free_drawing_mode,
        False for visualization
        :param state: triggering button or menu item state
        :return:
        """
        if free_edit is None:
            ctrl.free_drawing_mode = not ctrl.free_drawing_mode
        else:
            ctrl.free_drawing_mode = free_edit
        ctrl.ui.update_edit_mode()
        if ctrl.free_drawing_mode:
            return 'Free drawing mode: draw as you will, but there is no access to derivation ' \
                   'history for the structure.'
        else:
            return 'Derivation mode: you can edit the visualisation and browse the derivation ' \
                   'history, but the underlying structure cannot be changed.'

    def getter(self):
        return not ctrl.free_drawing_mode


class SwitchViewMode(KatajaAction):
    k_action_uid = 'switch_view_mode'
    k_command = 'Show all objects and their data'
    k_command_alt = 'Show only data available for syntactic computations.'
    k_tooltip = 'Some objects and some data fields in objects have no effect for' \
                ' syntactic computation. Omit them.'
    k_tooltip_alt = 'Nodes can show additional data because of a linguistic convention or ' \
                    'for other reason to help readability.'
    k_shortcut = 'Shift+b'
    k_checkable = True
    k_undoable = False

    def method(self, syntactic_mode=None):
        """ Switch between showing only syntactic objects and showing richer representation
        :param syntactic_mode: None to toggle between modes, True to hide other except syntactic
        objects and values, False to show all items
        syntactic only
        :return:
        """
        if syntactic_mode is None:
            syntactic_mode = not ctrl.settings.get('syntactic_mode', level=DOCUMENT)
        ctrl.forest.change_view_mode(syntactic_mode)

    def getter(self):
        return ctrl.settings.get('syntactic_mode', level=DOCUMENT)


class SwitchSyntaxViewMode(KatajaAction):
    k_action_uid = 'switch_syntax_view_mode'
    k_command = 'Switch between view modes offered by syntax'
    k_tooltip = 'Syntax engines may offer different views to their structures'
    k_shortcut = 'v'
    k_undoable = False
    k_checkable = True

    def method(self):
        """ Switch between showing only syntactic objects and showing richer representation
        :param syntactic_mode: None to toggle between modes, True to hide other except syntactic
        objects and values, False to show all items
        syntactic only
        :return:
        """
        mode_name = ctrl.forest.syntax.next_display_mode()
        ctrl.forest.derivation_steps.restore_derivation_step()
        return mode_name

    def getter(self):
        if ctrl.forest.syntax.display_modes:
            return ctrl.forest.syntax.syntax_display_mode

    def enabler(self):
        return bool(ctrl.forest.syntax.display_modes)


class ZoomToFit(KatajaAction):
    k_action_uid = 'zoom_to_fit'
    k_command = 'Enable automatic zoom'
    k_command_alt = 'Disable automatic zooming'
    k_shortcut = 'z'
    k_undoable = False
    k_checkable = True
    k_tooltip = 'Try to keep trees in the center of the view and wholly visible.'
    k_tooltip_alt = "You have to manually pan and zoom, but there are no unexpected shifts in view."

    def method(self):
        """ Fit graph to current window. Usually happens automatically, but also
        available as user action
        """
        old_value = ctrl.settings.get('auto_zoom', level=PREFS)
        ctrl.settings.set('auto_zoom', not old_value, level=PREFS)
        ctrl.graph_scene.fit_to_window(force=True)
        self.set_displayed_value(not old_value)

    def getter(self):
        return ctrl.settings.get('auto_zoom', level=PREFS)


class TogglePanMode(KatajaAction):
    k_action_uid = 'toggle_pan_mode'
    k_command = 'Move mode'
    k_shortcut = 'm'
    k_undoable = False
    k_checkable = True

    def method(self):
        """ """
        ctrl.graph_view.set_selection_mode(False)

    def getter(self):
        return not ctrl.graph_view.selection_mode


class ToggleSelectMode(KatajaAction):
    k_action_uid = 'toggle_select_mode'
    k_command = 'Select mode'
    k_shortcut = 'p'
    k_undoable = False
    k_checkable = True

    def method(self):
        """ """
        ctrl.graph_view.set_selection_mode(True)

    def getter(self):
        return ctrl.graph_view.selection_mode


class ChangeVisualisation(KatajaAction):
    k_action_uid = 'set_visualization'
    k_command = 'Change visualisation'
    k_exclusive = True
    k_viewgroup = 'visualizations'
    k_checkable = False

    def prepare_parameters(self, args, kwargs):
        """ There are four ui ways to trigger visualisation change. ComboBox in panel, top menu
        and buttons in top row. Top row buttons also set keyboard shortcuts 1-9, 0, +.
        :param args:
        :param kwargs:
        :return:
        """
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            return [str(sender.currentData())], kwargs
        elif isinstance(sender, TransmitAction):
            return [sender.key], kwargs
        elif isinstance(sender, QtWidgets.QButtonGroup):
            button = args[0]
            return [button.sub_type], kwargs
        else:
            print('unknown sender:', sender)
        return [], kwargs

    def method(self, visualization_key: str):
        """ Change current visualisation and play the animations.
        :param visualization_key: short identifier for visualisation
        :return:
        """
        ctrl.forest.set_visualization(visualization_key)

    def getter(self):
        if ctrl.forest and ctrl.forest.visualization:
            return ctrl.forest.visualization.say_my_name()


class ToggleFullScreen(KatajaAction):
    k_action_uid = 'fullscreen_mode'
    k_command = 'Fullscreen'
    k_undoable = False
    k_shortcut = QtGui.QKeySequence(QtGui.QKeySequence.FullScreen)
    k_checkable = True

    def method(self):
        """ Toggle between fullscreen mode and windowed mode
        :return: None
        """
        if ctrl.main.isFullScreen():
            ctrl.main.showNormal()
            log.info('(Cmd+f) windowed')
            ctrl.ui.restore_panel_positions()
        else:
            ctrl.ui.store_panel_positions()
            ctrl.main.showFullScreen()
            log.info('(Cmd+f) fullscreen')
        ctrl.graph_scene.fit_to_window(force=True)

