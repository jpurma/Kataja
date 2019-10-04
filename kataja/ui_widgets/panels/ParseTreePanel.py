from PyQt5 import QtCore, QtWidgets, QtGui
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel
from kataja.uniqueness_generator import next_available_type_id

def color_for(ds_type):
    return ctrl.cm.d[f'accent{(ds_type + 1) % 8}']

class DTNode(QtWidgets.QGraphicsEllipseItem):
    __qt_type_id__ = next_available_type_id()

    def __init__(self, state_id, x, y, msg, ds_type=0):
        super().__init__(x - 3, y - 3, 6, 6)
        self.state_id = state_id
        self.setPen(qt_prefs.no_pen)
        self.k_tooltip = msg
        self.ds_type = ds_type
        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setBrush(color_for(ds_type))
        self.selected = False

    def set_selected(self, value):
        self.selected = value
        if value:
            pen = QtGui.QPen(ctrl.cm.lighter(color_for(self.ds_type)))
            pen.setWidth(3)
            self.setPen(pen)
        else:
            self.setPen(qt_prefs.no_pen)

    def hoverEnterEvent(self, event):
        self.setBrush(ctrl.cm.lighter(color_for(self.ds_type)))
        self._hovering = True
        ctrl.ui.show_help(self, event)

    def hoverMoveEvent(self, event):
        ctrl.ui.move_help(event)

    def hoverLeaveEvent(self, event):
        self._hovering = False
        self.setBrush(color_for(self.ds_type))
        ctrl.ui.hide_help(self, event)

    def mouseReleaseEvent(self, event):
        ctrl.main.trigger_action('jump_to_derivation_by_id', self.state_id)
        super().mouseReleaseEvent(event)


class ParseTreePanel(Panel):
    """ Display parses and their derivation states as a tree """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, default_position, parent, folded)
        ctrl.main.forest_changed.connect(self.prepare_tree)
        self.preferred_size = QtCore.QSize(240, 200)
        self.preferred_floating_size = QtCore.QSize(320, 320)
        self.view = QtWidgets.QGraphicsView()
        self.view.setFixedSize(self.preferred_floating_size)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.setSceneRect(0, 0, 310, 300)
        self.view.setScene(self.scene)
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setWidget(self.view)
        self.prepare_tree()
        self.finish_init()
        self.dt_data = {}
        self.columns = []
        ctrl.main.forest_changed.connect(self.prepare_tree)
        ctrl.main.parse_changed.connect(self.update_selected)

        ctrl.graph_view.activateWindow()
        ctrl.graph_view.setFocus()

    def prepare_tree(self):
        if ctrl.main.signalsBlocked():
            return
        dt = ctrl.forest.derivation_tree
        if not dt:
            return
        self.dt_data = {}
        columns = []

        for branch_end in dt.branches:
            branch = dt.build_branch(branch_end)
            for i, node in enumerate(branch):
                if i < len(columns):
                    columns[i].add(node)
                else:
                    columns.append({node})
        self.columns = []
        width = len(columns) + 2
        for x, column in enumerate(columns, 1):
            ordered = sorted(list(column))
            height = len(column) + 2
            self.columns.append(ordered)
            for y, node in enumerate(ordered, 1):
                self.dt_data[node] = (1.0 / width) * x, (1.0 / height) * y
        self.draw_tree()
        self.update_selected()
        ctrl.graph_view.activateWindow()

    def draw_tree(self):
        sc = self.scene
        sc.clear()
        dt = ctrl.forest.derivation_tree
        width = sc.width()
        height = sc.height()
        nodes = []
        for node_id, (x, y) in self.dt_data.items():
            uid, data, msg, state_id, parent_id, state_type = dt.d[node_id]
            node = DTNode(node_id, x * width, y * height, msg, state_type)
            nodes.append(node)
            if parent_id in self.dt_data:
                parent_x, parent_y = self.dt_data[parent_id]
                sc.addLine(x * width, y * height, parent_x * width, parent_y * height, ctrl.cm.d[f'accent{(state_type + 1) % 8}tr'])

        for node in nodes:
            sc.addItem(node)

    def update_selected(self):
        selected_id = ctrl.forest.derivation_tree.current_step_id
        for item in self.scene.items():
            if isinstance(item, DTNode):
                was_selected = item.selected
                selected = item.state_id == selected_id
                if was_selected != selected:
                    item.set_selected(selected)
                    item.update()

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.prepare_tree()
        super().showEvent(event)
