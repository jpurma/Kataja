from kataja.singletons import ctrl
from kataja.ui_widgets.Panel import Panel
from PyQt5 import QtWidgets, QtCore
from kataja.ui_support.panel_utils import mini_button, text_button, set_value, label, box_row, \
    checkbox
import kataja.globals as g

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
        self.watchlist = ['view_mode_changed']
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                                 QtWidgets.QSizePolicy.MinimumExpanding))
        self.setMaximumWidth(220)
        self.setMaximumHeight(140)

        hlayout = box_row(layout)
        layout.addLayout(hlayout)
        ui = self.ui_manager
        self.show_display_labels = checkbox(ui, inner, hlayout,
                                               'Show display labels', 'toggle_show_display_label')
        grid = QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)

        label(self, grid, 'Show projections', 0, 0)
        self.highlighter_button = checkbox(ui, inner, grid,
                                              'with highlighter',
                                              'toggle_highlighter_projection',
                                              1, 0)
        self.strong_lines_button = checkbox(ui, inner, grid,
                                               'with stronger lines',
                                               'toggle_strong_lines_projection',
                                               1, 1)
        self.colorize_button = checkbox(ui, inner, grid,
                                           'with colorized lines',
                                           'toggle_colorized_projection',
                                           1, 2)

        layout.addLayout(grid)
        inner.setLayout(layout)
        self.setWidget(inner)
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
        self.widget().updateGeometry()
        self.widget().update()
        s = ctrl.settings
        set_value(self.show_display_labels, s.get('show_display_labels'))
        set_value(self.highlighter_button, s.get('projection_highlighter'))
        set_value(self.strong_lines_button, s.get('projection_strong_lines'))
        set_value(self.colorize_button, s.get('projection_colorized'))
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
        self.update_panel()

