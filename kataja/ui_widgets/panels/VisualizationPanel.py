from PyQt5 import QtWidgets, QtCore

from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel
from kataja.visualizations.available import VISUALIZATIONS
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.buttons.PanelButton import PanelButton

__author__ = 'purma'


class VisualizationPanel(Panel):
    """ Switch visualizations and adjust their settings """


    def __init__(self, name, default_position='right', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        inner = QtWidgets.QWidget()
        inner.preferred_size = QtCore.QSize(200, 70)
        inner.setMaximumWidth(220)
        inner.setMaximumHeight(80)
        inner.sizeHint = self.sizeHint

        layout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()

        self.selector = SelectionBox(self, action='set_visualization').to_layout(hlayout)
        self.selector.add_items([(key, '%s (%s)' % (key, item.shortcut)) for key, item in
                                 VISUALIZATIONS.items()])

        self.toggle_options = PanelButton(pixmap=qt_prefs.settings_pixmap,
                                          action='toggle_panel',
                                          parent=self,
                                          size=20).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.toggle_options.setFixedSize(26, 26)
        self.toggle_options.setCheckable(True)
        self.toggle_options.data = 'VisualizationOptionsPanel'

        layout.addLayout(hlayout)

        #layout.setContentsMargins(0, 0, 0, 0)
        inner.setLayout(layout)
        self.watchlist = ['visualization']
        self.preferred_size = inner.preferred_size
        self.setWidget(inner)
        inner.setAutoFillBackground(True)
        self.finish_init()

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        # ??
        super().showEvent(event)

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
        if signal == 'visualization':
            if value and 'name' in value:
                index = list(VISUALIZATIONS.keys()).index(value['name'])
                self.selector.setCurrentIndex(index)

    def sizeHint(self):
        #print("VisualizationPanel asking for sizeHint, ", self.preferred_size)
        return self.preferred_size