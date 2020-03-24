import json
from pathlib import Path

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


class WState:
    def __init__(self, id, parent_id, type, head_id, arg_id, head_num_id, arg_num_id, checked_features):
        self.id = id
        self.parent_id = parent_id
        self.type = type,
        self.head_id = head_id
        self.arg_id = arg_id
        self.head_num_id = head_num_id
        self.arg_num_id = arg_num_id
        self.checked_features = checked_features or []

    def as_dict(self):
        return {'id': self.id, 'parent_id': self.parent_id, 'type': self.type, 'head_id': self.head_id,
                'arg_id': self.arg_id, 'head_num_id': self.head_num_id, 'arg_num_id': self.arg_num_id,
                'checked_features': self.checked_features}

    @staticmethod
    def from_state(state):
        parent_id = state.parent and state.parent.state_id
        head_id = state.head and state.head.label
        arg_id = state.arg_ and state.arg_.label
        checked_features = [(str(f1), str(f2)) for f1, f2 in state.checked_features]
        return WState(state.state_id, parent_id, state.state_type, head_id, arg_id, None, None, checked_features)


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
        self.all_states = []
        self.all_routes = []
        self.states = {}
        self.routes = []
        print('created a web')

    def reset(self):
        print('reset web')
        if self.states:
            self.all_states.append(self.states)
            self.all_routes.append(self.routes)
        self.states = {}
        self.routes = []

    def _nodefy_feature(self, feat):
        f_id = str(feat)
        if f_id.startswith('✓'):
            f_id = f_id[1:]
        if f_id in self.nodes:
            return self.nodes[f_id]
        else:
            if feat.sign == '-' or feat.sign == '=' or feat.sign == '_':
                ftype = NEG_FEATURE
            else:
                ftype = POS_FEATURE
            fn = WNode(f_id, ftype)
            self.nodes[f_id] = fn
            return fn

    def _nodefy(self, state):
        def add_numeration_node_id(node, heads):
            numeration_index = heads.index(node)
            wnode = self.nodes[node.label]
            n_label = f'N{numeration_index}'
            if n_label in self.nodes:
                nnode = self.nodes[n_label]
            else:
                nnode = WNode(n_label, NUMERATION)
                self.nodes[n_label] = nnode
                if numeration_index:
                    prev_node = self.nodes[f'N{numeration_index - 1}']
                    prev_edge = WEdge.from_nodes(prev_node, nnode)
                    self.edges[prev_edge.id] = prev_edge
            n_edge_id = f'{nnode.id}_{wnode}'
            if n_edge_id not in self.edges:
                n_edge = WEdge.from_nodes(nnode, wnode)
                self.edges[n_edge_id] = n_edge
            return n_label

        if state.parent and state.parent.state_id not in self.states:
            self._nodefy(state.parent)
        wstate = WState.from_state(state)
        self.states[state.state_id] = wstate

        const = state.head
        if const.label in self.nodes:
            wnode = self.nodes[const.label]
        else:
            wnode = WNode(const.label, CONSTITUENT)
            self.nodes[const.label] = wnode

        heads = [x.head for x in state.route() if x.state_type == state.ADD]
        wstate.head_num_id = add_numeration_node_id(state.head, heads)
        if state.arg_:
            wstate.arg_num_id = add_numeration_node_id(state.arg_, heads)
        for f1, f2 in state.checked_features:
            fnode1 = self._nodefy_feature(f1)
            fnode2 = self._nodefy_feature(f2)
            edge_id = f'{fnode1.id}_{fnode2.id}'
            if edge_id not in self.edges:
                fedge = WEdge.from_nodes(fnode1, fnode2)
                self.edges[edge_id] = fedge

        wnode.features = []
        for feat in const.features:
            fnode = self._nodefy_feature(feat)
            edge_id = f'{wnode.id}_{fnode.id}'
            if edge_id not in self.edges:
                fedge = WEdge.from_nodes(wnode, fnode)
                self.edges[edge_id] = fedge
            wnode.features.append(fnode.id)
        return wstate

    def add_route(self, state):
        self.routes.append(state.route())

    def weave_in(self, state):
        self._nodefy(state)

    def export(self):
        return {
            'nodes': [n.as_dict() for n in self.nodes.values()],
            'links': [e.as_dict() for e in self.edges.values()],
            'states': [[s.as_dict() for s in states.values()] for states in self.all_states + [self.states]] ,
            'routes': [[[r.state_id for r in route] for route in routes] for routes in self.all_routes + [self.routes]]
        }

    def save_as_json(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        file = open(path, 'w')
        e = self.export()
        json.dump(e, file, ensure_ascii=False, indent=2)
        file.close()
        tot_states = sum([len(states) for states in e["states"]])
        tot_routes = sum([len(routes) for routes in e["routes"]])
        print(f'wrote into file {path} {len(e["nodes"])} nodes, {len(e["links"])} edges, {tot_states} states and {tot_routes} routes')
