from PyQt5 import QtGui, QtWidgets, QtCore
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
        self.grad = QtGui.QConicalGradient(8, 8, 0)
        self.grad.setColorAt(0, QtGui.QColor.fromHsv(359, 255, 255))
        self.grad.setColorAt(0.25, QtGui.QColor.fromHsv(270, 255, 255))
        self.grad.setColorAt(0.5, QtGui.QColor.fromHsv(180, 255, 255))
        self.grad.setColorAt(0.75, QtGui.QColor.fromHsv(90, 255, 255))
        self.grad.setColorAt(1.0, QtGui.QColor.fromHsv(0, 255, 255))


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
        c = ctrl.cm.get(self.color_key, allow_none=True)
        if c:
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
        else:
            self.grad.setCenter(rect.center())
            painter.setBrush(self.grad)
            painter.drawRoundedRect(rect, 2, 2)
            painter.setBrush(ctrl.cm.paper2())
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(rect.left() + 2, rect.top() + 2, rect.width() - 4, rect.height()
                                - 4)


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
        for c in color_keys:
            item = QtGui.QStandardItem(LineColorIcon(c, self), '')
            item.setData(c)
            item.setSizeHint(QSize(22, 20))
            item.setToolTip(c)
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
        if not color_key:
            return
        color = ctrl.cm.get(color_key, allow_none=True)
        # launch a color dialog if color_id is unknown or clicking
        # already selected color
        prev_color = self.selected_color
        self.selected_color = color_key
        if (not color) or prev_color == color_key:
            wheel = ctrl.ui.get_panel('ColorWheelPanel')
            if (not wheel) or not wheel.isVisible():
                ctrl.ui.toggle_panel(ctrl.ui.get_action('toggle_panel_ColorWheelPanel'),
                                     'ColorWheelPanel')
        self.update_color_dialog()
        return color_key

    def update_color_dialog(self):
        wheel = ctrl.ui.get_panel('ColorWheelPanel')
        if wheel and wheel.isVisible():
            wheel.set_color_role(self.selected_color, update_selector=True)
            wheel.show()
            wheel.raise_()

    def showEvent(self, event):
        ctrl.add_watcher(self, 'palette_changed')
        super().showEvent(event)

    def hideEvent(self, event):
        ctrl.remove_from_watch(self)
        super().hideEvent(event)

    def watch_alerted(self, *kw, **kwargs):
        self.update()  # it is palette_changed -signal, update forces redraw
