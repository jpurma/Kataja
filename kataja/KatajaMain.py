#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

# Note: convention that I try to start following is that Kataja methods are in
# small caps and underscore (Python convention), but Qt methods are in camelcase.
# Classnames are in camelcase.

import gc
# import gzip
import os.path
import time
import pickle

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from kataja.environment import default_userspace_path, plugins_path
from kataja.KeyPressManager import KeyPressManager

from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.Forest import Forest
from kataja.ForestKeeper import ForestKeeper
from kataja.GraphScene import GraphScene
from kataja.GraphView import GraphView
from kataja.Presentation import TextArea
from kataja.Edge import Edge
from kataja.UIManager import UIManager
from kataja.PaletteManager import PaletteManager
from kataja.object_factory import create
import kataja.globals as g
from kataja.utils import time_me, import_plugins
from kataja.visualizations.available import VISUALIZATIONS
import kataja.debug as debug
from kataja.BaseModel import BaseModel



# show labels

ONLY_LEAF_LABELS = 0
ALL_LABELS = 1
ALIASES = 2

# only for debugging (Apple-m, memory check), can be commented
# try:
# import objgraph
# except ImportError:
# objgraph = None

# KatajaMain > UIView > UIManager > GraphView > GraphScene > Leaves etc.


class KatajaMainModel(BaseModel):
    def __init__(self, host, unique=False):
        super().__init__(host, unique)
        self.forest_keeper = None
        self.forest = None
        self._forest_keeper_touched = False
        self._forest_touched = False


