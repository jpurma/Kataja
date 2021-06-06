try:
    from plugins.TreesAreMemory2.Constituent import Constituent
    from plugins.TreesAreMemory2.WebWeaver import Web
    from kataja.syntax.SyntaxState import SyntaxState
    from plugins.TreesAreMemory2.route_utils import *
    from plugins.TreesAreMemory2.operations import Add, Comp, Spec, Adj, Done, Fail
except ImportError:
    from Constituent import Constituent
    from WebWeaver import Web
    from route_utils import *
    from operations import Add, Comp, Spec, Adj, Done, Fail
    SyntaxState = None
from collections import Iterable, defaultdict, Counter
from pathlib import Path
import time
WEAVE = True

DATA_PATH = Path(__file__).parent.absolute() / 'webviewer/data/data.json'


def verify_feature_hosts(const):
    def collect_nodes(node):
        consts.add(node)
        if node.parts:
            for child in node.parts:
                collect_nodes(child)
        else:
            roots.add(node)

    consts = set()
    roots = set()
    collect_nodes(const)
    for const in consts:
        for f0, f1 in const.checked_features:
            if f0.host not in roots:
                print(f'{f0.host} at {f0} is missing from {roots}')
                print('can be found in consts: ', f0.host in consts)
            if f1.host not in roots:
                print(f'{f1.host} at {f1} is missing from {roots}')
                print('can be found in consts: ', f1.host in consts)
        for f in const.inherited_features:
            if f.host not in roots:
                print(f'{f.host} at {f} is missing from {roots}')
                print('can be found in consts: ', f.host in consts)
        for f in const.features:
            if f.host not in roots:
                print(f'{f.host} at {f} is missing from {roots}')
                print('can be found in consts: ', f.host in consts)


def is_positive(feat):
    return feat.sign == '' or feat.sign == '*'


def strictly_in(feat, feats):
    for f in feats:
        if feat is f:
            return True


def include_kataja_data(nodes):
    for node in nodes:
        reset_features(node)
    for node in nodes:
        mark_features(node)


def reset_features(node):
    done = set()

    def _reset_features(n):
        if n in done:
            return
        done.add(n)
        n.inherited_features = []
        for feat in n.features:
            feat.checked_by = None
            feat.checks = None
        for part in n.parts:
            _reset_features(part)

    _reset_features(node)


def is_or_in(node, other):
    return node and (node == other or (isinstance(node, Iterable) and [n for n in node if is_or_in(n, other)]))


def mark_features(top_node):
    done = {}

    def _mark_features(node):
        if node.uid in done:
            return done[node.uid]
        checked_here = []
        for f1, f2 in node.checked_features:
            if is_positive(f1):
                f1.checks = f2
                f2.checked_by = f1
            else:
                f2.checks = f1
                f1.checked_by = f2
            checked_here.append(f1)
            checked_here.append(f2)
        if node.parts:
            feats = []
            for part in node.parts:
                new_features = _mark_features(part)
                if is_or_in(node.head, part.head):
                    feats += new_features
                elif node.argument and is_or_in(node.argument.head, part.head):
                    feats += filter_strong(new_features)
        else:
            feats = list(node.features)
        node.inherited_features = [f for f in feats if f not in checked_here]
        done[node.uid] = node.inherited_features
        return node.inherited_features

    _mark_features(top_node)


