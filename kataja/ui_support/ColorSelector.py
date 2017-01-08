from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSize
from kataja.ui_support.TableModelSelectionBox import TableModelSelectionBox
from kataja.singletons import ctrl
from kataja.PaletteManager import color_keys


class ColorSwatchIconEngine(QtGui.QIconEngine):
    """ An icon which you can provide a method to draw on the icon """

    def __init__(self, color_key, selector):
        """
        :param paint_method: a compatible drawing method
        :param owner: an object that is queried for settings for paint_method
        :return:
        """
        QtGui.QIconEngine.__init__(self)
        self.color_key = color_key
        self.selector = selector

    # @caller
    def paint(self, painter, rect, mode, state):
        """

        :param painter:
        :param rect:
        :param mode:
        :param state:
        """
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        bg = ctrl.cm.get('background1')
        painter.fillRect(rect, bg)
        c = ctrl.cm.get(self.color_key)
        if not c:
            c = bg
        painter.setBrush(c)
        if self.selector.selected_color == self.color_key:
            pen = QtGui.QPen(c.lighter())
        else:
            pen = QtGui.QPen(c.darker())
        if self.selector.default_color == self.color_key:
            pen.setWidth(3)
        else:
            pen.setWidth(1)

        painter.setPen(pen)
        painter.drawRoundedRect(rect, 2, 2)
        # painter.fillRect(rect, ctrl.cm.get(self.color_key))


class LineColorIcon(QtGui.QIcon):
    """

    :param color_id:
    :param model:
    """

    def __init__(self, color_id, selector):
        QtGui.QIcon.__init__(self, ColorSwatchIconEngine(color_id, selector))


class ColorSelector(TableModelSelectionBox):
    """
    :param parent:
    :param role: 'node' or 'edge' or 'group'
    """

    def __init__(self, parent, role='node'):
        super().__init__(parent)
        self.setIconSize(QSize(16, 16))
        self.setMinimumWidth(40)
        self.setMaximumWidth(40)
        self.role = role
        self.color_items = []
        model = self.model()
        print(len(color_keys))
        for c in color_keys:
            item = QtGui.QStandardItem(LineColorIcon(c, self), '')
            item.setData(c)
            item.setSizeHint(QSize(22, 20))
            self.color_items.append(item)
        view = QtWidgets.QTableView()
        self.table = [self.color_items[0:5] + self.color_items[21:24],
                      self.color_items[5:13],
                      self.color_items[13:21],
                      self.color_items[24:31]]  # + [add_item]
        model.clear()
        self.selected_color = 'content1'
        self.default_color = 'content1'
        for c, column in enumerate(self.table):
            for r, item in enumerate(column):
                model.setItem(r, c, item)
        view.horizontalHeader().hide()
        view.verticalHeader().hide()
        view.setCornerButtonEnabled(False)
        view.setModel(model)
        view.resizeColumnsToContents()
        cw = view.columnWidth(0)
        view.setMinimumWidth(model.columnCount() * cw)
        self.setView(view)

    def select_by_data(self, data):
        """
        :param data:
        """
        super().select_by_data(data)
        self.selected_color = data

    def receive_color_selection(self) -> str:
        """ Logic for launching color dialog if necessary and returning the selected color key so
        that actions that use ColorSelector don't have to repeat this.
        :return: color_key
        """
        color_key = self.currentData()
        color = ctrl.cm.get(color_key)
        # launch a color dialog if color_id is unknown or clicking
        # already selected color
        start = False
        if not color:
            color = ctrl.cm.get('content1')
            ctrl.cm.set_color(color_key, color)
            start = True
        elif self.selected_color == color_key:
            start = True
        self.selected_color = color_key
        if start:
            self.start_color_dialog()
        self.update_color_dialog()
        return color_key

    def start_color_dialog(self):
        wheel = ctrl.ui.get_panel('ColorWheelPanel')
        if (not wheel) or not wheel.isVisible():
            ctrl.main.trigger_but_suppress_undo('toggle_panel_ColorWheelPanel')

    def update_color_dialog(self):
        wheel = ctrl.ui.get_panel('ColorWheelPanel')
        if wheel and wheel.isVisible():
            wheel.set_color_role(self.selected_color)
            wheel.show()
            wheel.raise_()

    def showEvent(self, event):
        ctrl.add_watcher('palette_changed', self)
        super().showEvent(event)

    def hideEvent(self, event):
        ctrl.remove_from_watch(self)
        super().hideEvent(event)

    def watch_alerted(self, *kw, **kwargs):
        self.update()  # it is palette_changed -signal, update forces redraw
