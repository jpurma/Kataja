# coding=utf-8
import random

from PyQt5 import QtCore

import kataja.globals as g
from kataja.actions._utils import get_ui_container, get_host
from kataja.singletons import ctrl, classes, log
from kataja.utils import guess_node_type
from kataja.saved.Edge import Edge
from kataja.ui_widgets.embeds.GroupLabelEmbed import GroupLabelEmbed

a = {}


def add_node(sender=None, ntype=None, pos=None):
    """ Generic add node, gets the node type as an argument.
    :param sender: field that called this action
    :param ntype: node type (str/int, see globals), if not provided,
    evaluates which add_node button was clicked.
    :param pos: QPoint for where the node should first appear
    :return: None
    """
    if not ntype:
        ntype = sender.data
    if not pos:
        pos = QtCore.QPoint(random.random() * 60 - 25,
                            random.random() * 60 - 25)
    node = ctrl.forest.create_node(pos=pos, node_type=ntype)
    nclass = classes.nodes[ntype]
    log.info('Added new %s.' % nclass.display_name[0])


a['add_node'] = {'command': 'Add node', 'sender_arg': True, 'method': add_node,
                 'tooltip': 'Add %s'}


def close_embeds(sender=None):
    """ If embedded menus (node creation / editing in place, etc.) are open,
    close them.
    This is expected behavior for pressing 'esc'.
    :param sender: field that called this action
    :return: None
    """
    embed = get_ui_container(sender)
    ctrl.ui.remove_ui(embed, fade=True)
    ctrl.ui.close_active_embed()


a['close_embed'] = {'command': 'Close panel', 'method': close_embeds,
                    'shortcut': 'Escape', 'undoable': False, 'sender_arg': True,
                    'shortcut_context': 'parent_and_children'}


def new_element_accept(sender=None):
    """ Create new element according to elements in this embed. Can create
    constituentnodes,
    features, arrows, etc.
    :param sender: field that called this action
    :return: None
    """

    embed = get_ui_container(sender)
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
        create_new_arrow(sender)
    elif node_type == g.DIVIDER:
        create_new_divider(sender)
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


a['create_new_node_from_text'] = {'command': 'New node from text', 'method': new_element_accept,
                                  'sender_arg': True, 'shortcut': 'Return',
                                  'shortcut_context': 'parent_and_children'}


def create_new_arrow(sender=None):
    """ Create a new arrow into embed menu's location
    :param sender: field that called this action
    :return: None
    """
    embed = get_ui_container(sender)
    p1, p2 = embed.get_marker_points()
    text = embed.input_line_edit.text()
    ctrl.forest.create_arrow(p2, p1, text)
    ctrl.ui.close_active_embed()


a['new_arrow'] = {'command': 'New arrow', 'sender_arg': True,
                  'method': create_new_arrow, 'shortcut': 'a',
                  'shortcut_context': 'parent_and_children'}


def create_new_divider(sender=None):
    """ Create a new divider into embed menu's location
    :param sender: field that called this action
    :return: None
    """
    embed = get_ui_container(sender)
    p1, p2 = embed.get_marker_points()
    ctrl.ui.close_active_embed()
    # fixme: finish this!


a['new_divider'] = {'command': 'New divider', 'method': create_new_divider,
                    'sender_arg': True, 'shortcut': 'd',
                    'shortcut_context': 'parent_and_children'}


def edge_label_accept(sender=None):
    """ Accept & update changes to edited edge label
    :param sender: field that called this action
    :return None:
    """
    embed = get_ui_container(sender)
    if embed:
        embed.host.set_label_text(embed.input_line_edit.text())
    ctrl.ui.close_active_embed()


a['edit_edge_label_enter_text'] = {'command': 'Enter',
                                   'method': edge_label_accept,
                                   'sender_arg': True, 'shortcut': 'Return',
                                   'shortcut_context': 'parent_and_children'}


def change_edge_ending(self, which_end, value):
    """

    :param which_end:
    :param value:
    :return:
    """
    if ctrl.ui.scope_is_selection:
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.ending(which_end, value)
                edge.update_shape()
    else:
        if which_end == 'start':
            ctrl.fs.set_edge_info(ctrl.ui.active_edge_type, 'arrowhead_at_start', value)
        elif which_end == 'end':
            ctrl.fs.set_edge_info(ctrl.ui.active_edge_type, 'arrowhead_at_end', value)
        else:
            print('Invalid place for edge ending: ', which_end)


