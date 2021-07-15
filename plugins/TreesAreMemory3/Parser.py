try:
    from plugins.TreesAreMemory3.Constituent import Constituent
    from plugins.TreesAreMemory3.Exporter import Exporter
    from plugins.TreesAreMemory3.RouteItem import RouteItem, operation_ids
    from plugins.TreesAreMemory3.operations import Add, Comp, Spec, Adj, Done, Fail
    from plugins.TreesAreMemory3.Feature import Feature
    from plugins.TreesAreMemory3.route_utils import *
except ImportError:
    from Constituent import Constituent
    from Exporter import Exporter
    from RouteItem import RouteItem, operation_ids
    from operations import Add, Comp, Spec, Adj, Done, Fail
    from Feature import Feature
    from route_utils import *
import time
from itertools import chain

debug_parse = False

show_bad_routes = True

use_classic_phrase_structure_exporter = False


def read_lexicon(lines, lexicon=None):
    if lexicon is None:
        lexicon = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        label, foo, feat_parts = line.partition('::')
        label = label.strip()
        consts = []
        for i, fstring in enumerate(feat_parts.split(',')):
            feats = [Feature.from_string(fs) for fs in fstring.split()]
            const_label = f'({label}{i})' if i else label
            consts.append(Constituent(label=const_label, features=feats))
        if label in lexicon:
            lexicon[label].append(consts)
        else:
            lexicon[label] = [consts]
    return lexicon


def is_positive(feat):
    return feat.sign == '' or feat.sign == '*'


def linearize(route):
    """ This is a very simple linearisation because route already has elements in correct order.
    To verify that the structure is valid, one should try to linearise the constituent tree """
    result = []
    for route_item in route:
        op = route_item.operation
        if type(op) is Add:
            label = route_item.operation.get_head_label()
            if label and not label.startswith('('):
                result.append(label)
    str_result = ' '.join(result)
    debug_linearization and print('linearised: ', str_result)
    return str_result


def is_fully_connected(route):
    heads = set()
    args = set()

    for route_item in route:
        op = route_item.operation
        if op.head not in args:
            heads.add(op.head)
        if op.arg:
            args.add(op.arg)
            heads.discard(op.arg)
        if type(op) is Adj:
            head1, head2 = op.head
            args.add(head1)
            args.add(head2)
            heads.discard(head1)
            heads.discard(head2)
    return len(heads) == 1


def has_unsatisfied_necessary_features(route):
    def add_unsatisfied_feat(ri):
        for feat in ri.features:
            if feat.sign == '>':
                if ri.head in unsatisfied_heads:
                    unsatisfied_heads[ri.head].append(feat)
                else:
                    unsatisfied_heads[ri.head] = [feat]

    unsatisfied_heads = {}
    for route_item in route:
        op = route_item.operation
        if type(op) is Add:
            add_unsatisfied_feat(route_item)
        elif type(op) is Adj:
            h1, h2 = op.head
            if h1 in unsatisfied_heads:
                del unsatisfied_heads[h1]
            if h2 in unsatisfied_heads:
                del unsatisfied_heads[h2]
            add_unsatisfied_feat(route_item)
        elif type(op) is Spec or type(op) is Comp:
            if op.head in unsatisfied_heads:
                unsatisfied_feats = unsatisfied_heads[op.head]
                unsatisfied_feats = [feat for feat in unsatisfied_feats if feat not in route_item.flat_checked_features]
                if not unsatisfied_feats:
                    del unsatisfied_heads[op.head]
    print(f'{unsatisfied_heads=}')
    return unsatisfied_heads


