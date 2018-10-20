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

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

import kataja.globals as g
from kataja.GraphScene import GraphScene
from kataja.GraphView import GraphView
from kataja.PaletteManager import PaletteManager
from kataja.ViewManager import ViewManager
from kataja.UIManager import UIManager
from kataja.singletons import ctrl, prefs, qt_prefs, running_environment, classes, log
from kataja.ui_support.ErrorDialog import ErrorDialog
from kataja.ui_support.PreferencesDialog import PreferencesDialog
from kataja.Recorder import Recorder
from kataja.utils import find_free_filename, quit
from kataja.visualizations.available import VISUALIZATIONS

# only for debugging (Apple-m, memory check), can be commented
# try:
# import objgraph
# except ImportError:
# objgraph = None


stylesheet = """
.QWidget, .SelectionBox, .QComboBox, QLabel, QAbstractButton, QAbstractSpinBox, QDialog, QFrame,
QMainWindow, QDialog, QDockWidget {font-family: "%(ui_font)s"; font-size: %(ui_font_size)spx;}
QComboBox QAbstractItemView {selection-color: %(ui)s;}
KatajaTextarea {font-family: "%(console_font)s"; font-size: %(console_font_size)spx;}
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
HeadingWidget QLabel {font-family: "%(main_font)s"; 
               font-size: %(heading_font_size)spx;}
"""
# EyeButton {border: 1px solid %(ui_darker)s;}
# EyeButton:checked {border: 1px solid %(ui)s; border-radius: 3}


# ProjectionButtons QPushButton:checked {border: 2px solid %(ui)s; border-radius: 3}


