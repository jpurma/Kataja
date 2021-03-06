# coding=utf-8
import random

from kataja.KatajaAction import KatajaAction
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


class SetActiveColorMode(KatajaAction):
    k_action_uid = 'set_active_color_theme'
    k_command = 'Change palette'
    k_tooltip = 'Change palette used for UI and drawings'

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        theme = sender.currentData()
        return [theme], kwargs

    def method(self, theme: str):
        """ Set the current color theme by using color theme keys.
        :param theme: str, theme name
        :return:
        """
        print('set_active_color_theme called with ', theme)
        ctrl.main.change_color_theme(theme)

    def getter(self):
        return ctrl.ui.get_active_setting('color_theme')


class RandomisePalette(KatajaAction):
    k_action_uid = 'randomise_palette'
    k_command = 'Randomise palette'
    k_tooltip = 'Roll new random colors'

    def method(self):
        """ Roll new colors for the current color theme, if the theme allows it.
        :return:
        """
        if ctrl.cm.can_randomise():
            ctrl.main.update_colors(randomise=True)

    def getter(self):
        """ Return unicode dice faces that represent current hsv.
        :return:
        """
        if ctrl.cm:
            hsv = ctrl.cm.hsv
        else:
            hsv = [0.5, 0.5, 0.5]
        dice = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']
        random.seed(str(hsv))
        return random.choice(dice) + random.choice(dice)

    def enabler(self):
        return ctrl.cm.can_randomise()


class RemoveColorTheme(KatajaAction):
    k_action_uid = 'remove_color_theme'
    k_command = 'Remove a custom color theme'
    k_tooltip = 'Remove a custom color theme'

    def prepare_parameters(self, args, kwargs):
        return [ctrl.cm.theme_key], kwargs

    def method(self, theme_key):
        """ Remove custom color theme from theme selection. Current active theme can be found from
        ctrl.cm.theme_key. Active theme can be safely removed.
        :param theme_key: str
        :return: msg:str
        """
        if theme_key == ctrl.cm.theme_key:
            ctrl.main.change_color_theme(ctrl.cm.default)
        ctrl.cm.remove_custom_theme(theme_key)
        return f"Removed custom theme '{theme_key}'."

    def enabler(self):
        return ctrl.cm.is_custom()


class GetColorThemes(KatajaAction):
    k_action_uid = 'get_color_themes'
    k_command = 'Get available color theme keys'

    def method(self):
        """ Return two lists of keys, first for default themes and second for custom themes
        :return: list, list
        """
        return ctrl.cm.default_themes, ctrl.cm.custom_themes


class RememberPalette(KatajaAction):
    k_action_uid = 'remember_palette'
    k_command = 'Store palette as favorite'
    k_tooltip = 'Create a custom palette from these colors'

    def method(self):
        """ Store the current colors as a new custom theme.
        :return: msg:str
        """
        key, name = ctrl.cm.create_theme_from_current_color()
        ctrl.main.change_color_theme(key)
        return "Added color theme '%s' (%s) as custom color theme." % (name, key)

    def enabler(self):
        return ctrl.cm.can_randomise()
