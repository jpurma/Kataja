# coding=utf-8
import random

from PyQt5 import QtCore

import kataja.globals as g
from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl, log, qt_prefs, classes
from kataja.actions.line_options_panel_actions import LinesPanelAction


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


class SetScopeForNodeStyle(KatajaAction):
    k_action_uid = 'set_scope_for_node_style'
    k_command = 'Set scope for style changes'
    k_tooltip = 'Changes here affect only selected nodes, nodes in this tree, nodes in this ' \
                'document or they are set as user defaults.'
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


class AbstractAddNode(KatajaAction):
    k_action_uid = 'add_node'
    k_command = 'Add node'
    k_tooltip = 'Add node'
    node_type = 0

    def method(self):
        """ Generic add node, gets the node type as an argument.
        :return: None
        """
        ntype = self.__class__.node_type
        pos = QtCore.QPoint(random.random() * 60 - 25, random.random() * 60 - 25)
        label = ctrl.free_drawing.next_free_label()
        node = ctrl.free_drawing.create_node(label=label, pos=pos, node_type=ntype)
        nclass = classes.nodes[ntype]
        log.info('Added new %s.' % nclass.display_name[0])
        ctrl.forest.forest_edited()


class AddConstituentNode(AbstractAddNode):
    k_action_uid = 'add_constituent_node'
    k_command = 'Add constituent node'
    k_tooltip = 'Create new constituent node'
    node_type = g.CONSTITUENT_NODE

    def enabler(self):
        if ctrl.free_drawing_mode:
            self.active_tooltip = self.tip0
        else:
            self.active_tooltip = self.k_tooltip + ' (only in Free drawing mode)'
        return ctrl.free_drawing_mode


class AddFeatureNode(AbstractAddNode):
    k_action_uid = 'add_feature_node'
    k_command = 'Add feature node'
    k_tooltip = 'Create new feature node'
    node_type = g.FEATURE_NODE

    def enabler(self):
        if ctrl.free_drawing_mode:
            self.active_tooltip = self.tip0
        else:
            self.active_tooltip = self.k_tooltip + ' (only in Free drawing mode)'
        return ctrl.free_drawing_mode


class AddGlossNode(AbstractAddNode):
    k_action_uid = 'add_gloss_node'
    k_command = 'Add gloss node'
    k_tooltip = 'Create new gloss node'
    node_type = g.GLOSS_NODE


class AddCommentNode(AbstractAddNode):
    k_action_uid = 'add_comment_node'
    k_command = 'Add comment node'
    k_tooltip = 'Create new comment node'
    node_type = g.COMMENT_NODE


class AbstractToggleVisibility(KatajaAction):
    k_action_uid = ''
    node_type = 0

    def prepare_parameters(self, args, kwargs):
        button = self.sender()
        if button:
            return [button.isChecked()], kwargs
        else:
            return [False], kwargs

    def method(self, checked):
        """ Change font key for current node or node type.
        :param font_id: str
        :return: None
        """
        node_type = self.__class__.node_type
        ctrl.settings.set_node_setting('visible', checked, node_type=node_type,
                                       level=ctrl.ui.active_scope)

    def enabler(self):
        return not ctrl.ui.scope_is_selection

    def getter(self):
        node_type = self.__class__.node_type
        return ctrl.settings.get_node_setting('visible', node_type=node_type)


class ToggleConstituentNodeVisibility(AbstractToggleVisibility):
    k_action_uid = 'toggle_constituent_visibility'
    k_command = 'Show or hide constituent nodes'
    k_tooltip = 'Show or hide constituent nodes'
    node_type = g.CONSTITUENT_NODE


class ToggleFeatureNodeVisibility(AbstractToggleVisibility):
    k_action_uid = 'toggle_feature_visibility'
    k_command = 'Show or hide feature nodes'
    k_tooltip = 'Show or hide feature nodes'
    node_type = g.FEATURE_NODE


class ToggleGlossNodeVisibility(AbstractToggleVisibility):
    k_action_uid = 'toggle_gloss_visibility'
    k_command = 'Show or hide gloss nodes'
    k_tooltip = 'Show or hide gloss nodes'
    node_type = g.GLOSS_NODE


