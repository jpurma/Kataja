from PyQt5 import QtCore, QtGui

from kataja.Shapes import SHAPE_PRESETS
import kataja.globals as g
from kataja.singletons import ctrl, classes
from kataja.ui_widgets.selection_boxes.TableModelSelectionBox import TableModelSelectionBox


class LineStyleIcon(QtGui.QIcon):
    def __init__(self, shape_key, size, color):
        super().__init__()
        self.shape_key = shape_key
        self.size_hint = size
        self.compose_icon(color)

    def compose_icon(self, color):
        size = self.size_hint

        hidp = ctrl.main.devicePixelRatio()
        isize = QtCore.QSize(size.width() * hidp, size.height() * hidp)

        image = QtGui.QImage(
            isize, QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(color)
        SHAPE_PRESETS[self.shape_key].icon_path(painter, image.rect(), color)
        painter.end()
        self.addPixmap(QtGui.QPixmap.fromImage(image))


class ShapeSelector(TableModelSelectionBox):
    def __init__(self, for_edge_type=None, **kwargs):
        TableModelSelectionBox.__init__(self, **kwargs)
        self._connections = []
        self.for_edge_type = for_edge_type
        self.setIconSize(QtCore.QSize(64, 16))
        items = []
        self.icons = []
        color = ctrl.cm.drawing()

        for lt in SHAPE_PRESETS.keys():
            icon = LineStyleIcon(lt, self.iconSize(), color=color)
            self.icons.append(icon)
            item = QtGui.QStandardItem(icon, '')
            item.setData(lt)
            if ctrl.main.use_tooltips:
                item.setToolTip(lt)
            item.setSizeHint(self.iconSize())
            items.append(item)
        model = self.model()
        model.setRowCount(len(items))
        for r, item in enumerate(items):
            model.setItem(r, 0, item)
        self.view().setModel(model)

    def get_active_color(self):
        c_id = ctrl.ui.get_active_edge_setting('color_key', edge_type=self.for_edge_type, skip_selection=True)
        if not c_id:
            node_type = classes.node_type_to_edge_type.get(self.for_edge_type, g.CONSTITUENT_NODE)
            c_id = ctrl.ui.get_active_node_setting('color_key', node_type=node_type, skip_selection=True)
        return ctrl.cm.get(c_id)

    def update_colors(self):
        m = self.model()
        color = self.get_active_color()
        for i in range(0, m.rowCount()):
            item = m.item(i, 0)
            icon = self.icons[i]
            icon.compose_icon(color)
            item.setIcon(icon)

    def connect_main(self):
        m = ctrl.main
        self._connections += [(m.palette_changed, m.palette_changed.connect(self.update_colors)),
                              (m.scope_changed, m.scope_changed.connect(self.update_colors)),
                              (m.active_edge_color_changed, m.active_edge_color_changed.connect(self.update_colors))]

    def disconnect_main(self):
        for host, item in self._connections:
            if item:
                host.disconnect(item)
        self._connections = []

    def showEvent(self, event):
        self.connect_main()
        super().showEvent(event)

    def hideEvent(self, event):
        self.disconnect_main()
        super().hideEvent(event)
