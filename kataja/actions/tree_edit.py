# coding=utf-8
import random

from PyQt5 import QtCore

import kataja.globals as g
from kataja.actions._utils import get_ui_container, get_host
from kataja.singletons import ctrl, classes
from kataja.utils import guess_node_type
from saved.Edge import Edge

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
    ctrl.add_message('Added new %s.' % nclass.name[0])


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
    if embed:
        embed.blur_away()


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
        node = ctrl.forest.create_node_from_string(text, simple_parse=True)

    else:
        node = ctrl.forest.create_node(synobj=None, pos=p2, node_type=node_type, text=text)
    if node:
        node.lock()
    embed.blur_away()


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
    embed.blur_away()


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
    embed.blur_away()
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
    embed.blur_away()


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


def edge_disconnect(sender=None):
    """ Remove connection between two nodes, this is triggered from the edge.
    :return: None
    """
    # Find the triggering edge
    button = get_ui_container(sender)
    if not button:
        return
    edge = button.host
    if button.role == g.START_CUT:
        start = True
        end = False
    elif button.role == g.END_CUT:
        start = False
        end = True
    old_start = edge.start
    if not edge:
        return
    # Then do the cutting
    if edge.delete_on_disconnect():
        ctrl.forest.disconnect_edge(edge)
    else:
        ctrl.forest.partial_disconnect(edge, start=start, end=end)
    if edge.edge_type is g.CONSTITUENT_EDGE:
        old_start.fix_edge_aligns()
    ctrl.ui.update_selections()


a['disconnect_edge'] = {'command': 'Disconnect', 'sender_arg': True,
                        'method': edge_disconnect}


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
    ctrl.add_message('folding in %s' % node.as_bracket_string())
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
    ctrl.add_message('unfolding from %s' % node.as_bracket_string())
    ctrl.forest.remove_triangle_from(node)
    ctrl.deselect_objects()


a['remove_triangle'] = {'command': 'Remove triangle', 'sender_arg': True,
                        'method': remove_triangle}


def finish_editing_node(sender=None):
    """ Set the new values and close the constituent editing embed.
    :return: None
    """
    embed = get_ui_container(sender)
    if embed.host:
        embed.submit_values()
    embed.blur_away()


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

a['constituent_set_head'] = {'command': 'Set head for inheritance',
                             'method': constituent_set_head,
                             'sender_arg': True}

# Actions for TouchAreas #######################################


def add_top_left(sender=None):
    """
    :type event: QMouseEvent
     """
    top = get_host(sender)
    new_node = ctrl.forest.create_node(relative=top)
    ctrl.forest.merge_to_top(top, new_node, True, new_node.current_position)

a['add_top_left'] = {'command': 'Add node to left',
                     'method': add_top_left,
                     'sender_arg': True}


def add_top_right(sender=None):
    """
    :type event: QMouseEvent
     """
    top = get_host(sender)
    new_node = ctrl.forest.create_node(relative=top)
    ctrl.forest.merge_to_top(top, new_node, False, new_node.current_position)

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
    embed = ctrl.ui.get_editing_embed_for_node(node)
    if embed:
        embed.close()
        ctrl.ui.remove_edit_embed(embed)
    else:
        ctrl.ui.start_editing_node(node)

a['toggle_node_edit_embed'] = {'command': 'Inspect and edit node',
                               'method': toggle_node_edit_embed,
                               'sender_arg': True}


def toggle_amoeba_options(sender=None):
    """

    :param sender:
    :return:
    """
    amoeba = get_host(sender)
    ctrl.ui.toggle_group_label_editing(amoeba)


a['toggle_amoeba_options'] = {'command': 'Options for saving this selection',
                              'method': toggle_amoeba_options,
                              'sender_arg': True}

# Generic keys ####
# 'key_esc'] = {
#     'command': 'key_esc',
#     'method': 'key_esc',
#     'shortcut': 'Escape'},

def change_amoeba_color(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        amoeba = get_host(sender)
        color_key = sender.currentData()
        sender.model().selected_color = color_key
        if color_key:
            amoeba.update_colors(color_key)
            embed = sender.parent()
            if embed and hasattr(embed, 'update_colors'):
                embed.update_colors()
            ctrl.main.add_message(
                'Group color changed to %s' % ctrl.cm.get_color_name(color_key))

a['change_amoeba_color'] = {'command': 'Change color for group',
                            'method': change_amoeba_color,
                            'sender_arg': True}


def change_amoeba_fill(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        amoeba = get_host(sender)
        amoeba.fill = sender.isChecked()
        amoeba.update()

a['change_amoeba_fill'] = {'command': 'Group area is marked with translucent color',
                               'method': change_amoeba_fill,
                               'sender_arg': True}


def change_amoeba_outline(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        amoeba = get_host(sender)
        amoeba.outline = sender.isChecked()
        amoeba.update()

a['change_amoeba_outline'] = {'command': 'Group is marked by line drawn around it',
                              'method': change_amoeba_outline,
                              'sender_arg': True}


def change_amoeba_overlaps(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        amoeba = get_host(sender)
        amoeba.allow_overlap = sender.isChecked()
        amoeba.update_selection(amoeba.selection)
        amoeba.update_shape()
        if amoeba.allow_overlap:
            ctrl.main.add_message('Group can overlap with other groups')
        else:
            ctrl.main.add_message('Group cannot overlap with other groups')


a['change_amoeba_overlaps'] = {'command': 'Allow group to overlap other groups',
                               'method': change_amoeba_overlaps,
                               'sender_arg': True}


def change_amoeba_children(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        amoeba = get_host(sender)
        amoeba.include_children = sender.isChecked()
        amoeba.update_selection(amoeba.selection)
        amoeba.update_shape()
        if amoeba.include_children:
            ctrl.main.add_message('Group includes children of its orginal members')
        else:
            ctrl.main.add_message('Group does not include children')


a['change_amoeba_children'] = {'command': 'Include children of the selected nodes in group',
                               'method': change_amoeba_children,
                               'sender_arg': True}


def amoeba_remove(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        amoeba = get_host(sender)
        amoeba.persistent = False
        ctrl.ui.toggle_group_label_editing(amoeba)
        if ctrl.ui.selection_amoeba is amoeba:
            ctrl.deselect_objects()
            # deselecting will remove the amoeba
        else:
            ctrl.ui.remove_ui_for(amoeba)
            ctrl.ui.remove_ui(amoeba)


a['amoeba_remove'] = {'command': 'Remove this group',
                      'method': amoeba_remove,
                      'sender_arg': True}


def amoeba_save(sender=None):
    """

    :param sender:
    :return:
    """
    if sender:
        embed = sender.parent()
        amoeba = get_host(sender) or ctrl.ui.selection_amoeba
        ctrl.ui.toggle_group_label_editing(amoeba)
        amoeba.set_label_text(embed.input_line_edit.text())
        amoeba.update_shape()
        name = amoeba.label_text or ctrl.cm.get_color_name(amoeba.color_key)
        if not amoeba.persistent:
            ctrl.forest.turn_selection_amoeba_to_group(amoeba)
            ctrl.deselect_objects()

        ctrl.main.add_message("Saved group '%s'" % name)


a['amoeba_save'] = {'command': 'Save this group',
                               'method': amoeba_save,
                               'shortcut': 'Return',
                               'shortcut_context': 'parent_and_children',
                               'sender_arg': True}

