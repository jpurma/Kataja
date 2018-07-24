from kataja.singletons import ctrl
from kataja.ui_widgets.Panel import Panel
from PyQt5 import QtWidgets
from kataja.ui_support.panel_utils import box_row

__author__ = 'purma'


class VisualizationOptionsPanel(Panel):
    """ Panel for editing how visualizations are drawn. """

    def __init__(self, name, default_position='float', parent=None, folded=False):
        """
        BUild all advanced line options. Then in update filter what to show based on the line type.

        All of the panel constructors follow the same format so that the construction can be automated:
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        ctrl.main.view_mode_changed.connect(self.update_panel)
        self.vlayout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                                 QtWidgets.QSizePolicy.MinimumExpanding))
        self.setMaximumWidth(220)
        self.setMaximumHeight(140)

        self.finish_init()

    def finish_init(self):
        """ Do initializations that need to be done after the subclass __init__
        has completed. e.g. hide this from view, which can have odd results
        for measurements for elements and layouts if it is called before
        setting them up. Subclass __init__:s must call finish_init at the end!
        :return:
        """
        Panel.finish_init(self)
        self.update_panel()
        self.show()

    def update_panel(self):
        """ Choose which selectors to show and update their values
        :return: None
        """
        s = ctrl.settings
        self.updateGeometry()
        self.update()

    def initial_position(self, next_to=''):
        """
        :return:
        """
        return Panel.initial_position(self, next_to=next_to or 'VisualizationPanel')

    def close(self):
        """ Raise button in VISUALIZATION panel """
        vp = self.ui_manager.get_panel('VisualizationPanel')
        if vp:
            vp.toggle_options.setChecked(False)
        Panel.close(self)

    def show(self):
        """ Depress button in VISUALIZATION panel """
        vp = self.ui_manager.get_panel('VisualizationPanel')
        if vp:
            vp.toggle_options.setChecked(True)
        Panel.show(self)

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.update_panel()
        super().showEvent(event)

