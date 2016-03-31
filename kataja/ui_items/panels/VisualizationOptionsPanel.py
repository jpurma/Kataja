from kataja.singletons import ctrl
from kataja.ui_items.Panel import Panel
from PyQt5 import QtWidgets, QtCore
from kataja.ui_support.panel_utils import mini_button, text_button, set_value, label
import kataja.globals as g

__author__ = 'purma'


class VisualizationOptionsPanel(Panel):
    """ Panel for editing how visualizations are drawn. """

    def __init__(self, name, key, default_position='float', parent=None, folded=False):
        """
        BUild all advanced line options. Then in update filter what to show based on the line type.

        All of the panel constructors follow the same format so that the construction can be automated:
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, key, default_position, parent, folded)
        self.watchlist = []
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                                 QtWidgets.QSizePolicy.MinimumExpanding))

        #checkbox(ui_manager, panel, layout, label, action)

        grid = QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        # layout.addLayout(grid)
        # label(self, grid, 'Show aliases', 0, 0)
        # self.show_leaf_alias = checkbox(ui_manager, self, grid,
        #                                 'for leaves',
        #                                 'toggle_show_leaf_alias', 1, 0)
        # self.show_internal_alias = checkbox(ui_manager, self, grid,
        #                                     'for inner nodes',
        #                                     'toggle_show_internal_alias', 1, 1)
        # label(self, grid, 'Show labels', 0, 2)
        # self.show_leaf_label = checkbox(ui_manager, self, grid,
        #                                 'for leaves',
        #                                 'toggle_show_leaf_label', 1, 2)
        # self.show_internal_label = checkbox(ui_manager, self, grid,
        #                                     'for inner nodes',
        #                                     'toggle_show_internal_label', 1, 3)

        layout.addLayout(grid)
        ui = self.ui_manager
        label(self, grid, 'For inner nodes show', 0, 0)
        self.show_internal_alias = mini_button(ui, self, grid,
                                               'aliases', 'toggle_show_internal_alias'
                                                , 3, 0, checkable=True)
        self.show_internal_label = mini_button(ui, self, grid,
                                               'labels',
                                               'toggle_show_internal_label',
                                               3, 1, checkable=True)
        label(self, grid, '╱', 2, 2)
        label(self, grid, 'For leaf nodes show', 0, 3)
        self.show_leaf_alias = mini_button(ui, self, grid,
                                           'aliases', 'toggle_show_leaf_alias',
                                           1, 3, checkable=True)
        self.show_leaf_label = mini_button(ui, self, grid,
                                           'labels', 'toggle_show_leaf_label',
                                           1, 4, checkable=True)

        layout.addLayout(grid)
        grid = QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)

        label(self, grid, 'Show projections', 0, 0)
        self.highlighter_button = text_button(ui, grid,
                                              'with highlighter',
                                              'toggle_highlighter_projection',
                                              1, 0, checkable=True)
        self.strong_lines_button = text_button(ui, grid,
                                               'with stronger lines',
                                               'toggle_strong_lines_projection',
                                               1, 1, checkable=True)
        self.colorize_button = text_button(ui, grid,
                                           'with colorized lines',
                                           'toggle_colorized_projection',
                                           1, 2, checkable=True)

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
        s = ctrl.fs
        set_value(self.show_internal_alias, s.show_internal_aliases)
        set_value(self.show_leaf_alias, s.show_leaf_aliases)
        set_value(self.show_internal_label, s.show_internal_labels)
        set_value(self.show_leaf_label, s.show_leaf_labels)
        set_value(self.highlighter_button, s.projection_highlighter)
        set_value(self.strong_lines_button, s.projection_strong_lines)
        set_value(self.colorize_button, s.projection_colorized)

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
            return Panel.initial_position(self)

    def close(self):
        """ Raise button in VISUALIZATION panel """
        vp = self.ui_manager.get_panel(g.VISUALIZATION)
        if vp:
            vp.toggle_options.setChecked(False)
        Panel.close(self)

    def show(self):
        """ Depress button in VISUALIZATION panel """
        vp = self.ui_manager.get_panel(g.VISUALIZATION)
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
        print('VisualizationOptions panel alerted:', signal, field_name, value)

