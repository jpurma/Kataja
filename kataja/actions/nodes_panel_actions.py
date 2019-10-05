# coding=utf-8
import random

from PyQt5 import QtCore

import kataja.globals as g
from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl, log, qt_prefs, classes
from kataja.ui_widgets.Panel import PanelAction


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
        label = ctrl.drawing.next_free_label()
        ctrl.drawing.create_node(label=label, pos=pos, node_type=ntype)
        nclass = classes.nodes[ntype]
        log.info('Added new %s.' % nclass.display_name[0])
        ctrl.forest.forest_edited()


class AddConstituentNode(AbstractAddNode):
    k_action_uid = 'add_constituent_node'
    k_command = 'Add constituent node'
    k_tooltip = 'Create new constituent node'
    node_type = g.CONSTITUENT_NODE

    def enabler(self):
        return False


class AddFeatureNode(AbstractAddNode):
    k_action_uid = 'add_feature_node'
    k_command = 'Add feature node'
    k_tooltip = 'Create new feature node'
    node_type = g.FEATURE_NODE

    def enabler(self):
        return False


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
        node_type = self.__class__.node_type
        ctrl.ui.set_active_node_setting('visible', checked, node_type=node_type)
        for node in ctrl.forest.nodes.values():
            node.update_visibility()

    def enabler(self):
        return not ctrl.ui.scope_is_selection

    def getter(self):
        node_type = self.__class__.node_type
        return ctrl.ui.get_active_node_setting('visible', node_type=node_type)


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
        edge_type = self.__class__.edge_type
        ctrl.ui.set_active_edge_setting('visible', checked, edge_type=edge_type)

    def enabler(self):
        return not ctrl.ui.scope_is_selection

    def getter(self):
        edge_type = self.__class__.edge_type
        return ctrl.ui.get_active_edge_setting('visible', edge_type=edge_type)


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
        ctrl.ui.set_active_node_setting('font_id', font_id, node_type)
        for node in ctrl.forest.nodes.values():
            if node.node_type == node_type:
                node.update_label()
        np = ctrl.ui.get_panel_by_node_type(node_type)
        if np:
            np.font_selector.set_dialog_font(qt_prefs.get_font(font_id))
            np.update_title_font(font_id)

    def enabler(self):
        return ctrl.ui.has_nodes_in_scope(self.__class__.node_type)

    def getter(self):
        my_type = self.__class__.node_type
        return ctrl.ui.get_active_node_setting('font_id', my_type)


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
        """

        # Update color for selected nodes
        node_type = self.__class__.node_type
        ctrl.ui.set_active_node_setting('color_key', color_key, node_type)
        for node in ctrl.forest.nodes.values():
            if node.node_type == node_type:
                node.update_label()
        panel = ctrl.ui.get_panel_by_node_type(node_type)
        if panel:
            panel.update_colors()

    def enabler(self):
        return ctrl.ui.has_nodes_in_scope(self.__class__.node_type)

    def getter(self):
        my_type = self.__class__.node_type
        return ctrl.ui.get_active_node_setting('color_key', node_type=my_type)


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


class ChangeEdgeShape(PanelAction):
    k_action_uid = 'change_edge_shape'
    k_command = 'Change edge shape'
    k_tooltip = 'Change shapes of lines between objects'
    k_undoable = True
    edge_type = None

    def get_edge_type(self):
        if self.__class__.edge_type:
            return self.__class__.edge_type
        else:
            return self.panel.active_edge_type

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        shape_name = sender.currentData()
        kwargs = {'level': ctrl.ui.active_scope}
        if self.__class__.edge_type:
            kwargs['edge_type'] = self.__class__.edge_type
        elif not ctrl.ui.scope_is_selection:
            kwargs['edge_type'] = self.panel.active_edge_type
        return [shape_name], kwargs

    def method(self, shape_name, level, edge_type=None):
        """ Change edge shape for selection or in currently active edge type.
        :param shape_name: str, shape_name from available shapes.
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_setting('shape_name', shape_name, edge_type)
        ctrl.forest.redraw_edges()
        if self.panel:
            self.panel.update_panel()

    def enabler(self):
        if self.__class__.edge_type:
            return ctrl.ui.has_edges_in_scope(of_type=self.__class__.edge_type)
        return self.panel and ctrl.ui.has_edges_in_scope()

    def getter(self):
        return ctrl.ui.get_active_edge_setting('shape_name', self.get_edge_type())


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