class KatajaMain(QtWidgets.QMainWindow):
    """ Qt's main window. When this is closed, application closes. Graphics are
    inside this, in scene objects with view widgets. This window also manages
    keypresses and menus. """

    active_edge_color_changed = QtCore.pyqtSignal()
    color_themes_changed = QtCore.pyqtSignal()
    document_changed = QtCore.pyqtSignal()
    forest_changed = QtCore.pyqtSignal()
    palette_changed = QtCore.pyqtSignal()
    scope_changed = QtCore.pyqtSignal()
    selection_changed = QtCore.pyqtSignal()
    ui_font_changed = QtCore.pyqtSignal()
    viewport_moved = QtCore.pyqtSignal()
    viewport_resized = QtCore.pyqtSignal()
    visualisation_changed = QtCore.pyqtSignal()

    def __init__(self, kataja_app, tree='', plugin='FreeDrawing', image_out='', no_prefs=False, reset_prefs=False):
        """ KatajaMain initializes all its children and connects itself to
        be the main window of the given application. Receives launch arguments:
        :param no_prefs: bool, don't load or save preferences
        :param reset_prefs: bool, don't attempt to load preferences, use defaults instead

        """
        QtWidgets.QMainWindow.__init__(self)
        silent = bool(image_out)
        self.init_done = False
        self._stored_init_state = True
        self.disable_signaling()
        kataja_app.processEvents()

        self.use_tooltips = True
        self.available_plugins = {}
        self.active_plugin_setup = {}
        self.active_plugin_path = ''
        self.setWindowTitle("Kataja")
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
        self.fontdb = QtGui.QFontDatabase()
        self.color_manager = PaletteManager(self)
        self.document = None
        ctrl.late_init(self)  # sets ctrl.main
        #capture_stdout(log, self.log_stdout_as_debug, ctrl)
        classes.late_init()  # make all default classes available
        prefs.import_node_classes(classes)  # add node styles defined at class to prefs
        prefs.load_preferences(disable=reset_prefs or no_prefs)
        qt_prefs.late_init(running_environment, prefs, self.fontdb, log)
        self.find_plugins(prefs.plugins_path or running_environment.plugins_path)
        self.setWindowIcon(qt_prefs.kataja_icon)
        self.view_manager = ViewManager()
        self.graph_scene = GraphScene()
        self.recorder = Recorder(self.graph_scene)
        self.graph_view = GraphView(self.graph_scene)
        self.view_manager.late_init(self.graph_scene, self.graph_view)
        self.ui_manager = UIManager(self)
        if not silent:
            self.ui_manager.populate_ui_elements()
        # make empty forest and forest keeper so initialisations don't fail because of their absence
        self.visualizations = VISUALIZATIONS
        self.create_default_document()
        self.color_manager.update_custom_colors()
        kataja_app.setPalette(self.color_manager.get_qt_palette())
        self.change_color_theme(prefs.color_theme, force=True)
        self.update_style_sheet()
        self.graph_scene.late_init()
        self.print_started = False
        if not silent:
            self.setCentralWidget(self.graph_view)
            self.setGeometry(x, y, w, h)
            self.show()
            self.raise_()
            kataja_app.processEvents()
            self.activateWindow()
        # self.status_bar = self.statusBar()
        self.install_plugins(activate=plugin)
        self.document.load_default_forests(tree=tree)
        self.document.play = not silent
        if not silent:
            self.enable_signaling()

            self.viewport_resized.emit()
            self.forest_changed.emit()
            self.action_finished(undoable=False, play=True)
            if self.forest:
                self.forest.undo_manager.flush_pile()
        else:
            self.action_finished(undoable=False, play=False)
        # toolbar = QtWidgets.QToolBar()
        # toolbar.setFixedSize(480, 40)
        # self.addToolBar(toolbar)
        #gestures = [QtCore.Qt.TapGesture, QtCore.Qt.TapAndHoldGesture, QtCore.Qt.PanGesture,
        #            QtCore.Qt.PinchGesture, QtCore.Qt.SwipeGesture, QtCore.Qt.CustomGesture]
        # for gesture in gestures:
        #    self.grabGesture(gesture)

        if image_out:
            self.print_to_file(running_environment.default_userspace_path, image_out)
            quit()


    @property
    def forest(self):
        return self.document.forest

    def update_style_sheet(self):
        c = ctrl.cm.drawing()
        ui = ctrl.cm.ui()
        f = qt_prefs.get_font(g.UI_FONT)
        fm = qt_prefs.get_font(g.MAIN_FONT)
        fc = qt_prefs.get_font(g.CONSOLE_FONT)
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
            'main_font_size': fm.pointSize(),
            'heading_font_size': fm.pointSize() * 2,
            'console_font': fc.family(),
            'console_font_size': fc.pointSize(),
        })

    def leaveEvent(self, event):
        ctrl.ui.force_hide_help()

    def disable_signaling(self):
        # shut down side effects
        self._stored_init_state = self.init_done
        self.init_done = False
        ctrl.disable_undo()
        self.blockSignals(True)
        # ----------------------

    def enable_signaling(self):
        # resume with side effects
        self.blockSignals(False)
        ctrl.resume_undo()
        self.init_done = self._stored_init_state
        # ----------------------

    # Plugins ################################

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
        base_ends = len(plugins_path.split(os.sep))
        for root, dirs, files in os.walk(plugins_path, followlinks=True):
            path_parts = root.split(os.sep)
            if len(path_parts) == base_ends + 1 and not path_parts[base_ends].startswith(
                    '__') and 'plugin.json' in files:
                success = False
                try:
                    plugin_file = open(os.path.join(root, 'plugin.json'), 'r')
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

    def set_active_plugin(self, plugin_key, enable):
        if enable:
            if prefs.active_plugin_name:
                self.disable_current_plugin()
            self.enable_plugin(plugin_key)
            self.document.load_default_forests()
            return "Enabled plugin '%s'" % plugin_key
        elif plugin_key == prefs.active_plugin_name:
            self.disable_current_plugin()
            self.document.load_default_forests()
            return "Disabled plugin '%s'" % plugin_key
        return ""

    def enable_plugin(self, plugin_key, reload=False):
        """ Start one plugin: save data, replace required classes with plugin classes, load data.

        """
        self.active_plugin_setup = self.load_plugin(plugin_key)
        if not self.active_plugin_setup:
            return

        self.disable_signaling()

        self.clear_document()

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

        if hasattr(self.active_plugin_setup, 'plugin_classes'):
            for classobj in self.active_plugin_setup.plugin_classes:
                base_class = classes.find_base_model(classobj)
                if base_class:
                    classes.add_mapping(base_class, classobj)
                    m = "replacing %s with %s " % (base_class.__name__, classobj.__name__)
                else:
                    m = "adding %s " % classobj.__name__
                log.info(m)
        actions_module = getattr(self.active_plugin_setup, 'plugin_actions', None)
        if actions_module:
            classes.replaced_actions = {}
            classes.added_actions = []
            ctrl.ui.load_actions_from_module(actions_module,
                                             added=classes.added_actions,
                                             replaced=classes.replaced_actions)
        dir_path = os.path.dirname(os.path.realpath(self.active_plugin_setup.__file__))
        if hasattr(self.active_plugin_setup, 'help_file'):

            self.ui_manager.set_help_source(dir_path, self.active_plugin_setup.help_file)
        if hasattr(self.active_plugin_setup, 'start_plugin'):
            self.active_plugin_setup.start_plugin(self, ctrl, prefs)
        self.create_default_document()
        self.enable_signaling()
        self.active_plugin_path = dir_path
        prefs.active_plugin_name = plugin_key

    def disable_current_plugin(self):
        """ Disable the current plugin and load the default trees instead.
        :param clear: if True, have empty treeset, if False, try to load default kataja treeset."""
        if not self.active_plugin_setup:
            print('bailing out disable plugin: no active plugin recognised')
            return

        self.disable_signaling()

        if hasattr(self.active_plugin_setup, 'tear_down_plugin'):
            self.active_plugin_setup.tear_down_plugin(self, ctrl, prefs)
        self.clear_document()
        ctrl.ui.unload_actions_from_module(classes.added_actions, classes.replaced_actions)
        classes.added_actions = []
        classes.replaced_actions = {}
        classes.restore_default_classes()
        self.create_default_document()
        self.enable_signaling()

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

    def install_plugins(self, activate=''):
        """ If there are plugins defined in preferences to be used, activate them now.
        :return: None
        """
        plugin = activate or prefs.active_plugin_name
        if plugin:
            log.info('Installing plugin %s...' % plugin)
            self.enable_plugin(plugin, reload=False)
        self.ui_manager.update_plugin_menu()

    # Preferences ###################################

    def reset_preferences(self):
        """

        :return:
        """
        prefs.restore_default_preferences(qt_prefs, running_environment, classes, log)
        self.color_themes_changed.emit()
        if self.ui_manager.preferences_dialog:
            self.ui_manager.preferences_dialog.close()
        self.ui_manager.preferences_dialog = PreferencesDialog(self)
        self.ui_manager.preferences_dialog.open()
        self.ui_manager.preferences_dialog.trigger_all_updates()

    # Document / Project #########################

    def start_new_document(self, name='Example'):
        document = classes.KatajaDocument(name=name)
        self.set_document(document)
        return document

    def set_document(self, document):
        if document is not self.document:
            if self.document:
                self.document.retire_from_display()
            self.document = document
            self.document_changed.emit()
            if document:
                document.update_forest()
                plug = f'{prefs.active_plugin_name} — ' if prefs.active_plugin_name else ''
                self.setWindowTitle(f'Kataja — {plug}{document.name}')

    def create_default_document(self):
        """ Put empty Kataja document in place -- you want to do this after
        plugins have changed the classes that implement these.
        :return:
        """
        self.start_new_document()

    def clear_document(self):
        """ Empty everything - maybe necessary before changing plugin """
        self.set_document(None)

    # ### Visualization
    # #############################################################

    def redraw(self):
        """ Call for forest redraw
        :return: None
        """
        if self.forest and self.forest.in_display:
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

    # ## Actions #######################################################

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
        if self.forest:
            if ctrl.action_redraw:
                self.forest.draw()
            if undoable and not error:
                self.forest.undo_manager.take_snapshot(m)
        if play:
            self.graph_scene.start_animations()
        ctrl.ui.update_actions()

    def trigger_action(self, name, *args, **kwargs):
        """ Helper for programmatically triggering actions (for tests and plugins)
        :param name: action name
        :param kwargs: keyword parameters
        :return:
        """
        if self.init_done:
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

    # Color theme #################################

    def change_color_theme(self, mode, force=False):
        """
        triggered by color mode selector in colors panel

        :param mode:
        """
        if self.document:
            if mode != self.document.settings.get('color_theme') or force:
                self.document.settings.set('color_theme', mode)
                self.update_colors()

    # Printing ###################################

    def timerEvent(self, event):
        """ Timer event only for printing, for 'snapshot' effect
        :param event:
        """
        if not self.print_started:
            return
        else:
            self.print_started = False
        self.killTimer(event.timerId())
        # Prepare file and path
        path = prefs.userspace_path or running_environment.default_userspace_path
        if not os.path.exists(path):
            print("bad path for printing (userspace_path in preferences) , "
                  "using '.' instead.")
            path = '.'
        # Prepare image
        self.graph_scene.removeItem(self.graph_scene.photo_frame)
        self.graph_scene.photo_frame = None
        self.print_to_file(path, prefs.print_file_name)

    def print_to_file(self, path, filename):
        if filename.endswith(('.pdf', '.png')):
            filename = filename[:-4]
        # Prepare printer
        png = prefs.print_format == 'png'
        source = self.view_manager.print_rect()

        for node in self.forest.nodes.values():
            node.setCacheMode(QtWidgets.QGraphicsItem.NoCache)

        if png:
            self._write_png(source, path, filename)
        else:
            self._write_pdf(source, path, filename)

        # Restore image
        for node in self.forest.nodes.values():
            node.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
        self.graph_scene.setBackgroundBrush(self.color_manager.gradient)

    def _write_png(self, source, path, filename):
        full_path = find_free_filename(os.path.join(path, filename), '.png', 0)
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
        msg = f"printed to {full_path} as PNG ({int(target.width())}px x {int(target.height())}px, {scale}x size)."
        print(msg)
        log.info(msg)

    def _write_pdf(self, source, path, filename):
        dpi = 25.4
        full_path = find_free_filename(os.path.join(path, filename), '.pdf', 0)
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
        msg = f"printed to {full_path} as PDF with {dpi} dpi."
        print(msg)
        log.info(msg)

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

    def update_colors(self, randomise=False, animate=True):
        """ This is the master palette change.
        Its effects should propagate to all objects in scene and ui, either through updated
        style sheets, paletteChanged -events or 'palette_changed' -signals.
        :param randomise:
        :param animate:
        :return:
        """
        cm = self.color_manager
        old_gradient_base = cm.paper()
        cm.update_colors(randomise=randomise)
        self.app.setPalette(cm.get_qt_palette())
        self.update_style_sheet()
        ctrl.main.palette_changed.emit()
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
        self.forest.set_visualization(prefs.visualization)
        self.redraw()

    def resize_ui_font(self):
        qt_prefs.toggle_large_ui_font(prefs.large_ui_text, prefs.fonts)
        self.update_style_sheet()
