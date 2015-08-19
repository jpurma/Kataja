from PyQt5 import QtWidgets, QtCore

from kataja.Edge import Edge
from kataja.singletons import ctrl
import kataja.globals as g
from kataja.ui.panels.field_utils import *
from kataja.utils import time_me
from kataja.ui.panels.UIPanel import UIPanel

__author__ = 'purma'


class VisualizationOptionsPanel(UIPanel):
    """ Panel for editing how visualizations are drawn. """

    def __init__(self, name, key, default_position='float', parent=None, ui_manager=None, folded=False):
        """
        BUild all advanced line options. Then in update filter what to show based on the line type.

        All of the panel constructors follow the same format so that the construction can be automated:
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        self.watchlist = []
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                                 QtWidgets.QSizePolicy.MinimumExpanding))

        proj_styles = [('Highlight projections', g.HIGHLIGHT_PROJECTIONS),
                       ('Colorize projections', g.COLORIZE_PROJECTIONS),
                       ('No visuals for projections', g.NO_PROJECTIONS)]
        self.proj_selector = QtWidgets.QComboBox(self)
        for key, value in proj_styles:
            self.proj_selector.addItem(key, value)

        ui_manager.connect_element_to_action(self.proj_selector,
                                             'set_projection_style')
        layout.addWidget(self.proj_selector)
        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()

    def finish_init(self):
        """ Do initializations that need to be done after the subclass __init__
        has completed. e.g. hide this from view, which can have odd results
        for measurements for fields and layouts if it is called before
        setting them up. Subclass __init__:s must call finish_init at the end!
        :return:
        """
        UIPanel.finish_init(self)
        self.update_panel()
        self.show()

    def update_panel(self):
        """ Choose which selectors to show and update their values
        :return: None
        """
        self.widget().updateGeometry()
        self.widget().update()
        self.updateGeometry()
        self.update()

    def initial_position(self):
        """


        :return:
        """
        dp = self.ui_manager.get_panel(g.VISUALIZATION)
        if dp:
            p = dp.mapToGlobal(dp.pos())
            return QtCore.QPoint(p.x() / dp.devicePixelRatio() + dp.width(), p.y() / dp.devicePixelRatio())
        else:
            return UIPanel.initial_position(self)

    def close(self):
        """ Raise button in VISUALIZATION panel """
        vp = self.ui_manager.get_panel(g.VISUALIZATION)
        if vp:
            vp.toggle_options.setChecked(False)
        UIPanel.close(self)

    def show(self):
        """ Depress button in VISUALIZATION panel """
        vp = self.ui_manager.get_panel(g.VISUALIZATION)
        if vp:
            vp.toggle_options.setChecked(True)
        UIPanel.show(self)

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
        print('VisualizationOptions panel alerted:', signal, field_name, value)

