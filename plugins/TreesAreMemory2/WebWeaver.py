import json

CONSTITUENT = 0
NEG_FEATURE = 1
POS_FEATURE = 2

CONSTITUENT_EDGE = 0
NEG_FEAT_EDGE = 1
POS_FEAT_EDGE = 2
FEAT_CHECK_EDGE = 3


class WNode:
    def __init__(self, id, type):
        self.id = id
        self.type = type
        self.edges_down = set()

    def __eq__(self, other):
        return self.id == other.id and self.type == other.type and self.parts == other.parts

    def as_dict(self):
        return {'id': self.id, 'type': self.type}


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
        else:
            etype = FEAT_CHECK_EDGE
        return WEdge(node1, node2, etype)


class Web:
    def __init__(self):
        self.structures = set()
        self.nodes = {}
        self.done_uids = {}
        self.edges = {}

    def _nodefy_feature(self, feat):
        if feat.uid in self.done_uids:
            return self.done_uids[feat.uid]
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

    def _nodefy(self, const):

        if const.label in self.nodes:
            wnode = self.nodes[const.label]
        else:
            wnode = WNode(const.label, CONSTITUENT)
            self.nodes[const.label] = wnode
        for f1, f2 in const.checked_features:
            fnode1 = self._nodefy_feature(f1)
            fnode2 = self._nodefy_feature(f2)
            edge_id = f'{fnode1.id}_{fnode2.id}'
            if edge_id not in self.edges:
                fedge = WEdge.from_nodes(fnode1, fnode2)
                self.edges[edge_id] = fedge

        for feat in const.features:
            fnode = self._nodefy_feature(feat)
            edge_id = f'{wnode.id}_{fnode.id}'
            if edge_id in self.edges:
                fedge = self.edges[edge_id]
            else:
                fedge = WEdge.from_nodes(wnode, fnode)
                self.edges[edge_id] = fedge
            wnode.edges_down.add(fedge)
        for part in const.parts:
            onode = self._nodefy(part)
            edge_id = f'{wnode.id}_{onode.id}'
            if edge_id not in self.edges:
                cedge = WEdge.from_nodes(wnode, onode)
                self.edges[edge_id] = cedge
                wnode.edges_down.add(cedge)
        return wnode

    def weave_in(self, const):
        self._nodefy(const)

    def export(self):
        return {
            'nodes': [n.as_dict() for n in self.nodes.values()],
            'links': [e.as_dict() for e in self.edges.values()]
        }

    def save_as_json(self, path):
        file = open(path, 'w')
        e = self.export()
        json.dump(e, file, ensure_ascii=False, indent=2)
        file.close()
        print(f'wrote into file {path} {len(e["nodes"])} nodes, {len(e["links"])} edges')
