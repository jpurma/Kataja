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

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

import kataja.globals as g
from kataja.GraphScene import GraphScene
from kataja.GraphView import GraphView
from kataja.LogWidgetPusher import capture_stdout
from kataja.PaletteManager import PaletteManager
from kataja.PluginManager import PluginManager
from kataja.PrintManager import PrintManager
from kataja.ViewManager import ViewManager
from kataja.UIManager import UIManager
from kataja.singletons import ctrl, prefs, qt_prefs, running_environment, classes, log
from kataja.ui_support.PreferencesDialog import PreferencesDialog
from kataja.Recorder import Recorder
from kataja.utils import quit
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

    def __init__(self, kataja_app, tree='', plugin='', image_out='', no_prefs=False, reset_prefs=False):
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
        self.outgoing = []
        kataja_app.processEvents()

        self.use_tooltips = True
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
        self.plugin_manager = PluginManager()
        self.document = None
        ctrl.late_init(self)  # sets ctrl.main
        capture_stdout(log, self.log_stdout_as_debug, ctrl)
        classes.late_init()  # make all default classes available
        prefs.import_node_classes(classes)  # add node styles defined at class to prefs
        prefs.load_preferences(disable=reset_prefs or no_prefs)
        qt_prefs.late_init(running_environment, prefs, self.fontdb, log)
        self.plugin_manager.find_plugins(prefs.plugins_path or running_environment.plugins_path)
        self.setWindowIcon(qt_prefs.kataja_icon)
        self.print_manager = PrintManager()
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
        if not silent:
            self.setCentralWidget(self.graph_view)
            self.setGeometry(x, y, w, h)
            self.show()
            self.raise_()
            kataja_app.processEvents()
            self.activateWindow()
        if tree:
            plugin = plugin or 'FreeDrawing'
        else:
            plugin = plugin or prefs.active_plugin_name
        self.plugin_manager.enable_plugin(plugin)
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
        #gestures = [QtCore.Qt.TapGesture, QtCore.Qt.TapAndHoldGesture, QtCore.Qt.PanGesture,
        #            QtCore.Qt.PinchGesture, QtCore.Qt.SwipeGesture, QtCore.Qt.CustomGesture]
        # for gesture in gestures:
        #    self.grabGesture(gesture)

        if image_out:
            self.print_manager.print_to_file(running_environment.default_userspace_path, image_out)
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
        self.outgoing.append(text)
        if text.endswith('\n') or text.endswith('\r'):
            log.debug((''.join(self.outgoing)).strip())
            self.outgoing = []

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

    def timerEvent(self, event):
        """ Timer event only for printing, for 'snapshot' effect
        :param event:
        """
        self.print_manager.snapframe_timer(event)

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
