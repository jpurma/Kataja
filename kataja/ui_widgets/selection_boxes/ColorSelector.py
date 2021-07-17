from PyQt6 import QtGui, QtWidgets, QtCore
from PyQt6.QtCore import QSize

from kataja.PaletteManager import color_keys
from kataja.singletons import ctrl
from kataja.ui_widgets.selection_boxes.TableModelSelectionBox import TableModelSelectionBox

stylesheet = """
QComboBox {
    background: transparent;
    border: 1px solid transparent;
    width: 16px;
}


QComboBox::down-arrow {
    border: 0px solid transparent;    
    background-color: %(current)s;    
    width: 12px;
    height: 12px;
}

QComboBox:hover {
    background: transparent;
    border: 1px solid %(lighter)s;
}

"""


class ColorSwatchIconEngine(QtGui.QIconEngine):
    """ An icon which you can provide a method to draw on the icon """

    def __init__(self, color_key, selector):
        QtGui.QIconEngine.__init__(self)
        self.color_key = color_key
        self.selector = selector
        self.grad = QtGui.QConicalGradient(8, 8, 0)
        color = QtGui.QColor()
        self.grad.setColorAt(0, color.fromHsv(359, 255, 255))
        self.grad.setColorAt(0.25, color.fromHsv(270, 255, 255))
        self.grad.setColorAt(0.5, color.fromHsv(180, 255, 255))
        self.grad.setColorAt(0.75, color.fromHsv(90, 255, 255))
        self.grad.setColorAt(1.0, color.fromHsv(0, 255, 255))

    # @caller
    def paint(self, painter, rect, mode, state):
        """

        :param painter:
        :param rect:
        :param mode:
        :param state:
        """
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
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
            self.grad.setCenter(QtCore.QPointF(rect.center()))
            painter.setBrush(self.grad)
            painter.drawRoundedRect(rect, 2, 2)
            painter.setBrush(ctrl.cm.paper2())
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.drawEllipse(rect.left() + 2, rect.top() + 2, rect.width() - 4,
                                rect.height() - 4)


class LineColorIcon(QtGui.QIcon):
    def __init__(self, color_key, selector):
        QtGui.QIcon.__init__(self, ColorSwatchIconEngine(color_key, selector))


class ColorSelector(TableModelSelectionBox):
    def __init__(self, **kwargs):
        TableModelSelectionBox.__init__(self, **kwargs)
        ctrl.main.palette_changed.connect(self.update)
        self.setIconSize(QSize(16, 16))
        self.setMinimumWidth(24)
        self.setMaximumWidth(24)
        self.setStyleSheet(stylesheet % {
            'current': 'transparent',
            'lighter': 'transparent'
        })
        self.color_items = []
        model = self.model()
        for c in color_keys:
            item = QtGui.QStandardItem(LineColorIcon(c, self), '')
            item.setData(c)
            item.setSizeHint(QSize(22, 20))
            item.k_tooltip = c
            self.color_items.append(item)
        view = QtWidgets.QTableView()
        self.table = [self.color_items[0:5] + self.color_items[21:24], self.color_items[5:13],
                      self.color_items[13:21], self.color_items[24:31]]  # + [add_item]
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
        # print('select by data: ', self, data)
        super().select_by_data(data)
        self.selected_color = data

    def receive_color_selection(self) -> str:
        """ Logic for launching color dialog if necessary and returning the selected color key so
        that actions that use ColorSelector don't have to repeat this.
        :return: color_key
        """
        color_key = self.currentData()
        if not color_key:
            ''
        color = ctrl.cm.get(color_key, allow_none=True)
        # launch a color dialog if color_key is unknown or clicking
        # already selected color
        prev_color = self.selected_color
        self.selected_color = color_key
        if (not color) or prev_color == color_key:
            wheel = ctrl.ui.get_panel('ColorWheelPanel')
            if (not wheel) or not wheel.isVisible():
                ctrl.ui.toggle_panel('ColorWheelPanel')
        self.update_color_dialog()
        self.setStyleSheet(stylesheet % {
            'current': ctrl.cm.get(color_key).name(),
            'lighter': ctrl.cm.get(color_key).lighter().name()
        })
        return color_key

    def update_color_dialog(self):
        wheel = ctrl.ui.get_panel('ColorWheelPanel')
        if wheel and wheel.isVisible():
            wheel.set_color_role(self.selected_color, update_selector=True)
            wheel.show()
            wheel.raise_()

    def set_color(self, color_key):
        self.setStyleSheet(stylesheet % {
            'current': ctrl.cm.get(color_key).name(),
            'lighter': ctrl.cm.get(color_key).lighter().name()
        })
        self.select_by_data(color_key)