class Parser:
    def __init__(self, lexicon, forest=None):
        self.exporter = PSExporter(forest) if use_classic_phrase_structure_exporter else Exporter(forest)
        self.operations = {}
        self.results = []
        self.correct = []
        self.lexicon = lexicon or {}
        self.total = 0
        self.total_good_routes = 0
        self.last_const_id = 0
        #self.func_parser = FuncParser(self)

    def set_forest(self, forest):
        self.exporter.forest = forest

    def get_const_uid(self, const):
        self.last_const_id += 1
        return f'{const.label}{self.last_const_id}'

    def _string_parse(self, sentence):
        routes = []
        for word in sentence.split():
            homonyms = self.get_from_lexicon(word)
            original_routes = list(routes)
            for complex_const in homonyms:
                routes = []
                new_routes = list(original_routes)
                for const in complex_const:
                    added = Add(const)
                    added.ord = operation_ids.get_id()
                    new_routes = [RouteItem(route_end, added) for route_end in new_routes] or [RouteItem(None, added)]
                    new_routes = list(chain.from_iterable(self.build_route(route) for route in new_routes))
                    print('-- new_routes: ', new_routes)
                routes += new_routes
        print('routes after parse: ', routes)
        return routes

    def get_from_lexicon(self, word):
        original_consts = self.lexicon.get(word, [[Constituent(label=word)]])
        consts = []
        for original_complex_const in original_consts:
            complex_const = []
            for const in original_complex_const:
                if isinstance(const, Constituent):
                    const = const.copy()
                else:
                    const = Constituent(label=const.label, features=[x.copy() for x in const.features])
                const.uid = self.get_const_uid(const)
                const.head = const
                complex_const.append(const)
            consts.append(complex_const)
        return consts

    def new_step(self, prev_route_item, operation):
        if operation.uid in self.operations:
            operation = self.operations[operation.uid]
        else:
            self.operations[operation.uid] = operation
            operation.ord = operation_ids.get_id()
        return RouteItem(prev_route_item, operation)

    def build_route(self, route_item):
        if not (route_item.parent and route_item.local_heads):
            return [route_item]
        new_route_items = []
        op_head = route_item.head
        is_sus = False
        previous = None
        local_heads = route_item.local_heads
        assert len(route_item.local_heads) == len({x.head for x in route_item.local_heads})
        if len(local_heads) < 2:
            ri = route_item.parent
            while ri and ri.head is op_head:
                ri = ri.parent
            local_heads = ri.local_heads
        print(f'building route item {route_item}, local heads: {local_heads} ')
        #assert previous is route_item.local_heads[0]

        # comp match from previous
        for previous in local_heads:
            if previous is route_item:
                continue
            # adjunct operation
            # (adjunktointi ei saisi olla poissulkeva vaihtoehto, vrt. 'show Mary castles' ja 'show Mary Castles')
            if has_adjunct_licensed(previous, route_item) and not find_shared_heads(previous, route_item):
                new_route_item = self.new_step(route_item, Adj(op_head, previous.operation.head))
                new_route_items.append(new_route_item)
                is_sus = True
            if not is_argument(previous, route_item, route_item):
                comp_match = find_matches(route_item.features, route_item.not_used(previous.features), '=>')
                if comp_match:
                    new_route_item = self.new_step(route_item, Comp(previous.operation.head, op_head, comp_match))
                    new_route_items.append(new_route_item)
            break

        # spec operations
        is_first = True
        for precedent in route_item.free_heads:
            if precedent is route_item:
                continue
            if not (is_first or allow_long_distance(precedent.features)):
                continue
            spec_match = find_matches(route_item.not_used(precedent.features), route_item.features, '=>')
            if spec_match:
                new_route_item = self.new_step(route_item, Spec(op_head, precedent.operation.head, spec_match))
                new_route_items.append(new_route_item)
                is_sus = is_sus or is_first
                break
            is_first = False
        # comp operations
        if not is_sus:
            found_comp = False
            for precedent in local_heads:
                if precedent is previous or precedent is route_item:
                    continue
                comp_match = find_matches(route_item.features, route_item.not_used(precedent.features), '=')
                #print('looked for comp match, comp: ', route_item, ' head: ', precedent, comp_match)
                if comp_match:
                    new_route_item = self.new_step(route_item, Comp(precedent.operation.head, op_head, comp_match))
                    new_route_items.append(new_route_item)
                    is_sus = True
                    found_comp = True
                    break
            if not found_comp:
                for precedent in route_item.free_heads:
                    if precedent is previous or precedent is route_item:
                        continue
                    #elif not allow_long_distance(precedent.features):
                    #    continue
                    comp_match = find_matches(route_item.features, route_item.not_used(precedent.features), '=')
                    #print('looked for comp match, comp: ', route_item, ' head: ', precedent, comp_match)
                    if comp_match:
                        new_route_item = self.new_step(route_item, Comp(precedent.operation.head, op_head, comp_match))
                        new_route_items.append(new_route_item)
                        is_sus = True
                        break

        if new_route_items:
            is_sus = is_sus and len(new_route_items) == 1
            new_route_items = list(chain.from_iterable(self.build_route(ri) for ri in new_route_items))
            if not is_sus:
                return new_route_items
        new_route_items.append(route_item)
        return new_route_items

    def parse(self, sentence):
        t = time.time()
        sentence = sentence.strip()
        func_parse = sentence.startswith('f(')
        self.exporter.reset()
        print('--------------')

        # if func_parse:
        #     print('using func parse')
        #     route_ends = self.func_parser.parse(sentence)
        #     target_linearisation = self.func_parser.compute_target_linearisation(routes[0])
        # else:
        route_ends = self._string_parse(sentence)

        print('==============')
        print(f"expecting: '{sentence}'")
        print(f'{len(route_ends)} result routes')
        good_routes = []
        bad_routes = []
        for route_item in list(route_ends):
            route = route_item.as_route()
            linear = linearize(route)
            is_valid = is_fully_connected(route) and not has_unsatisfied_necessary_features(route)
            if sentence == linear and is_valid:
                done = self.new_step(route_item, Done(route_item.operation.head, msg=f'done: {linear}'))
                route_ends.append(done)
                route_ends.remove(route_item)
                good_routes.append(done)
                print(f'result path: {route_str(route)} is in correct order and fully connected')
                if not func_parse:
                    print('possible derivation: ', '.'.join(route_item_.operation.entry for route_item_ in route))
            elif show_bad_routes:
                pass
                #fail = self.new_step(route_item, Fail(route_item.operation.head, msg=f'fail: {linear}'))
                #bad_routes.append(fail)
                #route_ends.append(fail)
                #route_ends.remove(route_item)
                bad_routes.append(route_item)

        self.exporter.export_to_kataja(good_routes + bad_routes)  # + bad_routes, good_routes)
        print()
        self.exporter.save_as_json()
        self.total += len(route_ends)
        self.total_good_routes += len(good_routes)
        print('parse took ', time.time() - t)
        return good_routes


