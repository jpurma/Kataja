try:
    from plugins.TreesAreMemory2.Constituent import Constituent
    from plugins.TreesAreMemory2.BarConstituent import BarConstituent
    from plugins.TreesAreMemory2.BarWebWeaver import Web
    from plugins.TreesAreMemory2.BarState import get_free_precedent_from_route
    from kataja.syntax.SyntaxState import SyntaxState
except ImportError:
    from BarConstituent import BarConstituent
    from Constituent import Constituent
    from BarWebWeaver import Web
    from BarState import get_free_precedent_from_route
    SyntaxState = None

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
        node.inherited_features = []
        my_strong_features = [f for f in node.features if f.sign == '*']
        my_head_features = [f for f in node.features if f.sign != '*']
        for part in node.parts:
            strong_features, head_features = _mark_features(part)
            if part.head is node.head or node.argument is part:
                my_strong_features += strong_features
                if part.head is node.head:
                    my_head_features += head_features

        node.inherited_features = my_head_features + my_strong_features
        my_strong_features = [f for f in my_strong_features if not strictly_in(f, checked_here)]
        my_head_features = [f for f in my_head_features if not strictly_in(f, checked_here)]
        done[node.uid] = my_strong_features, my_head_features
        return my_strong_features, my_head_features

    _mark_features(top_node)


def get_all_nodes(const):
    s = []

    def _get_children(c):
        for p in c.parts:
            _get_children(p)
        s.append(c)
    _get_children(const)
    return s


def route_str_from_state(state, route):
    return '_'.join([str(s.state_id) for s in route[:route.index(state) + 1]])


def simple_stack_top_from_route(route):
    pops = []
    for state in reversed(route):
        if state.state_type == state.FROM_STACK:
            pops.append(state)
        elif state.state_type == state.PUT_STACK:
            if pops and state.head is pops[-1].arg_:
                pops.pop()
            else:
                return state


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
        #print('turning to constituents: ', route)
        steps = []
        recent_heads = {}
        prev_const = None
        const = None
        passed_route = []
        for state in route:
            passed_route.append(str(state.state_id))
            path = '_'.join(passed_route)
            if path in self.states_as_const:
                const = self.get_const(path)
                #print('using existing path: ', path, const)
            elif state.state_type == state.ADD:
                if state.state_id in self.roots_for_states:
                    const = self.roots_for_states[state.state_id]
                else:
                    const = Constituent(state.head.label, features=list(state.head.features))
                    self.roots_for_states[state.state_id] = const
                #print(f'creating new ADD constituent {const.uid} {const.label} for path {path}')
                self.rehost_features(const)
                if prev_const and prev_const.head:
                    const = Constituent(const.label, parts=[prev_const, const], head=const.head)
                self.set_const(path, const)
            elif state.state_type == state.RAISE_ARG:
                arg = recent_heads[state.arg_.uid]
                head = recent_heads[state.head.uid]
                #print(f'creating new RAISE_ARG constituent for path {path}')
                const = Constituent(head.label, parts=[arg, head], checked_features=state.checked_features,
                                    argument=arg, head=head.head)
                self.set_const(path, const)
            elif state.state_type == state.CLOSE_ARG:
                arg = recent_heads[state.arg_.uid]
                head = recent_heads[state.head.uid]
                #print(f'creating new CLOSE_ARG constituent for path {path}')
                const = Constituent(head.label, parts=[head, arg], checked_features=state.checked_features,
                                    argument=arg, head=head.head)
                self.set_const(path, const)
            elif state.state_type == state.FROM_STACK:
                arg = recent_heads[state.arg_.uid]
                head = recent_heads[state.head.uid]
                #print(f'creating new FROM_STACK constituent for path {path}')
                const = Constituent(head.label, parts=[arg, head], checked_features=state.checked_features,
                                    argument=arg, head=head.head)
                self.set_const(path, const)
            elif state.state_type == state.PUT_STACK:
                #print(f'using existing constituent for PUT_STACK at path {path}')
                const = recent_heads[state.head.uid]
                self.set_const(path, const)

            elif state.head:
                const = recent_heads[state.head.uid]
                self.set_const(path, const)
            recent_heads[state.head.uid] = const
            steps.append((const, state, path))
            prev_const = const
        return steps

    def simple_export(self, const, message):
        if self.forest:
            # print('iteration ', iteration, ' : ', message)
            include_kataja_data(const)
            syn_state = SyntaxState(tree_roots=[const], msg=message)
            self.forest.add_step(syn_state)

    def add_route(self, state):
        if self.web:
            self.web.add_route(state)

    def export_to_kataja(self, routes):
        if WEAVE:
            self.web.weave_in(routes)

        if self.forest:
            const_routes = [self.to_constituents(route) for route in routes]
            print(const_routes)
            #print(len(self.states_as_const))
            #print('--------')
            t = time.time()
            paths = set()
            paths_n = 0
            for const_route in const_routes:
                parent_path = ''
                route = []
                for const, state, path in const_route:
                    route.append(state)
                    if path in paths:
                        parent_path = path
                        continue
                    paths_n += 1
                    paths.add(path)
                    include_kataja_data(const)
                    #verify_feature_hosts(const) # <-- this is for debugging purposes only, can be commented away

                    if path and state.state_type != state.DONE_SUCCESS and state.state_type != state.DONE_FAIL:
                        groups = [('', [const])]
                        precedent_state = get_free_precedent_from_route(route, [])
                        if precedent_state:
                            precedent_key = route_str_from_state(precedent_state, route)
                            groups.append(('', [self.get_const(precedent_key)]))
                        else:
                            groups.append(('', []))
                        stack_state = simple_stack_top_from_route(route)
                        if stack_state:
                            stack_top_key = route_str_from_state(stack_state, route)
                            groups.append(('', [self.get_const(stack_top_key)]))
                    else:
                        groups = []

                    if state.arg_:
                        msg = f'{state.entry} ({state.head.label}, {state.arg_.label})'
                    else:
                        msg = f'{state.entry} ({state.head.label})'
                    # if state.stack:
                    #    groups.append(('', [self.get_const(state.stack[-1])]))
                    syn_state = SyntaxState(tree_roots=[const], msg=msg, state_id=path, parent_id=parent_path,
                                            groups=groups, state_type=state.state_type)
                    #print([const.full_tree(), state.entry, path, parent_path, groups, state.state_type])
                    self.forest.add_step(syn_state)
                    parent_path = path
            print(f'exporting {len(paths)} ({paths_n}) took {time.time() - t} seconds')

    def show_const(self, state, linear):
        const = self.to_constituent(state)
        #self.simple_export(const, linear)
        print('as binary const: ', const)

    def save_as_json(self):
        if WEAVE:
            self.web.save_as_json(DATA_PATH)