class Exporter:
    def __init__(self, forest):
        self.forest = forest
        self.exported_ops = []
        self.route_items_to_consts = {}
        self.roots = {}
        self.c_counter = 0
        self.web = Web() if WEAVE else None

    def reset(self):
        self.exported_ops = []
        self.roots = {}
        self.route_items_to_consts = {}
        self.c_counter = 0
        if self.web:
            self.web.reset()

    @staticmethod
    def rehost_features(const):
        for feat in const.features:
            feat.host = const

    def _head_chain_to_consts(self, route_item, heads, branches):
        def create_keystring(const_):
            if getattr(const_.keystring, ''):
                return const_.keystring
            const_.keystring = [create_keystring(part) for part in const_.parts] if const_.parts else const_.uid

        def find_add(starting_ri):
            ri = starting_ri
            while ri:
                if ri.operation.state_type is ADD and ri.operation.head is starting_ri.operation.head:
                    return ri
                ri = ri.parent

        operation = route_item.operation
        if operation.head in branches:
            const = branches[operation.head]
            if isinstance(const, str):
                print('looping structure at ', operation)
                const = Constituent(f'loop: {get_label(operation.head)}')
                const.long_key = f'loop:{operation.uid}'
                const.original_head = operation.head
                self.c_counter += 1
                route_item.const = const
                return const
            return branches[operation.head]
        branches[operation.head] = 'loop'  # loops can be detected by trying to access this in sub branch, before the
        # branch is completed and this replaced with proper constituent
        #print('parts: ', heads[operation.head])
        const = None
        specs, adjs, comps = heads[operation.head]
        if adjs:
            for adj_item in adjs:
                head0, head1 = adj_item.operation.head
                head_item0 = adj_item.parent.find_closest_head(head0)
                head_item1 = adj_item.parent.find_closest_head(head1)
                adj0 = self._head_chain_to_consts(head_item0, heads, branches)
                adj1 = self._head_chain_to_consts(head_item1, heads, branches)
                long_key = f'A{adj0.long_key}{adj1.long_key}'
                if long_key in self.route_items_to_consts:
                    const = self.route_items_to_consts[long_key]
                else:
                    const = Constituent(f'{adj0.label}+{adj1.label}', parts=[adj0, adj1], head=(adj0.head, adj1.head))
                    const.long_key = long_key
                    const.path = adj_item.path
                    self.route_items_to_consts[long_key] = const
                    adj_item.const = const
                    const.original_head = adj_item.operation.head
                    self.c_counter += 1
        else:
            add_item = find_add(route_item)
            add_op = add_item.operation
            long_key = add_op.uid
            if add_op.uid in self.roots:
                const = self.roots[add_op.uid]
                route_item.const = const
            else:
                const = Constituent(add_op.get_head_label(), features=list(add_op.head.features))
                const.long_key = long_key
                const.path = add_item.path
                self.c_counter += 1
                self.roots[add_op.uid] = const
                const.original_head = add_op.head
                add_item.const = const
            self.rehost_features(const)
        for spec_item in specs:
            arg = self._head_chain_to_consts(spec_item.find_arg_item(), heads, branches)
            long_key = f'S{arg.long_key}{const.long_key}'
            spec_item.long_key = long_key
            if long_key in self.route_items_to_consts:
                const = self.route_items_to_consts[long_key]
            else:
                const = Constituent(const.label, parts=[arg, const], checked_features=spec_item.operation.checked_features,
                                    argument=arg, head=const.head)
                const.long_key = long_key
                const.path = spec_item.path
                self.route_items_to_consts[long_key] = const
                const.original_head = spec_item.operation.head
                spec_item.const = const
                self.c_counter += 1
        for comp_item in comps:
            arg = self._head_chain_to_consts(comp_item.find_arg_item(), heads, branches)
            long_key = f'C{const.long_key}{arg.long_key}'
            comp_item.long_key = long_key
            if long_key in self.route_items_to_consts:
                const = self.route_items_to_consts[long_key]
            else:
                const = Constituent(const.label, parts=[const, arg],
                                    checked_features=comp_item.operation.checked_features,
                                    argument=arg, head=const.head)
                const.long_key = long_key
                const.path = comp_item.path
                self.route_items_to_consts[long_key] = const
                comp_item.const = const
                const.original_head = comp_item.operation.head
                self.c_counter += 1
        branches[operation.head] = const
        return const

    def _flat_heads_to_consts(self, heads, free_route_items):
        return [self._head_chain_to_consts(route_item, heads, {}) for route_item in free_route_items]

    def to_constituents(self, route):
        def remove_head(route_items, head):
            return [route_item for route_item in route_items if route_item.operation.head is not head]

        def replace_head(route_items, replacement):
            replacement_head = replacement.operation.head
            return [replacement if route_item.operation.head is replacement_head else route_item
                    for route_item in route_items]

        heads = {}
        free_route_items = []
        for route_item in route:
            operation = route_item.operation
            if type(operation) is Add:
                heads[operation.head] = ([], [], [])
                free_route_items.append(route_item)
            elif type(operation) is Spec:
                specs, adjs, comps = heads[operation.head]
                specs.append(route_item)
                free_route_items = remove_head(free_route_items, operation.arg)
                free_route_items = replace_head(free_route_items, route_item)
            elif type(operation) is Comp:
                specs, adjs, comps = heads[operation.head]
                comps.append(route_item)
                free_route_items = remove_head(free_route_items, operation.arg)
                free_route_items = replace_head(free_route_items, route_item)
            elif type(operation) is Adj:
                specs, adjs, comps = heads.get(operation.head, ([], [], []))
                adjs.append(route_item)
                heads[operation.head] = specs, adjs, comps
                free_route_items = remove_head(free_route_items, operation.head[0])
                free_route_items = remove_head(free_route_items, operation.head[1])
                free_route_items.append(route_item)
            if not route_item.consts:
                if not free_route_items:
                    print('no free route items at route item ', route_item)
                route_item.consts = self._flat_heads_to_consts(heads, free_route_items)
        #print('open comps at end: ', open_comps)
        #print(f'{self.c_counter=}')

    def find_closest_const(self, head, consts):
        def _find_const(const):
            if const.original_head is head:
                return const
            for part in const.parts:
                found = _find_const(part)
                if found:
                    return found

        for top in reversed(consts):
            found_const = _find_const(top)
            if found_const:
                return found_const

    def export_to_kataja(self, route_ends):
        routes = [op.as_route() for op in route_ends]

        if WEAVE:
            self.web.weave_in(routes)
        routes.sort()
        if self.forest:
            t = time.time()
            paths = set()
            paths_n = 0
            for full_route in routes:
                self.to_constituents(full_route)

            for full_route in routes:
                parent_path = ''
                route = []
                for route_item in full_route:
                    route.append(route_item)
                    operation = route_item.operation
                    if route_item.path in paths:
                        parent_path = route_item.path
                        continue
                    paths_n += 1
                    paths.add(route_item.path)
                    include_kataja_data(route_item.consts)
                    #for const in consts:
                    #     verify_feature_hosts(const) # <-- this is for debugging purposes only, can be commented away
                    groups = []

                    if route_item.path and type(operation) is not Done and type(operation) is not Fail:
                        last_const = self.find_closest_const(route_item.operation.head, route_item.consts)
                        groups = [('last', [last_const])]
                        local_head_consts = []
                        free_head_consts = []
                        local_heads = route_item.local_heads
                        if len(local_heads) < 2 and route_item.parent:
                            local_heads = route_item.parent.local_heads

                        for precedent_item in local_heads:
                            local_head_consts.append(self.find_closest_const(precedent_item.operation.head, route_item.consts))
                        for precedent_item in route_item.free_heads:
                            free_head_consts.append(self.find_closest_const(precedent_item.operation.head, route_item.consts))

                        #heads = [ri.operation.get_head_label() for ri in route_item.free_precedents]
                        #assert len(heads) == len(set(heads))
                        #assert route_item.operation.head not in heads
                        groups.append(('free', free_head_consts))
                        groups.append(('local', local_head_consts))
                        if route_item.parent:
                            parent_const = self.find_closest_const(route_item.parent.operation.head, route_item.consts)
                            groups.append(('parent', [parent_const]))

                    arg = f', {repr(operation.get_arg_label())}' if operation.arg else ''
                    #ld = ', long_distance=True' if route_item.long_distance else ''
                    ld = ''
                    checked = f', {operation.checked_features}' if operation.checked_features else ''

                    msg = f"{paths_n}. {operation.__class__.__name__}({repr(operation.get_head_label())}{arg}{checked}{ld})"
                    syn_state = SyntaxState(tree_roots=route_item.consts, msg=msg, state_id=route_item.path, parent_id=parent_path,
                                            groups=groups, state_type=operation.state_type, sort_order=paths_n)
                    #print('exported consts ', [const.as_string(with_id=True) for const in route_item.consts])
                    self.forest.add_step(syn_state)
                    parent_path = route_item.path

            print(f'exporting {len(routes)} routes with {len(paths)} different path parts took {time.time() - t} seconds')

    def save_as_json(self):
        if WEAVE:
            self.web.save_as_json(DATA_PATH)
