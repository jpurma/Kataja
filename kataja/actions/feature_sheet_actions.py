# coding=utf-8
from PyQt5 import QtWidgets

from kataja.globals import FOREST, DOCUMENT, PREFS
from kataja.singletons import ctrl, prefs, log, classes
import kataja.globals as g
from kataja.KatajaAction import KatajaAction
from kataja.actions.line_options_panel_actions import ChangeEdgeShape


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


class SwitchFeatureCheckingMode(KatajaAction):
    k_action_uid = 'switch_feature_checking_mode'
    k_command = 'Switch how feature checking is represented'
    k_tooltip = "Features are plugged together, connected with strings or checking is not " \
                "displayed"
    k_checkable = False
    k_shortcut = 'Shift+f'

    def method(self):
        """ Toggle between no 
        :return:
        """
        current = ctrl.settings.get('feature_check_display', level=ctrl.ui.active_scope)
        if current == 2:
            current = 0
        else:
            current += 1
        ctrl.settings.set('feature_check_display', current, level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        mode_text = prefs.get_ui_text_for_choice(current, 'feature_check_display')
        return 'Feature checking mode: ' + mode_text

    def getter(self):
        return ctrl.settings.get('feature_check_display', ctrl.ui.active_scope)

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class SetFeaturesApart(KatajaAction):
    k_action_uid = 'set_features_apart'
    k_command = "Don't show feature checking"
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('feature_check_display', g.NO_CHECKING_EDGE, level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SwitchFeatureCheckingMode.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('feature_check_display', level=ctrl.ui.active_scope) == \
               g.NO_CHECKING_EDGE

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class SetFeaturesLocked(KatajaAction):
    k_action_uid = 'set_features_locked'
    k_command = "Checking features lock into each other"
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('feature_check_display', g.PUT_CHECKED_TOGETHER,
                          level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SwitchFeatureCheckingMode.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('feature_check_display', level=ctrl.ui.active_scope) == \
               g.PUT_CHECKED_TOGETHER

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class SetFeaturesConnected(KatajaAction):
    k_action_uid = 'set_features_connected'
    k_command = "Checking features are connected by line"
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('feature_check_display', g.SHOW_CHECKING_EDGE,
                          level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SwitchFeatureCheckingMode.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('feature_check_display', level=ctrl.ui.active_scope) == \
               g.SHOW_CHECKING_EDGE

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class SelectFeatureDisplayMode(KatajaAction):
    k_action_uid = 'select_feature_display_mode'
    k_command = 'Change how to display features'
    k_tooltip = 'Switch between ways to arrange features'
    k_shortcut = 'f'

    def method(self):
        f_mode = ctrl.settings.get('feature_positioning')
        f_mode += 1
        if f_mode == 4:
            f_mode = 0
        ctrl.settings.set('feature_positioning', f_mode, level=DOCUMENT)
        ctrl.forest.update_node_shapes()
        mode_text = prefs.get_ui_text_for_choice(f_mode, 'feature_positioning')
        return 'Features arranged as: ' + mode_text

    def getter(self):
        if ctrl.settings.get('node_shape') == g.CARD:
            return 3
        else:
            return ctrl.settings.get('feature_positioning')

    def enabler(self):
        return ctrl.settings.get('node_shape') != g.CARD


class SetFeaturesAsRow(KatajaAction):
    k_action_uid = 'set_features_as_row'
    k_command = "Features form a horizontal row below the constituent"
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('feature_positioning', g.HORIZONTAL_ROW,
                          level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SelectFeatureDisplayMode.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('feature_positioning', level=ctrl.ui.active_scope) == \
               g.HORIZONTAL_ROW

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class SetFeaturesAsColumn(KatajaAction):
    k_action_uid = 'set_features_as_column'
    k_command = "Features form a vertical column below the constituent"
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('feature_positioning', g.VERTICAL_COLUMN,
                          level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SelectFeatureDisplayMode.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('feature_positioning', level=ctrl.ui.active_scope) == \
               g.VERTICAL_COLUMN

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class SetFeaturesAsTwoColumns(KatajaAction):
    k_action_uid = 'set_features_as_2_columns'
    k_command = "Features form two columns, one for receiving and one for giving"
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('feature_positioning', g.TWO_COLUMNS,
                          level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SelectFeatureDisplayMode.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('feature_positioning', level=ctrl.ui.active_scope) == \
               g.TWO_COLUMNS

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class SetFeaturesHanging(KatajaAction):
    k_action_uid = 'set_features_hanging'
    k_command = "Features use physics to find their places"
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('feature_positioning', g.FREE_FLOATING,
                          level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SelectFeatureDisplayMode.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('feature_positioning', level=ctrl.ui.active_scope) == \
               g.FREE_FLOATING

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class ChangeFeatureEdgeShape(ChangeEdgeShape):
    k_action_uid = 'change_edge_shape_for_features'
    k_command = 'Change shape of feature edges'
    k_tooltip = 'Change shapes of edges that connect features'
    k_undoable = True

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        shape_name = sender.currentData()

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
        else:
            level = ctrl.ui.active_scope
        return [shape_name], {'edge_type': g.FEATURE_EDGE, 'level': level}

    def enabler(self):
        return ctrl.ui.has_edges_in_scope(of_type=g.FEATURE_EDGE)

    def getter(self):
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, classes.get('Edge')) and edge.edge_type == g.FEATURE_EDGE:
                    return ctrl.settings.cached_edge('shape_name', edge)
        return ctrl.settings.cached_edge_type('shape_name', g.FEATURE_EDGE)
