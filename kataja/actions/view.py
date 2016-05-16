# coding=utf-8
from PyQt5 import QtWidgets
from kataja.singletons import ctrl, prefs
import kataja.globals as g
from kataja.visualizations.available import action_key

a = {}

def toggle_bones_mode():
    """
    :return:
    """
    prefs.bones_mode = not prefs.bones_mode
    for node in ctrl.forest.nodes.values():
        node.update_label()
        node.update_label_visibility()
        node.update_visibility()

def get_bones_mode():
    return prefs.bones_mode

a['toggle_bones_mode'] = {'command': 'Show only &syntactic objects', 'method': toggle_bones_mode,
                          'shortcut': 's', 'checkable': True, 'check_state': get_bones_mode}


def toggle_brackets():
    """ Brackets are visible always for non-leaves, never or for important parts
    :return: None
    """
    bs = ctrl.fs.bracket_style
    bs += 1
    if bs == 3:
        bs = 0
    if bs == 0:
        ctrl.main.add_message('(b) 0: No brackets')
    elif bs == 1:
        ctrl.main.add_message('(b) 1: Use brackets for embedded structures')
    elif bs == 2:
        ctrl.main.add_message('(b) 2: Always use brackets')
    ctrl.fs.bracket_style = bs
    ctrl.forest.bracket_manager.update_brackets()


a['bracket_mode'] = {'command': 'Show &brackets', 'method': toggle_brackets,
                     'shortcut': 'b', 'checkable': True, }


def toggle_traces():
    """ Switch between multidomination, showing traces and a view where
    traces are grouped to their original position
    :return: None
    """
    fs = ctrl.fs

    if fs.traces_are_grouped_together and not fs.uses_multidomination:
        ctrl.forest.traces_to_multidomination()
        ctrl.main.add_message('(t) use multidominance')
    elif (not fs.traces_are_grouped_together) and not fs.uses_multidomination:
        ctrl.main.add_message('(t) use traces, group them to one spot')
        ctrl.forest.group_traces_to_chain_head()
        ctrl.action_redraw = False
    elif fs.uses_multidomination:
        ctrl.main.add_message(
            '(t) use traces, show constituents in their base merge positions')
        ctrl.forest.multidomination_to_traces()


a['trace_mode'] = {'command': 'Show &traces', 'method': toggle_traces,
                   'shortcut': 't', 'checkable': True, }


def toggle_merge_order_markers():
    """ Toggle showing numbers indicating merge orders
    :return: None
    """
    if ctrl.fs.shows_merge_order():
        ctrl.main.add_message('(o) Hide merge order')
        ctrl.fs.shows_merge_order(False)
        ctrl.forest.remove_order_features('M')
    else:
        ctrl.main.add_message('(o) Show merge order')
        ctrl.fs.shows_merge_order(True)
        ctrl.forest.add_order_features('M')


a['merge_order_attribute'] = {'command': 'Show merge &order',
                              'method': toggle_merge_order_markers,
                              'shortcut': 'o', 'checkable': True}


def show_select_order():
    """ Toggle showing numbers indicating order of lexical selection
    :return: None
    """
    if ctrl.fs.shows_select_order():
        ctrl.main.add_message('(O) Hide select order')
        ctrl.fs.shows_select_order(False)
        ctrl.forest.remove_order_features('S')
    else:
        ctrl.main.add_message('(O) Show select order')
        ctrl.fs.shows_select_order(True)
        ctrl.forest.add_order_features('S')


a['select_order_attribute'] = {'command': 'Show select &Order',
                               'method': show_select_order,
                               'shortcut': 'Shift+o', 'checkable': True}



def change_colors():
    """ DEPRECATED change colors -action (shift-c)
    :return: None
    """
    color_panel = ctrl.ui.get_panel('ColorThemePanel')
    if not color_panel.isVisible():
        color_panel.show()
    else:
        ctrl.fs._hsv = None
        ctrl.forest.update_colors()
        ctrl.main.activateWindow()
        # self.ui_support.add_message('Color seed: H: %.2f S: %.2f L: %.2f' % ( h, s,
        #  l))


a['change_colors'] = {'command': 'Change %Colors', 'method': change_colors,
                      'shortcut': 'Shift+c'}
a['adjust_colors'] = {'command': 'Adjust colors', 'method': change_colors,
                      'shortcut': 'Shift+Alt+c'}


def fit_to_window():
    """ Fit graph to current window. Usually happens automatically, but also
    available as user action
    :return: None
    """
    ctrl.graph_scene.fit_to_window(force=True)


a['zoom_to_fit'] = {'command': '&Zoom to fit', 'method': fit_to_window,
                    'shortcut': 'z'}


def toggle_pan_mode():
    """

    :return:
    """
    ctrl.graph_view.set_selection_mode(False)  # Pan mode

