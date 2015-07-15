import ast
import gzip
import json
import pickle
import pprint
import random
import shlex
import time
import subprocess

from PyQt5 import QtGui, QtWidgets, QtCore

from PyQt5.QtCore import Qt
from kataja.Node import Node
from kataja.errors import ForestError
import kataja.debug as debug
from kataja.ui.PreferencesDialog import PreferencesDialog
from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.visualizations.available import action_key


__author__ = 'purma'

from kataja.singletons import ctrl, prefs
import kataja.globals as g


def get_ui_container(qt_object):
    """ Traverse up in widget hierarchy until object governed by UIManager is found. Return this.
    :param qt_object:
    :return:
    """
    if not qt_object:
        return None
    if hasattr(qt_object, 'ui_key'):
        return qt_object
    else:
        p = qt_object.parent()
        if p:
            return get_ui_container(p)
        else:
            return None


def get_host(sender):
    """ Get the Kataja object that this UI element is about, the 'host' element.
    :param sender:
    :return:
    """
    container = get_ui_container(sender)
    if container:
        return container.host

a = {}

# ## Programmatically created actions ###############################################
# these are not necessarily found in actions.py


def toggle_panel(panel_id):
    """ Show or hide panel depending if it is visible or not
    :param panel_id: enum of panel identifiers (str)
    :return: None
    """
    panel = ctrl.ui.get_panel(panel_id)

    if panel:
        if panel.isVisible():
            panel.close()
        else:
            panel.setVisible(True)
            panel.set_folded(False)
    else:
        panel = ctrl.ui.create_panel(panel_id, default=True)
        panel.setVisible(True)
        panel.set_folded(False)



#### Actions from actions.py ######################################################


# (Order of actions is irrelevant, menus are built according to instructions at another dict.)
# key : used internally to fetch the action
# command : displayed in menus
# method : method that is called when the action is activated
# shortcut : keyboard shortcut to activate the action
# context : where the method is called 'main' is default, referring to KatajaMain
# other values: 'app', 'selected', 'node'...
# checkable : True/False -- as a menu item, does the action have two states

# ### File ######

file_extensions = {
    'pickle': '.kataja',
    'pickle.zipped': '.zkataja',
    'dict': '.dict',
    'dict.zipped': '.zdict',
    'json': '.json',
    'json.zipped': '.zjson',
} # Not sure if we need a separate set for windows, if they still use three-letter extensions

def open_kataja_file():
    """ Open file browser to load a kataja data file
    :return: None
    """
    m = ctrl.main
    # fileName  = QtGui.QFileDialog.getOpenFileName(self,
    # self.tr("Open File"),
    # QtCore.QDir.currentPath())
    file_help = """All (*.kataja *.zkataja *.dict *.zdict *.json *.zjson);;
Kataja files (*.kataja);; Packed Kataja files (*.zkataja);;
Python dict dumps (*.dict);; Packed python dicts (*.zdict);;
JSON dumps (*.json);; Packed JSON (*.zjson);;
Text files containing bracket trees (*.txt, *.tex)"""

    # inspection doesn't recognize that getOpenFileName is static, switch it off:
    # noinspection PyTypeChecker,PyCallByClass
    filename, filetypes = QtWidgets.QFileDialog.getOpenFileName(ctrl.main, "Open KatajaMain tree", "", file_help)
    if not filename:
        return
    save_format = 'pickle'
    zipped = False
    for key, value, in file_extensions.items():
        if filename.endswith(value):
            i = key.split('.')
            zipped = len(i) == 2
            save_format = i[0]
            break

    m.clear_all()
    if zipped:
        if save_format == 'json' or save_format == 'dict':
            f = gzip.open(filename, 'rt')
        elif save_format == 'pickle':
            f = gzip.open(filename, 'rb')
    else:
        if save_format == 'pickle':
            f = open(filename, 'rb')
        else:
            f = open(filename, 'r')
        # import codecs
        # f = codecs.open(filename, 'rb', encoding = 'utf-8')

    if save_format == 'pickle':
        pickle_worker = pickle.Unpickler(f)
        data = pickle_worker.load()
    elif save_format == 'dict':
        data = ast.literal_eval(f.read())
        # data = eval(f.read())
    elif save_format == 'json':
        data = json.load(f)
    f.close()
    # prefs.update(data['preferences'].__dict__)
    # qt_prefs.update(prefs)
    ctrl.undo_disabled = True
    m.load_objects(data, m)
    ctrl.undo_disabled = False
    m.change_forest(m.forest_keeper.forest)
    ctrl.add_message("Loaded '%s'." % filename)

a['open'] = {
    'command': '&Open',
    'method': open_kataja_file,
    'undoable': False,
    'shortcut': 'Ctrl+o'}

