# coding=utf-8
import random

from PyQt5 import QtCore

import kataja.globals as g
from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl, classes, log
from kataja.utils import guess_node_type
from kataja.saved.Edge import Edge
from kataja.ui_widgets.embeds.GroupLabelEmbed import GroupLabelEmbed


class AddNode(KatajaAction):
    k_action_uid = 'add_node'
    k_command = 'Add node'
    k_tooltip = 'Add %s'

    def method(self):
        """ Generic add node, gets the node type as an argument.
        :return: None
        """
        sender = self.sender()
        ntype = sender.data
        pos = QtCore.QPoint(random.random() * 60 - 25,
                            random.random() * 60 - 25)
        node = ctrl.forest.create_node(pos=pos, node_type=ntype)
        nclass = classes.nodes[ntype]
        log.info('Added new %s.' % nclass.display_name[0])


class CloseEmbed(KatajaAction):
    k_action_uid = 'close_embed'
    k_command = 'Close panel'
    k_shortcut = 'Escape'
    k_shortcut_context = 'parent_and_children'
    k_undoable = False

    def method(self):
        """ If embedded menus (node creation / editing in place, etc.) are open,
        close them.
        This is expected behavior for pressing 'esc'.
        :return: None
        """
        embed = self.get_ui_container()
        ctrl.ui.remove_ui(embed, fade=True)
        ctrl.ui.close_active_embed()


class CreateNewNodeFromText(KatajaAction):
    k_action_uid = 'create_new_node_from_text'
    k_command = 'New node from text'
    k_shortcut = 'Return'
    k_shortcut_context = 'parent_and_children'

    def method(self):

        """ Create new element according to elements in this embed. Can create
        constituentnodes,
        features, arrows, etc.
        :return: None
        """
        embed = self.get_ui_container()
        ci = embed.node_type_selector.currentIndex()
        node_type = embed.node_type_selector.itemData(ci)
        guess_mode = embed.guess_mode
        p1, p2 = embed.get_marker_points()
        text = embed.input_line_edit.text()
        ctrl.focus_point = p2
        node = None
        if guess_mode:
            node_type = guess_node_type(text)
        if node_type == g.ARROW:
            p1, p2 = embed.get_marker_points()
            text = embed.input_line_edit.text()
            ctrl.forest.create_arrow(p2, p1, text)
        elif node_type == g.DIVIDER:
            p1, p2 = embed.get_marker_points()
            # fixme: finish this!
        elif node_type == g.TREE:
            node = ctrl.forest.simple_parse(text)
            if node:
                ctrl.forest.create_tree_for(node)
        else:
            node = ctrl.forest.create_node(synobj=None, pos=p2, node_type=node_type, text=text)
            if node and node_type == g.CONSTITUENT_NODE:
                ctrl.forest.create_tree_for(node)
        if node:
            node.lock()
        ctrl.ui.close_active_embed()


class NewArrow(KatajaAction):
    k_action_uid = 'new_arrow'
    k_command = 'New arrow'
    k_shortcut = 'a'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """ Create a new arrow into embed menu's location
        """
        embed = self.get_ui_container()
        p1, p2 = embed.get_marker_points()
        text = embed.input_line_edit.text()
        ctrl.forest.create_arrow(p2, p1, text)
        ctrl.ui.close_active_embed()


class StartArrowFromNode(KatajaAction):
    k_action_uid = 'start_arrow_from_node'
    k_command = 'Add arrow from here to...'
    # k_shortcut = 'a'
    # k_shortcut_context = 'parent_and_children'

    def method(self):
        """
        :return:
        """
        button = self.get_ui_container()
        if not button:
            return
        node = button.host
        ex, ey = node.bottom_center_magnet()
        end_pos = QtCore.QPointF(ex + 20, ey + 40)
        ctrl.forest.create_arrow_from_node_to_point(node, end_pos)


