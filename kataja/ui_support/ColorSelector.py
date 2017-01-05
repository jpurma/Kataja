from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSize
from kataja.ui_support.TableModelSelectionBox import TableModelSelectionBox
from kataja.singletons import ctrl


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


class ColorDialogForSelector(QtWidgets.QColorDialog):
    """

    :param parent:
    :param role:
    :param initial_color:
    """

    def __init__(self, parent, initial_color):
        super().__init__(parent)
        self.setOption(QtWidgets.QColorDialog.NoButtons)
        # self.setOption(QtWidgets.QColorDialog.DontUseNativeDialog)
        self.setOption(QtWidgets.QColorDialog.ShowAlphaChannel)
        for i, key in enumerate(ctrl.cm.color_keys):
            self.setStandardColor(i, ctrl.cm.get(key))
        color = ctrl.cm.get(initial_color) or ctrl.cm.get('content1')
        self.setCurrentColor(color)
        self.currentColorChanged.connect(parent.receive_color_from_color_dialog)
        self.show()


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
        for c in ctrl.cm.color_keys + ctrl.cm.custom_colors:
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
        self.color_dialog = None
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

    def start_color_dialog(self):
        """
        :param parent:
        :param initial_color:
        :return:
        """
        self.color_dialog = ColorDialogForSelector(self, self.selected_color)

    def update_color_dialog(self):
        self.color_dialog.setCurrentColor(self.selected_color)

    def receive_color_from_color_dialog(self, color):
        """ Replace color in palette with new color
        :param color:
        :return:
        """
        color_key = self.selected_color
        ctrl.cm.d[color_key] = color
        if self.role == 'node':
            ctrl.main.trigger_but_suppress_undo('change_node_color')
        elif self.role == 'edge':
            ctrl.main.trigger_but_suppress_undo('change_edge_color')
        elif self.role == 'group':
            ctrl.main.trigger_but_suppress_undo('change_group_color')
        ctrl.call_watchers(self, 'palette_changed')

    def showEvent(self, event):
        ctrl.add_watcher('palette_changed', self)
        super().showEvent(event)

    def hideEvent(self, event):
        ctrl.remove_from_watch(self)
        super().hideEvent(event)

    def watch_alerted(self, *kw, **kwargs):
        self.update()  # it is palette_changed -signal, update forces redraw