def save_kataja_file(filename=None):
    """ Save kataja data with an existing file name.
    :param filename: filename received from dialog.
    Format is deduced from the extension of filename.
    :return: None
    """
    # action  = self.sender()
    save_format = 'pickle'
    zipped = False
    if not filename:
        filename = prefs.file_name
    for key, value, in file_extensions.items():
        if filename.endswith(value):
            i = key.split('.')
            zipped = len(i) == 2
            save_format = i[0]
            break

    all_data = ctrl.main.create_save_data()
    t = time.time()
    pickle_format = 4

    if save_format == 'pickle':
        if zipped:
            f = gzip.open(filename, 'wb')
        else:
            f = open(filename, 'wb')
        pickle_worker = pickle.Pickler(f, protocol=pickle_format)
        pickle_worker.dump(all_data)
    elif save_format == 'dict':
        if zipped:
            f = gzip.open(filename, 'wt')
        else:
            f = open(filename, 'w')
        pp = pprint.PrettyPrinter(indent=1, stream=f)
        print('is readable: ', pprint.isreadable(all_data))
        pp.pprint(all_data)
    elif save_format == 'json':
        if zipped:
            f = gzip.open(filename, 'wt')
        else:
            f = open(filename, 'w')
        json.dump(all_data, f, indent="\t", sort_keys=False)
    f.close()
    ctrl.main.add_message("Saved to '%s'. Took %s seconds." % (filename, time.time() - t))

    # fileFormat  = action.data().toByteArray()
    # self.saveFile(fileFormat)

a['save'] = {
    'command': '&Save',
    'method': save_kataja_file,
    'undoable': False,
    'shortcut': 'Ctrl+s'}


def save_as():
    """ Save kataja data to file set by file dialog """
    ctrl.main.action_finished()
    file_help = """"All (*.kataja *.zkataja *.dict *.zdict *.json *.zjson);;
Kataja files (*.kataja);; Packed Kataja files (*.zkataja);;
Python dict dumps (*.dict);; Packed python dicts (*.zdict);;
JSON dumps (*.json);; Packed JSON (*.zjson)
"""
    filename, file_type = QtWidgets.QFileDialog.getSaveFileName(ctrl.main, "Save Kataja tree",
                                                                "", file_help)
    if filename:
        save_kataja_file(filename)

a['save_as'] = {
    'command': '&Save as',
    'undoable': False,
    'method': save_as}


def print_to_file():
    """ Starts the printing process.
     1st step is to clean the scene for a printing and display the printed area -frame.
     2nd step: after 50ms remove printed area -frame and prints to pdf, and write the file.

     2nd step is triggered by a timer in main window.
     :return: None
    """
    debug.keys("Print to file called")
    sc = ctrl.graph_scene
    # hide unwanted components
    no_brush = QtGui.QBrush(Qt.NoBrush)
    sc.setBackgroundBrush(no_brush)
    sc.photo_frame = sc.addRect(sc.visible_rect().adjusted(-1, -1, 2, 2), ctrl.cm.selection())
    sc.update()
    ctrl.graph_view.repaint()
    ctrl.main.startTimer(50)

a['print_pdf'] = {
    'command': '&Print',
    'method': print_to_file,
    'undoable': False,
    'shortcut': 'Ctrl+p'}


def render_in_blender():
    """ (not working recently) Try to export as a blender file and run blender render.
    :return: None
    """
    ctrl.graph_scene.export_3d(prefs.blender_env_path + '/temptree.json', ctrl.forest)
    ctrl.main.add_message('Command-r  - render in blender')
    command = '%s -b %s/puutausta.blend -P %s/treeloader.py -o //blenderkataja -F JPEG -x 1 -f 1' % (
        prefs.blender_app_path, prefs.blender_env_path, prefs.blender_env_path)
    args = shlex.split(command)
    subprocess.Popen(args)  # , cwd =prefs.blender_env_path)

a['blender_render'] = {
    'command': '&Render in Blender',
    'method': render_in_blender,
    'shortcut': 'Ctrl+r'}


def open_preferences():
    """ Opens the large preferences dialog
    :return: None
    """
    if not ctrl.ui.preferences_dialog:
        ctrl.ui.preferences_dialog = PreferencesDialog(ctrl.main)
    ctrl.ui.preferences_dialog.open()

a['preferences'] = {
    'command': '&Preferences',
    'method': open_preferences}


def close_all_windows():
    """ Implements Quit command
    :return: None
    """
    ctrl.main.app.closeAllWindows()

a['quit'] = {
    'command': '&Quit',
    'method': close_all_windows,
    'shortcut': 'Ctrl+q'}


# ### Build ######

def next_structure():
    """ Show the next 'slide', aka Forest from a list in ForestKeeper.
    :return: None
    """
    i, forest = ctrl.main.forest_keeper.next_forest()
    ctrl.main.change_forest(forest)
    ctrl.main.add_message('(.) tree %s: %s' % (i + 1, forest.textual_form()))

a['next_forest'] = {
    'command': 'Next forest',
    'method': next_structure,
    'undoable': False,
    'shortcut': '.',
    'tooltip': 'Switch to next forest'}


def previous_structure():
    """ Show the previous 'slide', aka Forest from a list in ForestKeeper.
    :return: None
    """
    i, forest = ctrl.main.forest_keeper.prev_forest()
    ctrl.main.change_forest(forest)
    ctrl.main.add_message('(,) tree %s: %s' % (i + 1, forest.textual_form()))

a['prev_forest'] = {
    'command': 'Previous forest',
    'method': previous_structure,
    'shortcut': ',',
    'undoable': False,
    'tooltip': 'Switch to previous forest'}


def animation_step_forward():
    """ User action "step forward (>)", Move to next derivation step """
    ctrl.forest.derivation_steps.next_derivation_step()
    ctrl.main.add_message('Step forward')

a['next_derivation_step'] = {
    'command': 'Animation step forward',
    'method': animation_step_forward,
    'shortcut': '>'}


def animation_step_backward():
    """ User action "step backward (<)" , Move backward in derivation steps """
    ctrl.forest.derivation_steps.previous_derivation_step()
    ctrl.main.add_message('Step backward')

