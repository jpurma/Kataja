# coding=utf-8
import random

from PyQt5 import QtCore
from PyQt5.QtGui import QKeySequence

import kataja.globals as g
from kataja.KatajaAction import KatajaAction
from kataja.Triangle import Triangle
from kataja.singletons import ctrl, classes, log
from kataja.utils import guess_node_type
from kataja.saved.Edge import Edge
from kataja.ui_widgets.embeds.GroupLabelEmbed import GroupLabelEmbed
from kataja.ui_widgets.UIEmbed import EmbedAction


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


class ResetAdjustment(KatajaAction):
    k_action_uid = 'reset_adjustment'
    k_command = 'Remove position adjustment'

    def prepare_parameters(self, args, kwargs):
        node = self.get_host()
        return [node.uid], kwargs

    def method(self, node_uid):
        """ Remove given node
        :param node_uid: int or string, node's unique identifier
        :return:
        """
        node = ctrl.forest.nodes[node_uid]
        node.release()
        ctrl.ui.update_buttons_for_selected_node(node)


class AddTriangle(KatajaAction):
    k_action_uid = 'add_triangle'
    k_command = 'Turn node and its children into triangle'

    def prepare_parameters(self, args, kwargs):
        node = self.get_host()
        return [node.uid], kwargs

    def method(self, node_uid):
        """ Turn triggering node into triangle node
        :param node_uid: int or string, node's unique identifier
        :return: None
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        Triangle.add_or_update_triangle_for(node)
        ctrl.deselect_objects()
        node.update_label()


class RemoveTriangle(KatajaAction):
    k_action_uid = 'remove_triangle'
    k_command = 'Remove triangle'

    def prepare_parameters(self, args, kwargs):
        node = self.get_host()
        return [node.uid], kwargs

    def method(self, node_uid: int):
        """ If triggered node is triangle node, restore it to normal
        :param node_uid: int or string, node's unique identifier
        :return: None
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        Triangle.remove_triangle_from(node)
        ctrl.deselect_objects()
        node.update_label()


class FinishEditingNode(KatajaAction):
    k_action_uid = 'finish_editing_node'
    k_command = 'Save changes to node'

    # k_shortcut = 'Return'
    # k_shortcut_context = 'parent_and_children'

    def method(self):
        """ Set the new values and close the constituent editing embed.
        :return: None
        """
        embed = ctrl.ui.active_embed
        if embed and embed.host:
            embed.submit_values()
        ctrl.ui.close_active_embed()
        ctrl.forest.forest_edited()



# Floating buttons ##################################


class ToggleNodeEditEmbed(KatajaAction):
    k_action_uid = 'start_editing_node'
    k_command = 'Inspect and edit node'

    def prepare_parameters(self, args, kwargs):
        node = self.get_host()
        return [node.uid], kwargs

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

