from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs, prefs, classes
from kataja.saved.Edge import Edge
from kataja.saved.movables.Node import Node
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.panel_utils import  box_row, font_selector, color_selector, icon_button, \
    shape_selector, selector, mini_button
from kataja.ui_widgets.OverlayButton import PanelButton

__author__ = 'purma'


class ScopePanel(Panel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, default_position='right', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        ui = self.ui_manager
        self.setMaximumWidth(220)
        self.setMaximumHeight(140)
        scopes = []
        widget = QtWidgets.QWidget()
        widget.setBackgroundRole(QtGui.QPalette.AlternateBase)
        layout = QtWidgets.QVBoxLayout()
        #layout.setContentsMargins(4, 0, 4, 4)
        widget.setLayout(layout)
        hlayout = QtWidgets.QHBoxLayout()
        #label = QtWidgets.QLabel('Shape')
        #hlayout.addWidget(label)
        hlayout = box_row(layout)
        hlayout.setContentsMargins(0, 0, 0, 0)

        self.scope_selector = selector(ui, widget, hlayout,
                                       data=[],
                                       action='style_scope',
                                       label='Scope')
        self.scope_selector.setMinimumWidth(96)
        vline = QtWidgets.QFrame()
        vline.setFrameShape(QtWidgets.QFrame.VLine)
        hlayout.addWidget(vline)

        self.style_reset = mini_button(ui, widget, hlayout,
                                       text='reset',
                                       action='reset_style_in_scope')
        self.setWidget(widget)
        self.finish_init()


    def update_selection(self):
        """ Called after ctrl.selection has changed. Prepare panel to use
        selection as scope
        :return:
        """
        self.update_scope_selector_options()

    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this
        forest """
        items = [('This selection', g.SELECTION),
                 ('This forest', g.FOREST),
                 ('This document', g.DOCUMENT),
                 ('Preferences', g.PREFS)]
        self.scope_selector.add_items(items)

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
