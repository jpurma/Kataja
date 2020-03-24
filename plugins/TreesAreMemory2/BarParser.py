try:
    from plugins.TreesAreMemory2.BarConstituent import BarConstituent
    from plugins.TreesAreMemory2.BarExporter import Exporter
    from plugins.TreesAreMemory2.BarState import State, collect_checked_features_from_route, route_str, \
        collect_strong_features_from_route, get_free_precedent_from_route, get_stack_top_from_route, \
        is_fully_connected, linearize, simple_route
    from kataja.syntax.BaseFeature import BaseFeature as Feature
except ImportError:
    from BarConstituent import BarConstituent
    from BarState import State, collect_checked_features_from_route, collect_strong_features_from_route, \
        get_free_precedent_from_route, get_stack_top_from_route, is_fully_connected, route_str, linearize, simple_route
    from BarExporter import Exporter
    from Feature import Feature
import time
from collections import Counter
from string import ascii_letters
from itertools import chain

debug_parse = True
debug_features = True


def read_lexicon(filename):
    lexicon = {}
    for line in open(filename):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        label, foo, fstring = line.partition('::')
        label = label.strip()
        feats = [Feature.from_string(fs) for fs in fstring.split()]
        const = BarConstituent(label=label, features=feats)
        lexicon[label] = const
    return lexicon


def get_label(head):
    if isinstance(head, tuple):
        return f'{get_label(head[0])}+{get_label(head[1])}'
    else:
        return head.label


def are_congruent(feats_a, feats_b):
    for feat_a in feats_a:
        if feat_a.value:
            for feat_b in feats_b:
                if feat_b.name == feat_a.name and feat_a.sign == feat_b.sign and feat_b.value and feat_b.value != feat_a.value:
                    return False
    return True


def is_positive(feat):
    return feat.sign == '' or feat.sign == '*'


def strictly_in(feat, feats):
    for f in feats:
        if feat is f:
            return True


def has_focus(feats):
    for f in feats:
        if f.name == 'foc' and is_positive(f):
            return True


def add_focus_feature(head):
    for feat in head.features:
        if feat.name == 'foc' and feat.sign == '*':
            return
    foc = Feature('foc') #, sign='*')
    head.features.append(foc)
    foc.host = head


def stack_heads(path):
    if not path:
        return []
    added = []
    for state in path:
        if state.state_type == state.FROM_STACK:
            added.pop()
        elif state.state_type == state.PUT_STACK:
            added.append(state.head)
    return added


