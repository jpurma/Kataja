from PyQt5 import QtCore, QtWidgets, QtGui

from kataja.singletons import ctrl
from kataja.ui_support.CircleModel import CircleModel
from kataja.ui_support.TreeModel import TreeModel
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.buttons.TwoStateButton import TwoStateButton


class ParseTreePanel(Panel):
    """ Display parses and their derivation states as a tree """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        self.model = None
        Panel.__init__(self, name, default_position, parent, folded)
        self.preferred_size = QtCore.QSize(240, 200)
        self.preferred_floating_size = QtCore.QSize(320, 320)
        self.view = QtWidgets.QGraphicsView()
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.setSceneRect(0, 0, 310, 300)
        self.view.setScene(self.scene)
        self.view.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setWidget(self.view)
        self.columns = []
        self.circle_model = CircleModel(self)
        self.tree_model = TreeModel(self)
        self.model = self.circle_model
        self.tree_mode = False
        self.model.prepare()
        self.finish_init()
        self.mode_button = TwoStateButton('O', 'E', action='toggle_parse_panel_visualisation_mode', parent=self)
        self.mode_button.move(0, self.height() - 24)
        self.mode_button.show()
        self.mode_button.setFixedSize(20, 20)
        self.node_count = QtWidgets.QLabel('nodes:', parent=self)
        self.node_count.setFixedWidth(80)
        self.node_count.move(8, 18)
        self.node_count.show()
        self.edge_count = QtWidgets.QLabel('edges:', parent=self)
        self.edge_count.move(8, 32)
        self.edge_count.setFixedWidth(80)
        self.edge_count.show()

        ctrl.main.forest_changed.connect(self.prepare_model)
        ctrl.main.parse_changed.connect(self.update_selected)
        ctrl.graph_view.activateWindow()
        ctrl.graph_view.setFocus()

    def prepare_model(self):
        self.model.prepare()

    def change_mode(self, mode):
        self.tree_mode = mode
        self.model = self.tree_model if self.tree_mode else self.circle_model
        self.model.prepare()

    def initial_position(self, next_to=''):
        return Panel.initial_position(self, next_to=next_to or 'NavigationPanel')

    def update_selected(self):
        self.model.update_selected()
        self.mode_button.setChecked(self.tree_mode)

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        """
        if self.model:
            self.model.prepare()
        super().showEvent(event)

    def update_node_count(self, n_count):
        self.node_count.setText(f'nodes: {n_count}')

    def update_edge_count(self, e_count):
        self.edge_count.setText(f'edges: {e_count}')

    def resize(self, size):
        if hasattr(self, 'view'):
            self.view.setFixedSize(size)
        super().resize(size)
        # self.resize(self.widget().sizeHint())
