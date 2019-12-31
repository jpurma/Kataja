try:
    from SpreadNet.XBar import XBar
    from SpreadNet.Feature import Feature
    from kataja.syntax.SyntaxState import SyntaxState
    from kataja.saved.DerivationStep import DerivationStep
except ImportError:
    from XBar import XBar
    from Feature import Feature
import json
import time

REMOVE_BAD_PARSES = True

CONST_EDGE = 1
SPEC_MATCH = 2
COMP_MATCH = 3
OTHER_MATCH = 4
SPEC_EDGE = 5
COMP_EDGE = 6
OTHER_EDGE = 7
FEATURE = 11
SPEC_FEATURE = 12
COMP_FEATURE = 13


def start_element():
    fstring = ''  # ''-C -T -v'
    feats = [Feature.from_string(fs) for fs in fstring.split()]
    return XBar(label='', features=feats)


def read_lexicon(filename):
    lexicon = {}
    for line in open(filename):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        label, foo, fstring = line.partition('::')
        label = label.strip()
        feats = [Feature.from_string(fs) for fs in fstring.split()]
        const = XBar(label=label, features=feats)
        lexicon[label] = const
    return lexicon


#
# def linearize(tree):
#     done = set()
#     result = []
#
#     def _walk_tree(node):
#         if not node or node in done:
#             return
#         done.add(node)
#         if node.parts:
#             for child in node.parts:
#                 _walk_tree(child)
#         elif node.label:
#             result.append(node.label)
#
#     _walk_tree(tree)
#     return result

#
# def _update_check_information_for_features(tree):
#     feature_checks = set()
#     features = set()
#     done = set()
#
#     def walk_tree(node):
#         if node in done:
#             return
#         done.add(node)
#         if node.parts:
#             if node.checker or node.checked:
#                 feature_checks.add((node.checker, node.checked))
#             for part in node.parts:
#                 if part is not node.riser:
#                     walk_tree(part)
#         else:
#             for feature in node.features:
#                 features.add(feature)
#     walk_tree(tree)
#     for feature in features:
#         feature.checked_by = None
#         feature.checks = None
#     for checks, checked_by in feature_checks:
#         if checks:
#             checks.checked_by = checked_by
#         if checked_by:
#             checked_by.checks = checks

class Workspace:
    def __init__(self, parent=None, tree=None, mover=None, riser=None):
        self.parent = parent
        self.tree = tree
        self.mover = mover
        self.riser = riser


class Path:
    def __init__(self, prev=None, head=None, pos=None, neg=None, end=None, mover=None):
        self.head = head
        self.pos = pos
        self.neg = neg
        self.end = end
        self.mover = mover
        self.risers = []
        self.prev = prev

    def __contains__(self, item):
        return (item is self.head
                or item is self.end
                or item is self.pos
                or item is self.neg
                or (self.prev and item in self.prev))

    def __str__(self):
        prefix = f'{self.prev} -> ' if self.prev else ''
        return f'{prefix}({self.head}>{self.neg or ""}>{self.pos or ""}>{self.end or ""})'

    def __repr__(self):
        return f'({self.head},{self.neg or ""},{self.pos or ""},{self.end or ""})'

    def __eq__(self, other):
        return self.head == other.head and self.pos == other.pos and self.neg == other.neg and self.end == other.end

    def __hash__(self):
        return hash(repr(self))

    def __lt__(self, other):
        if other is None:
            return False
        return repr(self) < repr(other)

    def bracketize(self):
        """
            rpl 'rolled' -> [rolled Mary]
            rpl 'rolled' -> [John [rolled Mary]]
            rpl 'the' -> [the hill]
            rpl 'down' -> [down [the hill]]
            rpl 'rolled' -> [[John [rolled Mary]] [down [the hill]]]
        """
        path = [self]
        item = self
        while item.prev:
            path.append(item.prev)
            item = item.prev

        items = {}

        def replace_before(head, before):
            items[head] = [items.get(before, before), items.get(head, head)]

        def replace_after(head, after):
            items[head] = [items.get(head, head), items.get(after, after)]

        for item in reversed(path):
            if item.neg:
                if item.neg.sign == '-':
                    replace_before(item.head, item.end)
                elif item.neg.sign == '=':
                    replace_after(item.head, item.end)
        return items.get(self.head, self.head)

    def pathlets(self):
        pathlets = set()
        if self.neg and self.pos:
            pathlets.add(self)
        item = self
        while item.prev:
            item = item.prev
            if item and item.neg and item.pos:
                pathlets.add(item)
        return frozenset(pathlets)

    def linearize(self):
        def _linearize(l):
            for item in l:
                if isinstance(item, list):
                    _linearize(item)
                elif item not in done:
                    done.append(item)

        done = []
        _linearize([self.bracketize()])
        return ' '.join(str(x) for x in done)