class ToggleCommentNodeVisibility(AbstractToggleVisibility):
    k_action_uid = 'toggle_comment_visibility'
    k_command = 'Show or hide comment nodes'
    k_tooltip = 'Show or hide comment nodes'
    node_type = g.COMMENT_NODE


class AbstractToggleEdgeVisibility(KatajaAction):
    k_action_uid = ''
    node_type = 0

    def prepare_parameters(self, args, kwargs):
        button = self.sender()
        if button:
            return [button.isChecked()], kwargs
        else:
            return [False], kwargs

    def method(self, checked):
        """ Change font key for current node or node type.
        :param font_id: str
        :return: None
        """
        edge_type = self.__class__.edge_type
        ctrl.settings.set_edge_setting('visible', checked, edge_type=edge_type,
                                       level=ctrl.ui.active_scope)

    def enabler(self):
        return not ctrl.ui.scope_is_selection

    def getter(self):
        edge_type = self.__class__.edge_type
        return ctrl.settings.get_edge_setting('visible', edge_type=edge_type)


class ToggleConstituentEdgeVisibility(AbstractToggleEdgeVisibility):
    k_action_uid = 'toggle_constituent_edge_visibility'
    k_command = 'Show or hide constituent edges'
    k_tooltip = 'Show or hide constituent edges'
    edge_type = g.CONSTITUENT_EDGE


class ToggleFeatureEdgeVisibility(AbstractToggleEdgeVisibility):
    k_action_uid = 'toggle_feature_edge_visibility'
    k_command = 'Show or hide feature edges'
    k_tooltip = 'Show or hide feature edges'
    edge_type = g.FEATURE_EDGE


class ToggleGlossEdgeVisibility(AbstractToggleEdgeVisibility):
    k_action_uid = 'toggle_gloss_edge_visibility'
    k_command = 'Show or hide gloss edges'
    k_tooltip = 'Show or hide gloss edges'
    edge_type = g.GLOSS_EDGE


class ToggleCommentEdgeVisibility(AbstractToggleEdgeVisibility):
    k_action_uid = 'toggle_comment_edge_visibility'
    k_command = 'Show or hide comment edges'
    k_tooltip = 'Show or hide comment edges'
    edge_type = g.COMMENT_EDGE


class AbstractSelectFont(KatajaAction):
    k_action_uid = ''
    node_type = 0

    def prepare_parameters(self, args, kwargs):
        selector = self.sender()
        font_id = selector.currentData() or selector.selected_font
        if font_id.startswith('font_picker::'):
            font_id = font_id.split('::')[1]
            if not selector.font_dialog:
                selector.selected_font = font_id
                selector.start_font_dialog()
        else:
            selector.selected_font = font_id
        return [font_id], kwargs

    def method(self, font_id: str):
        """ Change font key for current node or node type.
        :param font_id: str
        :return: None
        """
        node_type = self.__class__.node_type
        if ctrl.ui.scope_is_selection:
            for node in ctrl.get_selected_nodes(of_type=node_type):
                ctrl.settings.set_node_setting('font_id', font_id, node=node)
                node.update_label()
        else:
            ctrl.settings.set_node_setting('font_id', font_id, node_type=node_type,
                                           level=ctrl.ui.active_scope)
            for node in ctrl.forest.nodes.values():
                node.update_label()
        np = ctrl.ui.get_panel_by_node_type(node_type)
        if np:
            np.font_selector.setCurrentFont(qt_prefs.get_font(font_id))
            np.update_title_font(font_id)

    def enabler(self):
        return ctrl.ui.has_nodes_in_scope(self.__class__.node_type)

    def getter(self):
        my_type = self.__class__.node_type
        if ctrl.ui.scope_is_selection:
            for node in ctrl.get_selected_nodes(of_type=my_type):
                if 'font_id' in node.settings:
                    return node.settings['font_id']
        return ctrl.settings.get_node_setting('font_id', node_type=my_type,
                                              level=ctrl.ui.active_scope)


class SelectConstituentFont(AbstractSelectFont):
    k_action_uid = 'select_constituent_font'
    k_command = 'Change label font for constituents'
    k_tooltip = 'Change font used for constituent labels'
    node_type = g.CONSTITUENT_NODE