class DeleteArrow(KatajaAction):
    k_action_uid = 'delete_arrow'
    k_command = 'Delete arrow'

    def method(self):
        button = self.get_ui_container()
        if not button:
            return
        edge = button.host
        if not edge:
            return
        # Then do the cutting
        ctrl.forest.disconnect_edge(edge)
        ctrl.ui.update_selections()


class NewDivider(KatajaAction):
    k_action_uid = 'new_divider'
    k_command = 'New divider'
    k_shortcut = 'd'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """ Create a new divider into embed menu's location
        """
        embed = self.get_ui_container()
        p1, p2 = embed.get_marker_points()
        ctrl.ui.close_active_embed()
        # fixme: finish this!


class EditEdgeLabelEnterText(KatajaAction):
    k_action_uid = 'edit_edge_label_enter_text'
    k_command = 'Enter'
    k_shortcut = 'Return'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """ Accept & update changes to edited edge label
        :return None:
        """
        embed = self.get_ui_container()
        if embed:
            embed.host.set_label_text(embed.input_line_edit.text())
        ctrl.ui.close_active_embed()


class DisconnectEdgeStart(KatajaAction):
    k_action_uid = 'disconnect_edge_start'
    k_command = 'Disconnect edge from start'

    def method(self):
        """ Remove connection between two nodes, this is triggered from the edge.
        :return: None
        """
        # Find the triggering edge
        button = self.get_ui_container()
        if not button:
            return
        edge = button.host
        if not edge:
            return
        # Then do the cutting
        if edge.delete_on_disconnect():
            ctrl.forest.disconnect_edge(edge)
        else:
            ctrl.forest.partial_disconnect(edge, start=True, end=False)
        ctrl.ui.update_selections()


class DisconnectEdgeEnd(KatajaAction):
    k_action_uid = 'disconnect_edge_end'
    k_command = 'Disconnect edge from end'

    def method(self):
        """ Remove connection between two nodes, this is triggered from the edge.
        :return: None
        """
        # Find the triggering edge
        button = self.get_ui_container()
        if not button:
            return
        edge = button.host
        if not edge:
            return
        # Then do the cutting
        if edge.delete_on_disconnect():
            ctrl.forest.disconnect_edge(edge)
        else:
            ctrl.forest.partial_disconnect(edge, start=False, end=True)
        ctrl.ui.update_selections()


class RemoveMerger(KatajaAction):
    k_action_uid = 'remove_merger'
    k_command = 'Remove merger'

    def method(self):
        """ In cases where there another part of binary merge is removed,
        and a stub edge is left dangling,
        there is an option to remove the unnecessary merge -- it is the
        triggering host.
        :return: None
        """
        node = self.get_host()
        if not node:
            return
        ctrl.remove_from_selection(node)
        ctrl.forest.delete_unnecessary_merger(node)


class RemoveNode(KatajaAction):
    k_action_uid = 'remove_node'
    k_command = 'Delete node'

    def method(self):
        """ Remove selected node
        :return:
        """
        node = self.get_host()
        ctrl.remove_from_selection(node)
        ctrl.forest.delete_node(node, ignore_consequences=False)


class AddTriangle(KatajaAction):
    k_action_uid = 'add_triangle'
    k_command = 'Add triangle'

    def method(self):
        """ Turn triggering node into triangle node
        :return: None
        """
        node = self.get_host()
        if not node:
            return
        log.info('folding in %s' % node.as_bracket_string())
        ctrl.forest.add_triangle_to(node)
        ctrl.deselect_objects()


class RemoveTriangle(KatajaAction):
    k_action_uid = 'remove_triangle'
    k_command = 'Remove triangle'

    def method(self):
        """ If triggered node is triangle node, restore it to normal
        :return: None
        """
        node = self.get_host()
        if not node:
            return
        log.info('unfolding from %s' % node.as_bracket_string())
        ctrl.forest.remove_triangle_from(node)
        ctrl.deselect_objects()


