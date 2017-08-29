from PyQt5 import QtCore, QtGui

from kataja.Shapes import SHAPE_PRESETS
import kataja.globals as g
from kataja.singletons import ctrl
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
        self.for_edge_type = for_edge_type
        self.setIconSize(QtCore.QSize(64, 16))
        items = []
        self.icons = []
        color = self.get_active_color()

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
        scope = ctrl.ui.get_active_scope()
        if self.for_edge_type:
            if scope == g.SELECTION:
                scope = g.HIGHEST
            color_id = ctrl.settings.get_edge_setting('color_id', edge_type=self.for_edge_type,
                                                      level=scope)
            edge_type = self.for_edge_type
        else:
            color_id = ctrl.settings.get_active_edge_setting('color_id')
            edge_type = ctrl.ui.active_edge_type
        if not color_id:
            node_type_map = {g.CONSTITUENT_EDGE: g.CONSTITUENT_NODE,
                             g.FEATURE_EDGE: g.FEATURE_NODE,
                             g.CHECKING_EDGE: g.FEATURE_NODE,
                             g.GLOSS_EDGE: g.GLOSS_NODE,
                             g.COMMENT_EDGE: g.COMMENT_NODE
            }
            node_type = node_type_map.get(edge_type, g.CONSTITUENT_NODE)
            scope = ctrl.ui.get_active_scope()
            if scope == g.SELECTION:
                scope = g.HIGHEST
            color_id = ctrl.settings.get_node_setting('color_id', node_type=node_type,
                                                      level=scope)
        return ctrl.cm.get(color_id)

    def update_colors(self):
        m = self.model()
        color = self.get_active_color()
        for i in range(0, m.rowCount()):
            item = m.item(i, 0)
            icon = self.icons[i]
            icon.compose_icon(color)
            item.setIcon(icon)

    def showEvent(self, event):
        ctrl.add_watcher(self, 'active_edge_color_changed')
        ctrl.add_watcher(self, 'palette_changed')
        ctrl.add_watcher(self, 'scope_changed')
        super().showEvent(event)

    def hideEvent(self, event):
        ctrl.remove_from_watch(self)
        super().hideEvent(event)

    def watch_alerted(self, *kw, **kwargs):
        self.update_colors()