if __name__ == '__main__':
    t = time.time()
    my_lexicon = read_lexicon(open('lexicon.txt'))
    parser = Parser(my_lexicon)
    sentences = []
    readfile = open('sentences_en.txt', 'r')
    for line in readfile:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('['):
            expect_success = True
            if line.startswith('--'):
                break
            if line.startswith('??'):
                line = line[3:]
                expect_success = False
            elif line.startswith('*?'):
                line = line[3:]
                expect_success = False
            elif line.startswith('?*'):
                line = line[3:]
                expect_success = False
            elif line.startswith('?'):
                line = line[2:]
            elif line.startswith('*'):
                line = line[2:]
                expect_success = False
            sentences.append((line, expect_success))
    successes = 0
    i = 0
    problems = []
    positives = []
    negatives = []
    false_negatives = []
    false_positives = []

    for i, (in_sentence, expect_success) in enumerate(sentences, 1):
        print(f'{i}. "{in_sentence}"')
        results = parser.parse(in_sentence)
        if results:
            if expect_success:
                positives.append(i)
                successes += 1
            else:
                false_positives.append(i)
                problems.append(i)
        else:
            if expect_success:
                false_negatives.append(i)
                problems.append(i)
            else:
                successes += 1
                negatives.append(i)


    print('=====================')
    print(f'  {successes}/{i}   ')
    print('=====================')
    print('Parsing sentences took: ', time.time() - t)
    print('Total routes inspected: ', parser.total)
    print('Total good routes found: ', parser.total_good_routes)
    print('Positives: ', len(positives))
    print('Negatives (as expected): ', len(negatives))
    print('False positives: ', len(false_positives), false_positives)
    print('False negatives: ', len(false_negatives), false_negatives)
    #print('problems at: ', problems)
