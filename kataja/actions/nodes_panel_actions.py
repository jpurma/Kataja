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
                if isinstance(node, Node) and node.node_type == self.__class__.node_type:
                    ctrl.settings.set_node_setting('font_id', font_id, node=node)
                    node.update_label()
        else:
            ctrl.settings.set_node_setting('font_id', font_id,
                                           node_type=self.__class__.node_type,
                                           level=ctrl.ui.active_scope)
            for node in ctrl.forest.nodes.values():
                node.update_label()
        font = qt_prefs.get_font(font_id)
        if selector.font_dialog:
            selector.font_dialog.setCurrentFont(font)

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
        selector.parentWidget().update_colors()
        if color_key:
            log.info('(s) Changed node color to: %s' % ctrl.cm.get_color_name(color_key))

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