class KatajaMain(QtWidgets.QMainWindow):
    """ Qt's main window. When this is closed, application closes. Graphics are
    inside this, in scene objects with view widgets. This window also manages
    keypresses and menus. """

    def __init__(self, kataja_app, splash, args):
        """ KatajaMain initializes all its children and connects itself to
        be the main window of the given application. """
        t = time.time()
        self.model = KatajaMainModel(self, unique=True)
        super().__init__()
        print('---- initialized MainWindow base class ... ', time.time() - t)
        self.app = kataja_app
        self.forest = None
        self.fontdb = QtGui.QFontDatabase()
        print('---- set up font db ... ', time.time() - t)
        self.color_manager = PaletteManager()
        print('---- Initialized color manager ... ', time.time() - t)
        prefs.load_preferences()
        qt_prefs.late_init(prefs, self.fontdb)
        import_plugins(prefs, plugins_path)
        self.setWindowIcon(QtGui.QIcon(qt_prefs.kataja_icon))
        self.app.setFont(qt_prefs.font(g.UI_FONT))
        self.app.processEvents()
        print('---- initialized prefs ... ', time.time() - t)
        ctrl.late_init(self)
        print('---- controller late init ... ', time.time() - t)
        self.graph_scene = GraphScene(main=self, graph_view=None)
        print('---- scene init ... ', time.time() - t)
        self.graph_view = GraphView(main=self, graph_scene=self.graph_scene)
        print('---- view init ... ', time.time() - t)
        self.graph_scene.graph_view = self.graph_view
        self.ui_manager = UIManager(self)
        self.ui_manager.populate_ui_elements()
        self.key_manager = KeyPressManager(self)
        self.object_factory = create
        print('---- ui init ... ', time.time() - t)
        self.model.forest_keeper = ForestKeeper()
        print('---- forest_keeper init ... ', time.time() - t)
        kataja_app.setPalette(self.color_manager.get_qt_palette())
        self.visualizations = VISUALIZATIONS
        print('---- visualizations init ... ', time.time() - t)
        self.forest = Forest()
        print('---- forest init ... ', time.time() - t)
        self.setCentralWidget(self.graph_view)

        print('---- set palette ... ', time.time() - t)
        self.load_treeset()
        print('---- loaded treeset ... ', time.time() - t)
        x, y, w, h = (50, 50, 940, 720)
        self.setMinimumSize(w, h)
        self.setWindowTitle(self.tr("Kataja"))
        self.setDockOptions(QtWidgets.QMainWindow.AnimatedDocks)
        self.setCorner(QtCore.Qt.TopLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.TopRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomRightCorner, QtCore.Qt.RightDockWidgetArea)
        # toolbar = QtWidgets.QToolBar()
        # toolbar.setFixedSize(480, 40)
        # self.addToolBar(toolbar)
        self.status_bar = self.statusBar()
        self.setGeometry(x, y, w, h)
        self.show()
        self.raise_()
        self.activateWindow()
        self.add_message('Welcome to Kataja! (h) for help')
        self.action_finished()
        print('---- finished start sequence... ', time.time() - t)

    def load_treeset(self, filename=''):
        """ Loads and initializes a new set of trees. Has to be done before the program can do anything sane.
        :param treeset_list:
        """
        print('----- Initializing -----')
        self.forest_keeper = ForestKeeper(filename=filename or prefs.debug_treeset)
        print('----- End Initializing -----')
        print('--- Changing forest ----')
        self.change_forest(self.forest_keeper.forest)
        print('--- End Changing forest ----')

    # ### Visualization #############################################################

    @property
    def forest(self):
        """


        :return:
        """
        return self.model.forest

    @forest.setter
    def forest(self, value):
        """ :param forest:
        :param value:
        """
        self.model.forest = value

    @property
    def forest_keeper(self):
        """ Return the forest keeper instance, there should be only one per Kataja instance
        :return: ForestKeeper instance
        """
        return self.model.forest_keeper

    @forest_keeper.setter
    def forest_keeper(self, value):
        """ Return the forest keeper instance, there should be only one per Kataja instance
        :param value: ForestKeeper instance
        """
        self.model.forest_keeper = value


    def change_forest(self, forest):
        """ Tells the scene to remove current tree and related data and change it to a new one
        :param forest:
        """
        ctrl.disable_undo = True
        self.ui_manager.clear_items()
        if self.forest:
            self.forest.retire_from_drawing()
        self.forest = self.forest_keeper.forest
        self.forest.prepare_for_drawing()
        ctrl.disable_undo = False

    def redraw(self):
        """ Call for forest redraw
        :return: None
        """
        self.forest.draw()

    def add_message(self, msg):
        """ Show a message in UI's console
        :param msg: str -- message
        """
        self.ui_manager.add_message(msg)

    def mousePressEvent(self, event):
        """ KatajaMain doesn't do anything with mousePressEvents, it delegates
        :param event:
        them downwards. This is for debugging. """
        QtWidgets.QMainWindow.mousePressEvent(self, event)

    def keyPressEvent(self, event):
        # if not self.key_manager.receive_key_press(event):
        """

        :param event:
        :return:
        """
        return QtWidgets.QMainWindow.keyPressEvent(self, event)


    # ### ConstituentNode's radial menu commands ################################

    # radial menu only
    def do_merge(self, caller, event):
        """

        :param caller:
        :param event:
        :return:
        """
        # if isinstance(caller, MenuItem):
        # caller = caller.host_node
        node_A = caller
        node_B = caller.get_root_node()
        assert (node_A is not node_B)
        merged = self.forest.merge_nodes(node_A, node_B)
        node_A.release()
        self.action_finished()
        merged.take_focus()
        return True

    # radial menu only
    def do_delete_node(self, caller, event):
        """

        :param caller:
        :param event:
        :return:
        """
        # if isinstance(caller, MenuItem):
        # caller = caller.host_node
        self.forest.command_delete(caller)
        self.action_finished()
        ctrl.focus = None
        return True

    # radial menu only
    def disconnect_node(self, caller=None, event=None):
        """

        :param caller:
        :param event:
        :return:
        """
        # if isinstance(caller, MenuItem):
        # caller = caller.host_node
        self.forest.disconnect_node_from_tree(caller)
        self.action_finished()
        ctrl.focus = None
        return True

    # radial menu only
    def copy_selected(self, **kw):
        """ Make a copy of element and put it beside the original
        :param kw:
        """
        for node in ctrl.get_all_selected():
            self.forest.copy_node(node)
        self.action_finished()
        return True

    # ## New node creation commands #############################################

    def add_text_box(self, caller=None):
        """

        :param caller:
        """
        text = ''
        if hasattr(caller, 'get_text_input'):
            text = caller.get_text_input()
            text_area = TextArea(text)
            text_area.set_original_position(caller.current_position)
            self.forest.store(text_area)
        self.action_finished()

    def add_new_constituent(self, caller=None):
        """

        :param caller:
        """
        text = ''
        if hasattr(caller, 'get_text_input'):
            text = caller.get_text_input()
        if ctrl.single_selection():  # live editing
            self.forest.reform_constituent_node_from_string(text, ctrl.get_selected())
        else:
            self.forest.create_node_from_string(text, caller.pos())
        self.action_finished()

    def add_new_tree(self, caller=None):
        """

        :param caller:
        """
        text = ''
        if hasattr(caller, 'get_text_input'):
            text = caller.get_text_input()
        # pos = caller.pos()
        self.forest.create_tree_from_string(text)  # , pos=pos)
        self.action_finished()

    # ## Menu management #######################################################

    def action_triggered(self):
        """ Trigger action with parameters received from action data object and designated UI element
        :return: None
        """
        # -- Redraw and undo flags: these are on by default, can be switched off by action method
        ctrl.action_redraw = True
        # ---------------------------
        sender = self.sender()
        key = sender.data()
        data = self.ui_manager.actions[key]
        args = list(data.get('args', []))
        undoable = data.get('undoable', True)
        element = self.ui_manager.get_element_value(data.get('ui_element', None))
        if element:
            args += element
        print("Doing action '%s' with method '%s' and with args: %s" % (key, data['method'], str(args)))

        # Disable undo if necessary
        if not undoable:
            remember_undo_state = ctrl.disable_undo
            ctrl.disable_undo = True

        # Call method
        data['method'](*args)

        # Restore undo state to what it was
        if not undoable:
            ctrl.disable_undo = remember_undo_state
        self.action_finished(m=data.get('command', ''), undoable=undoable)

    def action_finished(self, m='', undoable=True):
        """

        :param m: message for undo
        :param undoable: are we supposed to take a snapshot of changes after this action.
        """
        if ctrl.action_redraw:
            ctrl.forest.draw()
        if undoable:
            ctrl.forest.undo_manager.take_snapshot(m)
        else:
            ctrl.graph_scene.start_animations()


    def enable_actions(self):
        """ Restores menus """
        for action in self.ui_manager.qt_actions.values():
            action.setDisabled(False)

    def disable_actions(self):
        """ Actions shouldn't be initiated when there is other multi-phase
        action going on """
        for action in self.ui_manager.qt_actions.values():
            action.setDisabled(True)


    def adjust_colors(self, hsv):
        """
        adjust colors -action (shift-alt-c)

        :param hsv:
        """
        self.forest.settings.hsv(hsv)
        self.forest.update_colors()

    def change_color_mode(self, mode):
        """
        triggered by color mode selector in colors panel

        :param mode:
        """
        if mode != prefs.color_mode:
            prefs.color_mode = mode
            self.forest.update_colors()


    def toggle_magnets(self):
        """ Toggle lines to connect to margins or to centre of node (b)
        """
        if self.forest.settings.uses_magnets():
            self.add_message('(c) 0: Lines connect to node margins')
            self.forest.settings.uses_magnets(False)
        else:
            self.add_message('(c) 1: Lines aim to the center of the node')
            self.forest.settings.uses_magnets(True)


    def change_edge_ending(self, which_end, value):
        """

        :param which_end:
        :param value:
        :return:
        """
        if value is g.AMBIGUOUS_VALUES:
            return
        panel = self.ui_manager.get_panel(g.EDGES)
        if panel.scope == g.SELECTION:
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    edge.ending(which_end, value)
                    edge.update_shape()
        elif panel.scope:
            if which_end == 'start':
                self.forest.settings.edge_type_settings(panel.scope, 'arrowhead_at_start', value)
            elif which_end == 'end':
                self.forest.settings.edge_type_settings(panel.scope, 'arrowhead_at_end', value)
            else:
                print('Invalid place for edge ending: ', which_end)

    #





    def timerEvent(self, event):
        """ Timer event only for printing, for 'snapshot' effect
        :param event:
        """
        def find_path(fixed_part, extension, counter=0):

            if not counter:
                full_path = fixed_part + extension
            else:
                full_path = fixed_part + str(counter) + extension
            if os.path.exists(full_path):
                full_path = find_path(fixed_part, extension, counter + 1)
            return full_path

        self.killTimer(event.timerId())
        # Prepare file and path
        path = prefs.print_file_path or prefs.userspace_path or default_userspace_path
        if not path.endswith('/'):
            path += '/'
        if not os.path.exists(path):
            print("bad path for printing (print_file_path in preferences) , using '.' instead.")
            path = './'
        filename = prefs.print_file_name
        if filename.endswith('.pdf'):
            filename = filename[:-4]
        # Prepare image
        self.graph_scene.removeItem(self.graph_scene.photo_frame)
        self.graph_scene.photo_frame = None
        # Prepare printer
        png = True
        source = self.graph_scene.visible_rect()
        source.adjust(0, 0, 5, 10)

        if png:
            full_path = find_path(path + filename, '.png', 0)
            scale = 4
            target = QtCore.QRectF(QtCore.QPointF(0, 0), source.size() * scale)
            writer = QtGui.QImage(target.size().toSize(), QtGui.QImage.Format_ARGB32_Premultiplied)
            writer.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter()
            painter.begin(writer)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            self.graph_scene.render(painter, target=target, source=source)
            painter.end()
            iwriter = QtGui.QImageWriter(full_path)
            iwriter.write(writer)
            self.add_message("printed to %s as PNG (%spx x %spx, %sx size)." %
                             (full_path, int(target.width()), int(target.height()), scale))

        else:
            dpi = 25.4
            full_path = find_path(path + filename, '.pdf', 0)
            target = QtCore.QRectF(0, 0, source.width() / 2.0, source.height() / 2.0)

            writer = QtGui.QPdfWriter(full_path)
            writer.setResolution(dpi)
            writer.setPageSizeMM(target.size())
            writer.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))
            painter = QtGui.QPainter()
            painter.begin(writer)
            self.graph_scene.render(painter, target=target, source=source)
            painter.end()
            self.add_message("printed to %s as PDF with %s dpi." % (full_path, dpi))

        # Thank you!
        print('printing done.')
        # Restore image
        self.graph_scene.setBackgroundBrush(self.color_manager.gradient)

    # Not called from anywhere yet, but useful
    def release_selected(self, **kw):
        """

        :param kw:
        :return:
        """
        for node in ctrl.get_all_selected():
            node.release()
        self.action_finished()
        return True


    def clear_all(self):
        """ Empty everything - maybe necessary before loading new data. """
        self.ui_manager.clear_items()
        if self.forest:
            self.forest.retire_from_drawing()
            self.forest = None
        self.forest_keeper = None
        print('garbage stats:', gc.get_count())
        gc.collect()
        print('after collection:', gc.get_count())
        if gc.garbage:
            print('garbage:', gc.garbage)
        self.forest_keeper = ForestKeeper()

    # ### Action preconditions ##################################################

    # return True or False: should the related action be enabled or disabled

    # noinspection PyMethodMayBeStatic
    def can_root_merge(self):
        """ Check if the selected node can be merged upwards to the root node of its current tree.
        :return: bool
        """
        return ctrl.single_selection() and not ctrl.get_selected().is_root_node()

    # ### Unused two-phase actions ###############################################

    def start_pointing_mode(self, event, method=None, data=None):
        """ Begin pointing mode, mouse pointer draws a line behind it and normal actions are disabled
        :param event:
        :param method:
        :param data:
        """
        if not data:
            data = {}
        ctrl.pointing_mode = True
        ctrl.pointing_method = method
        ctrl.pointing_data = data
        self.ui_manager.begin_stretchline(data['start'].pos(), event.scenePos())  # +data['startposF']
        self.app.setOverrideCursor(QtCore.Qt.CrossCursor)
        self.graph.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    # noinspection PyUnusedLocal
    def end_pointing_mode(self, event):
        """ End pointing mode and return to normal
        :param event:
        """
        ctrl.pointing_mode = False
        ctrl.pointing_data = {}
        self.ui_manager.end_stretchline()
        self.app.restoreOverrideCursor()
        self.graph.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def begin_merge_to(self, event):
        """ MergeTo is a two phase action. First the target is selected in pointing mode, then 'end_merge_to' is called
        :param event:
        """
        self.start_pointing_mode(event, method=self.end_merge_to, data={'start': ctrl.get_selected()})
        return False

    def end_merge_to(self, event):
        """
        Merging a node -activity ends.
        :param event: mouse-event that triggered the end.
        :return:
        """
        node_a = ctrl.pointing_data['target']
        node_b = None
        self.forest.merge_nodes(node_a, node_b)
        node_a.release()
        # node_A.state =SELECTED # deselect doesn't have effect unless node is selected
        self.end_pointing_mode(event)
        self.action_finished()
        return True

    # ### Other window events ###################################################

    def closeEvent(self, event):
        """ Shut down the program, give some debug info
        :param event:
        """
        QtWidgets.QMainWindow.closeEvent(self, event)
        if ctrl.print_garbage:
            # import objgraph
            print('garbage stats:', gc.get_count())
            gc.collect()
            print('after collection:', gc.get_count())
            if gc.garbage:
                print('garbage:', gc.garbage)

                # objgraph.show_most_common_types(limit =40)
        prefs.save_preferences()
        print('...done')

    @time_me
    def create_save_data(self):
        """
        Make a large dictionary of all objects with all of the complex stuff and circular references stripped out.
        :return: dict
        """
        savedata = {}
        open_references = {}
        savedata['save_scheme_version'] = 0.2
        self.model.save_object(savedata, open_references)
        c = 0
        while open_references and c < 10:
            c += 1
            print(len(savedata))
            print('---------------------------')
            for obj in list(open_references.values()):
                if hasattr(obj, 'model') and hasattr(obj, 'save_key'):
                    obj.model.save_object(savedata, open_references)
                else:
                    print('cannot save open reference object ', obj)

        print('total savedata: %s chars in %s items.' % (len(str(savedata)), len(savedata)))
        # print(savedata)
        return savedata

        # f = open('kataja_default.cfg', 'w')
        # json.dump(prefs.__dict__, f, indent = 1)
        # f.close()

# def maybeSave(self):
# if False and self.scribbleArea.isModified():
# ret  = QtGui.QMessageBox.warning(self, self.tr("Scribble"),
# self.tr("The image has been modified.\n"
# "Do you want to save your changes?"),
# QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
# QtGui.QMessageBox.No,
# QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)
# if ret  == QtGui.QMessageBox.Yes:
# return True # self.saveFile("png")
# elif ret  == QtGui.QMessageBox.Cancel:
# return False
#
# return True
#
# def saveFile(self, fileFormat):
# initialPath  = QtCore.QDir.currentPath() + "/untitled." + fileFormat
#
# fileName  = QtGui.QFileDialog.getSaveFileName(self, self.tr("Save As"),
# initialPath,
# self.tr("%1 Files (*.%2);;All Files (*)")
# .arg(QtCore.QString(fileFormat.toUpper()))
# .arg(QtCore.QString(fileFormat)))
# if fileName.isEmpty():
# return False
# else:
# return self.scribbleArea.saveImage(fileName, fileFormat)