a['prev_derivation_step'] = {
    'command': 'Animation step backward',
    'method': animation_step_backward,
    'shortcut': '<'}

# Rules ######


# ## Menu actions ##########################################################

def toggle_label_visibility():
    """ toggle label visibility -action (l)
    :return: None
    """
    new_value = ctrl.forest.settings.label_style + 1
    if new_value == 3:
        new_value = 0
    if new_value == g.ONLY_LEAF_LABELS:
        ctrl.main.add_message('(l) 0: show only leaf labels')
    elif new_value == g.ALL_LABELS:
        ctrl.main.add_message('(l) 1: show all labels')
    elif new_value == g.ALIASES:
        ctrl.main.add_message('(l) 2: show leaf labels and aliases')
    # testing how to change labels
    # ConstituentNode.font = prefs.sc_font
    ctrl.forest.settings.label_style = new_value

    for node in ctrl.forest.nodes.values():
        node.update_visibility()
        # change = node.update_label()

a['label_visibility'] = {
    'command': 'Show &labels in middle nodes',
    'method': toggle_label_visibility,
    'shortcut': 'l',
    'checkable': True, }


def toggle_brackets():
    """ Brackets are visible always for non-leaves, never or for important parts
    :return: None
    """
    bs = ctrl.forest.settings.bracket_style
    bs += 1
    if bs == 3:
        bs = 0
    if bs == 0:
        ctrl.main.add_message('(b) 0: No brackets')
    elif bs == 1:
        ctrl.main.add_message('(b) 1: Use brackets for embedded structures')
    elif bs == 2:
        ctrl.main.add_message('(b) 2: Always use brackets')
    ctrl.forest.settings.bracket_style = bs
    ctrl.forest.bracket_manager.update_brackets()

a['bracket_mode'] = {
    'command': 'Show &brackets',
    'method': toggle_brackets,
    'shortcut': 'b',
    'checkable': True, }