# fixme: No UI to call this
a['change_edge_ending'] = {'command': 'Change edge ending',
                           'method': change_edge_ending}


def disconnect_edge_start(sender=None):
    """ Remove connection between two nodes, this is triggered from the edge.
    :return: None
    """
    # Find the triggering edge
    button = get_ui_container(sender)
    if not button:
        return
    edge = button.host
    old_start = edge.start
    if not edge:
        return
    # Then do the cutting
    if edge.delete_on_disconnect():
        ctrl.forest.disconnect_edge(edge)
    else:
        ctrl.forest.partial_disconnect(edge, start=True, end=False)
    ctrl.ui.update_selections()

a['disconnect_edge_start'] = {'command': 'Disconnect edge start', 'sender_arg': True,
                              'method': disconnect_edge_start}


def disconnect_edge_end(sender=None):
    """ Remove connection between two nodes, this is triggered from the edge.
    :return: None
    """
    # Find the triggering edge
    button = get_ui_container(sender)
    if not button:
        return
    edge = button.host
    old_start = edge.start
    if not edge:
        return
    # Then do the cutting
    if edge.delete_on_disconnect():
        ctrl.forest.disconnect_edge(edge)
    else:
        ctrl.forest.partial_disconnect(edge, start=False, end=True)
    ctrl.ui.update_selections()

a['disconnect_edge_end'] = {'command': 'Disconnect edge end', 'sender_arg': True,
                            'method': disconnect_edge_end}


def remove_merger(sender=None):
    """ In cases where there another part of binary merge is removed,
    and a stub edge is left dangling,
    there is an option to remove the unnecessary merge -- it is the
    triggering host.
    :return: None
    """
    node = get_host(sender)
    if not node:
        return
    ctrl.remove_from_selection(node)
    ctrl.forest.delete_unnecessary_merger(node)


a['remove_merger'] = {'command': 'Remove merger', 'sender_arg': True,
                      'method': remove_merger}


def remove_node(sender=None):
    """ Remove selected node
    :param sender:
    :return:
    """
    node = get_host(sender)
    ctrl.remove_from_selection(node)
    ctrl.forest.delete_node(node, ignore_consequences=False)

a['remove_node'] = {'command': 'Delete node', 'sender_arg': True, 'method': remove_node}


def add_triangle(sender=None):
    """ Turn triggering node into triangle node
    :return: None
    """
    node = get_host(sender)
    if not node:
        return
    log.info('folding in %s' % node.as_bracket_string())
    ctrl.forest.add_triangle_to(node)
    ctrl.deselect_objects()


a['add_triangle'] = {'command': 'Add triangle', 'sender_arg': True,
                     'method': add_triangle}


def remove_triangle(sender=None):
    """ If triggered node is triangle node, restore it to normal
    :return: None
    """
    node = get_host(sender)
    if not node:
        return
    log.info('unfolding from %s' % node.as_bracket_string())
    ctrl.forest.remove_triangle_from(node)
    ctrl.deselect_objects()


a['remove_triangle'] = {'command': 'Remove triangle', 'sender_arg': True,
                        'method': remove_triangle}


def finish_editing_node(sender=None):
    """ Set the new values and close the constituent editing embed.
    :return: None
    """
    embed = get_ui_container(sender)
    if embed and embed.host:
        embed.submit_values()
    ctrl.ui.close_active_embed()


a['finish_editing_node'] = {'command': 'Save changes to node',
                            'method': finish_editing_node, 'shortcut': 'Return',
                            'sender_arg': True,
                            'shortcut_context': 'parent_and_children'}


def toggle_raw_editing():
    """ This may be deprecated, but if there is raw latex/html editing
    possibility, toggle between that and visual
    editing
    :return: None
    """
    embed = ctrl.ui.get_node_edit_embed()
    embed.toggle_raw_edit(embed.raw_button.isChecked())


a['raw_editing_toggle'] = {'command': 'Toggle edit mode',
                           'method': toggle_raw_editing}


