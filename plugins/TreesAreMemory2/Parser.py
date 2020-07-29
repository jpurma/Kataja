try:
    from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
    from plugins.TreesAreMemory2.PSExporter import PSExporter, Exporter
    from plugins.TreesAreMemory2.State import State
    from plugins.TreesAreMemory2.FuncParser import FuncParser
    from plugins.TreesAreMemory2.operations import Add, Comp, Spec, Adj, Done, Fail, Return
    from plugins.TreesAreMemory2.Feature import Feature
    from plugins.TreesAreMemory2.route_utils import *
except ImportError:
    from SimpleConstituent import SimpleConstituent
    from PSExporter import PSExporter, Exporter
    from State import State
    from FuncParser import FuncParser
    from operations import Add, Comp, Spec, Adj, Done, Fail, Return
    from Feature import Feature
    from route_utils import *
import time
from collections import Counter
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


class Parser:
    def __init__(self, lexicon, forest=None):
        self.exporter = PSExporter(forest) if use_classic_phrase_structure_exporter else Exporter(forest)
        self.results = []
        self.correct = []
        self.lexicon = lexicon or {}
        self.states = {}
        self.total = 0
        self.total_good_routes = 0
        self.last_const_id = 0
        self.func_parser = FuncParser(self)

    def set_forest(self, forest):
        self.exporter.forest = forest

    def get_const_uid(self, const):
        self.last_const_id += 1
        return f'{const.label}{self.last_const_id}'

    def _string_parse(self, sentence):
        path_ends = []
        for word in sentence.split():
            consts = self.get_from_lexicon(word)
            paths_before = list(path_ends)
            path_ends = []
            for complex_const in consts:
                new_paths = list(paths_before)
                for const in complex_const:
                    added_paths = [Add(path_end, self.states, const) for path_end in new_paths] \
                                  or [Add(None, self.states, const)]
                    new_paths = list(chain.from_iterable(self.do_operations(path) for path in added_paths))
                path_ends += new_paths
        return path_ends

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

    def do_operations(self, operation):
        top_features = operation.features
        path_ends = []
        found = False  # kokeillaan täyttä poissulkevuutta
        precedent = operation.first_free_precedent()
        if not precedent:
            return [operation]
        # Entäpä adjunktointi?
        # (adjunktointi ei saisi olla poissulkeva vaihtoehto, vrt. 'show Mary castles' ja 'show Mary Castles')
        # nyt se on jotta ei tule luotua liikaa vaihtoehtoja. Jotain parempaa tarvitaan.
        if has_adjunct_licensed(precedent, operation) and \
                head_precedes(precedent, operation) and \
                not find_shared_heads(precedent, operation):
            new_operation = Adj(self.states, operation, precedent)
            return self.do_operations(new_operation)

        found_spec = False
        prev_features = precedent.features
        # Aluksi spec -mahdollisuus, eli viimeisin sana on head ja nostetaan lähin vapaa edeltävä head argumentiksi
        matches = find_matches(prev_features, top_features, '=')
        if matches:
            new_operation = Spec(self.states, operation, precedent, checked_features=matches)
            path_ends += self.do_operations(new_operation)
            found = True
            found_spec = True
        elif len(operation.free_precedents) > 1 and not precedent.is_phase_border():
            # pitkän kantaman spec
            top_allows_long_distance = allow_long_distance(top_features)
            for distant_precedent in operation.free_precedents[1:]:
                if distant_precedent.is_phase_border():
                    break
                prev_features = distant_precedent.features
                if not (top_allows_long_distance or allow_long_distance(prev_features)):
                    continue
                matches = find_matches(prev_features, top_features, '=')
                if matches:
                    new_operation = Spec(self.states, operation, distant_precedent, checked_features=matches,
                                         long_distance=True)
                    path_ends += self.do_operations(new_operation)
                    found = True
                    found_spec = True
                    break
        # Sitten comp -mahdollisuus, eli viimeisin sana on arg ja nostetaan lähin vapaa edeltävä head pääsanaksi
        if not found:
            prev_features = precedent.features
            matches = find_matches(top_features, prev_features, '=')
            if matches:
                new_operation = Comp(self.states, operation, precedent, checked_features=matches)
                path_ends += self.do_operations(new_operation)

            elif len(operation.free_precedents) > 1 and not precedent.is_phase_border():
                # pitkän kantaman comp
                top_allows_long_distance = allow_long_distance(top_features)
                for distant_precedent in operation.free_precedents[1:]:
                    if distant_precedent.is_phase_border():
                        break
                    prev_features = distant_precedent.features
                    if not (top_allows_long_distance or allow_long_distance(prev_features)):
                        continue
                    matches = find_matches(top_features, prev_features, '=')
                    if matches:
                        new_operation = Comp(self.states, operation, distant_precedent, checked_features=matches,
                                             long_distance=True)
                        path_ends += self.do_operations(new_operation)
                        break

        # Myös se vaihtoehto että jätetään nostot tekemättä:
        if not found_spec:
            path_ends.append(operation)

        return path_ends

    def parse(self, sentence):
        t = time.time()
        sentence = sentence.strip()
        func_parse = sentence.startswith('f(')
        self.states.clear()
        self.exporter.reset()
        print('--------------')

        if func_parse:
            print('using func parse')
            paths = self.func_parser.parse(sentence)
            target_linearisation = self.func_parser.compute_target_linearisation(paths[0])
        else:
            target_linearisation = sentence
            path_ends = self._string_parse(sentence)

        print('==============')
        print(f"expecting: '{target_linearisation}'")
        print(f'{len(path_ends)} result paths')
        good_routes = []
        bad_routes = []
        for operation in list(path_ends):
            route = operation.as_route()
            linear = linearize(route)
            is_valid = is_fully_connected(route)
            if target_linearisation == linear and is_valid:
                done = Done(self.states, operation, msg=f'done: {linear}')
                path_ends.append(done)
                path_ends.remove(operation)
                good_routes.append(done)
                print(f'result path: {route_str(route)} is in correct order and fully connected')
                if not func_parse:
                    print('possible derivation: ', '.'.join(operation.state.entry for operation in route))
            elif show_bad_routes:
                #path.append(Fail(self.states, operation, msg=f'fail: {linear}'))
                bad_routes.append(operation)
        self.exporter.export_to_kataja(good_routes + bad_routes)  # + bad_routes, good_routes)
        print()
        self.exporter.save_as_json()
        self.total += len(path_ends)
        self.total_good_routes += len(good_routes)
        print('parse took ', time.time() - t)
        return good_routes


if __name__ == '__main__':
    t = time.time()
    my_lexicon = read_lexicon(open('lexicon.txt'))
    parser = Parser(my_lexicon)
    sentences = []
    readfile = open('sentences1.txt', 'r')
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