class SelectFeatureFont(AbstractSelectFont):
    k_action_uid = 'select_feature_font'
    k_command = 'Change label font for features'
    k_tooltip = 'Change font used for feature labels'
    node_type = g.FEATURE_NODE


class SelectGlossFont(AbstractSelectFont):
    k_action_uid = 'select_gloss_font'
    k_command = 'Change label font for glosses'
    k_tooltip = 'Change font used for glosses'
    node_type = g.GLOSS_NODE


class SelectCommentFont(AbstractSelectFont):
    k_action_uid = 'select_comment_font'
    k_command = 'Change label font for comments'
    k_tooltip = 'Change font used for comments'
    node_type = g.COMMENT_NODE


class SelectFontFromDialog(KatajaAction):
    k_action_uid = 'select_font_from_dialog'
    k_undoable = False

    def method(self):
        # all the work is done before action is called, action is here because we want
        # action completion effects to happen
        pass


class AbstractChangeNodeColor(KatajaAction):
    k_action_uid = ''
    node_type = 0

    def prepare_parameters(self, args, kwargs):
        selector = self.sender()
        color_key = selector.receive_color_selection()
        return [color_key], kwargs

    def method(self, color_key):
        """ Change color for this type of node and its edges. Instead of setting colors
        directly, in Kataja you set items to use certain color roles, these roles are called by
        'color_key'. Roles can be content, background or accent colors. The actual color
        corresponding to role can change when the palette changes, but in general they should
        remain appropriate.

        Inspect ctrl.cm (kataja/PaletteManager.py) for further information.

        :param color_key: str, where color keys are 'content1-3', 'background1-2', 'accent1-8',
         'accent1-8tr' and 'custom1-n'
        :return: None
        """

        # Update color for selected nodes
        node_type = self.__class__.node_type
        if ctrl.ui.scope_is_selection:
            for node in ctrl.get_selected_nodes(of_type=node_type):
                ctrl.settings.set_node_setting('color_id', color_key, node=node)
                node.color_id = color_key
                node.update_label()
        # ... or update color for all nodes of this type
        else:
            ctrl.settings.set_node_setting('color_id', color_key,
                                           node_type=node_type,
                                           level=ctrl.ui.active_scope)
            for node in ctrl.forest.nodes.values():
                node.update_label()
        panel = ctrl.ui.get_panel_by_node_type(node_type)
        if panel:
            panel.update_colors()

    def enabler(self):
        return ctrl.ui.has_nodes_in_scope(self.__class__.node_type)

    def getter(self):
        my_type = self.__class__.node_type
        if ctrl.ui.scope_is_selection:
            for node in ctrl.get_selected_nodes(of_type=my_type):
                if 'color_id' in node.settings:
                    return node.settings['color_id']
        return ctrl.settings.get_node_setting('color_id', node_type=my_type,
                                              level=ctrl.ui.active_scope)


class ChangeConstituentColor(AbstractChangeNodeColor):
    k_action_uid = 'change_constituent_color'
    k_command = 'Change constituent color'
    k_tooltip = 'Change drawing color of constituent nodes'
    node_type = g.CONSTITUENT_NODE


class ChangeFeatureColor(AbstractChangeNodeColor):
    k_action_uid = 'change_feature_color'
    k_command = 'Change feature color'
    k_tooltip = 'Change drawing color of feature nodes'
    node_type = g.FEATURE_NODE


class ChangeGlossColor(AbstractChangeNodeColor):
    k_action_uid = 'change_gloss_color'
    k_command = 'Change gloss color'
    k_tooltip = 'Change drawing color of glosses'
    node_type = g.GLOSS_NODE


class ChangeCommentColor(AbstractChangeNodeColor):
    k_action_uid = 'change_comment_color'
    k_command = 'Change comment color'
    k_tooltip = 'Change drawing color for comments'
    node_type = g.COMMENT_NODE


