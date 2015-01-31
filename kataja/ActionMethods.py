import json
import pickle
import pprint
import shlex
import time
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5 import QtWidgets
import subprocess
from kataja.errors import ForestError
import kataja.debug as debug
from kataja.ui.PreferencesDialog import PreferencesDialog
from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.UIManager import PANELS

__author__ = 'purma'

from kataja.singletons import ctrl, prefs, qt_prefs
import kataja.globals as g

def _get_triggered_host():
    host = None
    for item in ctrl.ui.get_overlay_buttons():
        if item.just_triggered:
            item.just_triggered = False
            host = item.host
    return host

class ActionMethods:
    """ These are the methods that are triggered by actions defined in actions.py. Try to keep them in same order as in
    actions.py
    """

    def __init__(self, main):
        self.main = main


    ### Programmatically created actions ###############################################

    # Change visualization style -action (1...9)
    def change_visualization_command(self):
        """


        """
        visualization_key = str(ctrl.main.sender().text())
        ctrl.ui.update_field('visualization_selector', visualization_key)
        ctrl.forest.change_visualization(visualization_key)
        ctrl.add_message(visualization_key)

    def toggle_panel(self, panel_id):
        """
        UI action.
        :return:
        """
        panel = ctrl.ui.get_panel(panel_id)
        if panel:
            if panel.isVisible():
                panel.close()
            else:
                panel.setVisible(True)
                panel.set_folded(False)
        else:
            data = PANELS[panel_id]
            panel = ctrl.ui.create_panel(panel_id, **data)
            panel.setVisible(True)
            panel.set_folded(False)


    def toggle_fold_panel(self, panel_id):
        panel = ctrl.ui.get_panel(panel_id)
        panel.set_folded(not panel.folded)

    def pin_panel(self, panel_id):
        panel = ctrl.ui.get_panel(panel_id)
        panel.pin_to_dock()

    #### Actions from actions.py ######################################################


    def open_kataja_file(self):
        """ Open file browser to load kataja data file"""
        # fileName  = QtGui.QFileDialog.getOpenFileName(self,
        # self.tr("Open File"),
        # QtCore.QDir.currentPath())
        file_help = "KatajaMain files (*.kataja *.zkataja);;Text files containing bracket trees (*.txt, *.tex)"

        # inspection doesn't recognize that getOpenFileName is static, switch it off:
        # noinspection PyTypeChecker,PyCallByClass
        #filename, filetypes = QtWidgets.QFileDialog.getOpenFileName(self.main, "Open KatajaMain tree", "", file_help)
        filename = 'savetest.kataja'
        if filename:
            self.main.load_state_from_file(filename)
            self.main.add_message("Loaded '%s'." % filename)

    # save -action (Command-s)
    def save_kataja_file(self):
        """ Save kataja data with an existing file name. """
        # action  = self.sender()
        ctrl.main.action_finished()
        filename = prefs.file_name
        all_data = ctrl.main.create_save_data()
        t = time.time()
        pickle_format = 4
        if filename.endswith('.zkataja'):
            #f = gzip.open(filename, 'wb')
            f = open(filename, 'wb')
        else:
            f = open(filename, 'wb')
        pickle_worker = pickle.Pickler(f, protocol=pickle_format)
        pickle_worker.dump(all_data)
        f.close()
        ctrl.main.add_message("Saved to '%s'. Took %s seconds." % (filename, time.time()-t))
        return
        t = time.time()
        filename = prefs.file_name + '.dict'
        f = open(filename, 'w')
        pp = pprint.PrettyPrinter(indent=1, stream=f)
        print('is readable: ', pprint.isreadable(all_data))
        pp.pprint(all_data)
        f.close()
        ctrl.main.add_message("Saved to '%s'. Took %s seconds." % (filename, time.time()-t))

        filename = prefs.file_name + '.json'
        f = open(filename, 'w')
        json.dump(all_data, f, indent="\t", sort_keys=False)
        f.close()
        ctrl.main.add_message("Saved to '%s'. Took %s seconds." % (filename, time.time()-t))
        # fileFormat  = action.data().toByteArray()
        # self.saveFile(fileFormat)

    def save_as(self):
        """ Save kataja data to file set by file dialog """
        ctrl.main.action_finished()
        # noinspection PyCallByClass,PyTypeChecker
        filename = QtWidgets.QFileDialog.getSaveFileName(self.main, "Save KatajaMain tree", "",
                                                         "KatajaMain files (*.kataja *.zkataja)")
        prefs.file_name = filename
        ctrl.save_state_to_file(filename)
        ctrl.main.add_message("Saved to '%s'." % filename)

    # print as pdf -action (Command-p)
    def print_to_file(self):
        # hide unwanted components
        """


        """
        debug.keys("Print to file called")
        sc = ctrl.graph_scene
        no_brush = QtGui.QBrush(Qt.NoBrush)
        sc.setBackgroundBrush(no_brush)
        gloss = prefs.include_gloss_to_print
        if gloss:
            sc.photo_frame = sc.addRect(sc.visible_rect_and_gloss().adjusted(-1, -1, 2, 2),
                                                                    ctrl.cm.drawing())
        else:
            if ctrl.forest.gloss and ctrl.forest.gloss.isVisible():
                ctrl.forest.gloss.hide()
            sc.photo_frame = sc.addRect(sc.visible_rect().adjusted(-1, -1, 2, 2),
                                                                    ctrl.cm.selection())
        sc.update()
        ctrl.graph_view.repaint()
        ctrl.main.startTimer(50)

    # Blender export -action (Command-r)
    def render_in_blender(self):
        """
        Try to export as a blender file and run blender render.
        """
        ctrl.graph_scene.export_3d(prefs.blender_env_path + '/temptree.json', ctrl.forest)
        ctrl.main.add_message('Command-r  - render in blender')
        command = '%s -b %s/puutausta.blend -P %s/treeloader.py -o //blenderkataja -F JPEG -x 1 -f 1' % (
            prefs.blender_app_path, prefs.blender_env_path, prefs.blender_env_path)
        args = shlex.split(command)
        subprocess.Popen(args)  # , cwd =prefs.blender_env_path)

    def open_preferences(self):
        """


        """
        if not ctrl.ui.preferences_dialog:
            ctrl.ui.preferences_dialog = PreferencesDialog(self)
        ctrl.ui.preferences_dialog.open()

        # open -action (Command-o)

    def close_all_windows(self):
        self.main.app.closeAllWindows()


    # Next structure -action (.)
    def next_structure(self):
        """


        """
        ctrl.action_undo = False
        i = ctrl.main.switch_to_next_forest()
        ctrl.ui.clear_items()
        ctrl.main.add_message('(.) tree %s: %s' % (i + 1, ctrl.forest.textual_form()))

    # Prev structure -action (,)
    def previous_structure(self):
        """


        """
        ctrl.action_undo = False
        i = ctrl.main.switch_to_previous_forest()
        ctrl.ui.clear_items()
        ctrl.main.add_message('(,) tree %s: %s' % (i + 1, ctrl.forest.textual_form()))

    def animation_step_forward(self):
        """ User action "step forward (>)", Move to next derivation step """
        ctrl.forest.derivation_steps.next_derivation_step()
        ctrl.main.add_message('Step forward')


    def animation_step_backward(self):
        """ User action "step backward (<)" , Move backward in derivation steps """
        ctrl.forest.derivation_steps.previous_derivation_step()
        ctrl.main.add_message('Step backward')

    # ## Menu actions ##########################################################

    def toggle_label_visibility(self):
        """
        toggle label visibility -action (l)


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

    def toggle_brackets(self):
        """ Brackets are visible always for non-leaves, never or for important parts """
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

    def toggle_traces(self):
        """ Show traces -action (t) """
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

    # Change node edge shapes -action (s)
    def change_node_edge_shape(self, shape=''):
        """

        :param shape:
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
        ctrl.announce(g.EDGE_SHAPES_CHANGED, g.CONSTITUENT_EDGE, i)

    # Change feature edge shapes -action (S)
    def change_feature_edge_shape(self, shape):
        """


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
        ctrl.ui.ui_buttons['feature_line_type'].setCurrentIndex(i)
        ctrl.main.add_message('(s) Change feature edge shape: %s-%s' % (i, shape))


    def show_merge_order(self):
        """ Use merge order-features """
        if ctrl.forest.settings.shows_merge_order():
            ctrl.main.add_message('(o) Hide merge order')
            ctrl.forest.settings.shows_merge_order(False)
            ctrl.forest.remove_order_features('M')
        else:
            ctrl.main.add_message('(o) Show merge order')
            ctrl.forest.settings.shows_merge_order(True)
            ctrl.forest.add_order_features('M')

    def show_select_order(self):
        """ Use select order-features """
        if ctrl.forest.settings.shows_select_order():
            ctrl.main.add_message('(O) Hide select order')
            ctrl.forest.settings.shows_select_order(False)
            ctrl.forest.remove_order_features('S')
        else:
            ctrl.main.add_message('(O) Show select order')
            ctrl.forest.settings.shows_select_order(True)
            ctrl.forest.add_order_features('S')

    def change_colors(self):
        """
        change colors -action (shift-c)


        """
        color_panel = ctrl.ui._ui_panels['Colors']
        if not color_panel.isVisible():
            color_panel.show()
        else:
            ctrl.forest.settings._hsv = None
            ctrl.forest.update_colors()
            ctrl.main.activateWindow()
            # self.ui.add_message('Color seed: H: %.2f S: %.2f L: %.2f' % ( h, s, l))

    def fit_to_window(self):
        """ Fit graph to current window. Usually happens automatically, but also available as user action
        :return: None
        """
        ctrl.graph_scene.fit_to_window()

    def toggle_full_screen(self):
        """ Full screen -action (f) """
        if ctrl.main.isFullScreen():
            ctrl.main.showNormal()
            ctrl.main.add_message('(f) windowed')
            ctrl.ui.restore_panel_positions()
        else:
            ctrl.ui.store_panel_positions()
            ctrl.main.showFullScreen()
            ctrl.main.add_message('(f) fullscreen')
        ctrl.graph_scene.fit_to_window()

    def change_edge_panel_scope(self, selection):
        """ Change drawing panel to work on selection, constituent edges or other available edges
        :param selection: int scope identifier, from globals
        :return:
        """
        ctrl.action_undo = False
        p = ctrl.ui.get_panel(g.DRAWING)
        p.change_scope(selection)
        p.update_panel()
        p = ctrl.ui.get_panel(g.LINE_OPTIONS)
        p.update_panel()

    def change_edge_shape(self, shape):
        if shape is g.AMBIGUOUS_VALUES:
            return
        scope = ctrl.ui.get_panel(g.DRAWING).scope
        if scope == g.SELECTION:
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    edge.shape_name = shape
                    edge.update_shape()
        elif scope:
            ctrl.forest.settings.edge_type_settings(scope, 'shape_name', shape)
            ctrl.announce(g.EDGE_SHAPES_CHANGED, scope, shape)
        line_options = ctrl.ui.get_panel(g.LINE_OPTIONS)
        if line_options:
            line_options.update_panel()
        ctrl.main.add_message('(s) Changed relation shape to: %s' % shape)

    def change_edge_color(self, color):
        if color is g.AMBIGUOUS_VALUES:
            return
        panel = ctrl.ui.get_panel(g.DRAWING)
        if not color:
            ctrl.ui.start_color_dialog(panel, 'color_changed')
            return
        if panel.scope == g.SELECTION:
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    edge.color(color)
                    #edge.update_shape()
                    edge.update()
        elif panel.scope:
            ctrl.forest.settings.edge_type_settings(panel.scope, 'color', color)
            #ctrl.announce(g.EDGE_SHAPES_CHANGED, scope, color)
        panel.update_color(color)
        panel.update_panel()
        ctrl.main.add_message('(s) Changed relation color to: %s' % ctrl.cm.get_color_name(color))

    def toggle_line_options(self):
        print('toggle line options')
        lo = ctrl.ui.get_panel(g.LINE_OPTIONS)
        if lo:
            if lo.isVisible():
                lo.close()
            else:
                lo.show()
        else:
            ctrl.ui.create_panel(g.LINE_OPTIONS, **PANELS[g.LINE_OPTIONS])
            lo = ctrl.ui.get_panel(g.LINE_OPTIONS)
            lo.show()

    def adjust_control_point(self, cp_index, dim, value=0):
        """ Adjusting control point can be done only for selected edges, not for an edge type. So this method is
        simpler than other adjustments, as it doesn't have to handle both cases.
        :param cp_index: 1 or 2
        :param dim: 'x', 'y' or 'r' for reset
        :param value: new value for given dimension, doesn't matter for reset.
        :return:
        """
        cp_index -= 1
        for edge in ctrl.get_all_selected():
            if isinstance(edge, Edge):
                if dim == 'r':
                    edge.reset_control_point(cp_index)
                else:
                    edge.adjust_control_point_xy(cp_index, dim, value)

    def change_leaf_shape(self, dim, value=0):
        #if value is g.AMBIGUOUS_VALUES:
        #  if we need this, we'll need to find some impossible ambiguous value to avoid weird, rare incidents
        #    return
        panel = ctrl.ui.get_panel(g.DRAWING)
        if panel.scope == g.SELECTION:
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    edge.change_leaf_shape(dim, value)
        elif panel.scope:
            if dim == 'w':
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'leaf_x', value)
            elif dim == 'h':
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'leaf_y', value)
            elif dim == 'r':
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'leaf_x', g.DELETE)
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'leaf_y', g.DELETE)
                options_panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
                options_panel.update_panel()
            else:
                raise ValueError
            ctrl.announce(g.EDGE_SHAPES_CHANGED, panel.scope, value)
        #panel.update_color(color)
        #panel.update_panel()
        #ctrl.main.add_message('(s) Changed relation color to: %s' % ctrl.cm.get_color_name(color))

    def change_edge_thickness(self, dim, value=0):
        panel = ctrl.ui.get_panel(g.DRAWING)
        if panel.scope == g.SELECTION:
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    edge.change_thickness(dim, value)
        elif panel.scope:
            if dim == 'r':
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'thickness', g.DELETE)
                options_panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
                options_panel.update_panel()
            else:
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'thickness', value)
            ctrl.announce(g.EDGE_SHAPES_CHANGED, panel.scope, value)


    def change_curvature(self, dim, value=0):
        panel = ctrl.ui.get_panel(g.DRAWING)
        if panel.scope == g.SELECTION:
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    edge.change_curvature(dim, value)
            if dim == 'r' or dim == 's':
                options_panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
                options_panel.update_panel()
        elif panel.scope:
            options_panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
            relative = options_panel.relative_curvature()

            if dim == 'x':
                if relative:
                    ctrl.forest.settings.edge_shape_settings(panel.scope, 'rel_dx', value * .01)
                else:
                    ctrl.forest.settings.edge_shape_settings(panel.scope, 'fixed_dx', value)
            elif dim == 'y':
                if relative:
                    ctrl.forest.settings.edge_shape_settings(panel.scope, 'rel_dy', value * .01)
                else:
                    ctrl.forest.settings.edge_shape_settings(panel.scope, 'fixed_dy', value)
            elif dim == 'r':
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'rel_dx', g.DELETE)
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'rel_dy', g.DELETE)
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'fixed_dx', g.DELETE)
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'fixed_dy', g.DELETE)
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'relative', g.DELETE)
                options_panel.update_panel()
            elif dim == 's':
                ctrl.forest.settings.edge_shape_settings(panel.scope, 'relative', value == 'relative')
                options_panel.update_panel()
            else:
                raise ValueError
            ctrl.announce(g.EDGE_SHAPES_CHANGED, panel.scope, value)

    def change_edge_asymmetry(self, value):
        print('changing asymmetry: ', value)

    def change_visualization(self, i):
        """
        :param i: index of selected visualization in relevant panel
        :return:
        """
        pass

    # help -action (h)
    def show_help_message(self):
        """


        """
        m = ""

        # m ="""(h):------- KatajaMain commands ----------
        # (left arrow/,):previous structure   (right arrow/.):next structure
        # (1-5):change or refresh visualization of the tree
        # (f):fullscreen/windowed mode
        # (p):print tree to file
        # (b):show/hide labels in middle of edges
        # (c):curved/straight edges
        # (q):quit"""
        ctrl.main.add_message(m)

    # ui
    def close_embeds(self):
        ctrl.ui.close_new_element_embed()
        ctrl.ui.close_edge_label_editing()
        ctrl.ui.close_constituent_editing()

    # ui
    def new_element_accept(self):
        type = ctrl.ui.get_new_element_type_selection()
        text = ctrl.ui.get_new_element_text()
        p1, p2 = ctrl.ui.get_new_element_embed_points()
        ctrl.focus_point = p2

        if type == g.GUESS_FROM_INPUT:
            print("Guessing input type")
            # we can add a test if line p1 - p2 crosses several edges, then it can be a divider
            #Fixme Use screen coordinates instead, as if zoomed out, the default line can already be long enough. oops.
            if (p1 - p2).manhattanLength() > 20 and not text.startswith('['):
                # It's an Arrow!
                self.create_new_arrow()
                return
            else:
                print('trying to parse ', text)
                node = ctrl.forest.create_node_from_string(text)
                print(node)
        ctrl.ui.close_new_element_embed()

    def create_new_arrow(self):
        print("New arrow called")
        p1, p2 = ctrl.ui.get_new_element_embed_points()
        text = ctrl.ui.get_new_element_text()
        ctrl.forest.create_arrow(p1, p2, text)
        ctrl.ui.close_new_element_embed()

    def create_new_divider(self):
        print("New divider called")
        p1, p2 = ctrl.ui.get_new_element_embed_points()
        ctrl.ui.close_new_element_embed()

    #ui
    def edge_label_accept(self, **args):
        print('edge label accept, ', args)
        e = ctrl.ui.get_edge_label_embed()
        if e:
            e.edge.label_text = e.input_line_edit.text()
        ctrl.ui.close_edge_label_editing()

    #ui
    def edge_disconnect(self):
        """
        :return:
        """
        # Find the triggering edge
        edge = None
        role = None
        for item in ctrl.ui.get_overlay_buttons():
            if item.just_triggered:
                item.just_triggered = False
                edge = item.host
                role = item.role
        if not edge:
            return
        # Then do the cutting
        if role is 'start_cut':
            if edge.edge_type is g.CONSTITUENT_EDGE:
                raise ForestError("Trying edge disconnect at the start of constituent edge")
            else:
                ctrl.forest.disconnect_edge_start(edge)

        elif role is 'end_cut':
            if edge.edge_type is g.CONSTITUENT_EDGE:
                old_start = edge.start
                ctrl.forest._disconnect_node(first=old_start, second=edge.end, edge=edge)
                ctrl.forest.fix_stubs_for(old_start)
            else:
                ctrl.forest.disconnect_edge_end(edge)
        else:
            raise ForestError('Trying to disconnect node from unknown edge or unhandled cutting position')
        ctrl.ui.update_selections()

    def remove_merger(self):
        node = _get_triggered_host()
        if not node:
            return
        ctrl.remove_from_selection(node)
        ctrl.forest.delete_unnecessary_merger(node)

    def add_triangle(self):
        node = _get_triggered_host()
        if not node:
            return
        ctrl.forest.add_triangle_to(node)
        ctrl.ui.update_selections()

    def remove_triangle(self):
        node = _get_triggered_host()
        if not node:
            return
        ctrl.forest.remove_triangle_from(node)
        ctrl.ui.update_selections()

    ###### Constituent editing #################
    def finish_constituent_edit(self):
        print('Edited constituent!')
        embed = ctrl.ui.get_constituent_edit_embed()
        if not embed.node:
            ctrl.ui.close_constituent_editing()
            return
        node = embed.node
        embed.push_values_back()
        #node.alias = embed.alias_edit.text()
        #node.label = embed.input_line_edit.text()
        #node.index = embed.index_edit.text()
        #node.gloss = embed.gloss_edit.text()
        ctrl.ui.close_constituent_editing()


    ###### Keys #################
    def key_backspace(self):
        print('Backspace pressed')
        for item in ctrl.get_all_selected():
            ctrl.forest.delete_item(item)

    def undo(self):
        """ Undo -command triggered """
        ctrl.forest.undo_manager.undo()

    def redo(self):
        """ Redo -command triggered """
        ctrl.forest.undo_manager.redo()