def constituent_set_head(sender=None):
    """

    :return:
    """
    checked = sender.checkedButton()
    head = checked.my_value
    host = get_host(sender)
    host.set_projection(head)
    embed = get_ui_container(sender)
    if embed:
        embed.update_fields()


def can_set_head():
    return ctrl.free_drawing_mode

a['constituent_set_head'] = {'command': 'Set head for inheritance',
                             'method': constituent_set_head,
                             'sender_arg': True,
                             'enabler': can_set_head}

# Actions for TouchAreas #######################################


def add_top_left(sender=None):
    """
    :type event: QMouseEvent
     """
    top = get_host(sender)
    new_node = ctrl.forest.create_node(relative=top)
    ctrl.forest.merge_to_top(top, new_node, merge_to_left=True, pos=new_node.current_position)

a['add_top_left'] = {'command': 'Add node to left',
                     'method': add_top_left,
                     'sender_arg': True}


def add_top_right(sender=None):
    """
    :type event: QMouseEvent
     """
    top = get_host(sender)
    new_node = ctrl.forest.create_node(relative=top)
    ctrl.forest.merge_to_top(top, new_node, merge_to_left=False, pos=new_node.current_position)

a['add_top_right'] = {'command': 'Add node to right',
                      'method': add_top_right,
                      'sender_arg': True}


def inner_add_sibling_left(sender=None):
    """

    :param sender:
    :return:
    """
    node = get_host(sender)
    if isinstance(node, Edge):
        node = node.end
    ctrl.forest.add_sibling_for_constituentnode(node, add_left=True)

a['inner_add_sibling_left'] = {'command': 'Add sibling node to left',
                               'method': inner_add_sibling_left,
                               'sender_arg': True}


def inner_add_sibling_right(sender=None):
    """

    :param sender:
    :return:
    """
    node = get_host(sender)
    if isinstance(node, Edge):
        node = node.end
    ctrl.forest.add_sibling_for_constituentnode(node, add_left=False)

a['inner_add_sibling_right'] = {'command': 'Add sibling node to right',
                                'method': inner_add_sibling_right,
                                'sender_arg': True}


def unary_add_child_left(sender=None):
    """

    :param sender:
    :return:
    """
    node = get_host(sender)
    ctrl.forest.unary_add_child_for_constituentnode(node, add_left=True)

a['unary_add_child_left'] = {'command': 'Add child node to left',
                             'method': unary_add_child_left,
                             'sender_arg': True}


def unary_add_child_right(sender=None):
    """

    :param sender:
    :return:
    """
    node = get_host(sender)
    ctrl.forest.unary_add_child_for_constituentnode(node, add_left=False)

a['unary_add_child_right'] = {'command': 'Add child node to right',
                                'method': unary_add_child_right,
                                'sender_arg': True}


def leaf_add_sibling_left(sender=None):
    """

    :param sender:
    :return:
    """
    node = get_host(sender)
    ctrl.forest.add_sibling_for_constituentnode(node, add_left=True)

a['leaf_add_sibling_left'] = {'command': 'Add sibling node to left',
                              'method': leaf_add_sibling_left,
                              'sender_arg': True}


def leaf_add_sibling_right(sender=None):
    """

    :param sender:
    :return:
    """
    node = get_host(sender)
    ctrl.forest.add_sibling_for_constituentnode(node, add_left=False)

a['leaf_add_sibling_right'] = {'command': 'Add sibling node to right',
                               'method': leaf_add_sibling_right,
                               'sender_arg': True}

# Floating buttons ##################################


def toggle_node_edit_embed(sender=None):
    node = get_host(sender)
    ctrl.ui.start_editing_node(node)

a['toggle_node_edit_embed'] = {'command': 'Inspect and edit node',
                               'method': toggle_node_edit_embed,
                               'sender_arg': True}


def toggle_group_options(sender=None):
    """

    :param sender:
    :return:
    """
    group = get_host(sender)
    ctrl.ui.toggle_group_label_editing(group)


a['toggle_group_options'] = {'command': 'Options for saving this selection',
                             'method': toggle_group_options,
                             'sender_arg': True}

# Generic keys ####
# 'key_esc'] = {
#     'command': 'key_esc',
#     'method': 'key_esc',
#     'shortcut': 'Escape'},