def toggle_traces():
    """ Switch between multidomination, showing traces and a view where traces are grouped to their original position
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
        ctrl.main.add_message('(t) use traces, show constituents in their base merge positions')
        ctrl.forest.multidomination_to_traces()

a['trace_mode'] = {
    'command': 'Show &traces',
    'method': toggle_traces,
    'shortcut': 't',
    'checkable': True, }


def change_constituent_edge_shape(shape=''):
    """ Edges between constituents have preset shapes and these can be changed for
    :param shape: key for shape (str) if left empty, the next shape in list is cycled to.
    """
    if shape and shape in SHAPE_PRESETS:
        ctrl.forest.settings.edge_type_settings(g.CONSTITUENT_EDGE, 'shape_name', shape)
        i = list(SHAPE_PRESETS.keys()).index(shape)
    else:
        shape = ctrl.forest.settings.edge_type_settings(g.CONSTITUENT_EDGE, 'shape_name')
        i = list(SHAPE_PRESETS.keys()).index(shape)
        i += 1
        if i == len(SHAPE_PRESETS):
            i = 0
        shape = list(SHAPE_PRESETS.keys())[i]
        ctrl.forest.settings.edge_type_settings(g.CONSTITUENT_EDGE, 'shape_name', shape)
    ctrl.main.add_message('(s) Change constituent edge shape: %s-%s' % (i, shape))

a['merge_edge_shape'] = {
    'command': 'Change branch &shape',
    'method': change_constituent_edge_shape,
    'shortcut': 's'}


def change_feature_edge_shape(shape):
    """ Edges between features and constituents use same set of preset shapes as any other edges,
    but have different default.
    :param shape: key for shape (str) if left empty, the next shape in list is cycled to.
    """
    if shape and shape in SHAPE_PRESETS:
        ctrl.forest.settings.edge_shape_name(g.CONSTITUENT_EDGE, shape)
        i = list(SHAPE_PRESETS.keys()).index(shape)
    else:
        i = list(SHAPE_PRESETS.keys()).index(ctrl.forest.settings.edge_shape_name(g.FEATURE_EDGE))
        if i == len(SHAPE_PRESETS):
            i = 0
        shape = list(SHAPE_PRESETS.keys())[i]
        ctrl.forest.settings.edge_shape_name(g.FEATURE_EDGE, shape)
    #ctrl.ui.ui_buttons['feature_line_type'].setCurrentIndex(i)
    ctrl.main.add_message('(s) Change feature edge shape: %s-%s' % (i, shape))

a['feature_edge_shape'] = {
    'command': 'Change feature branch &shape',
    'method': change_feature_edge_shape,
    'shortcut': 'Shift+s'}


def toggle_merge_order_markers():
    """ Toggle showing numbers indicating merge orders
    :return: None
    """
    if ctrl.forest.settings.shows_merge_order():
        ctrl.main.add_message('(o) Hide merge order')
        ctrl.forest.settings.shows_merge_order(False)
        ctrl.forest.remove_order_features('M')
    else:
        ctrl.main.add_message('(o) Show merge order')
        ctrl.forest.settings.shows_merge_order(True)
        ctrl.forest.add_order_features('M')

a['merge_order_attribute'] = {
    'command': 'Show merge &order',
    'method': toggle_merge_order_markers,
    'shortcut': 'o',
    'checkable': True}


def show_select_order():
    """ Toggle showing numbers indicating order of lexical selection
    :return: None
    """
    if ctrl.forest.settings.shows_select_order():
        ctrl.main.add_message('(O) Hide select order')
        ctrl.forest.settings.shows_select_order(False)
        ctrl.forest.remove_order_features('S')
    else:
        ctrl.main.add_message('(O) Show select order')
        ctrl.forest.settings.shows_select_order(True)
        ctrl.forest.add_order_features('S')

a['select_order_attribute'] = {
    'command': 'Show select &Order',
    'method': show_select_order,
    'shortcut': 'Shift+o',
    'checkable': True}

# View ####



def toggle_fold_panel(sender):
    """ Fold panel into label line or reveal the whole panel.
    :param panel_id: enum of panel identifiers (str)
    :return: None
    """
    panel = get_ui_container(sender)
    if panel:
        panel.set_folded(not panel.folded)

a['toggle_fold_panel'] = {'command': 'Fold panel',
                          'method': toggle_fold_panel,
                          'sender_arg': True,
                          'checkable': True,
                          'undoable': False,
                          'tooltip': "Minimize this panel"}


def pin_panel(sender):
    """ Put panel back to panel dock area.
    :param panel_id: enum of panel identifiers (str)
    :return: None
    """
    panel = get_ui_container(sender)
    if panel:
        panel.pin_to_dock()

a['pin_panel'] = {'command': 'Pin to dock',
                  'method': pin_panel,
                  'sender_arg': True,
                  'undoable': False,
                  'tooltip': "Pin to dock"}


def change_colors():
    """ DEPRECATED change colors -action (shift-c)
    :return: None
    """
    color_panel = ctrl.ui.get_panel(g.COLOR_THEME)
    if not color_panel.isVisible():
        color_panel.show()
    else:
        ctrl.forest.settings._hsv = None
        ctrl.forest.update_colors()
        ctrl.main.activateWindow()
        # self.ui.add_message('Color seed: H: %.2f S: %.2f L: %.2f' % ( h, s, l))

a['change_colors'] = {
    'command': 'Change %Colors',
    'method': change_colors,
    'shortcut': 'Shift+c'}
a['adjust_colors'] = {
    'command': 'Adjust colors',
    'method': change_colors,
    'shortcut': 'Shift+Alt+c'}


def fit_to_window():
    """ Fit graph to current window. Usually happens automatically, but also available as user action
    :return: None
    """
    ctrl.graph_scene.fit_to_window()

a['zoom_to_fit'] = {
    'command': '&Zoom to fit',
    'method': fit_to_window,
    'shortcut': 'z'}


def toggle_full_screen():
    """ Toggle between fullscreen mode and windowed mode
    :return: None
    """
    if ctrl.main.isFullScreen():
        ctrl.main.showNormal()
        ctrl.main.add_message('(f) windowed')
        ctrl.ui.restore_panel_positions()
    else:
        ctrl.ui.store_panel_positions()
        ctrl.main.showFullScreen()
        ctrl.main.add_message('(f) fullscreen')
    ctrl.graph_scene.fit_to_window()

a['fullscreen_mode'] = {
    'command': '&Fullscreen',
    'method': toggle_full_screen,
    'shortcut': 'f',
    'undoable': False,
    'checkable': True}


def change_style_scope(sender):
    """ Change drawing panel to work on selected nodes, constituent nodes or other available
    nodes
    :param selection: int scope identifier, from globals
    :return: None
    """
    print('changing scope: ', sender)
    if sender:
        data = sender.currentData()
        ctrl.ui.scope = data
        ctrl.call_watchers(sender, 'scope_changed', 'scope', data)

a['style_scope'] = {
    'command': 'Select the scope for style changes',
    'method': change_style_scope,
    'sender_arg': True,
    'undoable': False,
    'tooltip': 'Select the scope for style changes'}

def open_font_selector(sender):
    """ Change drawing panel to work on selected nodes, constituent nodes or other available
    nodes
    :param selection: int scope identifier, from globals
    :return: None
    """
    print('opening font selector: ', sender)
    if sender:
        panel = get_ui_container(sender)
        font_key = panel.cached_font_id
        ctrl.ui.start_font_dialog(panel, 'node_font', font_key)

a['start_font_dialog'] = {
    'command': 'Use a custom font',
    'method': open_font_selector,
    'sender_arg': True,
    'undoable': False,
    'tooltip': 'Use a custom font'}


def select_font(sender):
    """ Change drawing panel to work on selected nodes, constituent nodes or other available
    nodes
    :param selection: int scope identifier, from globals
    :return: None
    """
    print('opening font selector: ', sender)
    if sender:
        font_key = sender.currentData()
        panel = get_ui_container(sender)
        panel.update_font_for_role('node_font', font_key)

a['font_selector'] = {
    'command': 'Change label font',
    'method': select_font,
    'sender_arg': True,
    'tooltip': 'Select the label font'}


def change_edge_shape(sender):
    """ Change edge shape for selection or in currently active edge type.
    :param shape: shape key (str)
    :return: None
    """
    shape = sender.currentData()
    if shape is g.AMBIGUOUS_VALUES:
        return
    scope = ctrl.ui.scope
    if scope == g.SELECTION:
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.shape_name = shape
                edge.update_shape()
    elif scope:
        edge_type = ctrl.forest.settings.node_settings(scope, 'edge')
        ctrl.forest.settings.edge_type_settings(edge_type, 'shape_name', shape)
        for edge in ctrl.forest.edges.values():
            edge.update_shape()
    line_options = ctrl.ui.get_panel(g.LINE_OPTIONS)

    if line_options:
        line_options.update_panel()
    ctrl.main.add_message('(s) Changed relation shape to: %s' % shape)

a['change_edge_shape'] = {
    'command': 'Change relation shape',
    'method': change_edge_shape,
    'sender_arg': True,
    'tooltip': 'Change shape of relations (lines, edges) between objects'}


def change_node_color(sender):
    """ Change color for selection or in currently active edge type.
    :param color: color key (str)
    :return: None
    """

    if sender:
        sender.model().selected_color = sender.currentData()
        panel = get_ui_container(sender)
        color_id = panel.update_color_for_role('node_color')
        if color_id:
            ctrl.main.add_message('(s) Changed node color to: %s' %
                                  ctrl.cm.get_color_name(color_id))

a['change_node_color'] = {
    'command': 'Change node color',
    'method': change_node_color,
    'sender_arg': True,
    'tooltip': 'Change drawing color of nodes'}


def change_edge_color(sender):
    """ Change edge shape for selection or in currently active edge type.
    :param color: color key (str)
    :return: None
    """
    if sender:
        panel = get_ui_container(sender)
        color_id = panel.update_color_for_role('edge_color')
        if color_id:
            ctrl.main.add_message('(s) Changed relation color to: %s' %
                                  ctrl.cm.get_color_name(color_id))

a['change_edge_color'] = {
    'command': 'Change relation color',
    'method': change_edge_color,
    'sender_arg': True,
    'tooltip': 'Change drawing color of relations'}


def toggle_line_options():
    """ Toggle panel for more options for edge drawing.
    :return: None
    """
    lo = ctrl.ui.get_panel(g.LINE_OPTIONS)
    if lo:
        if lo.isVisible():
            lo.close()
        else:
            lo.show()
    else:
        ctrl.ui.create_panel(g.LINE_OPTIONS, default=True)
        lo = ctrl.ui.get_panel(g.LINE_OPTIONS)
        lo.show()

a['toggle_line_options'] = {
    'command': 'Show line options',
    'command_alt': 'Hide line options',
    'method': toggle_line_options,
    'toggleable': True,
    'condition': 'are_line_options_visible',
    'tooltip': 'Show/hide advanced options for line drawing'}


def adjust_control_point(cp_index, dim, value=0):
    """ Adjusting control point can be done only for selected edges, not for an edge type. So this method is
    simpler than other adjustments, as it doesn't have to handle both cases.
    :param cp_index: 1 or 2 = which control point we are adjusting
    :param dim: 'x', 'y' or 'r' for reset
    :param value: new value for given dimension, doesn't matter for reset.
    :return: None
    """
    cp_index -= 1
    for edge in ctrl.selected:
        if isinstance(edge, Edge):
            if dim == 'r':
                edge.reset_control_point(cp_index)
            else:
                edge.adjust_control_point_xy(cp_index, dim, value)

a['control_point1_x'] = {
    'command': 'Adjust curvature, point 1 X',
    'method': adjust_control_point,
    'args': [1, 'x'],
    'tooltip': 'Adjust curvature, point 1 X'
}
a['control_point1_y'] = {
    'command': 'Adjust curvature, point 1 Y',
    'method': adjust_control_point,
    'args': [1, 'y'],
    'tooltip': 'Adjust curvature, point 1 Y'
}
a['control_point1_reset'] = {
    'command': 'Reset control point 1',
    'method': adjust_control_point,
    'args': [1, 'r'],
    'tooltip': 'Remove arc adjustments'
}
a['control_point2_x'] = {
    'command': 'Adjust curvature, point 2 X',
    'method': adjust_control_point,
    'args': [2, 'x'],
    'tooltip': 'Adjust curvature, point 2 X'
}
a['control_point2_y'] = {
    'command': 'Adjust curvature, point 2 Y',
    'method': adjust_control_point,
    'args': [2, 'y'],
    'tooltip': 'Adjust curvature, point 2 Y'
}
a['control_point2_reset'] = {
    'command': 'Reset control point 2',
    'method': adjust_control_point,
    'args': [2, 'r'],
    'tooltip': 'Remove arc adjustments'}


def change_leaf_shape(dim, value=0):
    """ Change width or height of leaf-shaped edge.
    :param dim: 'w' for width, 'h' for height, 'r' for reset
    :param value: new value (float)
    :raise ValueError:

    """
    # if value is g.AMBIGUOUS_VALUES:
    # if we need this, we'll need to find some impossible ambiguous value to avoid weird, rare incidents
    # return
    scope = ctrl.ui.scope
    if scope == g.SELECTION:
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.change_leaf_shape(dim, value)
    elif scope:
        if dim == 'w':
            ctrl.forest.settings.edge_shape_settings(scope, 'leaf_x', value)
        elif dim == 'h':
            ctrl.forest.settings.edge_shape_settings(scope, 'leaf_y', value)
        elif dim == 'r':
            ctrl.forest.settings.edge_shape_settings(scope, 'leaf_x', g.DELETE)
            ctrl.forest.settings.edge_shape_settings(scope, 'leaf_y', g.DELETE)
            options_panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
            options_panel.update_panel()
        else:
            raise ValueError

a['leaf_shape_x'] = {
    'command': 'Line leaf shape width',
    'method': change_leaf_shape,
    'args': ['w'],
    'tooltip': 'Line leaf shape width'
}
a['leaf_shape_y'] = {
    'command': 'Line leaf shape height',
    'method': change_leaf_shape,
    'args': ['h'],
    'tooltip': 'Line leaf shape height'
}
a['leaf_shape_reset'] = {
    'command': 'Reset leaf shape settings',
    'method': change_leaf_shape,
    'args': ['r'],
    'tooltip': 'Reset leaf shape settings'
}


def change_edge_thickness(dim, value=0):
    """ If edge is outline (not a leaf shape)

    :param dim: 'r' for reset, otherwise doesn't matter
    :param value: new thickness (float)
    """
    scope = ctrl.ui.scope
    if scope == g.SELECTION:
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.change_thickness(dim, value)
    elif scope:
        if dim == 'r':
            ctrl.forest.settings.edge_shape_settings(scope, 'thickness', g.DELETE)
            options_panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
            options_panel.update_panel()
        else:
            ctrl.forest.settings.edge_shape_settings(scope, 'thickness', value)

a['edge_thickness'] = {
    'command': 'Line thickness',
    'method': change_edge_thickness,
    'args': ['x'],
    'tooltip': 'Line thickness'
}
a['edge_thickness_reset'] = {
    'command': 'Reset line thickness',
    'method': change_edge_thickness,
    'args': ['r'],
    'tooltip': 'Reset line thickness'
}


def change_curvature(dim, value=0):
    """ Change curvature of arching lines. Curvature can be relative or absolute, and that can also be toggled
    by calling this method (dim: 's'). Curvature can be set for x or y dim.

    :param dim: 'x', 'y', 's' to toggle relative/absolute, 'r' to reset
    :param value: float
    :raise ValueError:
    """
    scope = ctrl.ui.scope
    if scope == g.SELECTION:
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.change_curvature(dim, value)
        if dim == 'r' or dim == 's':
            options_panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
            options_panel.update_panel()
    elif scope:
        options_panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
        relative = options_panel.relative_curvature()

        if dim == 'x':
            if relative:
                ctrl.forest.settings.edge_shape_settings(scope, 'rel_dx', value * .01)
            else:
                ctrl.forest.settings.edge_shape_settings(scope, 'fixed_dx', value)
        elif dim == 'y':
            if relative:
                ctrl.forest.settings.edge_shape_settings(scope, 'rel_dy', value * .01)
            else:
                ctrl.forest.settings.edge_shape_settings(scope, 'fixed_dy', value)
        elif dim == 'r': # reset
            ctrl.forest.settings.edge_shape_settings(scope, 'rel_dx', g.DELETE)
            ctrl.forest.settings.edge_shape_settings(scope, 'rel_dy', g.DELETE)
            ctrl.forest.settings.edge_shape_settings(scope, 'fixed_dx', g.DELETE)
            ctrl.forest.settings.edge_shape_settings(scope, 'fixed_dy', g.DELETE)
            ctrl.forest.settings.edge_shape_settings(scope, 'relative', g.DELETE)
            options_panel.update_panel()
        elif dim == 's': # toggle between relative and fixed
            ctrl.forest.settings.edge_shape_settings(scope, 'relative', value == 'relative')
            options_panel.update_panel()
        else:
            raise ValueError

a['edge_curvature_x'] = {
    'command': 'Line curvature modifier X',
    'method': change_curvature,
    'args': ['x'],
    'tooltip': 'Line curvature modifier X'
}
a['edge_curvature_y'] = {
    'command': 'Line curvature modifier Y',
    'method': change_curvature,
    'args': ['y'],
    'tooltip': 'Line curvature modifier Y'
}
a['edge_curvature_type'] = {
    'command': 'Change line curvature to be relative or fixed amount',
    'method': change_curvature,
    'args': ['s'],
    'tooltip': 'Change line curvature to be relative or fixed amount'
}
a['edge_curvature_reset'] = {
    'command': 'Reset line curvature to default',
    'method': change_curvature,
    'args': ['r'],
    'tooltip': 'Reset line curvature to default'
}


def change_edge_asymmetry(value):
    """ Toggle between showing different line weights for LEFT and RIGHT aligned edges.
    :param value: bool
    :return: None
    """
    print('changing asymmetry: ', value)

a['edge_asymmetry'] = {
    'command': 'Set left and right to differ significantly',
    'method': change_edge_asymmetry,
    'tooltip': 'Set left and right to differ significantly'
}


def change_visualization(sender, visualization_key=None):
    """ Switch the visualization being used.

    :return: None
    """
    print('change visualization: ', sender, visualization_key)
    if visualization_key is None and isinstance(sender, QtWidgets.QComboBox):
        visualization_key = str(sender.currentData())
        action = ctrl.ui.qt_actions[action_key(visualization_key)]
        action.setChecked(True)
    if visualization_key:
        ctrl.forest.set_visualization(visualization_key)
        ctrl.add_message(visualization_key)

a['set_visualization'] = {
    'command': 'Change visualization algorithm',
    'method': change_visualization,
    'sender_arg': True,
    'exclusive': True,
    'tooltip': 'Change visualization algorithm'
}


def add_node(sender, ntype=None, pos=None):
    """ Generic add node, gets the node type as an argument.
    :param ntype: node type (str/int, see globals), if not provided, evaluates which add_node button was clicked.
    :param pos: QPoint for where the node should first appear
    :return: None
    """
    if not ntype:
        ntype = sender.data
    if not pos:
        pos = QtCore.QPoint(random.random() * 60 - 25, random.random() * 60 - 25)
    ctrl.forest.create_node(pos=pos, node_type=ntype)
    nclass = ctrl.node_classes[ntype]
    ctrl.add_message('Added new %s.' % nclass.name[0])


a['add_node'] = {
    'command': 'Add node',
    'sender_arg': True,
    'method': add_node,
    'tooltip': 'Add %s'}


def show_help_message():
    """ Dump keyboard shortcuts to console. At some point, make this to use dialog window instead.
    :return: None
    """
    m = """(h):------- KatajaMain commands ----------
    (left arrow/,):previous structure   (right arrow/.):next structure
    (1-9, 0): switch between visualizations
    (f):fullscreen/windowed mode
    (p):print tree to file
    (b):show/hide labels in middle of edges
    (q):quit"""
    ctrl.main.add_message(m)

a['help'] = {
    'command': '&Help',
    'method': show_help_message,
    'shortcut': 'h'}


def close_embeds(sender):
    """ If embedded menus (node creation / editing in place, etc.) are open, close them.
    This is expected behavior for pressing 'esc'.
    :param sender:
    :return: None
    """
    embed = get_ui_container(sender)
    if embed:
        embed.blur_away()

a['close_embed'] = {
    'command': 'Cancel',
    'method': close_embeds,
    'shortcut': 'Escape',
    'undoable': False,
    'sender_arg': True,
    'shortcut_context': 'parent_and_children'
}


def new_element_accept(sender):
    """ Create new element according to fields in this embed. Can create constituentnodes,
    features, arrows, etc.
    :param sender:
    :return: None
    """

    embed = get_ui_container(sender)
    type = embed.input_action_selector.itemData(embed.input_action_selector.currentIndex())
    p1, p2 = embed.get_marker_points()
    text = embed.input_line_edit.text()
    ctrl.focus_point = p2

    if type == g.GUESS_FROM_INPUT:
        print("Guessing input type")
        # we can add a test if line p1 - p2 crosses several edges, then it can be a divider
        # Fixme Use screen coordinates instead, as if zoomed out, the default line can already be long enough. oops.
        if (p1 - p2).manhattanLength() > 20 and not text.startswith('['):
            # It's an Arrow!
            create_new_arrow(sender)
            return
        else:
            print('trying to parse ', text)
            node = ctrl.forest.create_node_from_string(text)
    embed.blur_away()

a['new_element_enter_text'] = {
    'command': 'Enter',
    'method': new_element_accept,
    'sender_arg': True,
    'shortcut': 'Return',
    'shortcut_context': 'parent_and_children'
}


def create_new_arrow(sender):
    """ Create a new arrow into embed menu's location
    :param sender:
    :return: None
    """
    print("New arrow called", sender)
    embed = get_ui_container(sender)
    p1, p2 = embed.get_marker_points()
    text = embed.input_line_edit.text()
    ctrl.forest.create_arrow(p1, p2, text)
    embed.blur_away()

a['new_arrow'] = {
    'command': 'New arrow',
    'sender_arg': True,
    'method':  create_new_arrow,
    'shortcut': 'a',
    'shortcut_context': 'parent_and_children'
}


def create_new_divider(sender):
    """ Create a new divider into embed menu's location
    :return: None
    """
    print("New divider called")
    embed = get_ui_container(sender)
    p1, p2 = embed.get_marker_points()
    embed.blur_away()
    # fixme: finish this!

a['new_divider'] = {
    'command': 'New divider',
    'method': create_new_divider,
    'sender_arg': True,
    'shortcut': 'd',
    'shortcut_context': 'parent_and_children'
}


def edge_label_accept(**args):
    """ Accept & update changes to edited edge label
    :param args: don't know? not used
    :return None:
    """
    print('edge label accept, ', args)
    e = ctrl.ui.get_edge_label_embed()
    if e:
        e.edge.label_text = e.input_line_edit.text()
    ctrl.ui.close_edge_label_editing()

a['edit_edge_label_enter_text'] = {
    'command': 'Enter',
    'method': edge_label_accept,
    'shortcut': 'Return',
    'shortcut_context': 'parent_and_children'
}

def change_edge_ending(self, which_end, value):
    """

    :param which_end:
    :param value:
    :return:
    """
    if value is g.AMBIGUOUS_VALUES:
        return
    scope = ctrl.ui.scope
    if scope == g.SELECTION:
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.ending(which_end, value)
                edge.update_shape()
    elif scope:
        if which_end == 'start':
            self.forest.settings.edge_type_settings(scope, 'arrowhead_at_start', value)
        elif which_end == 'end':
            self.forest.settings.edge_type_settings(scope, 'arrowhead_at_end', value)
        else:
            print('Invalid place for edge ending: ', which_end)

# fixme: No UI to call this
a['change_edge_ending'] = {
    'command': 'Change edge ending',
    'method': change_edge_ending
}

def edge_disconnect(sender):
    """ Remove connection between two nodes, by either cutting from the start or the end. This will result
    in a dangling edge, which should be either connected to another node or removed.
    :return: None
    """
    # Find the triggering edge
    button = get_ui_container(sender)
    if not button:
        return
    edge = button.host
    role = button.role
    if not edge:
        return
    # Then do the cutting
    if role is 'start_cut':
        if edge.edge_type is g.CONSTITUENT_EDGE:
            raise ForestError("Trying edge disconnect at the start of constituent edge")
        else:
            ctrl.forest.delete_edge(edge)

    elif role is 'end_cut':
        if edge.edge_type is g.CONSTITUENT_EDGE:
            old_start = edge.start
            ctrl.forest.disconnect_edge(edge)
            ctrl.forest.fix_stubs_for(old_start)
        else:
            ctrl.forest.delete_edge(edge)
    else:
        raise ForestError('Trying to disconnect node from unknown edge or unhandled cutting position')
    ctrl.ui.update_selections()

a['disconnect_edge'] = {
    'command': 'Disconnect',
    'sender_arg': True,
    'method': edge_disconnect
}


def remove_merger(sender):
    """ In cases where there another part of binary merge is removed, and a stub edge is left dangling,
    there is an option to remove the unnecessary merge -- it is the triggering host.
    :return: None
    """
    node = get_host(sender)
    if not node:
        return
    ctrl.remove_from_selection(node)
    ctrl.forest.delete_unnecessary_merger(node)

a['remove_merger'] = {
    'command': 'Remove merger',
    'sender_arg': True,
    'method': remove_merger
}


def add_triangle(sender):
    """ Turn triggering node into triangle node
    :return: None
    """
    node = get_host(sender)
    if not node:
        return
    ctrl.add_message('folding in %s' % node.as_bracket_string())
    ctrl.forest.add_triangle_to(node)
    ctrl.deselect_objects()


a['add_triangle'] = {
    'command': 'Add triangle',
    'sender_arg': True,
    'method': add_triangle
}


def remove_triangle(sender):
    """ If triggered node is triangle node, restore it to normal
    :return: None
    """
    node = get_host(sender)
    if not node:
        return
    ctrl.add_message('unfolding from %s' % node.as_bracket_string())
    ctrl.forest.remove_triangle_from(node)
    ctrl.deselect_objects()

a['remove_triangle'] = {
    'command': 'Remove triangle',
    'sender_arg': True,
    'method': remove_triangle
}


def finish_editing_node(sender):
    """ Set the new values and close the constituent editing embed.
    :return: None
    """
    embed = get_ui_container(sender)
    if embed.host:
        embed.submit_values()
    embed.blur_away()

a['finish_editing_node'] = {
    'command': 'Apply changes',
    'method': finish_editing_node,
    'shortcut': 'Return',
    'sender_arg': True,
    'shortcut_context': 'parent_and_children'
}


def toggle_raw_editing():
    """ This may be deprecated, but if there is raw latex/html editing possibility, toggle between that and visual
    editing
    :return: None
    """
    embed = ctrl.ui.get_node_edit_embed()
    embed.toggle_raw_edit(embed.raw_button.isChecked())

a['raw_editing_toggle'] = {
    'command': 'Toggle edit mode',
    'method': toggle_raw_editing
}

# Generic keys ####
# 'key_esc'] = {
#     'command': 'key_esc',
#     'method': 'key_esc',
#     'shortcut': 'Escape'},


def key_backspace():
    """ In many contexts this will delete something. Expand this as necessary
    for contexts that don't otherwise grab keyboard.
    :return: None
    """
    print('Backspace pressed')
    for item in ctrl.selected:
        ctrl.forest.delete_item(item)

a['key_backspace'] = {
    'command': 'key_backspace',
    'method': key_backspace,
    'shortcut': 'Backspace'
}


def undo():
    """ Undo -command triggered
    :return: None
    """
    ctrl.forest.undo_manager.undo()

a['undo'] = {
    'command': 'undo',
    'method': undo,
    'undoable': False,
    'shortcut': 'Ctrl+z'}


def redo():
    """ Redo -command triggered
    :return: None
    """
    ctrl.forest.undo_manager.redo()

a['redo'] = {
    'command': 'redo',
    'method': redo,
    'undoable': False,
    'shortcut': 'Ctrl+Shift+z'}


def key_m():
    """ Placeholder for keypress
    :return: None
    """
    print('key_m called')

a['key_m'] = {
    'command': 'key_m',
    'method': key_m,
    'shortcut': 'm'}

a['toggle_all_panels'] = {
    'command': 'Hide all panels',
    'command_alt': 'Show all panels',
    'method': 'toggle_all_panels',  # missing!
    'toggleable': True,
    'condition': 'are_panels_visible'
}

def key_left():
    """ Placeholder for keypress
    :return: None
    """
    print('key_left called')
    if not ctrl.ui_focus:
        ctrl.graph_scene.move_selection('left')

a['key_left'] = {
    'command': 'key_left',
    'undoable': False,
    'method': key_left,
    'shortcut': 'Left'}

def key_right():
    """ Placeholder for keypress
    :return: None
    """
    print('key_right called')
    if not ctrl.ui_focus:
        ctrl.graph_scene.move_selection('right')

a['key_right'] = {
    'command': 'key_right',
    'undoable': False,
    'method': key_right,
    'shortcut': 'Right'}

def key_up():
    """ Placeholder for keypress
    :return: None
    """
    print('key_up called')
    if not ctrl.ui_focus:
        ctrl.graph_scene.move_selection('up')

a['key_up'] = {
    'command': 'key_up',
    'undoable': False,
    'method': key_up,
    'shortcut': 'Up'}

def key_down():
    """ Placeholder for keypress
    :return: None
    """
    print('key_down called')
    if not ctrl.ui_focus:
        ctrl.graph_scene.move_selection('down')

a['key_down'] = {
    'command': 'key_down',
    'undoable': False,
    'method': key_down,
    'shortcut': 'Down'}

# def key_tab():
#     """ Placeholder for keypress
#     :return: None
#     """
#     print('key_tab called')
#
# a['key_tab'] = {
#     'command': 'key_tab',
#     'undoable': False,
#     'method': key_tab,
#     'shortcut': 'Tab'}

actions = a