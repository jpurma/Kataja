# coding=utf-8
from PyQt5 import QtWidgets

from kataja.Settings import FOREST, DOCUMENT
from kataja.singletons import ctrl, prefs, log
import kataja.globals as g
from kataja.KatajaAction import KatajaAction
from kataja.visualizations.available import action_key


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


class SwitchViewMode(KatajaAction):
    k_action_uid = 'switch_view_mode'
    k_command = 'Show only syntactic objects'
    k_tooltip = 'Show only syntactic objects or show all objects (Shift+b)'
    k_shortcut = 'Shift+b'
    k_undoable = False

    def method(self, syntactic_mode=None):
        """ Switch between showing only syntactic objects and showing richer representation
        :param syntactic_mode: None to toggle between modes, True to hide other except syntactic
        objects and values, False to show all items
        syntactic only
        :return:
        """
        if syntactic_mode is None:
            syntactic_mode = not ctrl.settings.get('syntactic_mode')
        ctrl.forest.change_view_mode(syntactic_mode)
        if syntactic_mode:
            return 'Showing only syntactic objects.'
        else:
            return 'Showing all elements, including those that have no computational effects.'

    def getter(self):
        return ctrl.settings.get('syntactic_mode')


class ActivateNoFrameNodeShape(KatajaAction):
    k_action_uid = 'set_no_frame_node_shape'
    k_command = 'Borderless nodes'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('label_shape', g.NORMAL, level=DOCUMENT)
        ctrl.forest.update_label_shape()

    def getter(self):
        return ctrl.settings.get('label_shape') == g.NORMAL

    def enabler(self):
        return ctrl.forest.visualization and \
               g.NORMAL not in ctrl.forest.visualization.banned_node_shapes


class ActivateScopeboxNodeShape(KatajaAction):
    k_action_uid = 'set_scopebox_node_shape'
    k_command = "Box showing node's scope"
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('label_shape', g.SCOPEBOX, level=DOCUMENT)
        ctrl.forest.update_label_shape()

    def getter(self):
        return ctrl.settings.get('label_shape') == g.SCOPEBOX

    def enabler(self):
        return ctrl.forest.visualization and \
               g.SCOPEBOX not in ctrl.forest.visualization.banned_node_shapes


class ActivateBracketedNodeShape(KatajaAction):
    k_action_uid = 'set_bracketed_node_shape'
    k_command = 'Bracketed nodes'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('label_shape', g.BRACKETED, level=DOCUMENT)
        ctrl.forest.update_label_shape()

    def getter(self):
        return ctrl.settings.get('label_shape') == g.BRACKETED

    def enabler(self):
        return ctrl.forest.visualization and \
               g.BRACKETED not in ctrl.forest.visualization.banned_node_shapes


class ActivateBoxShape(KatajaAction):
    k_action_uid = 'set_box_node_shape'
    k_command = 'Framed nodes'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('label_shape', g.BOX, level=DOCUMENT)
        ctrl.forest.update_label_shape()

    def getter(self):
        return ctrl.settings.get('label_shape') == g.BOX

    def enabler(self):
        return ctrl.forest.visualization and \
               g.BOX not in ctrl.forest.visualization.banned_node_shapes


class ActivateCardNodeShape(KatajaAction):
    k_action_uid = 'set_card_node_shape'
    k_command = 'Nodes as cards'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('label_shape', g.CARD, level=DOCUMENT)
        ctrl.forest.update_label_shape()

    def getter(self):
        return ctrl.settings.get('label_shape') == g.CARD

    def enabler(self):
        return ctrl.forest.visualization and \
               g.CARD not in ctrl.forest.visualization.banned_node_shapes


class ToggleLabelShape(KatajaAction):
    k_action_uid = 'toggle_label_shape'
    k_command = 'Rotate between node shapes'
    k_shortcut = 'b'
    k_checkable = True

    def method(self):
        """ Brackets are visible always for non-leaves, never or for important parts
        """
        bs = ctrl.settings.get('label_shape')
        bs += 1
        if bs > 4:
            bs = 0
        while bs in ctrl.forest.visualization.banned_node_shapes:
            bs += 1
            if bs > 4:
                bs = 0

        if bs == g.NORMAL:
            m = '(b) Node shape: Simple'
        elif bs == g.SCOPEBOX:
            m = '(b) Node shape: Scopeboxes'
        elif bs == g.BRACKETED:
            m = '(b) Node shape: Bracket bars'
        elif bs == g.BOX:
            m = '(b) Node shape: Boxes'
        elif bs == g.CARD:
            m = '(b) Node shape: Cards'
        ctrl.settings.set('label_shape', bs, level=DOCUMENT)
        ctrl.forest.update_label_shape()
        return m


