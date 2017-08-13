# coding=utf-8
from PyQt5 import QtCore
import kataja.globals as g
from kataja.globals import FOREST, DOCUMENT
from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl, prefs, log, qt_prefs, classes
from kataja.saved.movables.Node import Node
import random

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
        pos = QtCore.QPoint(random.random() * 60 - 25,
                            random.random() * 60 - 25)
        label = ctrl.free_drawing.next_free_label()
        node = ctrl.free_drawing.create_node(label=label, pos=pos, node_type=ntype)
        nclass = classes.nodes[ntype]
        log.info('Added new %s.' % nclass.display_name[0])
        ctrl.forest.forest_edited()


class AddConstituentNode(AbstractAddNode):
    k_action_uid = 'add_constituent_node'
    k_command = 'Add constituent node'
    k_tooltip = 'Create a new constituent node'
    node_type = g.CONSTITUENT_NODE


class AddFeatureNode(AbstractAddNode):
    k_action_uid = 'add_feature_node'
    k_command = 'Add feature node'
    k_tooltip = 'Create a new feature node'
    node_type = g.FEATURE_NODE


class AddGlossNode(AbstractAddNode):
    k_action_uid = 'add_gloss_node'
    k_command = 'Add gloss node'
    k_tooltip = 'Create a new gloss node'
    node_type = g.GLOSS_NODE


class AddCommentNode(AbstractAddNode):
    k_action_uid = 'add_comment_node'
    k_command = 'Add comment node'
    k_tooltip = 'Create a new comment node'
    node_type = g.COMMENT_NODE


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
            for node in ctrl.selected:
                if isinstance(node, Node) and node.node_type == node_type:
                    ctrl.settings.set_node_setting('font_id', font_id, node=node)
                    node.update_label()
        else:
            ctrl.settings.set_node_setting('font_id', font_id,
                                           node_type=node_type,
                                           level=ctrl.ui.active_scope)
            for node in ctrl.forest.nodes.values():
                node.update_label()
        font = qt_prefs.get_font(font_id)
        font_dialog = ctrl.ui.get_font_dialog(node_type)
        if font_dialog:
            font_dialog.setCurrentFont(font)
        panel = ctrl.ui.get_panel('NodesPanel')
        if panel:
            frame = panel.get_frame_for(node_type)
            frame.update_font(font_id)

    def enabler(self):
        return ctrl.ui.has_nodes_in_scope(self.__class__.node_type)

    def getter(self):
        return ctrl.settings.active_nodes('font_id',
                                          of_type=self.__class__.node_type,
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
        if ctrl.ui.scope_is_selection:
            for node in ctrl.selected:
                if isinstance(node, Node) and node.node_type == self.__class__.node_type:
                    ctrl.settings.set_node_setting('color_id', color_key, node=node)
                    node.color_id = color_key
                    node.update_label()
        # ... or update color for all nodes of this type
        else:
            ctrl.settings.set_node_setting('color_id', color_key,
                                           node_type=self.__class__.node_type,
                                           level=ctrl.ui.active_scope)
            for node in ctrl.forest.nodes.values():
                node.update_label()
        panel = ctrl.ui.get_panel('NodesPanel')
        if panel:
            frame = panel.get_frame_for(self.__class__.node_type)
            if frame:
                frame.update_colors()

    def enabler(self):
        return ctrl.ui.has_nodes_in_scope(self.__class__.node_type)

    def getter(self):
        return ctrl.settings.active_nodes('color_id',
                                          of_type=self.__class__.node_type,
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


class FoldNodeSheet(KatajaAction):
    k_action_uid = 'fold_node_sheet'
    k_command = 'Fold node sheet'
    k_command_alt = 'Unfold node sheet'
    k_tooltip = 'Hide option sheet'
    k_tooltip_alt = 'Show option sheet'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        fold = sender.isChecked()
        node_type = sender.data
        return [node_type, fold], kwargs

    def method(self, node_type: str, fold: bool):
        """ Fold or unfold UI sheet for this type of node.
        :param node_type: str, node type identifier
        :param fold: bool, fold if True, unfold if False.
        """
        panel = ctrl.ui.get_panel('NodesPanel')
        frame = panel.get_frame_for(node_type)
        frame.set_folded(fold)
        panel.updateGeometry()


class OpenLineOptions(KatajaAction):
    k_action_uid = 'open_line_options'
    k_command = 'Open more options'
    k_tooltip = 'Show more edge drawing options'

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        node_type = sender.data
        return [node_type], kwargs

    def method(self, node_type: str):
        """ Fold or unfold UI sheet for this type of node.
        :param node_type: str, node type identifier
        :param fold: bool, fold if True, unfold if False.
        """
        ctrl.ui.show_panel('LineOptionsPanel')


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