def change_group_color(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        group = get_host(sender)
        color_key = sender.currentData()
        sender.model().selected_color = color_key
        if color_key:
            group.update_colors(color_key)
            embed = sender.parent()
            if embed and hasattr(embed, 'update_colors'):
                embed.update_colors()
            log.info('Group color changed to %s' % ctrl.cm.get_color_name(color_key))


def can_edit_group():
    return ctrl.ui.active_embed and isinstance(ctrl.ui.active_embed, GroupLabelEmbed)
    #print(ctrl.ui.active_embed)
    #return ctrl.ui.active_embed and ctrl.ui.active_embed.ui_key == 'GroupEditEmbed'

def get_group_color():
    if ctrl.ui.active_embed and isinstance(ctrl.ui.active_embed, GroupLabelEmbed):
        group = ctrl.ui.active_embed.host
        return group.get_color_id()

a['change_group_color'] = {'command': 'Change color for group',
                           'method': change_group_color,
                           'sender_arg': True,
                           'enabler': can_edit_group,
                           'getter': get_group_color}


def change_group_fill(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        group = get_host(sender)
        group.fill = sender.isChecked()
        group.update()

a['change_group_fill'] = {'command': 'Group area is marked with translucent color',
                          'method': change_group_fill,
                          'sender_arg': True,
                          'enabler': can_edit_group
                          }


def change_group_outline(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        group = get_host(sender)
        group.outline = sender.isChecked()
        group.update()

a['change_group_outline'] = {'command': 'Group is marked by line drawn around it',
                             'method': change_group_outline,
                             'sender_arg': True,
                             'enabler': can_edit_group}


def change_group_overlaps(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        group = get_host(sender)
        group.allow_overlap = sender.isChecked()
        group.update_selection(group.selection)
        group.update_shape()
        if group.allow_overlap:
            log.info('Group can overlap with other groups')
        else:
            log.info('Group cannot overlap with other groups')


a['change_group_overlaps'] = {'command': 'Allow group to overlap other groups',
                              'method': change_group_overlaps,
                              'sender_arg': True,
                              'enabler': can_edit_group}


def change_group_children(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        group = get_host(sender)
        group.include_children = sender.isChecked()
        group.update_selection(group.selection)
        group.update_shape()
        if group.include_children:
            log.info('Group includes children of its orginal members')
        else:
            log.info('Group does not include children')


a['change_group_children'] = {'command': 'Include children of the selected nodes in group',
                              'method': change_group_children,
                              'sender_arg': True,
                              'enabler': can_edit_group}


def delete_group(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        group = get_host(sender)
        group.persistent = False
        ctrl.ui.close_group_label_editing(group)
        if ctrl.ui.selection_group is group:
            ctrl.deselect_objects()
            # deselecting will remove the (temporary) selection group
        else:
            ctrl.ui.remove_ui_for(group)
            ctrl.ui.remove_ui(group)


a['delete_group'] = {'command': 'Remove this group',
                     'method': delete_group,
                     'sender_arg': True,
                     'enabler': can_edit_group}


def save_group_changes(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        embed = sender.parent()
        group = get_host(sender) or ctrl.ui.selection_group
        ctrl.ui.close_group_label_editing(group)
        group.set_label_text(embed.input_line_edit.text())
        group.update_shape()
        name = group.get_label_text() or ctrl.cm.get_color_name(group.color_key)
        if not group.persistent:
            ctrl.forest.turn_selection_group_to_group(group)
            ctrl.deselect_objects()

        log.info("Saved group '%s'" % name)


a['save_group_changes'] = {'command': 'Save this group',
                           'method': save_group_changes,
                           'shortcut': 'Return',
                           'shortcut_context': 'parent_and_children',
                           'sender_arg': True,
                           'enabler': can_edit_group}


def set_assigned_feature(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        featurenode = get_host(sender)
        value = sender.isChecked()
        featurenode.set_assigned(value)
        featurenode.update_label()
        if value:
            return "Feature '%s' set to assigned" % featurenode.name
        else:
            return "Feature '%s' set to unassigned" % featurenode.name

a['set_assigned_feature'] = {'command': 'Set feature as assigned',
                             'method': set_assigned_feature,
                             'sender_arg': True}

