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
    print('linearised: ', str_result)
    return str_result


def is_fully_connected(route):
    unused_heads = set()
    args = set()

    for route_item in route:
        op = route_item.operation
        if op.head not in args:
            if not op.complex_parts or op is op.complex_parts[0]:
                unused_heads.add(op.head)
        if op.arg:
            args.add(op.arg)
            unused_heads.discard(op.arg)
        if type(op) is Adj:
            head1, head2 = op.head
            if head1 in args or head2 in args:
                args.add(op.head)
                unused_heads.discard(op.head)
            unused_heads.discard(head1)
            unused_heads.discard(head2)
    print('unused heads: ', unused_heads, len(unused_heads))
    heads = [const for const in unused_heads if isinstance(const, tuple) or not const.complex_parts]
    print('heads: ', heads, len(heads))
    print('top heads in parsed sentence (should be 1): ', len(heads), heads)
    #assert len(heads) == 1
    return len(heads) == 1

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

    def set_forest(self, forest):
        self.exporter.forest = forest

    def get_const_uid(self, const):
        self.last_const_id += 1
        return f'{const.label}{self.last_const_id}'

    def _string_parse(self, sentence):
        routes = []
        for word in sentence.split():
            homonyms = self.get_from_lexicon(word)
            routes_before_add = list(routes)
            for complex_const in homonyms:
                routes = []
                route_ends = list(routes_before_add)
                if len(complex_const) == 1:
                    const = complex_const[0]
                    added = Add(const)
                    added.ord = operation_ids.get_id()
                    route_ends = [RouteItem(route_end, added) for route_end in route_ends] or [RouteItem(None, added)]
                    route_ends = list(chain.from_iterable(
                        self.append_possible_route_operations(route_end) for route_end in route_ends
                    ))
                else:
                    complex_parts = []
                    for const in complex_const:
                        added = Add(const)
                        added.ord = operation_ids.get_id()
                        complex_parts.append(added)
                    for op in complex_parts:
                        op.complex_parts = complex_parts
                        op.head.complex_parts = [o.head for o in complex_parts]
                        route_ends = [RouteItem(route_end, op) for route_end in route_ends] or [RouteItem(None, op)]
                        route_ends = list(chain.from_iterable(
                            self.append_possible_route_operations(route_end) for route_end in route_ends
                        ))
                routes += route_ends
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
        #print('making new step for ', operation.uid)
        if operation.uid in self.operations:
            operation = self.operations[operation.uid]
            #print('fetch known operation, ', operation.uid)
        else:
            self.operations[operation.uid] = operation
            operation.ord = operation_ids.get_id()
        ri = RouteItem(prev_route_item, operation)
        if ri not in ri.parent.children:
            ri.parent.children.append(ri)
        return ri

    def append_possible_route_operations(self, route_item):
        if not route_item.parent:
            return [route_item]
        new_route_items = []
        op_head = route_item.head
        features = route_item.collect_available_features()
        for previous in route_item.find_local_heads():
            #print('checking previous local head', previous, ' for ', route_item)
            prev_features = previous.collect_available_features()
            if (adjunct_check := has_adjunct_licensed(prev_features, features)) and not find_shared_heads(previous, route_item):
                new_route_item = self.new_step(route_item, Adj(op_head, previous.operation.head, [adjunct_check]))
                new_route_items.append(new_route_item)
            if spec_match := find_matches(prev_features, features, '<'):
                new_route_item = self.new_step(route_item, Spec(op_head, previous.operation.head, spec_match))
                new_route_items.append(new_route_item)
                break
            if comp_match := find_matches(features, prev_features, '=>'):
                new_route_item = self.new_step(route_item, Comp(previous.operation.head, op_head, comp_match))
                new_route_items.append(new_route_item)
                break
            break

        if not new_route_items:
            for precedent in route_item.find_available_heads():
                if precedent is route_item:
                    continue
                prev_features = precedent.collect_available_features()
                if spec_match := find_matches(prev_features, features, '='):
                    new_route_item = self.new_step(route_item, Spec(op_head, precedent.operation.head, spec_match))
                    new_route_items.append(new_route_item)
                    break
                elif comp_match := find_matches(features, prev_features, '='):
                    new_route_item = self.new_step(route_item, Comp(precedent.operation.head, op_head, comp_match))
                    new_route_items.append(new_route_item)
                    break

        if new_route_items:
            new_route_items = list(chain.from_iterable(self.append_possible_route_operations(ri) for ri in new_route_items))
        else:
            new_route_items.append(route_item)
        return new_route_items

    def parse(self, sentence):
        t = time.time()
        sentence = sentence.strip()
        func_parse = sentence.startswith('f(')
        self.exporter.reset()
        print('--------------')

        route_ends = self._string_parse(sentence)

        print('==============')
        print(f"expecting: '{sentence}'")
        print(f'{len(route_ends)} result routes')
        good_routes = []
        bad_routes = []
        for route_item in route_ends:
            route = route_item.as_route()
            linear = linearize(route)
            is_valid = is_fully_connected(route)
            if sentence == linear and is_valid:
                done = self.new_step(route_item, Done(route_item.operation.head, msg=f'done: {linear}'))
                good_routes.append(done)
                print(f'result path: {route_str(route)} is in correct order and fully connected')
                if not func_parse:
                    print('possible derivation: ', '.'.join(route_item_.operation.entry for route_item_ in route))
            elif show_bad_routes:
                #fail = self.new_step(route_item, Fail(route_item.operation.head, msg=f'fail: {linear}'))
                #bad_routes.append(fail)
                #route_ends.append(fail)
                #route_ends.remove(route_item)
                bad_routes.append(route_item)

        print('parse took ', time.time() - t)
        self.exporter.export_to_kataja(good_routes + bad_routes)  # + bad_routes, good_routes)
        self.exporter.save_as_json()
        self.total += len(route_ends)
        self.total_good_routes += len(good_routes)
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