a['toggle_pan_mode'] = {'command': 'Move mode', 'method': toggle_pan_mode,
                        'shortcut': 'm', 'undoable': False}


def toggle_select_mode():
    """

    :return:
    """
    ctrl.graph_view.set_selection_mode(True)  # Select mode

a['toggle_select_mode'] = {'command': 'Select mode', 'method': toggle_select_mode,
                           'shortcut': 's', 'undoable': False}



def change_visualization(visualization_key=None, sender=None):
    """ Switch the visualization being used.

    :return: None
    """
    if visualization_key is None and isinstance(sender, QtWidgets.QComboBox):
        visualization_key = str(sender.currentData())
        action = ctrl.ui.qt_actions[action_key(visualization_key)]
        action.setChecked(True)
    if visualization_key:
        ctrl.forest.set_visualization(visualization_key)
        ctrl.add_message(visualization_key)


a['set_visualization'] = {'command': 'Change visualization algorithm',
                          'method': change_visualization, 'sender_arg': True,
                          'exclusive': True,
                          'tooltip': 'Change visualization algorithm'}


def set_projection_style(style, action=None):
    """ Toggle projection styles.
    :param action: KatajaAction that is calling this method
    :param style: 'highlighter'|'strong_lines'|'colorized'
    :return: str message
    """
    v = False
    if style == 'highlighter':
        v = ctrl.fs.projection_highlighter
        ctrl.fs.projection_highlighter = not v
    elif style == 'strong_lines':
        v = ctrl.fs.projection_strong_lines
        ctrl.fs.projection_strong_lines = not v
    elif style == 'colorized':
        v = ctrl.fs.projection_colorized
        ctrl.fs.projection_colorized = not v
    ctrl.forest.update_projection_display()
    if v:
        return action.command_alt
    else:
        return action.command

a['toggle_highlighter_projection'] = {'command': 'Show projections with '
                                                 'highlighter',
                                      'command_alt': 'Remove highlighter',
                                      'method': set_projection_style,
                                      'args': ['highlighter'],
                                      'action_arg': True,
                                      'tooltip': 'Use highlighter pen -like '
                                                 'lines to display projections'}
a['toggle_strong_lines_projection'] = {'command': 'Draw projections with '
                                                  'thicker lines',
                                       'command_alt': 'Remove strong lines',
                                       'method': set_projection_style,
                                       'args': ['strong_lines'],
                                       'action_arg': True,
                                       'tooltip': 'Draw thicker edges from '
                                                  'projecting nodes'}
a['toggle_colorized_projection'] = {'command': 'Use colors for projections',
                                    'command_alt': "Don't use colors for "
                                                   "projections",
                                    'method': set_projection_style,
                                    'args': ['colorized'],
                                    'action_arg': True,
                                    'tooltip': 'Use colors to distinguish '
                                               'projecting edges'}


def toggle_label_visibility(node_location, field, action=None):
    """ Toggle labels|aliases to be visible in inner|leaf nodes.
    :param node_location: 'internal'|'leaf'
    :param field: 'label'|'alias'
    :param action: KatajaAction that is calling this method
    :return: str message
    """
    v = False
    if node_location == 'internal':
        if field == 'label':
            v = not ctrl.fs.show_internal_labels
            ctrl.fs.show_internal_labels = v
        elif field == 'alias':
            v = not ctrl.fs.show_internal_aliases
            ctrl.fs.show_internal_aliases = v
    elif node_location == 'leaf':
        if field == 'label':
            v = not ctrl.fs.show_leaf_labels
            ctrl.fs.show_leaf_labels = v
        elif field == 'alias':
            v = not ctrl.fs.show_leaf_aliases
            ctrl.fs.show_leaf_aliases = v
    for node in ctrl.forest.nodes.values():
        node.update_label()
        node.update_label_visibility()
    if action:
        if v:
            return action.command % 'Show'
        else:
            return action.command % 'Hide'

a['toggle_show_internal_alias'] = {'command': '%s aliases in internal nodes',
                                   'method': toggle_label_visibility,
                                   'args': ['internal', 'alias'],
                                   'action_arg': True,
                                   'tooltip': 'Show aliases in internal nodes'}
a['toggle_show_internal_label'] = {'command': '%s labels in internal nodes',
                                   'method': toggle_label_visibility,
                                   'args': ['internal', 'label'],
                                   'action_arg': True,
                                   'tooltip': 'Show labels in internal nodes'}
a['toggle_show_leaf_alias'] = {'command': '%s aliases in leaf nodes',
                               'method': toggle_label_visibility,
                               'args': ['leaf', 'alias'],
                               'action_arg': True,
                               'tooltip': 'Show aliases in leaf nodes'}
a['toggle_show_leaf_label'] = {'command': '%s labels in leaf nodes',
                               'method': toggle_label_visibility,
                               'args': ['leaf', 'label'],
                               'action_arg': True,
                               'tooltip': 'Show labels in leaf nodes'}

