from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs, prefs, classes
from kataja.ui_support.panel_utils import box_row, icon_button, shape_selector, selector, \
    mini_button
from kataja.ui_widgets.OverlayButton import PanelButton
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.DraggableNodeFrame import DraggableNodeFrame
import importlib

__author__ = 'purma'




class NodesPanel(Panel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, default_position='right', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded,
                       scope_action='style_scope')
        outer = QtWidgets.QWidget(self)
        olayout = QtWidgets.QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        olayout.setContentsMargins(0, 0, 0, 0)
        outer.setLayout(olayout)
        outer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.watchlist = ['selection_changed', 'forest_changed', 'palette_changed']
        self.setMaximumWidth(220)
        self.sheets = []
        self.frames = []
        for key in classes.node_types_order:
            data = classes.node_info[key]
            if not data['display']:
                continue
            container = QtWidgets.QWidget(self)
            container.setContentsMargins(0, 0, 0, 0)
            clayout = QtWidgets.QVBoxLayout(container)
            clayout.setContentsMargins(0, 0, 0, 0)
            container.setLayout(clayout)
            olayout.addWidget(container)
            frame = DraggableNodeFrame(key, data['name'], parent=container)
            self.frames.append(frame)
            clayout.addWidget(frame)
            sheet_class = data['ui_sheet']
            if sheet_class:
                class_path, class_name = sheet_class
                sheet_module = importlib.import_module(class_path)
                if not sheet_module:
                    print('sheet module not found: ', class_path)
                    continue
                sheet_class = getattr(sheet_module, class_name, None)
                if not sheet_class:
                    print('sheet class not found: ', class_path, class_name)
                    continue
                sheet = sheet_class(parent=container)
                clayout.addWidget(sheet)
                self.sheets.append(sheet)
                frame.sheet = sheet
            frame.set_folded(frame.folded)  # updates sheet visibility

        self.reset_button = mini_button(ctrl.ui, outer, olayout,
                                        text='reset',
                                        action='reset_settings',
                                        align=QtCore.Qt.AlignRight)
        self.reset_button.setMinimumHeight(14)
        self.reset_button.setMaximumHeight(14)

        self.setWidget(outer)
        self.finish_init()

    def get_font_dialog(self, node_type):
        """ If there are font dialogs open, they are attached to font_selectors in node frames.
        Return the one that matches node_type, or None if it is closed.
        :param node_type:
        :return:
        """
        for frame in self.frames:
            if frame.key == node_type and frame.font_selector.font_dialog:
                return frame.font_selector.font_dialog

    def get_frame_for(self, node_type):
        for frame in self.frames:
            if frame.key == node_type:
                return frame

    def get_sheet_for(self, node_type):
        for sheet in self.sheets:
            if sheet.key == node_type:
                return sheet


    def update_selection(self):
        """ Called after ctrl.selection has changed. Prepare panel to use
        selection as scope
        :return:
        """
        #self.frame.update_frame()

    def update_colors(self):
        for frame in self.frames:
            frame.update_colors()

    # @time_me
    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this
        forest """
        pass

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.update_selection()
        super().showEvent(event)

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to
        listen. These signals are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act
         accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        if signal == 'selection_changed':
            self.update_selection()
        elif signal == 'forest_changed':
            self.update_selection()
        elif signal == 'palette_changed':
            self.update_colors()
