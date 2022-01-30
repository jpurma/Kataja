import json
from pathlib import Path
from collections import Counter
try:
    from plugins.TreesAreMemory3.operations import Add
    from plugins.TreesAreMemory3.route_utils import get_label
except ImportError:
    from operations import Add
    from route_utils import get_label


CONSTITUENT = 0
NEG_FEATURE = 1
POS_FEATURE = 2
NUMERATION = 3

CONSTITUENT_EDGE = 0
NEG_FEAT_EDGE = 1
POS_FEAT_EDGE = 2
FEAT_CHECK_EDGE = 3
NUMERATION_EDGE = 4


class WNode:
    def __init__(self, id, type, features=None):
        self.id = id
        self.type = type
        self.features = features or []

    def __eq__(self, other):
        return self.id == other.id and self.type == other.type

    def as_dict(self):
        return {'id': self.id, 'type': self.type, 'features': self.features}


class WOperation:
    def __init__(self, id, type, msg, checked_features):
        self.id = id
        self.type = type,
        self.head_ids = []
        self.arg_ids = []
        self.msg = msg
        self.checked_features = checked_features or []

    def as_dict(self):
        return {'id': self.id, 'type': self.type, 'head_ids': self.head_ids,
                'arg_ids': self.arg_ids, 'msg': self.msg, 'checked_features': self.checked_features}

    @staticmethod
    def from_operation(operation):
        checked_features = [(str(f1), str(f2)) for f1, f2 in operation.checked_features]
        return WOperation(operation.uid, operation.state_type, operation.entry, checked_features)


class WEdge:
    def __init__(self, start, end, type):
        self.id = f'{start.id}_{end.id}'
        self.type = type
        self.start = start
        self.end = end

    def __eq__(self, other):
        return self.id == other.id and self.type == other.type

    def as_dict(self):
        return {'id': self.id, 'type': self.type, 'start': self.start.id, 'end': self.end.id}

    def __hash__(self):
        return hash(self.id)

    @staticmethod
    def from_nodes(node1, node2):
        if node1.type == CONSTITUENT and node2.type == CONSTITUENT:
            etype = CONSTITUENT_EDGE
        elif node1.type == CONSTITUENT and node2.type == POS_FEATURE:
            etype = POS_FEAT_EDGE
        elif node1.type == CONSTITUENT and node2.type == NEG_FEATURE:
            etype = NEG_FEAT_EDGE
        elif node1.type == NUMERATION and node2.type == NUMERATION:
            etype = NUMERATION_EDGE
        elif node1.type == NUMERATION and node2.type == CONSTITUENT:
            etype = CONSTITUENT_EDGE
        else:
            etype = FEAT_CHECK_EDGE
        return WEdge(node1, node2, etype)


class Web:
    def __init__(self):
        self.nodes = {}
        self.done_uids = {}
        self.edges = {}
        self.all_operations = []
        self.all_routes = []
        self.operations = {}
        self.routes = []
        self.heads = []
        self.label_count = Counter()

    def reset(self):
        print('reset web')
        if self.operations:
            self.all_operations.append(self.operations)
            self.all_routes.append(self.routes)
        self.operations = {}
        self.routes = []

    def _nodefy_feature(self, feat):
        f_id = str(feat)
        if f_id.startswith('✓'):
            f_id = f_id[1:]
        if f_id in self.nodes:
            return self.nodes[f_id]
        else:
            if feat.sign in '-=_><':
                ftype = NEG_FEATURE
            else:
                ftype = POS_FEATURE
            fn = WNode(f_id, ftype)
            self.nodes[f_id] = fn
            return fn

    def _get_or_add_node(self, label, type):
        if label in self.nodes:
            return self.nodes[label]
        else:
            node = WNode(label, type)
            self.nodes[label] = node
            return node

    def _get_or_add_const_node(self, const):
        if const.label in self.nodes:
            return self.nodes[const.label]
        else:
            node = WNode(const.label, CONSTITUENT)
            node.features = []
            for feat in const.features:
                fnode = self._nodefy_feature(feat)
                self._get_or_add_edge(node, fnode)
                node.features.append(fnode.id)
            self.nodes[const.label] = node
            return node

    def _get_or_add_edge(self, node1, node2):
        n_edge_id = f'{node1.id}_{node2.id}'
        if n_edge_id in self.edges:
            return self.edges[n_edge_id]
        n_edge = WEdge.from_nodes(node1, node2)
        self.edges[n_edge_id] = n_edge
        return n_edge

    def _create_if_necessary(self, const):
        if not const:
            return []
        if isinstance(const, tuple):
            nodes = []
            for c in const:
                nodes += self._create_if_necessary(c)
            return nodes
        if const.uid in self.heads:
            numeration_node_label = f'N{self.heads.index(const.uid)}'
        else:
            numeration_node_label = f'N{len(self.heads)}'
            self.heads.append(const.uid)
        num_node = self._get_or_add_node(numeration_node_label, NUMERATION)
        lex_node = self._get_or_add_const_node(const)
        self._get_or_add_edge(num_node, lex_node)
        return [[num_node.id, lex_node.id]]

    def _create_dominance_relation(self, head_ids, arg_ids):
        if not arg_ids:
            return
        for head_num_id, head_id in head_ids:
            for arg_num_id, arg_id in arg_ids:
                edge_id = f'{head_num_id}_{arg_num_id}'
                if edge_id not in self.edges:
                    head_num = self.nodes[head_num_id]
                    arg_num = self.nodes[arg_num_id]
                    self.edges[edge_id] = WEdge(head_num, arg_num, NUMERATION_EDGE)

    def _nodefy(self, route_item):
        operation = route_item.operation
        w_op = self.operations.get(operation.uid, None)
        if w_op:
            if type(operation) is Add:
                self.heads.append(operation.head.uid)
            return w_op

        w_op = WOperation.from_operation(operation)
        self.operations[operation.uid] = w_op
        w_op.head_ids = self._create_if_necessary(operation.head)
        w_op.arg_ids = self._create_if_necessary(operation.arg)
        self._create_dominance_relation(w_op.head_ids, w_op.arg_ids)
        for f1, f2 in operation.checked_features:
            fnode1 = self._nodefy_feature(f1)
            fnode2 = self._nodefy_feature(f2)
            self._get_or_add_edge(fnode1, fnode2)

        return w_op

    def weave_in(self, routes):
        for route in routes:
            self.heads = []
            wroute = [self._nodefy(route_item) for route_item in route]
            self.routes.append(wroute)

    def export(self):
        return {
            'nodes': [n.as_dict() for n in self.nodes.values()],
            'links': [e.as_dict() for e in self.edges.values()],
            'states': [dict([(key, s.as_dict()) for key, s in self.operations.items()])],
            'routes': [[[s.id for s in route] for route in self.routes]]
        }

    def save_as_json(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        file = open(path, 'w')
        e = self.export()
        json.dump(e, file, ensure_ascii=False, indent=2)
        file.close()
        #tot_states = sum([len(states) for states in e["states"]])
        #tot_routes = sum([len(routes) for routes in e["routes"]])
        print(f'wrote into file {path} {len(e["nodes"])} nodes, {len(e["links"])} edges, {len(e["states"])} operations and {len(e["routes"])} routes')