class SwitchTraceMode(KatajaAction):
    k_action_uid = 'trace_mode'
    k_command = 'Show &traces'
    k_shortcut = 't'
    k_checkable = True

    def method(self):
        """ Switch between multidomination, showing traces and a view where
        traces are grouped to their original position
        :return: None
        """
        grouped_traces = ctrl.settings.get('traces_are_grouped_together')
        multidomination = ctrl.settings.get('uses_multidomination')

        if grouped_traces and not multidomination:
            ctrl.forest.traces_to_multidomination()
            log.info('(t) use multidominance')
        elif (not grouped_traces) and not multidomination:
            log.info('(t) use traces, group them to one spot')
            ctrl.forest.group_traces_to_chain_head()
            ctrl.action_redraw = False
        elif multidomination:
            log.info('(t) use traces, show constituents in their base merge positions')
            ctrl.forest.multidomination_to_traces()


class ToggleMergeOrder(KatajaAction):
    k_action_uid = 'merge_order_attribute'
    k_command = 'Show merge &order'
    k_shortcut = 'o'
    k_checkable = True

    def method(self):
        """ Toggle showing numbers indicating merge orders
        :return: None
        """
        if ctrl.settings.get('show_merge_order'):
            log.info('(o) Hide merge order')
            ctrl.settings.set('show_merge_order', False, level=FOREST)
            ctrl.forest.remove_order_features('M')
        else:
            log.info('(o) Show merge order')
            ctrl.settings.set('show_merge_order', True, level=FOREST)
            ctrl.forest.add_order_features('M')


class ToggleSelectOrder(KatajaAction):
    k_action_uid = 'select_order_attribute'
    k_command = 'Show select &Order'
    k_shortcut = 'Shift+o'
    k_checkable = True

    def method(self):
        """ Toggle showing numbers indicating order of lexical selection
        :return: None
        """
        if ctrl.settings.get('show_select_order'):
            log.info('(O) Hide select order')
            ctrl.settings.set('show_select_order', False, level=FOREST)
            ctrl.forest.remove_order_features('S')
        else:
            log.info('(O) Show select order')
            ctrl.settings.set('show_select_order', True, level=FOREST)
            ctrl.forest.add_order_features('S')


class ChangeColors(KatajaAction):
    k_action_uid = 'change_colors'
    k_command = 'Change &Colors'
    k_shortcut = 'Shift+c'

    def method(self):
        """ DEPRECATED change colors -action (shift-c)
        :return: None
        """
        color_panel = ctrl.ui.get_panel('ColorThemePanel')
        if not color_panel.isVisible():
            color_panel.show()
        else:
            ctrl.settings.set('hsv', None, level=FOREST)
            ctrl.forest.update_colors()
            ctrl.main.activateWindow()
            # self.ui_support.add_message('Color seed: H: %.2f S: %.2f L: %.2f' % ( h, s,
            #  l))


class ZoomToFit(KatajaAction):
    k_action_uid = 'zoom_to_fit'
    k_command = '&Zoom to fit'
    k_shortcut = 'z'
    k_undoable = False

    def method(self):
        """ Fit graph to current window. Usually happens automatically, but also
        available as user action
        """
        ctrl.graph_scene.fit_to_window(force=True)
        return "Zoom to fit"


class TogglePanMode(KatajaAction):
    k_action_uid = 'toggle_pan_mode'
    k_command = 'Move mode'
    k_shortcut = 'm'
    k_undoable = False

    def method(self):
        """ """
        ctrl.graph_view.set_selection_mode(False)

    def getter(self):
        return not ctrl.graph_view.selection_mode