class FinishEditingNode(KatajaAction):
    k_action_uid = 'finish_editing_node'
    k_command = 'Save changes to node'
    k_shortcut = 'Return'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """ Set the new values and close the constituent editing embed.
        :return: None
        """
        embed = self.get_ui_container()
        if embed and embed.host:
            embed.submit_values()
        ctrl.ui.close_active_embed()


class ToggleRawEditing(KatajaAction):
    k_action_uid = 'raw_editing_toggle'
    k_command = 'Toggle edit mode'

    def method(self):
        """ This may be deprecated, but if there is raw latex/html editing
        possibility, toggle between that and visual
        editing
        :return: None
        """
        embed = ctrl.ui.get_node_edit_embed()
        embed.toggle_raw_edit(embed.raw_button.isChecked())


class SetHeadConstituent(KatajaAction):
    k_action_uid = 'constituent_set_head'
    k_command = 'Set head which constituent is head'

    def method(self):
        """
        """
        checked = self.sender().checkedButton()
        head = checked.my_value
        host = self.get_host()
        host.set_projection(head)
        embed = self.get_ui_container()
        if embed:
            embed.update_fields()

    def enabler(self):
        return ctrl.free_drawing_mode


# Actions for TouchAreas #######################################

class AddTopLeft(KatajaAction):
    k_action_uid = 'add_top_left'
    k_command = 'Add node to left'

    def method(self):
        """ """
        top = self.get_host()
        new_node = ctrl.forest.create_node(relative=top)
        ctrl.forest.merge_to_top(top, new_node, merge_to_left=True, pos=new_node.current_position)


class AddTopRight(KatajaAction):
    k_action_uid = 'add_top_right'
    k_command = 'Add node to right'

    def method(self):
        """ """
        top = self.get_host()
        new_node = ctrl.forest.create_node(relative=top)
        ctrl.forest.merge_to_top(top, new_node, merge_to_left=False, pos=new_node.current_position)


class InnerAddSiblingLeft(KatajaAction):
    k_action_uid = 'inner_add_sibling_left'
    k_command = 'Add sibling node to left'

    def method(self):
        """ """
        node = self.get_host()
        if isinstance(node, Edge):
            node = node.end
        ctrl.forest.add_sibling_for_constituentnode(node, add_left=True)


class InnerAddSiblingRight(KatajaAction):
    k_action_uid = 'inner_add_sibling_right'
    k_command = 'Add sibling node to right'

    def method(self):
        """ """
        node = self.get_host()
        if isinstance(node, Edge):
            node = node.end
        ctrl.forest.add_sibling_for_constituentnode(node, add_left=False)


class UnaryAddChildLeft(KatajaAction):
    k_action_uid = 'unary_add_child_left'
    k_command = 'Add child node to left'

    def method(self):
        """ """
        node = self.get_host()
        ctrl.forest.unary_add_child_for_constituentnode(node, add_left=True)


class UnaryAddChildRight(KatajaAction):
    k_action_uid = 'unary_add_child_right'
    k_command = 'Add child node to right'

    def method(self):
        """ """
        node = self.get_host()
        ctrl.forest.unary_add_child_for_constituentnode(node, add_left=False)


class LeafAddSiblingLeft(KatajaAction):
    k_action_uid = 'leaf_add_sibling_left'
    k_command = 'Add sibling node to left'

    def method(self):
        """ """
        node = self.get_host()
        ctrl.forest.add_sibling_for_constituentnode(node, add_left=True)


class LeafAddSiblingRight(KatajaAction):
    k_action_uid = 'leaf_add_sibling_right'
    k_command = 'Add sibling node to right'

    def method(self):
        """ """
        node = self.get_host()
        ctrl.forest.add_sibling_for_constituentnode(node, add_left=False)

# Floating buttons ##################################


class ToggleNodeEditEmbed(KatajaAction):
    k_action_uid = 'toggle_node_edit_embed'
    k_command = 'Inspect and edit node'

    def method(self):
        node = self.get_host()
        ctrl.ui.start_editing_node(node)


