try:
    from plugins.TreesAreMemory3.Constituent import Constituent
    from plugins.TreesAreMemory3.WebWeaver import Web
    from kataja.syntax.SyntaxState import SyntaxState
    from plugins.TreesAreMemory3.route_utils import *
    from plugins.TreesAreMemory3.operations import Add, Comp, Spec, Adj, Done, Fail
    from plugins.TreesAreMemory3.RouteItem import RouteItem
    from plugins.TreesAreMemory3.HeadTrees import HeadTrees
except ImportError:
    from Constituent import Constituent
    from WebWeaver import Web
    from route_utils import *
    from operations import Add, Comp, Spec, Adj, Done, Fail
    from RouteItem import RouteItem
    from HeadTrees import HeadTrees
    SyntaxState = None
from collections.abc import Iterable
from collections import defaultdict, Counter
from pathlib import Path
import time
WEAVE = False

DATA_PATH = Path(__file__).parent.absolute() / 'webviewer/data/data.json'


class Exporter:
    def __init__(self, forest):
        self.forest = forest
        self.exported_ops = []
        self.route_items_to_consts = {}
        self.route_items_to_head_trees = {}
        self.roots = {}
        self.c_counter = 0
        self.branches = {}
        self.path_counter = 0
        self.web = Web() if WEAVE else None

    def reset(self):
        self.exported_ops = []
        self.roots = {}
        self.route_items_to_consts = {}
        self.c_counter = 0
        self.branches = {}
        self.path_counter = 0
        if self.web:
            self.web.reset()

    def find_closest_const(self, head, consts):
        def _find_const(const):
            if const.head is head:
                return const
            elif getattr(const, 'original_head', None) is head:
                return const
            for part in const.parts:
                found = _find_const(part)
                if found:
                    return found

        for top in reversed(consts):
            found_const = _find_const(top)
            if found_const:
                return found_const

    def save_as_json(self):
        if WEAVE:
            self.web.save_as_json(DATA_PATH)

    def routes_to_constituents_ffs(self, route_item: RouteItem):
        route_item.head_trees = HeadTrees(route_item, self.route_items_to_head_trees, self.route_items_to_consts)
        route_item.consts = [head_tree.const for head_tree in route_item.head_trees.trees]
        for child in route_item.children:
            self.routes_to_constituents(child)

    def replace_heads_with_highest(self, route_item: RouteItem):

        trees = route_item.consts
        done = set()

        def _find_higher_head_in_tree(_const, node):
            if node in done or _const is node:
                return
            if node.parts:
                if _const.head is node.head or (isinstance(node.head, tuple) and _const.head in node.head):
                    return node
                elif found := _find_higher_head_in_tree(_const, node.parts[0]):
                    return found
                elif found := _find_higher_head_in_tree(_const, node.parts[1]):
                    return found

        def _find_higher_head_in_trees(_const):
            for tree in trees:
                if node := _find_higher_head_in_tree(_const, tree):
                    return node

        def _find_higher_head_in_new_trees(_const):
            for tree in new_trees:
                if get_label(tree.head) == get_label(_const.head):
                    return tree

        def _rebuild(old_const):
            #if old_const in done:
            #    #print('old const done already ', old_const)
            #    return old_const
            done.add(old_const)
            print('rebuilding ', old_const.head, id(old_const.head), ' with new trees ', new_trees,
                  [(x.head, id(x.head)) for x in new_trees])
            if found := _find_higher_head_in_trees(old_const):
                print('found higher head ', found, ' for const ', old_const)
                const = _rebuild(found)
                print('returning rebuilt const ', const)
            elif found := _find_higher_head_in_new_trees(old_const):
                print('found head from new trees: ', found, ' for const ', old_const)
                const = found
                new_trees.remove(found)
            elif old_const.parts:
                parts = [_rebuild(part) for part in old_const.parts]
                #print('doing merge with ', parts)
                const = Constituent(old_const.label, parts=parts)
                #print('v merged const ', const)
                const.contained_feats = dict(old_const.contained_feats)
                const.checked_features = list(old_const.checked_features)
                const.inherited_features = list(old_const.inherited_features)
            else:
                #print('returning atomic const ', old_const)
                const = old_const
            return const

        new_trees = []
        for const in route_item.consts:
            if const not in done and const.parts:
                new_trees.append(_rebuild(const))
        print('consts:', [t.print_tree() for t in trees])
        print('new trees:', [t.print_tree() for t in new_trees])
        route_item.consts = new_trees

    def replace_heads_with_highest_old(self, route_item: RouteItem):
        topmost_heads = {}

        def _replace_heads_with_highest(_const):
            if _const.left:
                if _const.left.head in topmost_heads and _const.head is not _const.left.head:
                    topmost = topmost_heads[_const.left.head]
                    print('replacing: ', _const.left, topmost)
                    del topmost_heads[_const.left.head]
                    _const.parts = [topmost, _const.right]
                    print(_const.print_tree())
                    if topmost in route_item.consts:
                        route_item.consts.remove(topmost)
                _replace_heads_with_highest(_const.left)
            if _const.right:
                if _const.right.head in topmost_heads and _const.head is not _const.right.head:
                    topmost = topmost_heads[_const.right.head]
                    print('replacing: ', _const.right, topmost)
                    del topmost_heads[_const.right.head]
                    _const.parts = [_const.left, topmost]
                    print(_const.print_tree())
                    if topmost in route_item.consts:
                        route_item.consts.remove(topmost)
                _replace_heads_with_highest(_const.right)

        for const in reversed(route_item.consts):
            if const.head not in topmost_heads:
                topmost_heads[const.head] = const
        print(route_item.consts)
        print(topmost_heads)
        for const in route_item.consts:
            if const.parts:
                _replace_heads_with_highest(const)
                break
        print('done replacing with highest')
        print(route_item.consts)


    def routes_to_constituents(self, route_item: RouteItem):
        # def _replace_upwards(old, new, parents):
        #     for const in reversed(parents):
        #         if const.parts:
        #             left, right = const.parts
        #             if left is old:
        #                 left = new
        #             elif right is old:
        #                 right = new
        #             print('replacing ', old.long_key, ' with ', new.long_key)
        #             long_key = const.long_key.replace(old.long_key, new.long_key)
        #             if long_key in self.branches:
        #                 new_const = self.branches[long_key]
        #             else:
        #                 new_const = Constituent(label=const.label, features=const.features, checked_features=const.checked_features, parts=[left, right])
        #                 new_const.long_key = long_key
        #                 new_const.original_head = const.original_head
        #                 new_const.contained_feats = left.contained_feats | right.contained_feats
        #                 self.branches[long_key] = new_const
        #             old = const
        #             new = new_const
        #     return new
        #
        # def _replace_first(old, new, node, parents):
        #     parents.append(node)
        #     if node.parts:
        #         if node.parts[1] is old:
        #             #print('find it at depth ', len(parents))
        #             return _replace_upwards(old, new, parents)
        #         elif new_top := _replace_first(old, new, node.parts[1], list(parents)):
        #             return new_top
        #         elif node.parts[0] is old:
        #             return _replace_upwards(old, new, parents)
        #         elif new_top := _replace_first(old, new, node.parts[0], list(parents)):
        #             return new_top
        #
        # def replace_first(old, new, consts):
        #     for i, const in reversed(list(enumerate(consts))):
        #         if const is old:
        #             consts[i] = new
        #             #print(f'replaced top {old.as_string()} with {new.as_string()}')
        #             #print([c.as_string() for c in consts])
        #             return True
        #         elif new_top := _replace_first(old, new, const, []):
        #             consts[i] = new_top
        #             return True
        def replace_parts_with_merged(left, right, merged, consts):
            if left in consts:
                consts.remove(left)
            if right in consts:
                consts.remove(right)
            consts.append(merged)

        def create_constituent(op):
            const = Constituent(op.get_head_label(), features=list(op.head.features))
            const.contained_feats = dict((f, []) for f in op.head.features)
            const.long_key = op.uid
            const.original_head = op.head
            self.branches[const.long_key] = const
            return const

        route_item.consts = list(route_item.parent.consts) if route_item.parent else []
        op = route_item.operation
        #print([c.as_string() for c in route_item.consts])
        if type(op) is Add:
            long_key = route_item.operation.uid
            if long_key in self.branches:
                #print(f'(add) found existing long_key "{long_key}" in branches: ', self.branches[long_key])
                route_item.const = self.branches[long_key]
                route_item.long_key = long_key
            else:
                if op.complex_parts:
                    if op is op.complex_parts[0]:
                        merged = None
                        for part in op.complex_parts:
                            const = create_constituent(part)
                            const.is_highest = True
                            if merged:
                                merged.is_highest = False
                                merged = Constituent(merged.label, parts=[merged, const], head=merged.head)
                                merged.is_highest = True
                                merged.contained_feats = merged.parts[0].contained_feats | merged.parts[1].contained_feats
                                merged.inherited_features = merged.parts[0].inherited_features
                                merged.long_key = f'{merged.parts[0].long_key}|{merged.parts[1].long_key}'
                                merged.original_head = op.head
                                self.branches[long_key] = merged
                            else:
                                merged = const
                        route_item.const = merged
                        route_item.long_key = route_item.const.long_key
                        #print(f'(add complex) creating for long_key "{long_key}", in branches: ',
                        #      self.branches[long_key])
                else:
                    route_item.const = create_constituent(op)
                    route_item.long_key = route_item.const.long_key
                    route_item.const.is_highest = True
                    #print(f'(add simple) creating for long_key "{long_key}", in branches: ', self.branches[long_key])

            route_item.consts.append(route_item.const)
        elif type(op) is Adj:
            head0, head1 = op.head
            head_item0 = route_item.parent.find_closest_head(head0)
            head_item1 = route_item.parent.find_closest_head(head1)
            assert head_item1 is route_item.parent
            long_key = f'({head_item0.long_key}+{head_item1.long_key})'
            adj0 = head_item0.const
            adj1 = head_item1.const
            if long_key not in self.branches:
                merged = Constituent(f'{adj0.label}+{adj1.label}', parts=[adj0, adj1], head=(adj0.head, adj1.head))
                merged.long_key = long_key
                merged.original_head = op.head
                merged.inherited_features = route_item.features
                merged.contained_feats = adj0.contained_feats | adj1.contained_feats
                self.branches[long_key] = merged
                #print(f'(adj) creating for long_key "{long_key}", in branches: ', merged)
            route_item.long_key = long_key
            route_item.const = self.branches[long_key]
            replace_parts_with_merged(adj0, adj1, route_item.const, route_item.consts)
        elif type(op) is Comp:
            head_item = route_item.parent.find_closest_head(op.head)
            arg_item = route_item.parent.find_closest_head(op.arg)
            long_key = f'[{head_item.long_key} {arg_item.long_key} {op.checked_features}]'
            if long_key not in self.branches:
                head = head_item.const
                arg = arg_item.const
                merged = Constituent(head.label, parts=[head, arg], checked_features=op.checked_features,
                                     argument=arg, head=head.head)
                merged.long_key = long_key
                merged.original_head = op.head
                merged.is_highest = True
                head.is_highest = False
                merged.contained_feats = head.contained_feats | arg.contained_feats
                for pos, neg in op.checked_features:
                    merged.contained_feats[pos] = merged.contained_feats[pos] + [neg]
                merged.inherited_features = route_item.features
                self.branches[long_key] = merged
                #print(f'(comp) creating for long_key "{long_key}", in branches: ', merged)

            route_item.long_key = long_key
            route_item.const = self.branches[long_key]
            replace_parts_with_merged(head_item.const, arg_item.const, route_item.const, route_item.consts)
        elif type(op) is Spec:
            head_item = route_item.parent.find_closest_head(op.head)
            arg_item = route_item.parent.find_closest_head(op.arg)
            long_key = f'[{arg_item.long_key} {head_item.long_key} {op.checked_features}]'
            if long_key not in self.branches:
                head = head_item.const
                arg = arg_item.const
                merged = Constituent(head.label, parts=[arg, head], checked_features=op.checked_features,
                                     argument=arg, head=head.head)
                merged.is_highest = True
                head.is_highest = False
                merged.long_key = long_key
                merged.contained_feats = head.contained_feats | arg.contained_feats
                for pos, neg in op.checked_features:
                    merged.contained_feats[pos] = merged.contained_feats[pos] + [neg]
                merged.inherited_features = route_item.features
                merged.original_head = op.head
                self.branches[long_key] = merged
                #print(f'(spec) creating for long_key "{long_key}", in branches: ', merged)

            #replace_first(arg_item.const, route_item.const, route_item.consts)
            route_item.long_key = long_key
            route_item.const = self.branches[long_key]
            replace_parts_with_merged(head_item.const, arg_item.const, route_item.const, route_item.consts)
        elif type(op) is Done:
            pass
            self.replace_heads_with_highest(route_item)

        # olisiko joku yksi tapa toimia mergeillä jotka kohdistuvat oikeaan alakulmaan?
        #route_item.head_trees = HeadTrees(route_item, self.route_items_to_head_trees, self.route_items_to_consts)
        if route_item.children:
            for child in route_item.children:
                self.routes_to_constituents(child)

    def export_to_kataja(self, route_ends):
        def set_feature_checks(const):
            for f, checks in const.contained_feats.items():
                f.checks = None
                f.checked_by = None
            for f, checks in const.contained_feats.items():
                for target in checks:
                    f.checks = target
                    target.checked_by = f

        def prepare_groups(route_item):
            groups = []
            if route_item.consts and route_item.const:
                groups.append(('current', [route_item.const]))
            local_head_consts = []
            available_head_consts = []
            local_heads = route_item.local_heads
            # if len(local_heads) < 2:
            #     ri = route_item.parent
            #     while ri and ri.head is route_item.head:
            #         ri = ri.parent
            #     if ri:
            #         local_heads = ri.local_heads

            for precedent_item in local_heads:
                if precedent_item is not route_item:
                    local_head_consts.append(self.find_closest_const(precedent_item.operation.head, route_item.consts))
            for precedent_item in route_item.available_heads:
                if precedent_item is not route_item:
                    available_head_consts.append(self.find_closest_const(precedent_item.operation.head, route_item.consts))

            #heads = [ri.operation.get_head_label() for ri in route_item.free_precedents]
            #assert len(heads) == len(set(heads))
            #assert route_item.operation.head not in heads
            groups.append(('available', available_head_consts))
            groups.append(('local', local_head_consts))
            #if route_item.parent:
            #    parent_const = self.find_closest_const(route_item.parent.operation.head, route_item.consts)
            #    groups.append(('parent', [parent_const]))
            return groups

        def export_route_items(route_item):
            self.path_counter += 1
            for const in route_item.consts:
                set_feature_checks(const)
            groups = prepare_groups(route_item)
            parent_path = route_item.parent and route_item.parent.path
            op = route_item.operation
            arg = f', {repr(op.get_arg_label())}' if op.arg else ''
            checked = f', {op.checked_features}' if op.checked_features else ''
            msg = f"{paths_n}. {op.__class__.__name__}({repr(op.get_head_label())}{arg}{checked})"
            #print('*** exporting syntactic state *** ', route_item.path)
            #for const in route_item.consts:
            #    print('exporting root ', const, const.parts)
            syn_state = SyntaxState(tree_roots=route_item.consts, msg=msg, state_id=route_item.path, parent_id=parent_path,
                                    groups=groups, state_type=op.state_type, sort_order=self.path_counter)
            self.forest.add_step(syn_state)
            self.forest.undo_manager.take_snapshot(str(route_item.path))
            for child in route_item.children:
                export_route_items(child)

        t = time.time()
        self.branches = {}
        self.path_counter = 0
        route_root = route_ends[0]
        while route_root.parent:
            route_root = route_root.parent
        # kun kulkee yhden routen loppuun, on ehtinyt muokata const:n sen valmiiksi versioksi. Siinä on liikaa tavaraa.
        # kun const haetaan varastosta, se pitää hakea ilman lapsia ja muuta käsittelyä.
        # jos meillä on haara jossa on const A jolla on lapsia niin ei voi olla yhtäaikaa eri versioita samasta A:sta, joista
        # jollakin on lapsia ja toisilla ei. Toisaalta tälle ei pitäisikään olla tarvetta jos tehdään vain mergellä.
        self.routes_to_constituents(route_root)
        #print(f'created {len(self.branches)} constituents')
        #print(f'it took {time.time() - t} seconds')
        if WEAVE:
            routes = [op.as_route() for op in route_ends]
            self.web.weave_in(routes)
        if self.forest:
            paths_n = 0
            route_item = route_root
            export_route_items(route_item)
            #print('branches: ', self.branches)

            print(f'exporting {len(route_ends)} routes with {self.path_counter} different path parts took {time.time() - t} seconds')
