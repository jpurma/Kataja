# coding=utf-8
from PyQt6.QtGui import QKeySequence

from kataja.KatajaAction import KatajaAction, MediatingAction
from kataja.singletons import ctrl


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


class ToggleAllPanels(KatajaAction):
    k_action_uid = 'toggle_all_panels'
    k_command = 'hide or show all panels'
    k_undoable = False


class TogglePanel(KatajaAction):
    k_action_uid = 'toggle_panel'
    k_checkable = True
    k_viewgroup = 'Panels'
    k_undoable = False
    k_exclusive = False

    def prepare_parameters(self, args, kwargs):
        """ All panels use the same action, so it should check dynamically which panel triggered
        it. Cannot use PanelAction's .panel for that.
        """
        sender = self.sender()
        if isinstance(sender, MediatingAction):
            key = sender.key
        else:
            key = sender.data
        return [key], kwargs

    def method(self, panel_id: str):
        """ Show or hide panel depending if it is visible or not
        :param panel_id: enum of panel identifiers (str)
        """
        ctrl.ui.toggle_panel(panel_id)


class ToggleHeading(KatajaAction):
    k_action_uid = 'toggle_heading'
    k_command = 'Fold heading'
    k_command_alt = 'Unfold heading'
    k_checkable = True
    k_undoable = False
    k_exclusive = False
    k_tooltip = 'Hide or show heading'
    k_tooltip_alt = 'Show this heading'

    def method(self):
        ctrl.ui.toggle_heading()


class ToggleFoldPanel(KatajaAction):
    k_action_uid = 'toggle_fold_panel'
    k_command = 'Fold panel'
    k_command_alt = 'Unfold panel'
    k_checkable = True
    k_undoable = False
    k_tooltip = 'Minimize this panel'
    k_tooltip_alt = 'Reveal this panel'

    def prepare_parameters(self, args, kwargs):
        """ All panels use the same action, so it should check dynamically which panel triggered
        it. Cannot use PanelAction's .panel for that.
        """
        sender = self.sender()
        panel_id = sender.data
        folded = sender.isChecked()
        return [panel_id, folded], kwargs

    def method(self, panel_id: str, folded: bool):
        """ Fold panel into label line or reveal the whole panel.
        """
        panel = ctrl.ui.get_panel(panel_id)
        if panel:
            panel.set_folded(folded)


class CloseEmbed(KatajaAction):
    k_action_uid = 'close_embed'
    k_command = 'Close panel'
    k_shortcut = QKeySequence(QKeySequence.StandardKey.Close)
    k_shortcut_context = 'parent_and_children'
    k_undoable = False

    def method(self):
        """ Close the currently active embedded edit panel.
        :return: None
        """
        ctrl.ui.close_active_embed()
