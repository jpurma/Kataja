try:
    from plugins.TreesAreMemory2.Constituent import Constituent
    from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
    from plugins.TreesAreMemory2.WebWeaver import Web
    from kataja.syntax.SyntaxState import SyntaxState
    from plugins.TreesAreMemory2.route_utils import *
except ImportError:
    from SimpleConstituent import SimpleConstituent
    from Constituent import Constituent
    from WebWeaver import Web
    from route_utils import *
    SyntaxState = None
from collections import Iterable
import time
WEAVE = False

DATA_PATH = 'webviewer/data/data.json'


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


def include_kataja_data(node):
    reset_features(node)
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
        self.exported_states = []
        self.states_as_const = {}
        self.roots_for_states = {}
        self.web = Web() if WEAVE else None

    def reset(self):
        self.exported_states = []
        self.states_as_const = {}
        self.roots_for_states = {}
        if self.web:
            self.web.reset()

    @staticmethod
    def rehost_features(const):
        for feat in const.features:
            feat.host = const

    def get_const(self, path):
        return self.states_as_const[path]

    def set_const(self, path, const):
        self.states_as_const[path] = const

    def to_constituents(self, route):
        def features_have_host(c):
            for f0, f1 in c.checked_features:
                if not (f0.host and f1.host):
                    print('missing host at checked features: ', f0, id(f0), f0.host, f1, id(f1), f1.host, c)
                    return False
            for f in c.features:
                if not f.host:
                    print('missing host for feature: ', f, id(f))
                    return False
            return True

        steps = []
        original_heads = {}
        recent_heads = {}
        prev_const = None
        const = None
        passed_route = []
        path = ''
        for route_item in route:
            state = route_item.state
            passed_route.append(route_item)
            last_path = path
            path = make_path(passed_route)
            if path in self.states_as_const:
                const = self.get_const(path)
            elif state.state_type == state.ADD:
                if state.state_id in self.roots_for_states:
                    const = self.roots_for_states[state.state_id]
                else:
                    const = Constituent(state.head.label, features=list(state.head.features))
                    self.roots_for_states[state.state_id] = const
                self.rehost_features(const)
                original_heads[state.head.uid] = const
                if prev_const and prev_const.head:
                    const = Constituent(const.label, parts=[prev_const, const], head=const.head)
                assert features_have_host(const)
                self.set_const(path, const)
            elif state.state_type == state.RAISE_ARG:
                route_to_look = passed_route[:-1]
                if not route_item.long_distance:
                    precedent_ri = get_free_precedent_from_route(route_to_look)
                    if precedent_ri:
                        route_to_look = passed_route[:passed_route.index(precedent_ri) + 1]
                arg_ri = find_route_item_with_features([fpos for fpos, fneg in state.checked_features], route_to_look)
                assert arg_ri
                arg_path = make_path(passed_route[:passed_route.index(arg_ri) + 1])
                arg = self.get_const(arg_path)
                head = self.get_const(last_path)
                const = Constituent(head.label, parts=[arg, head], checked_features=state.checked_features,
                                    argument=arg, head=head.head)
                assert features_have_host(const)
                self.set_const(path, const)
            elif state.state_type == state.CLOSE_ARG:
                route_to_look = passed_route[:-1]
                if not route_item.long_distance:
                    precedent_ri = get_free_precedent_from_route(route_to_look)
                    if precedent_ri:
                        route_to_look = passed_route[:passed_route.index(precedent_ri) + 1]
                head_ri = find_route_item_with_features([fneg for fpos, fneg in state.checked_features], route_to_look)
                assert head_ri
                head_path = make_path(passed_route[:passed_route.index(head_ri) + 1])
                head = self.get_const(head_path)
                arg = self.get_const(last_path)
                const = Constituent(head.label, parts=[head, arg], checked_features=state.checked_features,
                                    argument=arg, head=head.head)
                assert features_have_host(const)
                self.set_const(path, const)
            elif state.state_type == state.ADJUNCT:
                precedent_ri = get_free_precedent_from_route(passed_route[:-1])
                head_path1 = make_path(passed_route[:passed_route.index(precedent_ri)+1])
                head_path2 = make_path(passed_route[:-1])
                head1 = self.get_const(head_path1)
                head2 = self.get_const(head_path2)
                const = Constituent(f'{head1.label}+{head2.label}', parts=[head1, head2], head=(head1.head, head2.head))
                self.set_const(path, const)
            elif state.head:
                const = recent_heads[state.get_head_uid()]
                self.set_const(path, const)
            recent_heads[state.get_head_uid()] = const
            steps.append((const, state, path))
            prev_const = const
        return steps

    def add_route(self, state):
        if self.web:
            self.web.add_route(state)

    def export_to_kataja(self, routes):
        if WEAVE:
            self.web.weave_in(routes)

        if self.forest:
            const_routes = [self.to_constituents(route) for route in routes]
            t = time.time()
            paths = set()
            paths_n = 0
            for ri_route, const_route in zip(routes, const_routes):
                parent_path = ''
                route = []
                for route_item, (const, state, path) in zip(ri_route, const_route):
                    route.append(route_item)
                    if path in paths:
                        parent_path = path
                        continue
                    paths_n += 1
                    paths.add(path)
                    include_kataja_data(const)
                    #verify_feature_hosts(const) # <-- this is for debugging purposes only, can be commented away
                    groups = []

                    if path and state.state_type != state.DONE_SUCCESS and state.state_type != state.DONE_FAIL:
                        groups = [('', [const])]
                        precedent_ri = get_free_precedent_from_route(route)
                        if precedent_ri:
                            precedent_key = make_path(route[:route.index(precedent_ri) + 1])
                            groups.append(('', [self.get_const(precedent_key)]))
                        else:
                            groups.append(('', []))
                    arg = f', {state.get_arg_label()}' if state.arg_ else ''
                    ld = ' (long distance)' if route_item.long_distance else ''

                    msg = f'{state.entry} ({state.get_head_label()}{arg}){ld}'
                    syn_state = SyntaxState(tree_roots=[const], msg=msg, state_id=path, parent_id=parent_path,
                                            groups=groups, state_type=state.state_type)
                    #print([const.full_tree(), state.entry, path, parent_path, groups, state.state_type])
                    self.forest.add_step(syn_state)
                    parent_path = path
            print(f'exporting {len(const_routes)} routes with {len(paths)} different paths parts took {time.time() - t} seconds')

    def save_as_json(self):
        if WEAVE:
            self.web.save_as_json(DATA_PATH)