class Parser:
    def __init__(self, lexicon, forest=None):
        self.forest = forest
        self.processed = []
        self.lexicon = lexicon or {}
        self.good_paths = []
        self.ticks = 0
        self.nodes = 0

    def pick_const(self, item):
        if item in self.lexicon:
            node = self.lexicon[item].copy()
        else:
            node = XBar(label=item)
            self.lexicon[item] = node.copy()
        node.head = node
        return node

    @staticmethod
    def _do_external_merge(const, workspaces):
        # add unjustified merges
        new_workspaces = []
        is_riser = any(f.sign == '*' for f in const.features)
        # if workspaces:
        #     for workspace in workspaces:
        #         tree = Constituent(head=const, end=prev_path.head, mover=prev_path)
        #         new_workspace = Workspace(parent=workspace, tree=tree)
        #         if is_riser:
        #             new_path.risers.append(const)
        #         new_paths.append(new_path)
        # else:
        new_path = Path(head=const)
        new_path.mover = new_path
        if is_riser:
            new_path.risers.append(const)
        new_paths.append(new_path)

        # print(f'external merge "{const}" as head for {len(paths)} paths')
        return new_paths

    def _do_internal_merges(self, path):
        # print(f'Internal merge for path')
        required = []
        optional = []
        if not path.mover:
            # print('no mover available')
            return []
        mover = path.mover.head
        top = path.head
        if mover is top:
            # print('path mover is path head')
            return []
        # print(f'top: "{top}" ({top.features})  mover: "{mover}" ({mover.features})')
        # Spec merges

        for plus_feature in mover.features:
            if plus_feature.sign == '' or plus_feature.sign == '*':
                for neg_feature in top.features:
                    if neg_feature.sign == '-' and neg_feature.name == plus_feature.name and \
                            neg_feature not in path and plus_feature not in path:
                        new_path = Path(prev=path, head=top, neg=neg_feature, pos=plus_feature, end=mover,
                                        mover=path.mover.mover)
                        # print(f'possible relation: head "{top}" has spec "{mover}" due {neg_feature, plus_feature}')
                        if neg_feature.required:
                            required.append(new_path)
                        else:
                            optional.append(new_path)
        # Comp merges
        for plus_feature in top.features:
            if plus_feature.sign == '' or plus_feature.sign == '*':
                for neg_feature in mover.features:
                    if neg_feature.sign == '=' and neg_feature.name == plus_feature.name and \
                            neg_feature not in path and plus_feature not in path:
                        new_path = Path(prev=path, head=mover, neg=neg_feature, pos=plus_feature, end=top,
                                        mover=path.mover.mover)
                        # print(f'possible relation: head "{mover}" has comp "{top}" due {neg_feature, plus_feature}')
                        if neg_feature.required:
                            required.append(new_path)
                        else:
                            optional.append(new_path)

        # raising wh-elements
        if True:
            for riser in list(top.risers):
                for plus_feature in riser.features:
                    if plus_feature.sign == '*':
                        for neg_feature in top.features:
                            # Wh-spec merges
                            if neg_feature.sign == '-' and neg_feature.name == plus_feature.name and \
                                    neg_feature not in path and plus_feature not in path:
                                new_path = Path(prev=path, head=riser, neg=neg_feature, pos=plus_feature, end=top,
                                                mover=path.mover.mover)
                                if neg_feature.required:
                                    required.append(new_path)
                                else:
                                    optional.append(new_path)
                            # Wh-comp merges
                            if neg_feature.sign == '=' and neg_feature.name == plus_feature.name and \
                                    neg_feature not in path and plus_feature not in path:
                                new_path = Path(prev=path, head=riser, neg=neg_feature, pos=plus_feature, end=top,
                                                mover=path.mover.mover)
                                if neg_feature.required:
                                    required.append(new_path)
                                else:
                                    optional.append(new_path)
        if True:
            if required:
                new_paths = required
            else:
                new_paths = optional
        # else:
        #     new_paths = required + optional
        if new_paths:
            # print(f'continue looking for internal merges for heads {new_paths}...')
            for i, path in enumerate(list(new_paths), 1):
                new_paths += self._do_internal_merges(path)
        return new_paths

    def parse(self, sentence):
        """ Parse that is greedy to internal merge. Do internal merge if there would be compatible features w. trunk"""
        # print(f'*** Parsing {sentence}')
        self.good_paths = []
        self.nodes = 0
        if isinstance(sentence, str):
            words = sentence.split()
        else:
            words = list(sentence)
        self.processed = []
        paths = []
        all_paths = set()

        for i, word in enumerate(words, 1):
            const = self.pick_const(word)
            paths = self._do_external_merge(const, paths)
            # add spec and comp merges
            # print(f'{i}. do internal merges for head "{const}"...')
            new_paths = []
            for path in paths:
                new_paths.append(path)
                new_paths += self._do_internal_merges(path)
            paths = new_paths
            for path in paths:
                all_paths.add(path)
            self.processed.append(const)

        succs = []
        brackets = set()
        successes = set()
        fackets = []
        good_pathlets = set()
        pathlet_sets = set()
        for path in paths:
            bracketed = path.bracketize()
            brackets.add(str(bracketed))
            fackets.append(bracketed)
            linear = path.linearize()
            pathlets = path.pathlets()
            if pathlets in pathlet_sets:
                print('pathlets already in pathlet sets: ', pathlets)
                pathlet_sets.add(pathlets)
            pathlet_sets.add(str(sorted(pathlets)))
            if linear == sentence:
                successes.add(str(bracketed))
                succs.append(path)
                p = path
                while p:
                    good_pathlets.add(p)
                    p = p.prev
                print('--------- Path ---------')
                print(path)
                print('--------- Bracketed ---------')
                print(bracketed)
                print('--------- Linearized ---------')
                print(path.linearize())
        print(f'{len(paths)} paths, {len(succs)} good ones')
        print(f'different bracketisations: {len(brackets)} / {len(fackets)}')
        print(f'successes: {len(successes)} / {len(succs)}')
        print('paths total: ', len(all_paths))
        print('good pathlets: ', len(good_pathlets))
        for p in sorted([repr(p) for p in good_pathlets]):
            print(p)

        print('===============================')
        for pathlet in pathlet_sets:
            print(pathlet)
        return succs, None
        # results = self.linearize(heads)
        # graph = self.export_graph(heads, results, sentence)
        # succs = []
        # for path, line, success in results:
        #    if success:
        #        succs.append(path)
        # print(f'  {"✔" if succs else "-"} {len(succs)} / {len(results)} paths, {len(self.processed)} nodes')
        # if self.forest:
        #    self.export_to_kataja()
        # return succs, graph

    def linearize(self, heads):
        def find_route(xbar, path_feats):
            paths = []
            for ng, pl, child in xbar.specs:
                if ng in path_feats or pl in path_feats:
                    continue
                head = [(xbar, pl, ng, child)]
                _child_paths = find_route(child, path_feats | {pl, ng})
                _child_paths = [path + head for path in _child_paths] or [head]
                paths += _child_paths
            for ng, pl, child in xbar.comps:
                if ng in path_feats or pl in path_feats:
                    continue
                head = [(xbar, pl, ng, child)]
                _child_paths = find_route(child, path_feats | {pl, ng})
                _child_paths = [head + path for path in _child_paths] or [head]
                paths += _child_paths
            return paths

        lines = []
        for _head in heads:
            child_paths = find_route(_head, set())
            lines += child_paths
        results = []
        for line in lines:
            nodes = []
            for parent, pl, ng, child in line:
                if parent not in nodes:
                    nodes.append(parent)
                if child not in nodes:
                    nodes.append(child)
            if len(nodes) == len(self.processed):
                results.append((line, nodes, nodes == self.processed))
        return results

    @staticmethod
    def _build_data(heads, results, sentence):
        nodes = {}
        links = {}

        def add_const(const):
            if const.uid not in nodes:
                nodes[const.uid] = {'id': const.uid, 'label': const.label, 'group': 10}
                # for feature in const.features:
                #    add_feature(feature)
                #    add_cf_link(const, feature)
                for other in const.unjustified:
                    add_const(other)
                    add_cc_link(const, other)
                for plus_feat, neg_feat, target in const.specs + const.comps:
                    add_const(target)
                    add_feature(plus_feat)
                    add_feature(neg_feat)
                    add_cf_link(const, plus_feat)
                    add_cf_link(target, neg_feat)
                    add_ff_link(plus_feat, neg_feat)

        def add_feature(feat):
            if feat.sign == '-':
                group = SPEC_FEATURE
            elif feat.sign == '=':
                group = COMP_FEATURE
            else:
                group = FEATURE
            nodes[feat.uid] = {'id': feat.uid, 'sign': feat.sign, 'name': feat.name, 'value': feat.value,
                               'label': str(feat), 'group': group}

        def add_ff_link(neg_feat, plus_feat):
            if neg_feat.sign == '-':
                group = SPEC_MATCH
            elif neg_feat.sign == '=':
                group = COMP_MATCH
            else:
                group = OTHER_MATCH
            uid = f'{plus_feat.uid}-{neg_feat.uid}-{group}'
            links[uid] = {'source': plus_feat.uid, 'target': neg_feat.uid, 'group': group,
                          'id': uid}

        def add_cf_link(const, feat):
            if feat.sign == '-':
                group = SPEC_EDGE
            elif feat.sign == '=':
                group = COMP_EDGE
            else:
                group = OTHER_EDGE
            uid = f'{const.uid}-{feat.uid}-{group}'
            links[uid] = {'source': const.uid, 'target': feat.uid, 'group': group,
                          'id': uid}

        def add_cc_link(const, other):
            uid = f'{const.uid}-{other.uid}-{CONST_EDGE}'
            links[uid] = {'source': const.uid, 'target': other.uid, 'group': CONST_EDGE,
                          'id': uid}

        for head in heads:
            add_const(head)

        paths = []
        for line, foo, success in results:
            path = []
            for source, plus, neg, dest in line:
                if plus and neg:
                    link = 0
                    group = 0
                    if neg.sign == '-':
                        group = SPEC_EDGE
                        link = SPEC_MATCH
                    elif neg.sign == '=':
                        group = COMP_EDGE
                        link = COMP_MATCH
                    add_cf_link(source, plus)
                    add_cf_link(dest, neg)
                    add_ff_link(neg, plus)
                    path.append((f'{source.uid}-{plus.uid}-{OTHER_EDGE}', f'{plus.uid}-{neg.uid}-{link}',
                                 f'{dest.uid}-{neg.uid}-{group}'))
                else:
                    print('short line: ', source, plus, neg, dest)
            if path:
                paths.append(path)
        for path in paths:
            for pathlet in path:
                for item in pathlet:
                    if item not in links:
                        print(f'{item} not found in {links.keys()}')
                    assert item in links
        return {'nodes': list(nodes.values()), 'links': list(links.values()), 'paths': paths, 'sentence': sentence}

    def export_to_json(self, graphs):
        if not self.forest:  # make path relative to plugin path
            path = 'mg0.js'
        else:
            path = 'mg0.js'
        file = open(path, 'w')
        file.write('const graphs = ')
        json.dump(graphs, file, ensure_ascii=False, indent=2)
        file.close()

    def export_graph(self, heads, results, sentence):
        return self._build_data(heads, results, sentence)


