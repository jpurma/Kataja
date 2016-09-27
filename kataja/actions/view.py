# coding=utf-8
from PyQt5 import QtWidgets
from kataja.singletons import ctrl, prefs, log
from kataja.KatajaAction import KatajaAction
from kataja.visualizations.available import action_key


class SwitchViewMode(KatajaAction):
    k_action_uid = 'switch_view_mode'
    k_command = 'Show only syntactic objects'
    k_tooltip = 'Show only syntactic objects or show all objects (Shift+b)'
    k_shortcut = 'Shift+b'
    k_undoable = False

    def method(self, show_all_mode=None):
        """ Switch between showing only syntactic objects and showing richer representation
        :type show_all_mode: None to toggle between modes, True for all items, False for
        syntactic only
        :return:
        """
        if show_all_mode is None:
            prefs.show_all_mode = not prefs.show_all_mode
        else:
            prefs.show_all_mode = show_all_mode
        ctrl.ui.update_view_mode()

        if prefs.show_all_mode:
            prefs.temp_color_mode = ''
        else:
            if ctrl.main.color_manager.paper().value() < 100:
                prefs.temp_color_mode = 'dk_gray'
            else:
                prefs.temp_color_mode = 'gray'
        ctrl.forest.update_colors()
        if prefs.show_all_mode:
            return 'Showing all elements, including those that have no computational effects.'
        else:
            return 'Showing only syntactic objects.'

    def getter(self):
        return not prefs.show_all_mode


class SwitchBracketMode(KatajaAction):
    k_action_uid = 'bracket_mode'
    k_command = 'Show &brackets'
    k_shortcut = 'b'
    k_checkable = True

    def method(self):
        """ Brackets are visible always for non-leaves, never or for important parts
        """
        bs = ctrl.fs.bracket_style
        bs += 1
        if bs == 3:
            bs = 0
        if bs == 0:
            log.info('(b) 0: No brackets')
        elif bs == 1:
            log.info('(b) 1: Use brackets for embedded structures')
        elif bs == 2:
            log.info('(b) 2: Always use brackets')
        ctrl.fs.bracket_style = bs
        ctrl.forest.bracket_manager.update_brackets()


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
        fs = ctrl.fs

        if fs.traces_are_grouped_together and not fs.uses_multidomination:
            ctrl.forest.traces_to_multidomination()
            log.info('(t) use multidominance')
        elif (not fs.traces_are_grouped_together) and not fs.uses_multidomination:
            log.info('(t) use traces, group them to one spot')
            ctrl.forest.group_traces_to_chain_head()
            ctrl.action_redraw = False
        elif fs.uses_multidomination:
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
        if ctrl.fs.shows_merge_order():
            log.info('(o) Hide merge order')
            ctrl.fs.shows_merge_order(False)
            ctrl.forest.remove_order_features('M')
        else:
            log.info('(o) Show merge order')
            ctrl.fs.shows_merge_order(True)
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
        if ctrl.fs.shows_select_order():
            log.info('(O) Hide select order')
            ctrl.fs.shows_select_order(False)
            ctrl.forest.remove_order_features('S')
        else:
            log.info('(O) Show select order')
            ctrl.fs.shows_select_order(True)
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
            ctrl.fs._hsv = None
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


class ToggleSelectMode(KatajaAction):
    k_action_uid = 'toggle_select_mode'
    k_command = 'Select mode'
    k_shortcut = 's'
    k_undoable = False

    def method(self):
        """ """
        ctrl.graph_view.set_selection_mode(True)


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


class ToggleHighlighterProjection(KatajaAction):
    k_action_uid = 'toggle_highlighter_projection'
    k_command = 'Show projections with highlighter'
    k_undoable = False
    k_tooltip = 'Use highlighter pen-like marks to distinguish projecting nodes'

    def method(self):
        """ """
        ctrl.fs.projection_highlighter = not ctrl.fs.projection_highlighter
        ctrl.forest.update_projection_display()


class ToggleStrongLinesProjection(KatajaAction):
    k_action_uid = 'toggle_strong_lines_projection'
    k_command = 'Use thicker lines for projections'
    k_undoable = False
    k_tooltip = 'Use thicker lines to distinguish projecting nodes'

    def method(self):
        """ """
        ctrl.fs.projection_strong_lines = not ctrl.fs.projection_strong_lines
        ctrl.forest.update_projection_display()


class ToggleColorizedProjection(KatajaAction):
    k_action_uid = 'toggle_colorized_projection'
    k_command = 'Use colors for projections'
    k_undoable = False
    k_tooltip = 'Use colors to distinguish projecting nodes'

    def method(self):
        """ """
        ctrl.fs.projection_colorized = not ctrl.fs.projection_colorized
        ctrl.forest.update_projection_display()


class ToggleShowInternalAlias(KatajaAction):
    k_action_uid = 'toggle_show_internal_alias'
    k_command = '%s aliases in internal nodes'
    k_tooltip = 'Show aliases in internal nodes'

    def method(self):
        return self.toggle_label_visibility('internal', 'display_label')

    def toggle_label_visibility(self, node_location, field):
        """ Toggle labels|aliases to be visible in inner|leaf nodes.
        :param node_location: 'internal'|'leaf'
        :param field: 'label'|'display_label'
        :return: str message
        """
        v = False
        if node_location == 'internal':
            if field == 'label':
                v = not ctrl.fs.show_internal_labels
                ctrl.fs.show_internal_labels = v
            elif field == 'display_label':
                v = not ctrl.fs.show_internal_aliases
                ctrl.fs.show_internal_aliases = v
        elif node_location == 'leaf':
            if field == 'label':
                v = not ctrl.fs.show_leaf_labels
                ctrl.fs.show_leaf_labels = v
            elif field == 'display_label':
                v = not ctrl.fs.show_leaf_aliases
                ctrl.fs.show_leaf_aliases = v
        for node in ctrl.forest.nodes.values():
            node.update_label()
            node.update_label_visibility()
        if v:
            return self.command % 'Show'
        else:
            return self.command % 'Hide'


class ToggleShowInternalLabel(ToggleShowInternalAlias):
    k_action_uid = 'toggle_show_internal_label'
    k_command = '%s labels in internal nodes'
    k_tooltip = 'Show labels in internal nodes'

    def method(self):
        return self.toggle_label_visibility('internal', 'label')


class ToggleShowLeafAlias(ToggleShowInternalAlias):
    k_action_uid = 'toggle_show_leaf_alias'
    k_command = '%s aliases in leaf nodes'
    k_tooltip = 'Show aliases in leaf nodes'

    def method(self):
        return self.toggle_label_visibility('leaf', 'display_label')


class ToggleShowLeafLabel(ToggleShowInternalAlias):
    k_action_uid = 'toggle_show_leaf_label'
    k_command = '%s labels in leaf nodes'
    k_tooltip = 'Show labels in leaf nodes'

    def method(self):
        return self.toggle_label_visibility('leaf', 'label')
