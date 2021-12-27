try:
    from plugins.TreesAreMemory3.Constituent import Constituent
    from plugins.TreesAreMemory3.operations import Add, Comp, Spec, Adj, Done, Fail
    from plugins.TreesAreMemory3.route_utils import get_uid, get_label
except ImportError:
    from Constituent import Constituent
    from operations import Add, Comp, Spec, Adj, Done, Fail
    from route_utils import get_uid, get_label


class HeadTrees:
    def __init__(self, route_item, head_tree_dict, constituent_dict):
        self.heads = dict(route_item.parent.head_trees.heads) if route_item.parent else {}
        op = route_item.operation
        if isinstance(op, Done) or isinstance(op, Fail):
            return
        head, adjs, specs, comps, replaces = self.prepare_components(route_item)
        uid = self.build_uid(head, adjs, specs, comps)
        if uid in head_tree_dict:
            print('uid for head_tree exists: ', uid)
            head_tree = head_tree_dict[uid]
        else:
            print('new head tree: ', uid)
            head_tree = HeadTree(uid, head, adjs, specs, comps)
            head_tree.build_constituents(self.heads, constituent_dict)
            head_tree_dict[uid] = head_tree
        for replaced in replaces:
            del self.heads[replaced]
        self.heads[head] = head_tree

    @staticmethod
    def build_uid(head, adjs, specs, comps):
        def joined_tuple(items):
            return f"[{','.join(get_uid(item) for item, op in items)}]"

        def joined(items):
            return f"[{','.join(get_uid(item) for item in items)}]"

        return f'{get_uid(head)}_{get_label(head)}_{joined(adjs)}_{joined_tuple(specs)}_{joined_tuple(comps)}'

    def prepare_components(self, route_item):
        op = route_item.operation
        replaces = []
        head = op.head
        if head in self.heads:
            head_tree = self.heads[head]
            adjs = list(head_tree.adjs)
            specs = list(head_tree.specs)
            comps = list(head_tree.comps)
        else:
            adjs = []
            specs = []
            comps = []
        if type(op) is Add:
            pass
        elif type(op) is Adj:
            adjs += list(op.head)
            replaces = list(op.head)
        elif type(op) is Comp:
            comps.append((op.arg, route_item.checked_features))
            replaces = [op.arg]
        elif type(op) is Spec:
            specs.append((op.arg, route_item.checked_features))
            replaces = [op.arg]
        return head, adjs, specs, comps, replaces


# HeadTrees.heads sisältää aina sille elementille uusimmat päät. Sitä voi käyttää tässä varastona.

class HeadTree:
    def __init__(self, uid, head, adjs, specs, comps):
        self.uid = uid
        self.head = head
        self.adjs = adjs or []
        self.specs = specs or []
        self.comps = comps or []

    def __str__(self):
        return self.uid

    def __repr__(self):
        return str({'head': self.head, 'adjs': self.adjs, 'specs': self.specs, 'comps': self.comps})

    def build_constituents(self, heads, constituent_dict):
        def get_or_build(head):
            return constituent_dict[head] if head in constituent_dict else head.build_constituents(heads, constituent_dict)

        if self.adjs:
            parts = [get_or_build(heads[adj]) for adj in self.adjs]
            merged = parts.pop()
            while parts:
                *parts, adj0 = parts
                adj1 = merged
                merged = Constituent(get_label(self.head), parts=[adj0, adj1], head=(adj0.head, adj1.head))
                merged.original_head = self.head
                #merged.inherited_features = route_item.features
                #merged.contained_feats = adj0.contained_feats | adj1.contained_feats
        else:
            merged = Constituent(self.head.label, features=list(self.head.features))
            merged.head = merged
        for comp, checked_features in self.comps:
            comp_const = get_or_build(heads[comp])
            merged = Constituent(self.head.label, parts=[merged, comp_const], checked_features=list(checked_features))

        #for spec in self.specs:
        return merged

