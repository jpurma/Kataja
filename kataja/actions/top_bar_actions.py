# coding=utf-8
from PyQt6 import QtWidgets, QtGui

from kataja.KatajaAction import KatajaAction, MediatingAction
from kataja.globals import ViewUpdateReason
from kataja.singletons import ctrl, log, prefs
from kataja.ui_widgets.KatajaButtonGroup import KatajaButtonGroup


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
    k_action_uid = 'play_animations'
    k_command = 'Play or pause animations'
    k_shortcut = 'Space'
    k_undoable = False
    k_tooltip = '''
<p><b>Play:</b> Let nodes move into their computed places. Can be slow on large trees
 and some force-based visualisation algorithms can get stuck in a loop. </p>
<p><b>Pause:</b> Pause visualisation updates. </p>
'''
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        return [sender.isChecked()], {}

    def method(self, value):
        """ Switch between visualisation mode and free edit mode
        :param value: None to toggle between modes, True for play,
        False for pause
        :return:
        """
        if value:
            ctrl.graph_scene.start_animations()
            self.autoplay = True
        else:
            ctrl.graph_scene.stop_animations()
            self.autoplay = False
        ctrl.document.play_animations(value, from_button=True)

    def getter(self):
        return ctrl.play


class ToggleRecording(KatajaAction):
    k_action_uid = 'toggle_recording'
    k_command = 'Record as gif'
    k_shortcut = 'Ctrl+r'
    k_undoable = False
    k_checkable = True
    k_tooltip = '''
    <p><b>Record:</b> Record next actions (anything that causes redrawing) as a gif animation. </p>
    <p><b>Stop:</b> Finish recording. </p>
    '''

    def prepare_parameters(self, args, kwargs):
        if not ctrl.main.recorder.recording:
            start = True
            kwargs = {'width': prefs.animation_width,
                      'height': prefs.animation_height,
                      'every_nth': prefs.animation_skip_frames,
                      'gif': prefs.animation_gif,
                      'webp': prefs.animation_webp}
        else:
            start = False
            kwargs = {}
        return [start], kwargs

    def method(self, start, width=640, height=480, every_nth=1, gif=True, webp=False):
        self.autoplay = False
        if start:
            ctrl.main.recorder.start_recording(width, height, every_nth, gif, webp)
            return 'Started recording.'
        else:
            ctrl.main.recorder.stop_recording()
            return 'Finished recording.'

    def getter(self):
        return ctrl.main.recorder and ctrl.main.recorder.recording


class SwitchSyntaxViewMode(KatajaAction):
    k_action_uid = 'switch_syntax_view_mode'
    k_command = 'Switch between view modes offered by syntax'
    k_tooltip = 'Syntax engines may offer different views to their structures'
    k_shortcut = 'v'
    k_undoable = False
    k_checkable = True

    def method(self):
        """ Switch between showing only syntactic objects and showing richer representation """
        mode_name = ctrl.syntax.next_display_mode()
        ctrl.forest.derivation_tree.restore_derivation_step()
        return mode_name

    def getter(self):
        return ctrl.syntax.display_mode

    def enabler(self):
        return ctrl.syntax and bool(ctrl.syntax.display_modes)


class DrawArrow(KatajaAction):
    k_action_uid = 'draw_arrow'
    k_command = 'Draw arrow'
    k_shortcut = 'a'
    k_undoable = True
    k_checkable = True
    k_tooltip = 'Draw a an arrow (syntactically inert, for commenting or annotating)'

    def method(self):
        if ctrl.ui.arrow_drawing_mode:
            ctrl.ui.escape_arrow_drawing_mode()
            return 'Arrow canceled'
        else:
            ctrl.ui.start_arrow_drawing_mode()
            return 'Started arrow drawing, place the starting point (arrow FROM here).'


class ZoomToFit(KatajaAction):
    k_action_uid = 'zoom_to_fit'
    k_command = 'Zoom to fit'
    k_shortcut = 'z'
    k_undoable = False
    k_tooltip = 'Zoom to fit all elements into display.'

    def method(self):
        ctrl.view_manager.update_viewport(ViewUpdateReason.FIT_IN_TRIGGERED)


class ToggleAutomaticZoom(KatajaAction):
    k_action_uid = 'auto_zoom'
    k_command = 'Toggle automatic zooming'
    k_shortcut = 'Shift+Z'
    k_undoable = False
    k_checkable = True
    k_tooltip = '''<p><b>Auto zoom:</b></p><p><b>On:</b> Try to keep all elements in view</p><p><b>Off:</b> Manual 
    pan and zoom</p> '''

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        return [sender.isChecked()], {}

    def method(self, value):
        """ Fit graph to current window. Usually happens automatically, but also
        available as user action
        """
        ctrl.view_manager.auto_zoom = value

    def getter(self):
        return ctrl.view_manager.auto_zoom


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
        elif isinstance(sender, MediatingAction):
            return [sender.key], kwargs
        elif isinstance(sender, KatajaButtonGroup):
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
    k_shortcut = QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.FullScreen)
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
        ctrl.view_manager.update_viewport(ViewUpdateReason.FIT_IN_TRIGGERED)
