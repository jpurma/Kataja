try:
    from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
    from plugins.TreesAreMemory2.Feature import Feature
    from plugins.TreesAreMemory2.route_utils import *
    from plugins.TreesAreMemory2.Parser import read_lexicon
except ImportError:
    from SimpleConstituent import SimpleConstituent
    from Feature import Feature
    from route_utils import *
    from Parser import read_lexicon
import time
from collections import Counter, defaultdict
from itertools import chain
from pprint import pprint

debug_parse = False

show_bad_routes = True

use_classic_phrase_structure_exporter = False


def is_positive(feat):
    return feat.sign == '' or feat.sign == '*'


class NumNode:
    def __init__(self, n, const):
        self.n = n or 0
        self.const = const
        self.active = False

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def __hash__(self):
        return self.n

    def __str__(self):
        return f'N{self.n}:{self.const}'

    def __repr__(self):
        return f'N{self.n}'

class ConstNode:
    def __init__(self, label, features):
        self.label = label
        self.pos_features = []
        self.neg_features = []
        self.features = features
        for feature in features:
            if is_negative(feature):
                self.neg_features.append(feature)
            else:
                self.pos_features.append(feature)

    def is_arg_for(self, head):
        for neg_feat in head.neg_features:
            for pos_feat in self.pos_features:
                if neg_feat in pos_feat.satisfies:
                    return pos_feat, neg_feat

    def __repr__(self):
        return f'{self.label}{self.features}'


class FeatNode:
    def __init__(self, feat):
        self.id = str(feat)
        self.sign = feat.sign
        self.name = feat.name
        self.value = feat.value
        self.satisfies = []

    def __repr__(self):
        return self.id

# class Route:
#     def __init__(self, route=None):
#         if route:
#             self.ops = list(route.ops)
#             self.free_precedents = route.free_precedents
#         else:
#             self.ops = []
#             self.free_precedents = []
#
#     def append(self, op):
#         self.ops.append(op)


def is_long_distance(num_node):
    for feat in num_node.const.features:
        if feat.name == 'ld':
            return True


class RouteItem:
    def __init__(self, parent, precedent, top, head):
        self.parent = parent
        self.precedent = precedent
        self.top = top
        self.head = head

    def evaluate_route(self, expected_size):
        found = set()
        route = []
        node = self
        while node:
            if not isinstance(node.top, tuple):
                found.add(node.top)
            route.append(node.top)
            node = self.parent
        return list(reversed(route)), len(found) == expected_size


