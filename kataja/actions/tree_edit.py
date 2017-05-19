# coding=utf-8
import random

from PyQt5 import QtCore
from PyQt5.QtGui import QKeySequence

import kataja.globals as g
from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl, classes, log
from kataja.utils import guess_node_type
from kataja.saved.Edge import Edge
from kataja.ui_widgets.embeds.GroupLabelEmbed import GroupLabelEmbed


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

# tree_edit has various tree editing and node editing actions


class CreateNewNodeFromText(KatajaAction):
    k_action_uid = 'create_new_node_from_text'
    k_command = 'New node from text'
    #k_shortcut = 'Return'
    #k_shortcut_context = 'parent_and_children'

    def prepare_parameters(self):
        embed = self.get_ui_container()
        ci = embed.node_type_selector.currentIndex()
        node_type = embed.node_type_selector.itemData(ci)
        guess_mode = embed.guess_mode
        starting_point, focus_point = embed.get_marker_points()
        starting_point = int(starting_point.x()), int(starting_point.y())
        focus_point = int(focus_point.x()), int(focus_point.y())
        text = embed.input_line_edit.text()
        return [focus_point, text], {'starting_point': starting_point, 'node_type': node_type,
                                     'guess_mode': guess_mode}

    def method(self, focus_point, text, starting_point=None, node_type=None,
               guess_mode=True):

        """ Create new element according to elements in this embed. Can create
        constituentnodes,
        features, arrows, etc.
        :return: None
        """
        ctrl.focus_point = focus_point
        node = None
        if (not node_type) or node_type == g.GUESS_FROM_INPUT:
            if guess_mode:
                node_type = guess_node_type(text)
            else:
                node_type = g.CONSTITUENT_NODE
        if node_type == g.ARROW:
            ctrl.free_drawing.create_arrow(focus_point, starting_point, text)
        elif node_type == g.DIVIDER:
            pass
            # fixme: finish this!
        elif node_type == g.TREE:
            node = ctrl.forest.simple_parse(text)
            #if node:
            #    ctrl.forest.tree_manager.create_tree_for(node)
        else:
            node = ctrl.free_drawing.create_node(pos=focus_point, node_type=node_type, label=text)
            #if node and node_type == g.CONSTITUENT_NODE:
            #    ctrl.forest.tree_manager.create_tree_for(node)
        if node:
            node.lock()
        ctrl.ui.close_active_embed()
        ctrl.forest.forest_edited()


class RemoveMerger(KatajaAction):
    k_action_uid = 'remove_merger'
    k_command = 'Remove merger'
    k_tooltip = "Remove intermediate node (If binary branching is assumed, these shouldn't exist.)"

    def prepare_parameters(self):
        node = self.get_host()
        return [node.uid], {}

    def method(self, node_uid):
        """ In cases where there another part of binary merge is removed,
        and a stub edge is left dangling, there is an option to remove the unnecessary
        merge -- this is the triggering host.
        :param node_uid: int or string, node's unique identifier
        :return: None
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        children = node.get_children(similar=True)
        if len(children) != 1:
            log.warn('Trying to remove an intermediate monobranch node, but node "%s" '
                     'is not such node.' % node)
        ctrl.remove_from_selection(node)
        ctrl.free_drawing.delete_unnecessary_merger(node)
        ctrl.forest.forest_edited()


class RemoveNode(KatajaAction):
    k_action_uid = 'remove_node'
    k_command = 'Delete node'

    def prepare_parameters(self):
        node = self.get_host()
        return [node.uid], {}

    def method(self, node_uid):
        """ Remove given node
        :param node_uid: int or string, node's unique identifier
        :return:
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        ctrl.remove_from_selection(node)
        ctrl.free_drawing.delete_node(node, touch_edges=True)
        ctrl.forest.forest_edited()


class AddTriangle(KatajaAction):
    k_action_uid = 'add_triangle'
    k_command = 'Turn node and its children into triangle'

    def prepare_parameters(self):
        node = self.get_host()
        return [node.uid], {}

    def method(self, node_uid):
        """ Turn triggering node into triangle node
        :param node_uid: int or string, node's unique identifier
        :return: None
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        ctrl.free_drawing.add_or_update_triangle_for(node)
        ctrl.deselect_objects()
        node.update_label()


class RemoveTriangle(KatajaAction):
    k_action_uid = 'remove_triangle'
    k_command = 'Remove triangle'

    def prepare_parameters(self):
        node = self.get_host()
        return [node.uid], {}

    def method(self, node_uid: int):
        """ If triggered node is triangle node, restore it to normal
        :param node_uid: int or string, node's unique identifier
        :return: None
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        ctrl.free_drawing.remove_triangle_from(node)
        ctrl.deselect_objects()
        node.update_label()


class FinishEditingNode(KatajaAction):
    k_action_uid = 'finish_editing_node'
    k_command = 'Save changes to node'
    #k_shortcut = 'Return'
    #k_shortcut_context = 'parent_and_children'

    def method(self):
        """ Set the new values and close the constituent editing embed.
        :return: None
        """
        embed = ctrl.ui.active_embed
        if embed and embed.host:
            embed.submit_values()
        ctrl.ui.close_active_embed()
        ctrl.forest.forest_edited()


