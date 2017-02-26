# coding=utf-8
from kataja.globals import FOREST, DOCUMENT
from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl, prefs, log, qt_prefs
from kataja.saved.movables.Node import Node


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


class SetColorMode(KatajaAction):
    k_action_uid = 'set_color_theme'
    k_command = 'Change palette'
    k_tooltip = 'Change palette used for UI and drawings'

    def method(self):
        sender = self.sender()
        mode = sender.currentData()
        ctrl.main.change_color_theme(mode)

    def getter(self):
        return ctrl.settings.get('color_theme')


class RandomisePalette(KatajaAction):
    k_action_uid = 'randomise_palette'
    k_command = 'Randomise palette'
    k_tooltip = 'Roll new random colors'

    def method(self):
        ctrl.main.update_colors(randomise=True)
        sender = self.sender()
        if sender and hasattr(sender, 'reroll'):
            sender.reroll()

    def enabler(self):
        return ctrl.cm.can_randomise()

class RemoveTheme(KatajaAction):
    k_action_uid = 'remove_theme'
    k_command = 'Remove a custom color theme'
    k_tooltip = 'Remove a custom color theme'

    def method(self):
        active = ctrl.cm.theme_key
        ctrl.main.change_color_theme(ctrl.cm.default)
        ctrl.cm.remove_custom_theme(active)
        return f"Removed custom theme '{active}'."

    def enabler(self):
        return ctrl.cm.is_custom()


class RememberPalette(KatajaAction):
    k_action_uid = 'remember_palette'
    k_command = 'Store palette as favorite'
    k_tooltip = 'Create a custom palette from these colors'

    def method(self):
        key, name = ctrl.cm.create_theme_from_current_color()
        ctrl.main.change_color_theme(key)
        return "Added color theme '%s' (%s) as custom color theme." % (name, key)

    def enabler(self):
        return ctrl.cm.can_randomise()


# class CustomizeMasterStyle(KatajaAction):
#     k_action_uid = 'customize_master_style'
#     k_command = 'Customize style'
#     k_tooltip = 'Modify the styles of lines and nodes'
#     k_undoable = False
#
#     def method(self):
#         """ """
#         panel = ctrl.ui.get_panel('StylePanel')
#         panel.toggle_customization(not self.getter())
#
#     def getter(self):
#         panel = ctrl.ui.get_panel('StylePanel')
#         return panel.style_widgets.isVisible()
#
#
# class ChangeMasterStyle(KatajaAction):
#     k_action_uid = 'change_master_style'
#     k_command = 'Change drawing style'
#     k_tooltip = 'Changes the style of lines and nodes'
#     k_undoable = False
#
#     def method(self):
#         """ """
#         sender = self.sender()
#         value = sender.currentData(256)
#         ctrl.settings.set('style', value, level=DOCUMENT)
#         ctrl.forest.redraw_edges()
#         return "Changed master style to '%s'" % value
#
#     def enabler(self):
#         return ctrl.forest is not None and ctrl.settings.get('style')
#
#     def getter(self):
#         return ctrl.settings.get('style')
#

class ChangeStyleScope(KatajaAction):
    k_action_uid = 'style_scope'
    k_command = 'Select the scope for style changes'
    k_tooltip = 'Select the scope for style changes'
    k_undoable = False

    def method(self):
        """ Change drawing panel to work on selected nodes, constituent nodes or
        other available
        nodes
        """
        sender = self.sender()
        if sender:
            value = sender.currentData(256)
            ctrl.ui.set_scope(value)

    def enabler(self):
        return ctrl.forest is not None

    def getter(self):
        return ctrl.ui.active_scope


class ResetStyleInScope(KatajaAction):
    k_action_uid = 'reset_style_in_scope'
    k_command = 'Reset style to original definition'
    k_tooltip = 'Reset style to default within the selected scope'

    def method(self):
        """ Restore style to original
        :return: None
        """
        if ctrl.ui.scope_is_selection:
            for item in ctrl.selected:
                if hasattr(item, 'reset_style'):
                    item.reset_style()
        else:
            ctrl.settings.reset_node_settings(ctrl.ui.active_node_type, level=FOREST)
            ctrl.settings.reset_edge_settings(ctrl.ui.active_edge_type, level=FOREST)
        ctrl.forest.redraw_edges(ctrl.ui.active_edge_type)
        for node in ctrl.forest.nodes.values():
            node.update_label()

    def enabler(self):
        if ctrl.forest is None:
            return False
        return True


class SelectFont(KatajaAction):
    k_action_uid = 'select_font'
    k_command = 'Change label font'
    k_tooltip = 'Change font for current selection or for a node type'
    k_undoable = False

    def method(self):
        """ Change font key for current node or node type.
        :return: None
        """
        selector = self.sender()
        font_id = selector.currentData() or selector.selected_font
        if font_id.startswith('font_picker::'):
            font_id = font_id.split('::')[1]
            if not selector.font_dialog:
                selector.selected_font = font_id
                selector.start_font_dialog()
        else:
            selector.selected_font = font_id

        if ctrl.ui.scope_is_selection:
            for node in ctrl.selected:
                if isinstance(node, Node):
                    ctrl.settings.set_node_setting('font_id', font_id, node=node)
                    node.update_label()
        else:
            ctrl.settings.set_node_setting('font_id', font_id,
                                           node_type=ctrl.ui.active_node_type,
                                           level=FOREST)
            for node in ctrl.forest.nodes.values():
                node.update_label()
        font = qt_prefs.get_font(font_id)
        if selector.font_dialog:
            selector.font_dialog.setCurrentFont(font)

    def enabler(self):
        return ctrl.ui.has_nodes_in_scope()

    def getter(self):
        return ctrl.settings.active_nodes('font_id')


class SelectFontFromDialog(KatajaAction):
    k_action_uid = 'select_font_from_dialog'
    k_undoable = False

    def method(self):
        # all the work is done before action is called, action is here because we want
        # action completion effects to happen
        pass


class ChangeNodeColor(KatajaAction):
    k_action_uid = 'change_node_color'
    k_command = 'Change node color'
    k_tooltip = 'Change drawing color of nodes'
    k_undoable = False

    def method(self):
        """ Change color for selection or in currently active edge type.
        :return: None
        """
        selector = self.sender()
        color_key = selector.receive_color_selection()
        if not color_key:
            return

        # Update color for selected nodes
        if ctrl.ui.scope_is_selection:
            for node in ctrl.selected:
                if isinstance(node, Node):
                    ctrl.settings.set_node_setting('color_id', color_key, node=node)
                    node.color_id = color_key
                    node.update_label()
        # ... or update color for all nodes of this type
        else:
            ctrl.settings.set_node_setting('color_id', color_key,
                                           node_type=ctrl.ui.active_node_type,
                                           level=FOREST)
            for node in ctrl.forest.nodes.values():
                node.update_label()
        if color_key:
            log.info('(s) Changed node color to: %s' % ctrl.cm.get_color_name(color_key))

    def enabler(self):
        return ctrl.ui.has_nodes_in_scope()

    def getter(self):
        return ctrl.settings.active_nodes('color_id')
