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
# small caps and underscore (Python convention), but Qt methods are in
# camelcase.
# Classnames are in camelcase.

import gc
import importlib
import json
import os.path
import sys
import traceback
import queue

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import time

import kataja.globals as g
from syntax.SyntaxConnection import SyntaxConnection
from kataja.GraphScene import GraphScene
from kataja.GraphView import GraphView
from kataja.PaletteManager import PaletteManager
from kataja.SavedField import SavedField
from kataja.SavedObject import SavedObject
from kataja.Settings import Settings
from kataja.UIManager import UIManager
from kataja.saved.Forest import Forest
from kataja.singletons import ctrl, prefs, qt_prefs, running_environment, classes, log
from kataja.ui_support.ErrorDialog import ErrorDialog
from kataja.ui_support.PreferencesDialog import PreferencesDialog
from kataja.utils import time_me
from kataja.visualizations.available import VISUALIZATIONS
from kataja.LogWidgetPusher import capture_stdout

# only for debugging (Apple-m, memory check), can be commented
# try:
# import objgraph
# except ImportError:
# objgraph = None



# KatajaMain > UIView > UIManager > GraphView > GraphScene > Leaves etc.
# .SelectionBox, .QComboBox,
stylesheet = """
.QWidget, .SelectionBox, .QComboBox, QLabel, QAbstractButton, QAbstractSpinBox, QDialog, QFrame,
QMainWindow, QDialog, QDockWidget {font-family: "%(ui_font)s"; font-size: %(ui_font_size)spx;}
OverlayLabel {color: %(ui)s; border-radius: 3; padding: 4px;}
QComboBox QAbstractItemView {selection-color: %(ui)s;}
b {font-family: StixGeneral Bold; font-weight: 900; font-style: bold}
sub sub {font-size: 8pt; vertical-align: sub}
sup sub {font-size: 8pt; vertical-align: sub}
sub sup {font-size: 8pt; vertical-align: sup}
sup sup {font-size: 8pt; vertical-align: sup}
QComboBox, TwoColorButton {background-color: %(paper)s;}
UnicodeIconButton {background-color: %(paper)s; font-family: "%(main_font)s"; 
                   font-size: %(main_font_size)spx;}
TwoStateButton {border: 1px transparent none; color: %(ui)s; font-family: "%(ui_font)s";
           font-size: %(ui_font_larger)spx}
TwoStateButton:hover {border: 1px solid %(ui)s; border-radius: 3}
TwoStateButton:pressed {border: 1px solid %(ui_lighter)s; background-color: %(paper)s;
                         border-radius: 3}
TwoStateButton:checked:!hover {border: 1px solid %(paper)s; background-color: %(ui)s; 
                                border-radius: 3; color: %(paper)s}
TwoStateButton:checked:hover {border-color: %(ui_lighter)s; background-color: %(ui)s; 
                               border-radius: 3; color: %(ui_lighter)s}
VisButton {font-size: %(ui_font_larger)spx; color: %(ui)s;}
PanelButton {border: 1px transparent none;}
PanelButton:hover {border: 1px solid %(ui)s; border-radius: 3}
PanelButton:pressed {border: 1px solid %(ui_lighter)s; background-color: %(paper)s;
                     border-radius: 3}
PanelButton:checked {border: 1px solid %(ui)s; border-radius: 3}
PanelButton:checked:disabled {border-color: %(draw)s}
EyeButton {border: 1px transparent none;}
EyeButton:hover, EyeButton:checked:hover {border: 1px solid %(ui)s; border-radius: 3}
EyeButton:pressed {border: 1px solid %(ui_lighter)s; background-color: %(paper)s;
                     border-radius: 3}
EyeButton:checked {border: 1px transparent none;}

ColorSelector:hover {border: 1px solid %(ui)s; border-radius: 3}
TwoStateIconButton, TwoStateIconButton:checked {border: 1px solid transparent; 
                                             background-color: transparent;}
TwoStateIconButton:pressed {border: 1px solid %(ui_lighter)s; background-color: %(paper)s;}
TwoStateIconButton:hover {border: 1px solid %(ui)s; background-color: %(paper)s; border-radius: 3}
"""
# EyeButton {border: 1px solid %(ui_darker)s;}
# EyeButton:checked {border: 1px solid %(ui)s; border-radius: 3}


# ProjectionButtons QPushButton:checked {border: 2px solid %(ui)s; border-radius: 3}


