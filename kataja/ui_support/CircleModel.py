import math

from kataja.singletons import ctrl
from kataja.ui_support.DTNode import DTNode
from kataja.ui_support.DTLine import DTLine
from kataja.ui_support.TreeModel import ParseTreeBaseModel


class PathNode:
    def __init__(self, state_id, node_type, msg):
        self.state_id = ''
        self.parents = []
        self.x = 0
        self.y = 0
        self.msg = msg
        self.node_type = node_type

    def add_parent(self, parent):
        if parent not in self.parents:
            self.parents.append(parent)


class CircleModel(ParseTreeBaseModel):
    def update_selected(self):
        dt = ctrl.forest.derivation_tree
        route_lines = set()
        if isinstance(dt.current_step_id, str):
            route_parts = [int(part) for part in dt.current_step_id.split('_')]
            selected_id = route_parts[-1]
            parent_id = route_parts[0]
            if len(route_parts) > 1:
                for state_id in route_parts[1:]:
                    route_lines.add((state_id, parent_id))
                    parent_id = state_id
        else:
            selected_id = 0

        for item in self.scene.items():
            if isinstance(item, DTNode):
                selected = item.state_id == selected_id
                item.set_selected(selected)
                item.set_fog(not selected)
                item.update()

            elif isinstance(item, DTLine):
                selected = item.get_id() in route_lines
                item.set_selected(selected)
                item.set_fog(not selected)
                item.update()

    def prepare(self):
        nodes = {}
        root_ids = []

        def add_nodes(state_paths):
            for state_path in state_paths:
                states = [int(state) for state in state_path.split('_')]
                prev_node_id = None
                state_id = None
                for state_id in states:
                    if state_id in nodes:
                        node = nodes[state_id]
                    else:
                        command, node_type = state_metadata[state_id]
                        node = PathNode(state_id, node_type, command)
                        nodes[state_id] = node
                    if prev_node_id:
                        node.add_parent(prev_node_id)
                    prev_node_id = state_id
                if states:
                    if state_id not in root_ids:
                        root_ids.append(state_id)

        if ctrl.main.signalsBlocked():
            return
        dt = ctrl.forest.derivation_tree
        if not dt:
            return
        state_metadata = dt.collect_states()
        add_nodes(dt.branches)
        for i, (key, node) in enumerate(sorted(nodes.items())):
            p = ((math.pi * 2) / len(nodes)) * i
            node.x = math.cos(p)
            node.y = math.sin(p)

        self.draw(nodes)
        self.update_selected()
        ctrl.graph_view.activateWindow()

    def draw(self, nodes):
        sc = self.scene
        sc.clear()
        w2 = (sc.width() - 8) / 2
        h2 = (sc.height() - 8) / 2
        graph_nodes = {}
        self.node_count = 0
        self.line_count = 0
        for node_id, node in nodes.items():
            node.nx = node.x * w2 + w2 + 4
            node.ny = node.y * h2 + h2 + 4
            g_node = DTNode(node_id, node.nx, node.ny, node_id, node.node_type)
            graph_nodes[node_id] = g_node
            sc.addItem(g_node)
        for key, graph_node in graph_nodes.items():
            node = nodes[key]
            for parent_id in node.parents:
                other_node = nodes[parent_id]
                line = DTLine(key, parent_id, node.nx, node.ny, other_node.nx, other_node.ny, other_node.node_type)
                sc.addItem(line)
                self.line_count += 1
        self.node_count = len(graph_nodes)
        self.update_node_counts()