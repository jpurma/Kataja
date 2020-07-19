try:
    from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
    from plugins.TreesAreMemory2.Exporter import Exporter
    from plugins.TreesAreMemory2.State import State
    from plugins.TreesAreMemory2.FuncParser import FuncParser
    from plugins.TreesAreMemory2.operations import Add, Comp, Spec, Adj, Done, Fail
    from plugins.TreesAreMemory2.Feature import Feature
    from plugins.TreesAreMemory2.route_utils import *
except ImportError:
    from SimpleConstituent import SimpleConstituent
    from Exporter import Exporter
    from State import State
    from FuncParser import FuncParser
    from operations import Add, Comp, Spec, Adj, Done, Fail
    from Feature import Feature
    from route_utils import *
import time
from collections import Counter
from itertools import chain

debug_parse = False

show_bad_routes = True


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
            const_label = f'({label})' if i else label
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
        self.exporter = Exporter(forest)
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
        paths = []
        for word in sentence.split():
            consts = self.get_from_lexicon(word)
            paths_before = list(paths)
            paths = []
            for complex_const in consts:
                new_paths = list(paths_before)
                for const in complex_const:
                    if new_paths:
                        added_paths = []
                        for path in new_paths:
                            add_operation = Add(self.states, const)
                            added_path = path + [add_operation]
                            add_operation.calculate_free_precedents(added_path)
                            added_paths.append(added_path)
                    else:
                        added_paths = [[Add(self.states, const)]]
                    new_paths = list(chain.from_iterable(self.do_operations_specs_only(path) for path in added_paths))
                new_paths = list(chain.from_iterable(self.do_operations(path) for path in new_paths))
                paths += new_paths
        return paths

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

    def do_operations_specs_only(self, path):
        path_str = route_str(path)
        debug_parse and print('checking path ', path_str)
        operation = path[-1]
        state = operation.state
        if not state.head:
            return {path}
        top_features = operation.features

        precedent = operation.free_precedents[0] if operation.free_precedents else None
        if precedent:
            prev_features = precedent.features
            # Aluksi spec -mahdollisuus, eli viimeisin sana on head ja nostetaan lähin vapaa edeltävä head argumentiksi
            matches = find_matches(prev_features, top_features, '-=')
            if matches: # and matches[0][0].name == 'N':
                new_operation = Spec(self.states, operation, precedent, checked_features=matches)
                new_path = path + [new_operation]
                new_operation.calculate_free_precedents(new_path)
                return [new_path]

        if len(operation.free_precedents) > 1:
            for distant_precedent in operation.free_precedents[1:]:
                if phase_border(distant_precedent):
                    break
                prev_features = distant_precedent.features
                matches = find_matches(prev_features, top_features, '-')
                if matches: # and matches[0][0].name == 'N':
                    new_operation = Spec(self.states, operation, distant_precedent, checked_features=matches, long_distance=True)
                    new_path = path + [new_operation]
                    new_operation.calculate_free_precedents(new_path)
                    return [new_path]

        return [path]

    def do_operations(self, path):
        def add_to_paths(paths, new_operation):
            new_path = path + [new_operation]
            new_operation.calculate_free_precedents(new_path)
            paths += self.do_operations(new_path)

        path_str = route_str(path)
        debug_parse and print('checking path ', path_str)
        operation = path[-1]
        state = operation.state
        if not state.head:
            return {path}
        top_features = operation.features

        paths = []
        found_spec = False
        found_comp = False
        precedent = operation.free_precedents[0] if operation.free_precedents else None
        if precedent:
            prev_features = precedent.features
            # Aluksi spec -mahdollisuus, eli viimeisin sana on head ja nostetaan lähin vapaa edeltävä head argumentiksi
            matches = find_matches(prev_features, top_features, '-=')
            if matches:
                add_to_paths(paths, Spec(self.states, operation, precedent, checked_features=matches))
                found_spec = True

            # Sitten comp -mahdollisuus, eli viimeisin sana on arg ja nostetaan lähin vapaa edeltävä head pääsanaksi
            matches = find_matches(top_features, prev_features, '-=')
            if matches:
                add_to_paths(paths, Comp(self.states, operation, precedent, checked_features=matches))
                found_comp = True

            # Entäpä adjunktointi?
            common_features = find_common_features(top_features, prev_features)
            if common_features and not find_shared_heads(precedent, operation):
                shared_features = find_shared_features(top_features, prev_features)
                add_to_paths(paths, Adj(self.states, operation, precedent, shared_features=shared_features))

        # Myös se vaihtoehto että jätetään nostot tekemättä:
        paths.append(path)

        if len(operation.free_precedents) > 1:
            if not found_spec:
                # pitkän kantaman spec
                for distant_precedent in operation.free_precedents[1:]:
                    prev_features = distant_precedent.features
                    matches = find_matches(prev_features, top_features, '-')
                    if matches:
                        add_to_paths(paths, Spec(self.states, operation, distant_precedent, checked_features=matches, long_distance=True))
                        break
            if not found_comp:
                # pitkän kantaman comp
                for distant_precedent in operation.free_precedents[1:]:
                    if phase_border(distant_precedent):
                        break
                    prev_features = distant_precedent.features
                    matches = find_matches(top_features, prev_features, '-')
                    if matches:
                        add_to_paths(paths, Comp(self.states, operation, distant_precedent, checked_features=matches, long_distance=True))
                        break
        return paths

    def parse(self, sentence):
        t = time.time()
        result_trees = []
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
            paths = self._string_parse(sentence)

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
        self.exporter.export_to_kataja(good_routes + bad_routes)  # + bad_routes, good_routes)
        print()
        self.exporter.save_as_json()
        self.total += len(paths)
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
    print('False positives: ', len(false_positives))
    print('False negatives: ', len(false_negatives), false_negatives)
    #print('problems at: ', problems)