class OpenLineOptions(KatajaAction):
    k_action_uid = 'open_line_options'
    k_command = 'Open more options'
    k_tooltip = 'Show more edge drawing options'
    k_undoable = False

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        node_type = sender.data
        return [node_type], kwargs

    def method(self, node_type: str):
        """ Open or close panel for line options.
        :param node_type: str, node type identifier
        """
        ctrl.ui.show_panel('LineOptionsPanel')
        panel = ctrl.ui.get_panel('LineOptionsPanel')
        panel.active_node_type = node_type


class ResetSettings(KatajaAction):
    k_action_uid = 'reset_settings'
    k_command = 'Reset node settings'
    k_tooltip = 'Reset settings in certain level and in all of the more specific levels'

    def prepare_parameters(self, args, kwargs):
        level = ctrl.ui.active_scope
        return [level], kwargs

    def method(self, level: int):
        """ Reset node settings in given level and in more specific levels.
        :param level: int, level enum: 66 = SELECTED, 2 = FOREST, 3 = DOCUMENT, 4 = PREFS.
        """
        log.warning('not implemented: reset_settings')


class ChangeEdgeShape(LinesPanelAction):
    k_action_uid = 'change_edge_shape'
    k_command = 'Change edge shape'
    k_tooltip = 'Change shapes of lines between objects'
    k_undoable = True
    edge_type = None

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        shape_name = sender.currentData()
        if self.__class__.edge_type:
            return [shape_name, ctrl.ui.active_scope], {
                'edge_type': self.__class__.edge_type
            }
        elif ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [shape_name], kwargs

    def method(self, shape_name, level, edge_type=None):
        """ Change edge shape for selection or in currently active edge type.
        :param shape_name: str, shape_name from available shapes.
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        level = level or ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.get_selected_edges(of_type=edge_type):
                edge.shape_name = shape_name
                edge.update_shape()
                edge.flatten_settings()
        else:
            ctrl.settings.set_edge_setting('shape_name', shape_name,
                                           edge_type=edge_type, level=level)
            ctrl.settings.flatten_shape_settings(edge_type)
            for edge in ctrl.forest.edges.values():
                if edge.edge_type == edge_type:
                    edge.flatten_settings()
            ctrl.forest.redraw_edges()
        if self.panel:
            self.panel.update_panel()

    def enabler(self):
        if self.__class__.edge_type:
            return ctrl.ui.has_edges_in_scope(of_type=self.__class__.edge_type)
        return self.panel and ctrl.ui.has_edges_in_scope()

    def getter(self):
        return self.panel.get_active_edge_setting('shape_name')

    def getter(self):
        if self.__class__.edge_type:
            if ctrl.ui.scope_is_selection:
                for edge in ctrl.get_selected_edges(of_type=self.__class__.edge_type):
                    return ctrl.settings.get_edge_setting('shape_name', edge=edge)
            return ctrl.settings.get_edge_setting('shape_name', edge_type=self.__class__.edge_type,
                                                  level=ctrl.ui.active_scope)
        else:
            return self.panel.get_active_edge_setting('shape_name')


class ChangeConstituentEdgeShape(ChangeEdgeShape):
    k_action_uid = 'change_edge_shape_for_constituents'
    k_command = 'Change shape of constituents edges'
    k_tooltip = 'Change shapes of edges that connect constituents'
    k_undoable = True
    edge_type = g.CONSTITUENT_EDGE


class ChangeFeatureEdgeShape(ChangeEdgeShape):
    k_action_uid = 'change_edge_shape_for_features'
    k_command = 'Change shape of feature edges'
    k_tooltip = 'Change shapes of edges that connect features'
    k_undoable = True
    edge_type = g.FEATURE_EDGE


class ChangeGlossEdgeShape(ChangeEdgeShape):
    k_action_uid = 'change_edge_shape_for_glosses'
    k_command = 'Change shape of gloss edges'
    k_tooltip = 'Change shapes of edges that connect glosses'
    k_undoable = True
    edge_type = g.GLOSS_EDGE


class ChangeCommentEdgeShape(ChangeEdgeShape):
    k_action_uid = 'change_edge_shape_for_comments'
    k_command = 'Change shape of comment edges'
    k_tooltip = 'Change shapes of edges that connect comments'
    k_undoable = True
    edge_type = g.COMMENT_EDGE