class Parser:
    def __init__(self, lexicon, forest=None):
        self.exporter = Exporter(forest)
        self.results = []
        self.correct = []
        self.lexicon = lexicon or {}
        self.states = {}
        self.func_state = None
        self.ids = 0
        self.total = 0
        self.func_parsing = False
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
        if self.func_parsing:
            self.func_state = new_state
        self.states[new_state.key] = new_state
        return new_state

    @staticmethod
    def compute_target_linearisation(sentence):
        words = []
        in_word = False
        for part in sentence.split("'"):
            if in_word:
                words.append(part)
                in_word = False
            else:
                in_word = True
        return ' '.join(words)

    def _func_parse(self, sentence):

        def f(word):
            if self.func_state:
                return self.func_state.add(word)
            else:
                const = BarConstituent(word)
                return State.add_initial_const(const, self)

        func_locals = {'f': f}
        self.func_parsing = True
        exec(sentence, globals(), func_locals)
        self.func_parsing = False
        return [simple_route(self.func_state)]

    def _string_parse(self, sentence):
        paths = []
        for word in sentence.split():
            paths = list(chain.from_iterable(self.do_operations(path) for path in paths))
            paths = [self.do_stack_put(path) for path in paths]
            const = self.get_from_lexicon(word)
            if paths:
                paths = [path + [path[-1].add_const(const)] for path in paths]
            else:
                paths = [[State.add_initial_const(const, self)]]

        # Finally attempt to raise what can be raised
        paths = list(chain.from_iterable(self.do_operations(path) for path in paths))
        return paths

    def get_from_lexicon(self, word):
        const = self.lexicon[word]
        if isinstance(const, BarConstituent):
            const = const.copy()
        else:
            const = BarConstituent(label=const.label, features=[x.copy() for x in const.features])
            for f in const.features:
                f.host = const
        const.uid = self.get_const_uid(const)
        const.head = const
        return const

    def speculate_features(self, head, arg, arg_first=False):
        pos_feature = Feature(ascii_letters[self.last_used_feature], sign='')
        neg_feature = Feature(ascii_letters[self.last_used_feature], sign='-')
        self.last_used_feature += 1
        head.features.append(pos_feature)
        pos_feature.host = head
        arg.features.append(neg_feature)
        neg_feature.host = arg
        if arg_first:
            return [(neg_feature, pos_feature)]
        else:
            return [(pos_feature, neg_feature)]

    @staticmethod
    def _find_matches(pos_features, neg_features, neg_signs='-='):
        matches = []
        for pos_feat in pos_features:
            if is_positive(pos_feat):
                for neg_feat in neg_features:
                    if neg_feat.sign and neg_feat.name == pos_feat.name and neg_feat.sign in neg_signs and \
                            (pos_feat.value == neg_feat.value or not neg_feat.value):
                        matches.append((pos_feat, neg_feat))
                        break  # one pos feature can satisfy only one neg feature
        return matches

    def do_stack_put(self, path):
        if not path:
            return []
        state = path[-1]
        if state.head: # and state.head not in stack_heads(path):
            for feat in state.head.features:
                if feat.name == 'foc' and is_positive(feat):
                    new_state = state.put_stack()
                    print('>>> putting to stack, new state: ', new_state)
                    path += [new_state]
        return path

    def do_operations(self, path):
        path_str = route_str(path)
        debug_parse and print('attempt raising ', path_str)
        state = path[-1]
        if not state.head:
            return {path}
        used_features_for_top = collect_checked_features_from_route(path)
        print('checked features:', used_features)
        precedent = get_free_precedent_from_route(path, used_features)
        stack_top = get_stack_top_from_route(path, used_features)
        print('stack top:', stack_top)
        top_features = [f for f in state.collect_available_features(path) if not strictly_in(f, used_features)]
        if precedent and precedent.head:
            second_features = [f for f in precedent.collect_available_features(path) if not strictly_in(f, used_features)]
        else:
            second_features = []
        assert not precedent or (precedent.head is not state.head)
        debug_features and print('my features: ', top_features)
        debug_features and print('precedent features: ', second_features)
        paths = []
        # raise from stack

        if stack_top and stack_top.head != state.head:
            stack_features = [f for f in stack_top.collect_available_features(path) if not strictly_in(f, used_features)]
            debug_features and print('stack_features: ', stack_features)
            head_features = top_features
            stack_focus_features = [f for f in stack_features if f.name == 'foc' and is_positive(f)]
            print('head:', state, head_features)
            print('stack:', stack_top, stack_focus_features)
            assert(stack_focus_features)
            stack_focus_feature = stack_focus_features[0]
            head_focus_feature = [f for f in head_features if f.name == 'foc' and f.sign == '_']
            if head_focus_feature:
                head_focus_feature = head_focus_feature[0]
                matches = self._find_matches(stack_features, head_features, '=-')
                if matches:
                    new_state = state.from_stack(checked_features=[(stack_focus_feature, head_focus_feature)] + matches, arg_state=stack_top)
                    paths += self.do_operations(path + [new_state])

        # close argument (H ARG)
        arg_features = top_features
        head_features = second_features
        matches = self._find_matches(arg_features, head_features, '-=')
        if matches:
            new_state = state.close_argument(free_precedent=precedent, checked_features=matches)
            paths += self.do_operations(path + [new_state])

        paths.append(path)
        return paths

    def parse(self, sentence):
        t = time.time()
        result_trees = []
        sentence = sentence.strip()
        func_parse = sentence.startswith('f(')

        self.states = {}
        self.ids = 0
        self.last_used_feature = 0
        self.func_state = None
        self.exporter.reset()
        print('--------------')

        if func_parse:
            print('using func parse')
            target_linearisation = self.compute_target_linearisation(sentence)
            paths = self._func_parse(sentence)
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
            state = path[-1]
            if target_linearisation == linear and is_fully_connected(path):
                new_state = state.new_state(state.head, None, f'done: {linear}', 'done()', State.DONE_SUCCESS)
                new_path = path + [new_state]
                if new_path not in result_trees:
                    good_routes.append(new_path)
                    print(f'result path: {route_str(path)} is in correct order and fully connected')
                    if not func_parse:
                        print('possible derivation: ', '.'.join(state.entry for state in reversed(new_path)))
            else:
                #new_state = state.new_state(state.head, None, f'fail', 'fail()', State.DONE_FAIL)
                #new_path = path + [new_state]
                #bad_routes.append(new_path)
                bad_routes.append(path)
        self.exporter.export_to_kataja(good_routes + bad_routes) # + bad_routes, good_routes)
        print()
        self.exporter.save_as_json()
        print(f'total states: {len(self.states)}')
        self.total += len(self.states)
        print('parse took ', time.time() - t)
        return good_routes


if __name__ == '__main__':
    t = time.time()
    lexicon = read_lexicon('lexicon.txt')
    parser = Parser(lexicon)
    sentences = []
    readfile = open('bar_sentences.txt', 'r')
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
