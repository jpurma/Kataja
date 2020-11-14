try:
    from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
    from plugins.TreesAreMemory2.PSExporter import PSExporter, Exporter
    #from plugins.TreesAreMemory2._deprecated_func_support.FuncParser import FuncParser
    from plugins.TreesAreMemory2.RouteItem import RouteItem
    from plugins.TreesAreMemory2.operations import Add, Comp, Spec, Adj, Done, Fail
    from plugins.TreesAreMemory2.Feature import Feature
    from plugins.TreesAreMemory2.route_utils import *
except ImportError:
    from SimpleConstituent import SimpleConstituent
    from PSExporter import PSExporter, Exporter
    #from FuncParser import FuncParser
    from RouteItem import RouteItem
    from operations import Add, Comp, Spec, Adj, Done, Fail, Return
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
            consts.append(SimpleConstituent(label=const_label, features=feats))
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
                    print()
                    print('starting new constituent: ', const)
                    new_routes = [RouteItem(route_end, Add(const)) for route_end in new_routes] or [RouteItem(None, Add(const))]
                    new_routes = list(chain.from_iterable(self.build_route(route) for route in new_routes))
                    print('-- new_routes: ', new_routes)
                routes += new_routes
        print('routes after parse: ', routes)
        return routes

    def get_from_lexicon(self, word):
        original_consts = self.lexicon.get(word, [[SimpleConstituent(label=word)]])
        consts = []
        for original_complex_const in original_consts:
            complex_const = []
            for const in original_complex_const:
                if isinstance(const, SimpleConstituent):
                    const = const.copy()
                else:
                    const = SimpleConstituent(label=const.label, features=[x.copy() for x in const.features])
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
        return RouteItem(prev_route_item, operation)

    def build_route(self, route_item):
        print('* building route from ', route_item)
        print(f'{route_item} has precedents {route_item.free_precedents}')
        print(f'{route_item} has previous {route_item.previous}')
        if not route_item.free_precedents:
            return [route_item]
        new_route_items = []
        previous = route_item.previous
        # adjunct operation
        # (adjunktointi ei saisi olla poissulkeva vaihtoehto, vrt. 'show Mary castles' ja 'show Mary Castles')
        if has_adjunct_licensed(previous, route_item) and not find_shared_heads(previous, route_item):
            new_route_item = self.new_step(route_item, Adj(route_item.operation.head, previous.operation.head))
            new_route_items.append(new_route_item)
        matches = find_matches(route_item.features, previous.features, '=>')
        if matches:
            print('comp from previous ', route_item, previous, matches)
            new_route_item = self.new_step(route_item,
                                           Comp(previous.operation.head, route_item.operation.head, matches))
            new_route_items.append(new_route_item)

        # spec operations
        found = False
        for i, precedent in enumerate(route_item.free_precedents):
            matches = find_matches(precedent.features, route_item.features, '=')
            if matches:
                new_route_item = self.new_step(route_item,
                                               Spec(route_item.operation.head, precedent.operation.head, matches))
                print(f'with precedent {i} {precedent} adding spec operation {new_route_item}')
                new_route_items.append(new_route_item)
                #found = True
            break
        # comp operations
        if not found:
            for i, precedent in enumerate(route_item.free_precedents):
                if precedent is previous:
                    continue
                matches = find_matches(route_item.features, precedent.features, '=')
                if matches:
                    print('comp from precedent ', i, route_item, precedent, matches)
                    new_route_item = self.new_step(route_item,
                                                   Comp(precedent.operation.head, route_item.operation.head, matches))
                    new_route_items.append(new_route_item)
                break
        if new_route_items:
            print('got new operations: ', new_route_items)
            new_route_items = list(chain.from_iterable(self.build_route(ri) for ri in new_route_items))
            print('recursively new operations: ', new_route_items)
            return new_route_items
        else:
            new_route_items.append(route_item)
            print('no new operations, returning: ', new_route_items)
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
            is_valid = is_fully_connected(route)
            if sentence == linear and is_valid:
                done = self.new_step(route_item, Done(route_item.operation.head, msg=f'done: {linear}'))
                route_ends.append(done)
                route_ends.remove(operation)
                good_routes.append(done)
                print(f'result path: {route_str(route)} is in correct order and fully connected')
                if not func_parse:
                    print('possible derivation: ', '.'.join(route_item_.entry for route_item_ in route))
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