class ToggleGroupOptions(KatajaAction):
    k_action_uid = 'toggle_group_options'
    k_command = 'Inspect, edit and keep this group'

    def method(self):
        group = self.get_host()
        ctrl.ui.toggle_group_label_editing(group)


class ChangeGroupColor(KatajaAction):
    k_action_uid = 'change_group_color'
    k_command = 'Change color for group'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            group = self.get_host()
            color_key = sender.currentData()
            sender.model().selected_color = color_key
            if color_key:
                group.update_colors(color_key)
                embed = sender.parent()
                if embed and hasattr(embed, 'update_colors'):
                    embed.update_colors()
                log.info('Group color changed to %s' % ctrl.cm.get_color_name(color_key))

    def enabler(self):
        return ctrl.ui.active_embed and isinstance(ctrl.ui.active_embed, GroupLabelEmbed)

    def getter(self):
        if ctrl.ui.active_embed and isinstance(ctrl.ui.active_embed, GroupLabelEmbed):
            group = ctrl.ui.active_embed.host
            return group.get_color_id()


class ChangeGroupFill(KatajaAction):
    k_action_uid = 'change_group_fill'
    k_command = 'Group is filled with color'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            group = self.get_host()
            group.fill = sender.isChecked()
            group.update()


class ChangeGroupOutline(KatajaAction):
    k_action_uid = 'change_group_outline'
    k_command = 'Group has visible outline'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            group = self.get_host()
            group.outline = sender.isChecked()
            group.update()


class ChangeGroupOverlaps(KatajaAction):
    k_action_uid = 'change_group_overlaps'
    k_command = 'Allow group to overlap other groups'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            group = self.get_host()
            group.allow_overlap = sender.isChecked()
            group.update_selection(group.selection)
            group.update_shape()
            if group.allow_overlap:
                log.info('Group can overlap with other groups')
            else:
                log.info('Group cannot overlap with other groups')


class ChangeGroupChildren(KatajaAction):
    k_action_uid = 'change_group_children'
    k_command = 'Include children'
    k_tooltip = 'Include children of the selected nodes in group'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            group = self.get_host()
            group.include_children = sender.isChecked()
            group.update_selection(group.selection)
            group.update_shape()
            if group.include_children:
                log.info('Group includes children of its orginal members')
            else:
                log.info('Group does not include children')


class DeleteGroup(KatajaAction):
    k_action_uid = 'delete_group'
    k_command = 'Remove this group'

    def method(self):
        group = self.get_host()
        group.persistent = False
        ctrl.ui.close_group_label_editing(group)
        if ctrl.ui.selection_group is group:
            ctrl.deselect_objects()
            # deselecting will remove the (temporary) selection group
        else:
            ctrl.ui.remove_ui_for(group)
            ctrl.ui.remove_ui(group)


class SaveGroupChanges(KatajaAction):
    k_action_uid = 'save_group_changes'
    k_command = 'Save this group'
    k_shortcut = 'Return'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            embed = sender.parent()
            group = self.get_host() or ctrl.ui.selection_group
            ctrl.ui.close_group_label_editing(group)
            group.set_label_text(embed.input_line_edit.text())
            group.update_shape()
            name = group.get_label_text() or ctrl.cm.get_color_name(group.color_key)
            if not group.persistent:
                ctrl.forest.turn_selection_group_to_group(group)
                ctrl.deselect_objects()

            log.info("Saved group '%s'" % name)


class SetAssignedFeature(KatajaAction):
    k_action_uid = 'set_assigned_feature'
    k_command = 'Set feature as assigned'

    def method(self):
        """ """
        sender = self.sender()
        if sender:
            featurenode = self.get_host()
            value = sender.isChecked()
            featurenode.set_assigned(value)
            featurenode.update_label()
            if value:
                return "Feature '%s' set to assigned" % featurenode.name
            else:
                return "Feature '%s' set to unassigned" % featurenode.name

