# coding=utf-8
from PyQt5.QtGui import QKeySequence

from kataja.singletons import ctrl, log
from kataja.KatajaAction import KatajaAction, DynamicKatajaAction


# ==== Class variables for KatajaActions:
#
# k_action_uid : unique id for calling this action. required, other are optional
# k_command : text used for menu command and log feedback, unless the method returns a fdback string
# k_tooltip : tooltip text for ui element. If not given, uses k_command as tooltip.
# k_undoable : is the action undoable, default is True
# k_shortcut : keyboard shortcut given as string, e.g. 'Ctrl+x'
# k_shortcut_context : can be nothing or 'parent_and_children' if shortcut is active only when the
#                      parent widget is visible and active
# k_dynamic : if True, there are many instances of this action with different ids, generated by
#             code, e.g. visualisation1...9
# k_checkable : should the action be checkable, default False
# k_exclusive : use together with k_dynamic, only one of the instances can be checked at time.
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


class ToggleFullScreen(KatajaAction):
    k_action_uid = 'fullscreen_mode'
    k_command = 'Fullscreen'
    k_undoable = False
    k_shortcut = QKeySequence(QKeySequence.FullScreen)
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

