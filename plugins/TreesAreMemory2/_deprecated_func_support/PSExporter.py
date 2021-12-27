#try:
from plugins.TreesAreMemory2.Constituent import Constituent
from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
from plugins.TreesAreMemory2.WebWeaver import Web
from plugins.TreesAreMemory2.Exporter import *
from kataja.syntax.SyntaxState import SyntaxState
from plugins.TreesAreMemory2.route_utils import *
# except ImportError:
#     from SimpleConstituent import SimpleConstituent
#     from Exporter import *
#     from Constituent import Constituent
#     from WebWeaver import Web
#     from route_utils import *
#     SyntaxState = None
from collections import Iterable
import time
WEAVE = False


class PSExporter(Exporter):
    """ Exports parses as if treelets are built in separate workspaces before merging.
     It results in linearization problems, or requiring a different reading for linearization, but trees are simpler and
     more compatible with other parsers.
     """

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
        passed_route = []
        path = ''
        for operation in route:
            state = operation.state
            passed_route.append(operation)
            last_path = path
            path = make_path(passed_route)
            if path in self.states_as_const:
                trees = self.get_const(path)
            else:
                if last_path in self.states_as_const:
                    trees = self.get_const(last_path)
                else:
                    trees = []
                if state.state_type == state.ADD:
                    if state.state_id in self.roots_for_states:
                        const = self.roots_for_states[state.state_id]
                    else:
                        const = Constituent(state.head.label, features=list(state.head.features))
                        self.roots_for_states[state.state_id] = const
                    self.rehost_features(const)
                    original_heads[state.head.uid] = const
                    assert features_have_host(const)
                    trees = [const] + trees
                    self.set_const(path, trees)
                elif state.state_type == state.SPECIFIER:
                    arg_path = make_path(passed_route[:passed_route.index(operation.arg_op) + 1])
                    arg = self.get_const(arg_path)[0]
                    head = self.get_const(last_path)[0]
                    const = Constituent(head.label, parts=[arg, head], checked_features=state.checked_features,
                                        argument=arg, head=head.head)
                    trees = list(trees)
                    if arg in trees:
                        trees.remove(arg)
                    trees.remove(head)
                    trees = [const] + trees
                    assert features_have_host(const)
                    self.set_const(path, trees)
                elif state.state_type == state.COMPLEMENT:
                    head_path = make_path(passed_route[:passed_route.index(operation.head_op) + 1])
                    head = self.get_const(head_path)[0]
                    arg = self.get_const(last_path)[0]
                    const = Constituent(head.label, parts=[head, arg], checked_features=state.checked_features,
                                        argument=arg, head=head.head)
                    trees = list(trees)
                    trees.remove(arg)
                    if head in trees:
                        trees.remove(head)
                    trees = [const] + trees
                    assert features_have_host(const)
                    self.set_const(path, trees)
                elif state.state_type == state.ADJUNCT:
                    head_path1 = make_path(passed_route[:passed_route.index(operation.arg_op)+1])
                    head_path2 = make_path(passed_route[:-1])
                    head1 = self.get_const(head_path1)[0]
                    head2 = self.get_const(head_path2)[0]
                    const = Constituent(f'{head1.label}+{head2.label}', parts=[head1, head2], head=(head1.head, head2.head))
                    trees = list(trees)
                    trees.remove(head1)
                    trees.remove(head2)
                    trees = [const] + trees
                    self.set_const(path, trees)
                elif state.head:
                    const = recent_heads[state.get_head_uid()]
                    self.set_const(path, const)
            recent_heads[state.get_head_uid()] = trees
            steps.append((trees, state, path))
        return steps

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
                for operation, (trees, state, path) in zip(ri_route, const_route):
                    route.append(operation)
                    if path in paths:
                        parent_path = path
                        continue
                    paths_n += 1
                    paths.add(path)
                    for const in trees:
                        include_kataja_data(const)
                    #verify_feature_hosts(const) # <-- this is for debugging purposes only, can be commented away
                    groups = []

                    if path and state.state_type != state.DONE_SUCCESS and state.state_type != state.DONE_FAIL:
                        groups = [('', trees[:1])]
                        precedent_op = operation.first_free_precedent()
                        if precedent_op:
                            precedent_key = make_path(route[:route.index(precedent_op) + 1])
                            groups.append(('', self.get_const(precedent_key)[:1]))
                        else:
                            groups.append(('', []))
                    arg = f', {state.get_arg_label()}' if state.arg_ else ''
                    ld = ' (long distance)' if operation.long_distance else ''

                    msg = f'{state.entry} ({state.get_head_label()}{arg}){ld} {path}'
                    syn_state = SyntaxState(tree_roots=trees, msg=msg, state_id=path, parent_id=parent_path,
                                            groups=groups, state_type=state.state_type)
                    #print([const.print_tree(), state.entry, path, parent_path, groups, state.state_type])
                    self.forest.add_step(syn_state)
                    parent_path = path
            print(f'exporting {len(const_routes)} routes with {len(paths)} different paths parts took {time.time() - t} seconds')
