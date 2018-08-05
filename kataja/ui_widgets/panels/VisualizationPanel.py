from PyQt5 import QtWidgets, QtCore

from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel
from kataja.visualizations.available import VISUALIZATIONS
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_support.panel_utils import box_row

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
        inner = self.widget()
        inner.preferred_size = QtCore.QSize(200, 70)
        inner.setMaximumWidth(220)
        inner.setMaximumHeight(80)
        inner.sizeHint = self.sizeHint
        inner.setAutoFillBackground(True)
        self.preferred_size = inner.preferred_size
        layout = self.vlayout
        hlayout = box_row(layout)

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

        ctrl.main.visualisation_changed.connect(self.update_visualisation)
        self.finish_init()

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        # ??
        super().showEvent(event)

    def update_visualisation(self):
        if not (ctrl.main.document and ctrl.forest):
            return
        data = ctrl.forest.vis_data
        if data and 'name' in data:
            index = list(VISUALIZATIONS.keys()).index(data['name'])
            self.selector.setCurrentIndex(index)

    def sizeHint(self):
        #print("VisualizationPanel asking for sizeHint, ", self.preferred_size)
        return self.preferred_size