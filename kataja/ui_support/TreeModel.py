from kataja.singletons import ctrl
from kataja.ui_support.DTNode import DTNode
from kataja.ui_support.DTLine import DTLine


class ParseTreeBaseModel:
    def __init__(self, panel):
        self.panel = panel
        self.dt_data = {}
        self.scene = panel.scene
        self.node_count = 0
        self.line_count = 0

    def update_node_counts(self):
        self.panel.update_node_count(self.node_count)
        self.panel.update_edge_count(self.line_count)


class TreeModel(ParseTreeBaseModel):
    def update_selected(self):
        dt = ctrl.forest.derivation_tree
        route_lines = set()
        selected_id = dt.current_step_id
        state_id = selected_id
        for parent_id in dt.iterate_branch(selected_id):
            route_lines.add((state_id, parent_id))
            state_id = parent_id

        for item in self.scene.items():
            if isinstance(item, DTNode):
                selected = item.state_id == selected_id
                item.set_selected(selected)
                item.set_fog(selected_id not in dt.iterate_branch(item.state_id))
                item.update()

            elif isinstance(item, DTLine):
                selected = item.get_id() in route_lines
                item.set_selected(selected)
                item.set_fog(selected_id not in dt.iterate_branch(item.state_id))
                item.update()

    def prepare(self):
        def add_children(state_ids, depth):
            if depth == len(columns):
                columns.append([])
            columns[depth] += state_ids
            next_ids = []
            empty = True
            for state_id in state_ids:
                children = dt.child_map[state_id] if state_id else None
                if not children:
                    next_ids.append(None)
                else:
                    empty = False
                    next_ids += children
            if not empty:
                add_children(next_ids, depth + 1)

        if ctrl.main.signalsBlocked():
            return
        dt = ctrl.forest.derivation_tree
        if not dt:
            return
        roots = dt.get_roots()
        columns = []
        add_children(roots, 0)

        self.dt_data = {}
        width = len(columns) + 1
        for x, column in enumerate(columns, 1):
            height = len(column) + 1
            for y, node in enumerate(column, 1):
                if node:
                    self.dt_data[node] = (1.0 / width) * x, (1.0 / height) * y
        self.draw()
        self.update_selected()
        ctrl.graph_view.activateWindow()

    def draw(self):
        sc = self.scene
        sc.clear()
        dt = ctrl.forest.derivation_tree
        width = sc.width()
        height = sc.height()
        nodes = []
        self.line_count = 0
        for node_id, (x, y) in self.dt_data.items():
            uid, data, msg, state_id, parent_id, state_type = dt.d[node_id]
            nx = x * width
            ny = y * height
            node = DTNode(node_id, nx, ny, msg, state_type)
            nodes.append(node)
            if parent_id in self.dt_data:
                parent_x, parent_y = self.dt_data[parent_id]
                px = parent_x * width
                py = parent_y * height
                line = DTLine(state_id, parent_id, nx, ny, px, py, state_type)
                sc.addItem(line)
                self.line_count += 1

        for node in nodes:
            sc.addItem(node)
        self.node_count = len(nodes)
        self.update_node_counts()