class SetProjectingNode(KatajaAction):
    k_action_uid = 'set_projecting_node'
    k_command = 'Set projecting node'
    k_tooltip = 'Set which child constituent projects to this constituent'

    def prepare_parameters(self):
        button_group = self.sender()
        heads = []
        for button in button_group.buttons():
            if button.isChecked():
                child = ctrl.forest.nodes.get(button.my_value, None)
                if child:
                    heads += child.heads
        host = self.get_host()
        return [host.uid, [x.uid for x in heads]], {}

    def method(self, node_uid: int, projecting_uids: list):
        """ Set which child constituent projects to this constituent
        :param node_uid: int or string, node's unique identifier
        :param projecting_uids: list of uids, projecting nodes' unique identifiers
        """
        if isinstance(projecting_uids, (str, int)):
            projecting_uids = [projecting_uids]
        node = ctrl.forest.nodes[node_uid]
        heads = [ctrl.forest.nodes[uid] for uid in projecting_uids]
        node.set_heads(heads)
        ctrl.forest.forest_edited()
        embed = ctrl.ui.active_embed
        if embed:
            embed.update_fields()

    def enabler(self):
        return ctrl.free_drawing_mode


# Actions for TouchAreas #######################################


class AddNodeTo(KatajaAction):
    k_action_uid = 'add_node_to'
    k_command = 'Add node to'

    def prepare_parameters(self):
        sender = self.sender()
        node = self.get_host()
        if isinstance(node, Edge):
            node = node.end
        return [node.uid, sender.action_arg], {}

    def method(self, node_uid: int, position: str):
        """ Create and add a new node into a relation with an existing node.
        :param node_uid: int, uid for existing node
        :param position: str, position must be one of the following:
            'top_left',
            'top_right',
            'sibling_left',
            'sibling_right',
            'child_left',
            'child_right'
        """
        node = ctrl.forest.nodes[node_uid]
        label = ctrl.free_drawing.next_free_label()
        new_node = ctrl.free_drawing.create_node(label=label, relative=node)
        if position == 'top_left':
            # fixme: check that this is top node
            ctrl.free_drawing.merge_to_top(node, new_node, merge_to_left=True,
                                           pos=new_node.current_position)
        elif position == 'top_right':
            ctrl.free_drawing.merge_to_top(node, new_node, merge_to_left=False,
                                           pos=new_node.current_position)
        elif position == 'sibling_left':
            ctrl.free_drawing.add_sibling_for_constituentnode(new_node, node, add_left=True)
        elif position == 'sibling_right':
            ctrl.free_drawing.add_sibling_for_constituentnode(new_node, node, add_left=False)
        elif position == 'child_left':
            ctrl.free_drawing.unary_add_child_for_constituentnode(new_node, node,
                                                                  add_left=True)
        elif position == 'child_right':
            ctrl.free_drawing.unary_add_child_for_constituentnode(new_node, node,
                                                                  add_left=False)
        ctrl.forest.forest_edited()

class MergeToTop(KatajaAction):
    k_action_uid = 'merge_to_top'
    k_command = 'Merge this node to left of topmost node'

    def prepare_parameters(self):
        node = self.get_host()
        return [node.uid], {}

    def method(self, node_uid):
        """ Merge this node to left of topmost node of node's tree. It's internal merge!
        :param node_uid: int or str, node_uid for node to merge.
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        ctrl.free_drawing.merge_to_top(node.get_top_node(), node, merge_to_left=True)
        ctrl.forest.forest_edited()


# Floating buttons ##################################


class ToggleNodeEditEmbed(KatajaAction):
    k_action_uid = 'start_editing_node'
    k_command = 'Inspect and edit node'

    def prepare_parameters(self):
        node = self.get_host()
        return [node.uid], {}

    def method(self, node_uid):
        """ Open the editing panel for this node.
        :param node_uid: int or str
        """
        node = ctrl.forest.nodes[node_uid]
        ctrl.ui.start_editing_node(node)

# Actions resulting from drop events: there may be not UI element connected to them,
# they are triggered directly in drop events. See TouchAreas


class AdjustNode(KatajaAction):
    k_action_uid = 'adjust_node'
    k_command = 'Adjust node position'

    def method(self, node_uid, x, y):
        """ Node has been dragged to this position and the current algorithm has a static position
        computed for it. Coords are relative adjustment to that computed position.
        :param node_uid:
        :param x:
        :param y:
        :return:
        """
        node = ctrl.forest.nodes[node_uid]
        node.adjustment = x, y
        if x or y:
            node.lock()
            node.update_position()
        else:
            node.release()


class MoveNode(KatajaAction):
    k_action_uid = 'move_node'
    k_command = 'Move node position'

    def method(self, node_uid, x, y):
        """ Immediately move node to given scene position. If node was using force algorithm to
        move, the node is also locked into place.
        :param node_uid:
        :param x:
        :param y:
        :return:
        """
        node = ctrl.forest.nodes[node_uid]
        node.current_position = node.from_scene_position(x, y)
        node.lock()
        node.update_position()