if __name__ == '__main__':
    t = time.time()
    lexicon = read_lexicon('lexicon_en.txt')
    parser = Parser(lexicon)
    sentences = []
    readfile = open('sentences_en2.txt', 'r')
    for line in readfile:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('['):
            sentences.append(line)
    successes = 0
    fails = 0
    i = 0
    graphs = []
    for i, sentence in enumerate(sentences, 1):
        print(f'{i}. "{sentence}"')
        result_trees, graph = parser.parse(sentence)
        graphs.append(graph)
        if result_trees:
            successes += 1
        else:
            fails += 1
        break
    # parser.export_to_json(graphs)

    print('=====================')
    print(f'    {successes}/{i} ')
    print('=====================')
    print('Parsing sentences took: ', time.time() - t)
    print('ticks: ', parser.ticks)

    # def add_to_parse_path(self, path, root, message):
    #     if self.forest:
    #         mover = self._find_mover(root)
    #         riser = self._find_riser(root)
    #         groups = [('mover', [mover] if mover else []),
    #                   ('tree', [root] if root else []),
    #                   ('riser', [riser] if riser else [])]
    #         if root:
    #             _update_check_information_for_features(root)
    #         syn_state = SyntaxState(tree_roots=[root], msg=message, groups=groups)
    #         derivation_step = DerivationStep(syn_state)
    #         derivation_step.freeze()
    #         return path + [derivation_step]
    #     else:
    #         return path + [root]
    #
    # def export_to_kataja(self):
    #     if REMOVE_BAD_PARSES and self.good_paths:
    #         paths = self.good_paths
    #     else:
    #         paths = [path for path, tree in self.results]
    #     for i, path in enumerate(paths):
    #         for syn_state in path:
    #             self.forest.add_step(syn_state, i)
