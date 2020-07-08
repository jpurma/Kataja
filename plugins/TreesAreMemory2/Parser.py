#try:
from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
from plugins.TreesAreMemory2.Exporter import Exporter
from plugins.TreesAreMemory2.State import State
from plugins.TreesAreMemory2.RouteItem import RouteItem, route_str, linearize, is_fully_connected
from plugins.TreesAreMemory2.Feature import Feature
from plugins.TreesAreMemory2.route_utils import *
# except ImportError:
#     from SimpleConstituent import SimpleConstituent
#     from State import State
#     from RouteItem import RouteItem, route_str
#     from Exporter import Exporter
#     from Feature import Feature
#     from route_utils import *
import time
from collections import Counter
from string import ascii_letters
from itertools import chain

debug_parse = True
debug_features = True

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
        lexicon[label] = consts
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
        self.ids = 0
        self.total = 0
        self.active_route = []
        self.last_used_feature = 0
        self.last_const_id = 0

    def set_forest(self, forest):
        self.exporter.forest = forest

    def get_const_uid(self, const):
        self.last_const_id += 1
        return f'{const.label}{self.last_const_id}'

    def add_state(self, new_state):
        self.ids += 1
        new_state.state_id = self.ids
        new_state.parser = self
        self.states[new_state.key] = new_state
        return new_state

    @staticmethod
    def compute_target_linearisation(route):
        words = []
        for route_item in route:
            if route_item.state.state_type == State.ADD:
                words.append(route_item.state.head.label)
        return ' '.join(words)

    def _func_parse(self, sentence):

        def f(word, *feats):
            if self.active_route:
                return self.active_route[-1].func_add(word, *feats)
            else:
                const = SimpleConstituent(word)
                route_item = RouteItem.create_initial_state(const, self, feats)
                self.active_route = [route_item]
                return route_item

        func_locals = {'f': f}
        self.active_route = []
        exec(sentence, globals(), func_locals)
        return [self.active_route]

    def _string_parse(self, sentence):
        paths = []
        for word in sentence.split():
            paths = list(chain.from_iterable(self.do_operations(path) for path in paths))
            consts = self.get_from_lexicon(word)
            for const in consts:
                if paths:
                    paths = [path + [path[-1].add_const(const)] for path in paths]
                else:
                    paths = [[RouteItem.create_initial_state(const, self)]]

        # Finally attempt to raise what can be raised
        paths = list(chain.from_iterable(self.do_operations(path) for path in paths))
        return paths

    def get_from_lexicon(self, word):
        original_consts = self.lexicon[word]
        consts = []
        for const in original_consts:
            if isinstance(const, SimpleConstituent):
                const = const.copy()
            else:
                const = SimpleConstituent(label=const.label, features=[x.copy() for x in const.features])
            const.uid = self.get_const_uid(const)
            const.head = const
            consts.append(const)
        return consts

    def add_feat_to_route(self, feat, head):
        for route_item in self.active_route:
            if route_item.state.head is head and feat not in route_item.features and feat not in route_item.used_features:
                print('adding missing feat for ', route_item.state.head, feat)
                route_item.features.append(feat)
                add_feature(route_item.state.head, feat)

    def speculate_features(self, head, arg):
        pos_feature = Feature(ascii_letters[self.last_used_feature], sign='')
        neg_feature = Feature(ascii_letters[self.last_used_feature], sign='-')
        self.last_used_feature += 1
        add_feature(head, neg_feature)
        add_feature(arg, pos_feature)
        return pos_feature, neg_feature

    def do_operations(self, path):
        path_str = route_str(path)
        debug_parse and print('attempt raising ', path_str)
        route_item = path[-1]
        state = route_item.state
        if not state.head:
            return {path}
        top_head = state.head
        top_features = route_item.features
        my_heads = [ri.state.arg_ for ri in path if ri.state.arg_ and ri.state.head is top_head]
        my_args = [ri.state.head for ri in path if ri.state.arg_ and ri.state.arg_ is top_head]
        reversed_path = list(reversed(path))

        paths = []
        found_arg = False
        found_comp = False
        precedent = get_free_precedent_from_route(path)
        if precedent and precedent.state.head is not top_head:
            prev_features = precedent.features
            # Aluksi arg-raise -mahdollisuus, eli top on head ja nostetaan lähin sopiva edeltävä head argumentiksi
            matches = find_matches(prev_features, top_features, '-=')
            if matches:
                new_route_item = route_item.raise_arg(precedent, checked_features=matches)
                # return self.do_operations(path + [new_route_item])
                paths += self.do_operations(path + [new_route_item])
                found_arg = True

            # Sitten close arg -mahdollisuudet, eli top on arg ja nostetaan lähin sopiva edeltävä head pääsanaksi
            matches = find_matches(top_features, prev_features, '-=')
            if matches:
                new_route_item = route_item.complement(precedent, checked_features=matches)
                #return self.do_operations(path + [new_route_item])
                paths += self.do_operations(path + [new_route_item])
                found_comp = True

            # Entäpä adjunktointi?
            common_features = find_common_features(top_features, prev_features)
            if common_features and not find_shared_heads(precedent, route_item):
                shared_features = find_shared_features(top_features, prev_features)
                new_route_item = route_item.adjunct(precedent, shared_features=shared_features)
                paths += self.do_operations(path + [new_route_item])

        # Myös se vaihtoehto että jätetään nostot tekemättä:
        paths.append(path)

        if not found_arg:
            closest_available_found = False
            found_args = set()
            for previous_route_item in reversed_path:
                previous_state = previous_route_item.state
                if previous_state.arg_:
                    found_args.add(previous_state.arg_)
                if previous_state.head is top_head:
                    continue
                if previous_state.head in my_heads or previous_state.head in my_args:
                    continue
                if (not closest_available_found) and previous_state.head not in found_args:
                    closest_available_found = previous_state
                prev_features = previous_route_item.features
                matches = find_matches(prev_features, top_features, '-=' if closest_available_found is previous_state else '-')
                if matches:
                    new_route_item = route_item.raise_arg(previous_route_item, checked_features=matches, long_distance=True)
                    #return self.do_operations(path + [new_route_item])
                    paths += self.do_operations(path + [new_route_item])
                    break

        if not found_comp and False:
            closest_available_found = False
            found_args = set()
            for previous_route_item in reversed_path:
                previous_state = previous_route_item.state
                if previous_state.arg_:
                    found_args.add(previous_state.arg_)
                if previous_state.head is top_head:
                    continue
                if previous_state.head in my_heads or previous_state.head in my_args:
                    continue
                if (not closest_available_found) and previous_state.head not in found_args:
                    # print('(close arg) closest available: ', previous_state, ' for ', top_head)
                    closest_available_found = previous_state
                prev_features = previous_route_item.features
                matches = find_matches(top_features, prev_features,
                                       '-=' if closest_available_found is previous_state else '-')
                if matches:
                    new_route_item = route_item.complement(previous_route_item, checked_features=matches, long_distance=True)
                    # return self.do_operations(path + [new_route_item])
                    paths += self.do_operations(path + [new_route_item])
                    break

        return paths

    def parse(self, sentence):
        t = time.time()
        result_trees = []
        sentence = sentence.strip()
        func_parse = sentence.startswith('f(')

        self.states = {}
        self.ids = 0
        self.last_used_feature = 0
        self.exporter.reset()
        print('--------------')

        if func_parse:
            print('using func parse')
            paths = self._func_parse(sentence)
            target_linearisation = self.compute_target_linearisation(paths[0])
        else:
            target_linearisation = sentence
            paths = self._string_parse(sentence)

        print('==============')
        print(f"expecting: '{target_linearisation}'")
        print(f'{len(paths)} result paths')
        print(paths)
        good_routes = []
        bad_routes = []
        for path in paths:
            self.active_route = path
            linear = linearize(path)
            print(linear)
            route_item = path[-1]
            state = route_item.state
            is_valid = is_fully_connected(path)
            if target_linearisation == linear and is_valid:
                route_item.new_route_item(head=state.head, head_ri=route_item, msg=f'done: {linear}', entry='done()',
                                          state_type=State.DONE_SUCCESS)
                if path not in result_trees:
                    good_routes.append(path)
                    print(f'result path: {route_str(path)} is in correct order and fully connected')
                    if not func_parse:
                        print('possible derivation: ', '.'.join(route_item.state.entry for route_item in reversed(path)))
            elif show_bad_routes:
                route_item.new_route_item(head=state.head, head_ri=route_item, msg=f'fail: {linear}',
                                          entry=f'fail: {linear}', state_type=State.DONE_FAIL)
                bad_routes.append(path)
        self.exporter.export_to_kataja(good_routes + bad_routes)  # + bad_routes, good_routes)
        print()
        self.exporter.save_as_json()
        print(f'total states: {len(self.states)}')
        self.total += len(self.states)
        print('parse took ', time.time() - t)
        return good_routes


if __name__ == '__main__':
    t = time.time()
    my_lexicon = read_lexicon(open('lexicon.txt'))
    parser = Parser(my_lexicon)
    sentences = []
    readfile = open('sentences.txt', 'r')
    for line in readfile:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('['):
            sentences.append(line)
    successes = 0
    i = 0

    for i, in_sentence in enumerate(sentences, 1):
        print(f'{i}. "{in_sentence}"')
        results = parser.parse(in_sentence)
        if results:
            successes += 1

    print('=====================')
    print(f'  {successes}/{i}   ')
    print('=====================')
    print('Parsing sentences took: ', time.time() - t)
    print('Total considerations: ', parser.total)