class KatajaMain(SavedObject, QtWidgets.QMainWindow):
    """ Qt's main window. When this is closed, application closes. Graphics are
    inside this, in scene objects with view widgets. This window also manages
    keypresses and menus. """
    unique = True

    def __init__(self, kataja_app, no_prefs=False, reset_prefs=False):
        """ KatajaMain initializes all its children and connects itself to
        be the main window of the given application. Receives launch arguments:
        :param no_prefs: bool, don't load or save preferences
        :param reset_prefs: bool, don't attempt to load preferences, use defaults instead

        """
        QtWidgets.QMainWindow.__init__(self)
        kataja_app.processEvents()
        SavedObject.__init__(self)

        self.use_tooltips = True
        self.available_plugins = {}
        self.setDockOptions(QtWidgets.QMainWindow.AnimatedDocks)
        self.setCorner(QtCore.Qt.TopLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.TopRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomRightCorner, QtCore.Qt.RightDockWidgetArea)
        x, y, w, h = (50, 50, 1152, 720)
        self.setMinimumSize(w, h)
        self.app = kataja_app
        self.classes = classes
        self.save_prefs = not no_prefs
        self.forest = None
        self.fontdb = QtGui.QFontDatabase()
        self.color_manager = PaletteManager()
        self.settings_manager = Settings()
        self.forest_keepers = []
        self.forest_keeper = None
        ctrl.late_init(self)
        # capture_stdout(log, self.log_stdout_as_debug, ctrl)

        classes.late_init()
        prefs.import_node_classes(classes)
        self.syntax = SyntaxConnection()
        prefs.load_preferences(disable=reset_prefs or no_prefs)
        qt_prefs.late_init(running_environment, prefs, self.fontdb, log)
        self.settings_manager.set_prefs(prefs)
        self.color_manager.update_custom_colors()
        self.find_plugins(prefs.plugins_path or running_environment.plugins_path)
        self.setWindowIcon(qt_prefs.kataja_icon)
        self.graph_scene = GraphScene(main=self, graph_view=None)
        self.graph_view = GraphView(main=self, graph_scene=self.graph_scene)
        self.graph_scene.graph_view = self.graph_view
        self.ui_manager = UIManager(self)
        self.settings_manager.set_ui_manager(self.ui_manager)
        self.ui_manager.populate_ui_elements()
        # make empty forest and forest keeper so initialisations don't fail because of their absence
        self.visualizations = VISUALIZATIONS
        self.init_forest_keepers()
        self.settings_manager.set_document(self.forest_keeper)
        kataja_app.setPalette(self.color_manager.get_qt_palette())
        self.forest = Forest()
        self.settings_manager.set_forest(self.forest)
        self.change_color_theme(prefs.color_theme, force=True)
        self.update_style_sheet()
        self.graph_scene.late_init()
        self.setCentralWidget(self.graph_view)
        self.setGeometry(x, y, w, h)
        self.setWindowTitle(self.tr("Kataja"))
        self.print_started = False
        self.show()
        self.raise_()
        kataja_app.processEvents()
        self.activateWindow()
        # self.status_bar = self.statusBar()
        self.install_plugins()
        self.load_initial_treeset()
        log.info('Welcome to Kataja! (h) for help')
        # ctrl.call_watchers(self.forest_keeper, 'forest_changed')
        # toolbar = QtWidgets.QToolBar()
        # toolbar.setFixedSize(480, 40)
        # self.addToolBar(toolbar)
        gestures = [QtCore.Qt.TapGesture, QtCore.Qt.TapAndHoldGesture, QtCore.Qt.PanGesture,
                    QtCore.Qt.PinchGesture, QtCore.Qt.SwipeGesture, QtCore.Qt.CustomGesture]
        # for gesture in gestures:
        #    self.grabGesture(gesture)
        self.action_finished(undoable=False, play=True)
        self.forest.undo_manager.flush_pile()

    def update_style_sheet(self):
        c = ctrl.cm.drawing()
        ui = ctrl.cm.ui()
        f = qt_prefs.get_font(g.UI_FONT)
        fm = qt_prefs.get_font(g.MAIN_FONT)
        self.setStyleSheet(stylesheet % {
            'draw': c.name(),
            'lighter': c.lighter().name(),
            'paper': ctrl.cm.paper().name(),
            'ui': ui.name(),
            'ui_lighter': ui.lighter().name(),
            'ui_font': f.family(),
            'ui_font_size': f.pointSize(),
            'ui_font_larger': int(f.pointSize() * 1.2),
            'ui_darker': ui.darker().name(),
            'main_font': fm.family(),
            'main_font_size': fm.pointSize()
        })

    def leaveEvent(self, event):
        ctrl.ui.force_hide_help()

    def find_plugins(self, plugins_path):
        """ Find the plugins dir for the running configuration and read the metadata of plugins.
        Don't try to load actual python code yet
        :return: None
        """
        if not plugins_path:
            return
        self.available_plugins = {}
        plugins_path = os.path.normpath(plugins_path)
        os.makedirs(plugins_path, exist_ok=True)
        sys.path.append(plugins_path)
        base_ends = len(plugins_path.split('/'))
        for root, dirs, files in os.walk(plugins_path):
            path_parts = root.split('/')
            if len(path_parts) == base_ends + 1 and not path_parts[base_ends].startswith(
                    '__') and 'plugin.json' in files:
                success = False
                try:
                    plugin_file = open(root + '/plugin.json', 'r')
                    data = json.load(plugin_file)
                    plugin_file.close()
                    success = True
                except:
                    log.error(sys.exc_info())
                    print(sys.exc_info())
                if success:
                    mod_name = path_parts[base_ends]
                    data['module_name'] = mod_name
                    data['module_path'] = root
                    self.available_plugins[mod_name] = data

    def enable_plugin(self, plugin_key, reload=False):
        """ Start one plugin: save data, replace required classes with plugin classes, load data.

        """
        self.active_plugin_setup = self.load_plugin(plugin_key)
        if not self.active_plugin_setup:
            return
        self.clear_all()
        ctrl.disable_undo()
        if reload:
            available = []
            for key in sys.modules:
                if key.startswith(plugin_key):
                    available.append(key)
            if getattr(self.active_plugin_setup, 'reload_order', None):
                to_reload = [x for x in self.active_plugin_setup.reload_order if x in available]
            else:
                to_reload = sorted(available)
            for mod_name in to_reload:
                importlib.reload(sys.modules[mod_name])
                log.info('reloaded module %s' % mod_name)

        if hasattr(self.active_plugin_setup, 'plugin_parts'):
            for classobj in self.active_plugin_setup.plugin_parts:
                base_class = classes.find_base_model(classobj)
                if base_class:
                    classes.add_mapping(base_class, classobj)
                    m = "replacing %s with %s " % (base_class.__name__, classobj.__name__)
                else:
                    m = "adding %s " % classobj.__name__
                log.info(m)
        if hasattr(self.active_plugin_setup, 'help_file'):
            dir_path = os.path.dirname(os.path.realpath(self.active_plugin_setup.__file__))
            print(dir_path)
            self.ui_manager.set_help_source(dir_path, self.active_plugin_setup.help_file)
        if hasattr(self.active_plugin_setup, 'start_plugin'):
            self.active_plugin_setup.start_plugin(self, ctrl, prefs)
        self.init_forest_keepers()
        ctrl.resume_undo()
        prefs.active_plugin_name = plugin_key

    def disable_current_plugin(self):
        """ Disable the current plugin and load the default trees instead.
        :param clear: if True, have empty treeset, if False, try to load default kataja treeset."""
        if not self.active_plugin_setup:
            return
        ctrl.disable_undo()
        if hasattr(self.active_plugin_setup, 'tear_down_plugin'):
            self.active_plugin_setup.tear_down_plugin(self, ctrl, prefs)
        self.clear_all()
        # print(classes.base_name_to_plugin_class)
        # if hasattr(self.active_plugin_setup, 'plugin_parts'):
        #     for classobj in self.active_plugin_setup.plugin_parts:
        #         class_name = classobj.__name__
        #         if class_name:
        #             log.info(f'removing {class_name}')
        #             print(f'removing {class_name}')
        #             classes.remove_class(class_name)
        classes.restore_default_classes()
        self.init_forest_keepers()
        ctrl.resume_undo()
        prefs.active_plugin_name = ''

    def load_plugin(self, plugin_module):
        setup = None
        importlib.invalidate_caches()
        if plugin_module in self.available_plugins:
            retry = True
            while retry:
                try:
                    setup = importlib.import_module(plugin_module + ".setup")
                    retry = False
                except:
                    e = sys.exc_info()
                    error_dialog = ErrorDialog(self)
                    error_dialog.set_error('%s, line %s\n%s: %s' % (
                        plugin_module + ".setup.py", e[2].tb_lineno, e[0].__name__, e[1]))
                    error_dialog.set_traceback(traceback.format_exc())
                    retry = error_dialog.exec_()
                    setup = None
        return setup

    def install_plugins(self):
        """ If there are plugins defined in preferences to be used, activate them now.
        :return: None
        """
        if prefs.active_plugin_name:
            log.info('Installing plugin %s...' % prefs.active_plugin_name)
            self.enable_plugin(prefs.active_plugin_name, reload=False)
        self.ui_manager.update_plugin_menu()

    def reset_preferences(self):
        """

        :return:
        """
        prefs.restore_default_preferences(qt_prefs, running_environment, classes, log)
        ctrl.call_watchers(self, 'color_themes_changed')
        if self.ui_manager.preferences_dialog:
            self.ui_manager.preferences_dialog.close()
        self.ui_manager.preferences_dialog = PreferencesDialog(self)
        self.ui_manager.preferences_dialog.open()
        self.ui_manager.preferences_dialog.trigger_all_updates()

    def init_forest_keepers(self):
        """ Put empty forest keepers (Kataja documents) in place -- you want to do this after
        plugins have changed the classes that implement these.
        :return:
        """
        self.forest_keepers = [classes.get('KatajaDocument')()]
        self.forest_keeper = self.forest_keepers[0]
        ctrl.call_watchers(self.forest_keeper, 'document_changed')

    def load_initial_treeset(self):
        """ Loads and initializes a new set of trees. Has to be done before
        the program can do anything sane.
        """

        self.forest_keeper.create_forests(clear=False)
        self.change_forest()
        self.ui_manager.update_projects_menu()

    def create_new_project(self):
        names = [fk.name for fk in self.forest_keepers]
        name_base = 'New project'
        name = 'New project'
        c = 1
        while name in names:
            name = '%s %s' % (name_base, c)
            c += 1
        self.forest.retire_from_drawing()
        self.forest_keepers.append(classes.KatajaDocument(name=name))
        self.forest_keeper = self.forest_keepers[-1]
        ctrl.call_watchers(self.forest_keeper, 'document_changed')
        self.change_forest()
        self.ui_manager.update_projects_menu()
        return self.forest_keeper

    def switch_project(self, i):
        self.forest.retire_from_drawing()
        self.forest_keeper = self.forest_keepers[i]
        ctrl.call_watchers(self.forest_keeper, 'document_changed')
        self.change_forest()
        self.ui_manager.update_projects_menu()
        return self.forest_keeper

    # ### Visualization
    # #############################################################

    def change_forest(self):
        """ Tells the scene to remove current trees and related data and
        change it to a new one. Signal 'forest_changed' is already sent by forest keeper.
        """
        ctrl.disable_undo()
        if self.forest:
            self.forest.retire_from_drawing()
        if not self.forest_keeper.forest:
            self.forest_keeper.create_forests(clear=True)
        self.forest = self.forest_keeper.forest
        self.settings_manager.set_forest(self.forest)
        if self.forest.is_parsed:
            if self.forest.derivation_steps:
                ds = self.forest.derivation_steps
                if not ds.activated:
                    print('jumping to derivation step: ', ds.derivation_step_index)
                    ds.jump_to_derivation_step(ds.derivation_step_index)
            else:
                print('no derivation steps')
        self.forest.prepare_for_drawing()
        ctrl.resume_undo()
        # if self.forest.undo_manager.

    def redraw(self):
        """ Call for forest redraw
        :return: None
        """
        self.forest.draw()

    def log_stdout_as_debug(self, text):
        if text.strip():
            log.debug(text)

    def attach_widget_to_log_handler(self, browserwidget):
        """ This has to be done once: we have a logger set up before there is any output widget,
        once the widget is created it is connected to logger.
        :param browserwidget:
        :return:
        """
        self.app.log_handler.set_widget(browserwidget)

        #    def mousePressEvent(self, event):

    #        """ KatajaMain doesn't do anything with mousePressEvents, it delegates
    #        :param event:
    #        them downwards. This is for debugging. """
    #        QtWidgets.QMainWindow.mousePressEvent(self, event)

    #    def keyPressEvent(self, event):
    #        # if not self.key_manager.receive_key_press(event):
    #        """
    #
    #        :param event:
    #        :return:
    #        """
    #        return QtWidgets.QMainWindow.keyPressEvent(self, event)

    # ## Menu management #######################################################

    def action_finished(self, m='', undoable=True, error=None, play=False):
        """ Write action to undo stack, report back to user and redraw trees
        if necessary
        :param m: message for undo
        :param undoable: are we supposed to take a snapshot of changes after
        this action.
        :param error message
        """
        if error:
            log.error(error)
        elif m:
            log.info(m)
        if ctrl.action_redraw:
            ctrl.forest.draw()
        if undoable and not error:
            ctrl.forest.undo_manager.take_snapshot(m)
        if play:
            ctrl.graph_scene.start_animations()
        ctrl.ui.update_actions()

    def trigger_action(self, name, *args, **kwargs):
        """ Helper for programmatically triggering actions (for tests and plugins)
        :param name: action name
        :param kwargs: keyword parameters
        :return:
        """
        action = self.ui_manager.actions[name]
        action.run_command(*args, **kwargs)

    def trigger_but_suppress_undo(self, name, *args, **kwargs):
        """ Helper for programmatically triggering actions (for tests and plugins)
        :param name: action name
        :param kwargs: keyword parameters
        :return:
        """
        action = self.ui_manager.actions[name]
        action.trigger_but_suppress_undo(*args, **kwargs)

    def enable_actions(self):
        """ Restores menus """
        for action in self.ui_manager.actions.values():
            action.setDisabled(False)

    def disable_actions(self):
        """ Actions shouldn't be initiated when there is other multi-phase
        action going on """
        for action in self.ui_manager.actions.values():
            action.setDisabled(True)

    def change_color_theme(self, mode, force=False):
        """
        triggered by color mode selector in colors panel

        :param mode:
        """
        if mode != ctrl.settings.get('color_theme') or force:
            if ctrl.settings.document:
                ctrl.settings.set('color_theme', mode, level=g.DOCUMENT)
            ctrl.settings.set('color_theme', mode, level=g.PREFS)
            self.update_colors()

    def timerEvent(self, event):
        """ Timer event only for printing, for 'snapshot' effect
        :param event:
        """

        def find_path(fixed_part, extension, counter=0):
            """ Generate file names until free one is found
            :param fixed_part: blah
            :param extension: blah
            :param counter: blah
            """
            if not counter:
                fpath = fixed_part + extension
            else:
                fpath = fixed_part + str(counter) + extension
            if os.path.exists(fpath):
                fpath = find_path(fixed_part, extension, counter + 1)
            return fpath

        if not self.print_started:
            return
        else:
            self.print_started = False
        self.killTimer(event.timerId())
        # Prepare file and path
        path = prefs.print_file_path or prefs.userspace_path or \
               running_environment.default_userspace_path
        if not path.endswith('/'):
            path += '/'
        if not os.path.exists(path):
            print("bad path for printing (print_file_path in preferences) , "
                  "using '.' instead.")
            path = './'
        filename = prefs.print_file_name
        if filename.endswith(('.pdf', '.png')):
            filename = filename[:-4]
        # Prepare image
        self.graph_scene.removeItem(self.graph_scene.photo_frame)
        self.graph_scene.photo_frame = None
        # Prepare printer
        png = prefs.print_format == 'png'
        source = self.graph_scene.print_rect()

        for node in ctrl.forest.nodes.values():
            node.setCacheMode(QtWidgets.QGraphicsItem.NoCache)

        if png:
            full_path = find_path(path + filename, '.png', 0)
            scale = 4
            target = QtCore.QRectF(QtCore.QPointF(0, 0), source.size() * scale)
            writer = QtGui.QImage(target.size().toSize(), QtGui.QImage.Format_ARGB32_Premultiplied)
            writer.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter()
            painter.begin(writer)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)

            self.graph_scene.render(painter, target=target, source=source)
            painter.end()
            iwriter = QtGui.QImageWriter(full_path)
            iwriter.write(writer)
            log.info("printed to %s as PNG (%spx x %spx, %sx size)." % (
                full_path, int(target.width()), int(target.height()), scale))

        else:
            dpi = 25.4
            full_path = find_path(path + filename, '.pdf', 0)
            target = QtCore.QRectF(0, 0, source.width() / 2.0, source.height() / 2.0)

            writer = QtGui.QPdfWriter(full_path)
            writer.setResolution(dpi)
            writer.setPageSizeMM(target.size())
            writer.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))
            ctrl.printing = True
            painter = QtGui.QPainter()
            painter.begin(writer)
            # painter.setRenderHint(QtGui.QPainter.Antialiasing)
            # painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
            self.graph_scene.render(painter, target=target, source=source)
            painter.end()
            ctrl.printing = False
            log.info("printed to %s as PDF with %s dpi." % (full_path, dpi))

        # Thank you!
        # Restore image
        self.graph_scene.setBackgroundBrush(self.color_manager.gradient)

    # Not called from anywhere yet, but useful
    def release_selected(self, **kw):
        """

        :param kw:
        :return:
        """
        for node in ctrl.get_selected_nodes():
            node.release()
        self.action_finished()
        return True

    def clear_all(self):
        """ Empty everything - maybe necessary before loading new data. """
        if self.forest:
            self.forest.retire_from_drawing()
        self.forest_keeper = None
        # Garbage collection doesn't mix well with animations that are still running
        # print('garbage stats:', gc.get_count())
        # gc.collect()
        # print('after collection:', gc.get_count())
        # if gc.garbage:
        #    print('garbage:', gc.garbage)
        self.forest_keepers.append(classes.KatajaDocument(clear=True))
        self.forest_keeper = self.forest_keepers[-1]
        self.settings_manager.set_document(self.forest_keeper)
        self.forest = None

    # ## Other window events
    ###################################################

    def closeEvent(self, event):
        """ Shut down the program, give some debug info
        :param event:
        """
        QtWidgets.QMainWindow.closeEvent(self, event)
        if ctrl.print_garbage:
            # import objgraph
            log.debug('garbage stats: ' + str(gc.get_count()))
            gc.collect()
            log.debug('after collection: ' + str(gc.get_count()))
            if gc.garbage:
                log.debug('garbage: ' + str(gc.garbage))

                # objgraph.show_most_common_types(limit =40)
        if self.save_prefs:
            prefs.save_preferences()
        log.info('...done')

    def create_save_data(self):
        """
        Make a large dictionary of all objects with all of the complex stuff
        and circular references stripped out.
        :return: dict
        """
        savedata = {}
        open_references = {}
        savedata['save_scheme_version'] = 0.4
        self.save_object(savedata, open_references)
        max_rounds = 10
        c = 0
        while open_references and c < max_rounds:
            c += 1
            # print(len(savedata))
            # print('---------------------------')
            for obj in list(open_references.values()):
                if hasattr(obj, 'uid'):
                    obj.save_object(savedata, open_references)
                else:
                    print('cannot save open reference object ', obj)
        assert (c < max_rounds)
        print('total savedata: %s chars in %s items.' % (len(str(savedata)), len(savedata)))
        # print(savedata)
        return savedata

    def update_colors(self, randomise=False, animate=True):
        """ This is the master palette change.
        Its effects should propagate to all objects in scene and ui, either through updated
        style sheets, paletteChanged -events or 'palette_changed' -watchers.
        :param randomise:
        :param animate:
        :return:
        """
        cm = self.color_manager
        old_gradient_base = cm.paper()
        cm.update_colors(randomise=randomise)
        self.app.setPalette(cm.get_qt_palette())
        self.update_style_sheet()
        ctrl.call_watchers(self, 'palette_changed')
        if cm.gradient:
            if old_gradient_base != cm.paper() and animate:
                self.graph_scene.fade_background_gradient(old_gradient_base, cm.paper())
            else:
                self.graph_scene.setBackgroundBrush(cm.gradient)
        else:
            self.graph_scene.setBackgroundBrush(qt_prefs.no_brush)
        self.update()

    ### Applying specific preferences globally.
    # These are on_change -methods for various preferences -- these are called if changing a
    # preference should have immediate consequences. They are hosted here because they need to
    # have access to prefs, qt_prefs, main etc.

    def prepare_easing_curve(self):
        qt_prefs.prepare_easing_curve(prefs.curve, prefs.move_frames)

    def update_color_theme(self):
        self.change_color_theme(prefs.color_theme, force=True)

    def update_visualization(self):
        ctrl.forest.set_visualization(prefs.visualization)
        self.redraw()

    def resize_ui_font(self):
        qt_prefs.toggle_large_ui_font(prefs.large_ui_text, prefs.fonts)
        self.update_style_sheet()

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        pass

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    forest_keeper = SavedField("forest_keeper")
    forest = SavedField("forest")