class NodeParser:
    def __init__(self, lexicon, forest=None):
        self.exporter = None
        self.results = []
        self.correct = []
        self.lexicon = lexicon or {}
        self.moves = defaultdict(set)
        self.states = {}
        self.total = 0
        self.total_good_routes = 0
        self.last_const_id = 0
        self.num_nodes = []
        self.const_nodes = {}
        self.features = {}
        self.routes = []
        self.prepare_network()

    def prepare_network(self):
        self.num_nodes = []
        for key, li_entries in self.lexicon.items():
            for li_entry in li_entries[:1]:
                for li_part in li_entry:
                    fnodes = [self.add_or_get_feat(feat) for feat in li_part.features]
                    self.const_nodes[li_part.label] = ConstNode(li_part.label, fnodes)

    def add_or_get_feat(self, feat):
        f_str = str(feat)
        f_node = self.features.get(f_str, None)
        if f_node:
            return f_node
        f_node = FeatNode(feat)
        if is_negative(feat):
            for pos_node in self.features.values():
                if pos_node.sign == '' and pos_node.name == f_node.name and ((not f_node.value) or f_node.value == pos_node.value):
                    pos_node.satisfies.append(f_node)
        else:
            for neg_node in self.features.values():
                if neg_node.sign == '=' and f_node.name == neg_node.name and ((not neg_node.value) or neg_node.value == f_node.value):
                    f_node.satisfies.append(neg_node)
        return f_node

    def set_forest(self, forest):
        self.exporter.forest = forest

    def get_const_uid(self, const):
        self.last_const_id += 1
        return f'{const.label}{self.last_const_id}'

    # route koostuu tupleista ((Num, Feat), (Num, Feat))? Tässä Feat on redundantti. Num riittäisi. (Num1, Num2)
    # add: (NumT, None)
    # (prec, top, head)
    # comp: (NumP, NumT, NumP)
    # spec: (NumP, NumT, NumT)
    # adj: (NumP, NumT, (NumP, NumT))
    # N1 = Pekka
    # N2 = nukkuu
    # N3 = nukkuu1
    # N4 = kotona

    # [(Pekka, nukkuu, nukkuu), (nukkuu, nukkuu1, nukkuu), (nukkuu1, kotona, nukkuu1)]

    # adjunkti tarkoittaa että kun NumA aktivoituu niin myös NumB aktivoituu ja toisinpäin.

    # Jos teen tietyn operaation, niin voiko siitä kelata taaksepäin mitkä parsinnat mahdollistivat tämän operaation?
    # Muuten kyllä, mutta siirtymät hankaloittaa.
    # Kaikkien edellisten edeltäjien joukko on helppo käsitellä, mutta varhaisemmat edeltäjät ovat joukko listoja jotka voivat olla
    # eri järjestyksissä ja niissä ei saisi hyppiä ohi mahdollisten. Koko asia että miten estää etäisempi operaatio silloin kun läheisempi on tarjolla
    # on vaikea käsitellä.

    def _node_parse(self, sentence):
        tick = 0
        n = 0
        self.route_ends = []
        for word in sentence.split():
            lex_consts = self.lexicon.get(word, [[]])
            lex_const_parts = lex_consts[0]  # cannot handle homonyms that have different lengths in numeration yet
            for lex_const_part in lex_const_parts:
                num_node = NumNode(n, self.const_nodes[lex_const_part.label])
                self.num_nodes.append(num_node)
                num_node.activate()
                for route_item in list(self.route_ends):
                    self.do_operations(route_item, num_node)
                tick += 1
                n += 1
        good_routes = []
        for route_item in self.route_ends:
            route, is_good = route_item.evaluate_route(n)
            if is_good:
                good_routes.append(route)
        print(f'good routes: {len(good_routes)} of {len(routes)}')
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

    def do_operations(self, precedent_ri, top):
        precedent = precedent_ri.node
        print('do operations, top: ', top.const.label, ' precedent: ', precedent.const.label)
        result = {top}
        top_features = top.const.features
        prev_features = precedent.const.features
        found_spec = False
        # Aluksi spec -mahdollisuus, eli viimeisin sana on head ja nostetaan lähin vapaa edeltävä head argumentiksi
        matches = find_matches(prev_features, top_features, '=')
        self.route_ends.remove(precedent_ri)
        if matches:
            print(f'adding spec {precedent.n} ({precedent.const.label}) for head {top.n} ({top.const.label})')
            self.route_ends.append(RouteItem(precedent_ri, precedent, top, top))
            found_spec = True

        # Sitten comp -mahdollisuus, eli viimeisin sana on arg ja nostetaan lähin vapaa edeltävä head pääsanaksi
        if not found_spec:
            matches = find_matches(top_features, prev_features, '=')
            if matches:
                result.add(precedent)
                print(f'adding comp {top.n} ({top.const.label}) for head {precedent.n} ({precedent.const.label})')
                self.route_ends.append(RouteItem(precedent_ri, precedent, top, precedent))

            # On mahdollista että comp lykätään, mutta silloin tämä uusi top täytyy haudata jonoon.
            self.route_ends.append(RouteItem(precedent_ri, precedent, top, None))

        # Entäpä adjunktointi?
        if has_adjunct_licensed(precedent.const, top.const):
            result.add(precedent)
            print(f'adding adjunct {precedent.n} ({precedent.const.label}) for head {top.n} ({top.const.label})')
            self.route_ends.append(RouteItem(precedent_ri, precedent, top, (precedent, top)))

        return result

    def parse(self, sentence):
        t = time.time()
        result_trees = []
        sentence = sentence.strip()
        func_parse = sentence.startswith('f(')

        self.states.clear()
        #self.exporter.reset()
        print('--------------')

        target_linearisation = sentence
        paths = self._node_parse(sentence)

        print('==============')
        print(f"expecting: '{target_linearisation}'")
        print(f'{len(paths)} result paths')
        good_routes = []
        bad_routes = []
        for path in paths:
            linear = linearize(path)
            operation = path[-1]
            is_valid = is_fully_connected(path)
            if target_linearisation == linear and is_valid:
                path.append(Done(self.states, operation, msg=f'done: {linear}'))
                if path not in result_trees:
                    good_routes.append(path)
                    print(f'result path: {route_str(path)} is in correct order and fully connected')
                    if not func_parse:
                        print('possible derivation: ', '.'.join(operation.state.entry for operation in path))
            elif show_bad_routes:
                #path.append(Fail(self.states, operation, msg=f'fail: {linear}'))
                bad_routes.append(path)
        if self.exporter:
            self.exporter.export_to_kataja(good_routes + bad_routes)  # + bad_routes, good_routes)
            self.exporter.save_as_json()
        print()
        self.total += len(paths)
        self.total_good_routes += len(good_routes)
        print('parse took ', time.time() - t)
        return good_routes


if __name__ == '__main__':
    t = time.time()
    my_lexicon = read_lexicon(open('../lexicon.txt'))
    parser = NodeParser(my_lexicon)
    sentences = []
    readfile = open('../sentences_en.txt', 'r')
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

    for i, (in_sentence, expect_success) in enumerate(sentences[:1], 1):
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
