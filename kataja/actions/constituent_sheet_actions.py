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


class SelectLabelShape(KatajaAction):
    k_action_uid = 'select_node_shape'
    k_command = 'Rotate between node shapes'
    k_shortcut = 'b'
    k_checkable = True

    def method(self):
        """ Brackets are visible always for non-leaves, never or for important parts
        """
        bs = ctrl.settings.get('node_shape', level=ctrl.ui.active_scope)
        bs += 1
        if bs > 4:
            bs = 0
        while bs in ctrl.forest.visualization.banned_node_shapes:
            bs += 1
            if bs > 4:
                bs = 0
        if bs == g.NORMAL:
            m = 'Node shape: Simple'
        elif bs == g.SCOPEBOX:
            m = 'Node shape: Scopeboxes'
        elif bs == g.BRACKETED:
            m = 'Node shape: Bracket bars'
        elif bs == g.BOX:
            m = 'Node shape: Boxes'
        elif bs == g.CARD:
            m = 'Node shape: Cards'
            ctrl.settings.set('feature_check_display', 2, level=ctrl.ui.active_scope)

        ctrl.settings.set('node_shape', bs, level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return m

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class ActivateNoFrameNodeShape(KatajaAction):
    k_action_uid = 'set_no_frame_node_shape'
    k_command = 'Borderless nodes'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('node_shape', g.NORMAL, level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SelectLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('node_shape', level=ctrl.ui.active_scope) == g.NORMAL

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and ctrl.forest.visualization and \
               g.NORMAL not in ctrl.forest.visualization.banned_node_shapes


class ActivateScopeboxNodeShape(KatajaAction):
    k_action_uid = 'set_scopebox_node_shape'
    k_command = "Box showing node's scope"
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('node_shape', g.SCOPEBOX, level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SelectLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('node_shape', level=ctrl.ui.active_scope) == g.SCOPEBOX

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and ctrl.forest.visualization and \
               g.SCOPEBOX not in ctrl.forest.visualization.banned_node_shapes


class ActivateBracketedNodeShape(KatajaAction):
    k_action_uid = 'set_bracketed_node_shape'
    k_command = 'Bracketed nodes'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('node_shape', g.BRACKETED, level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SelectLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('node_shape', level=ctrl.ui.active_scope) == g.BRACKETED

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and ctrl.forest.visualization and \
               g.BRACKETED not in ctrl.forest.visualization.banned_node_shapes


class ActivateBoxShape(KatajaAction):
    k_action_uid = 'set_box_node_shape'
    k_command = 'Framed nodes'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('node_shape', g.BOX, level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SelectLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('node_shape', level=ctrl.ui.active_scope) == g.BOX

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and ctrl.forest.visualization and \
               g.BOX not in ctrl.forest.visualization.banned_node_shapes


class ActivateCardNodeShape(KatajaAction):
    k_action_uid = 'set_card_node_shape'
    k_command = 'Nodes as cards'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('node_shape', g.CARD, level=ctrl.ui.active_scope)
        ctrl.settings.set('feature_check_display', 2, level=ctrl.ui.active_scope)
        ctrl.forest.update_node_shapes()
        return f'{self.k_command} ({SelectLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('node_shape', level=ctrl.ui.active_scope) == g.CARD

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and ctrl.forest.visualization and \
               g.CARD not in ctrl.forest.visualization.banned_node_shapes


class SelectTraceMode(KatajaAction):
    k_action_uid = 'select_trace_strategy'
    k_command = 'Show traces'
    k_shortcut = 't'

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            trace_mode = sender.currentData()
        else:
            trace_mode = None
        return [], {'trace_mode': trace_mode}

    def method(self, trace_mode=None):
        """ Switch between multidomination, showing traces and a view where
        traces are grouped to their original position.
        :param trace_mode: int or None -- either switch to given trace mode, or rotate to next one
        if None is given.
        :return: None
        """

        level = ctrl.ui.active_scope
        if trace_mode is None:
            trace_mode = ctrl.settings.get('trace_strategy', level=level)
            trace_mode += 1
            if trace_mode == 3:
                trace_mode = 0
        ctrl.settings.set('trace_strategy', trace_mode, level=level)
        ctrl.forest.forest_edited()
        mode_text = prefs.get_ui_text_for_choice(trace_mode, 'trace_strategy')
        return f'Set trace strategy to: {mode_text}'

    def getter(self):
        return ctrl.settings.get('trace_strategy', level=ctrl.ui.active_scope)

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class SelectLinearizationMode(KatajaAction):
    k_action_uid = 'select_linearization_mode'
    k_command = 'Select linearization strategy'
    k_shortcut = 'i'

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            linearization_mode = sender.currentData()
        else:
            linearization_mode = None
        return [], {'linearization_mode': linearization_mode}

    def method(self, linearization_mode=None):
        """
        :param linearization_mode: int or None -- either switch to given trace mode, or rotate to
        next one if None is given.
        :return: None
        """

        level = ctrl.ui.active_scope
        if level == g.HIGHEST or level == g.OBJECT:
            level = g.FOREST
        if linearization_mode is None:
            linearization_mode = ctrl.settings.get('linearization_mode', level=level)
            linearization_mode += 1
            if linearization_mode == 3:
                linearization_mode = 0
        ctrl.settings.set('linearization_mode', linearization_mode, level=level)
        ctrl.forest.forest_edited()
        mode_text = prefs.get_ui_text_for_choice(linearization_mode, 'linearization_mode')
        return f'Set linearization mode: {mode_text}'

    def getter(self):
        return ctrl.settings.get('linearization_mode', level=ctrl.ui.active_scope)

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class SetVisibleLabel(KatajaAction):
    k_action_uid = 'set_visible_label'
    k_command = 'Select label text mode'
    k_undoable = True
    k_shortcut = 'l'
    k_tooltip = 'Switch what to show as label text'

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            label_mode = sender.currentData()
        else:
            label_mode = None
        return [], {'label_mode': label_mode}

    def method(self, label_mode=None, node_uid=None):
        """ """
        if node_uid:
            node = ctrl.forest.get_object_by_uid(node_uid)
            level = g.OBJECT
        else:
            level = ctrl.ui.active_scope
            node = None
        if label_mode is None:
            label_mode = ctrl.settings.get('label_text_mode', obj=node, level=level)
            syn_mode = ctrl.settings.get('syntactic_mode')
            support_secondary = ctrl.forest.syntax.supports_secondary_labels
            # some labels are not allowed in syn mode. If called without arguments, rotate to
            # next available mode.
            ok = False
            while not ok:
                label_mode += 1
                if label_mode == g.SECONDARY_LABELS and not support_secondary:
                    ok = False
                elif label_mode == g.NODE_LABELS_FOR_LEAVES and syn_mode:
                    ok = False
                elif label_mode == g.NODE_LABELS and syn_mode:
                    ok = False
                elif label_mode == g.XBAR_LABELS and syn_mode:
                    ok = False
                elif label_mode > g.SECONDARY_LABELS:
                    ok = False
                    label_mode = -1
                else:
                    ok = True
        ctrl.settings.set('label_text_mode', label_mode, obj=node, level=level)
        ctrl.forest.update_node_shapes()
        mode_text = prefs.get_ui_text_for_choice(label_mode, 'label_text_mode')
        return f'Set labeling strategy to: {mode_text}'

    def getter(self):
        return ctrl.settings.get('label_text_mode')


class SelectProjectionStyle(KatajaAction):
    k_action_uid = 'select_projection_style'
    k_command = 'Select projection style'
    k_tooltip = 'Switch between different ways to show projecting constituents'
    k_shortcut = 'Shift+P'

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            projection_style = sender.currentData()
        else:
            projection_style = None
        return [], {'projection_style': projection_style}

    def method(self, projection_style=None):
        """ """
        if projection_style is None:
            projection_style = ctrl.settings.get('projection_style', level=ctrl.ui.active_scope)
            projection_style += 1
            if projection_style == 3:
                projection_style = 0
        ctrl.settings.set('projection_style', projection_style, level=ctrl.ui.active_scope)
        ctrl.forest.projection_manager.update_projection_display()
        mode_text = prefs.get_ui_text_for_choice(projection_style, 'projection_style')
        return 'Projection style: ' + mode_text

    def getter(self):
        return ctrl.settings.get('projection_style', level=ctrl.ui.active_scope)

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class ChangeConstituentEdgeShape(ChangeEdgeShape):
    k_action_uid = 'change_edge_shape_for_constituents'
    k_command = 'Change shape of constituents edges'
    k_tooltip = 'Change shapes of edges that connect constituents'
    k_undoable = True

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        shape_name = sender.currentData()

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
        else:
            level = ctrl.ui.active_scope
        return [shape_name], {'edge_type': g.CONSTITUENT_EDGE, 'level': level}

    def enabler(self):
        return ctrl.ui.has_edges_in_scope(of_type=g.CONSTITUENT_EDGE)

    def getter(self):
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, classes.get('Edge')) and edge.edge_type == g.CONSTITUENT_EDGE:
                    return ctrl.settings.cached_edge('shape_name', edge)
        return ctrl.settings.cached_edge_type('shape_name', g.CONSTITUENT_EDGE)