class ToggleSelectMode(KatajaAction):
    k_action_uid = 'toggle_select_mode'
    k_command = 'Select mode'
    k_shortcut = 's'
    k_undoable = False

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

    def method(self, visualization_key=None):
        sender = self.sender()
        if visualization_key is None and isinstance(sender, QtWidgets.QComboBox):
            visualization_key = str(sender.currentData())
            action = ctrl.ui.actions[action_key(visualization_key)]
            action.setChecked(True)
        if visualization_key:
            ctrl.forest.set_visualization(visualization_key)
            log.info(visualization_key)


class ToggleInnerLabels(KatajaAction):
    k_action_uid = 'toggle_inner_labels'
    k_command = 'Use labels in inner nodes'
    k_undoable = True
    k_shortcut = 'l'
    k_tooltip = 'Switch what to show as label text in inner nodes'

    def method(self):
        """ """
        now = ctrl.settings.get('inner_labels')
        now += 1
        if ctrl.forest.syntax.supports_secondary_labels:
            if now == 3:
                now = 0
        else:
            if now == 2:
                now = 0
        ctrl.settings.set('inner_labels', now, level=DOCUMENT)
        ctrl.forest.update_label_shape()

    def getter(self):
        return ctrl.settings.get('inner_labels')

class ToggleHighlighterProjection(KatajaAction):
    k_action_uid = 'toggle_highlighter_projection'
    k_command = 'Show projections with highlighter'
    k_undoable = False
    k_tooltip = 'Use highlighter pen-like marks to distinguish projecting nodes'

    def method(self):
        """ """
        ctrl.settings.set('projection_highlighter', not ctrl.settings.get(
            'projection_highlighter'), level=FOREST)
        ctrl.forest.update_projection_display()

    def getter(self):
        return ctrl.settings.get('projection_highlighter')


class ToggleStrongLinesProjection(KatajaAction):
    k_action_uid = 'toggle_strong_lines_projection'
    k_command = 'Use thicker lines for projections'
    k_undoable = False
    k_tooltip = 'Use thicker lines to distinguish projecting nodes'

    def method(self):
        """ """
        ctrl.settings.set('projection_strong_lines', not ctrl.settings.get(
            'projection_strong_lines'), level=FOREST)
        ctrl.forest.update_projection_display()

    def getter(self):
        return ctrl.settings.get('projection_strong_lines')


class ToggleColorizedProjection(KatajaAction):
    k_action_uid = 'toggle_colorized_projection'
    k_command = 'Use colors for projections'
    k_undoable = False
    k_tooltip = 'Use colors to distinguish projecting nodes'

    def method(self):
        """ """
        ctrl.settings.set('projection_colorized', not ctrl.settings.get(
            'projection_colorized'), level=FOREST)
        ctrl.forest.update_projection_display()

    def getter(self):
        return ctrl.settings.get('projection_colorized')


class ToggleShowDisplayLabel(KatajaAction):
    k_action_uid = 'toggle_show_display_label'
    k_command = '%s display labels'
    k_tooltip = 'Show display labels for nodes when available'

    def method(self):
        v = not ctrl.settings.get('show_display_labels')
        ctrl.settings.set('show_display_labels', v, level=FOREST)
        for node in ctrl.forest.nodes.values():
            node.update_label()
            node.update_label_visibility()
        if v:
            return self.command % 'Show'
        else:
            return self.command % 'Hide'

    def getter(self):
        return ctrl.settings.get('show_display_labels')


class ToggleFeatureDisplayMode(KatajaAction):
    k_action_uid = 'toggle_feature_display_mode'
    k_command = 'Change how to display features'
    k_tooltip = 'Switch between ways to arrange features'
    k_shortcut = 'f'

    def method(self):
        f_mode = ctrl.settings.get('feature_positioning')
        f_mode += 1
        if f_mode == 4:
            f_mode = 0
        ctrl.settings.set('feature_positioning', f_mode, level=DOCUMENT)
        parents = []
        shape = ctrl.settings.get('label_shape')
        for node in ctrl.forest.nodes.values():
            node.update_relations(parents, shape=shape, position=f_mode)
            node.update_label()
        for parent in parents:
            parent.gather_children()

    def getter(self):
        if ctrl.settings.get('label_shape') == g.CARD:
            return 3
        else:
            return ctrl.settings.get('feature_positioning')

    def enabler(self):
        return ctrl.settings.get('label_shape') != g.CARD

