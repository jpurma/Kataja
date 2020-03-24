try:
    from plugins.TreesAreMemory2.Constituent import Constituent
    from plugins.TreesAreMemory2.WebWeaver import Web
    from kataja.syntax.BaseFeature import BaseFeature as Feature
    from kataja.syntax.SyntaxState import SyntaxState
except ImportError:
    from Constituent import Constituent
    from WebWeaver import Web
    from Feature import Feature
    SyntaxState = None
import time
from collections import Counter

# State types
DONE_SUCCESS = 7
DONE_FAIL = 2
ADD = 0
ADJUNCT = 3
RAISE_ARG = 4
CLOSE_ARG = 5
FROM_STACK = 6
PUT_STACK = 1

WEAVE = False

DATA_PATH = 'webviewer/data/data.json'


def read_lexicon(filename):
    lexicon = {}
    for line in open(filename):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        label, foo, fstring = line.partition('::')
        label = label.strip()
        feats = [Feature.from_string(fs) for fs in fstring.split()]
        const = Constituent(label=label, features=feats, set_hosts=True)
        lexicon[label] = const
    return lexicon


def linearize(const):
    done = set()
    result = []

    def _lin(x):
        if not x or x in done:
            return
        done.add(x)
        result.append(x.label.replace('+', ' '))

    _lin(const)
    return ' '.join(result)


def include_kataja_data(node):
    reset_features(node)
    mark_features(node)


def get_head_features(head):
    if isinstance(head, tuple):
        feats = []
        for h in head:
            feats += [feat for feat in get_head_features(h) if feat not in feats]
        return feats
    else:
        return head.features


def get_label(head):
    if isinstance(head, tuple):
        return f'{get_label(head[0])}+{get_label(head[1])}'
    else:
        return head.label


def reset_features(node):
    done = set()

    def _reset_features(n):
        if n in done:
            return
        done.add(n)
        n.inherited_features = []
        for feat in n.features:
            feat.checked_by = None
            feat.checks = None
        for part in n.parts:
            _reset_features(part)

    _reset_features(node)


def collect_strong_features(const, done=None):
    if done is None:
        done = set()
    elif const in done:
        return set()
    done.add(const)
    strong_features = set()
    for part in const.parts:
        if part.head is const.head or part is const.argument:
            strong_features |= collect_strong_features(part, done)
    for feature in const.features:
        if feature.sign == '*':
            strong_features.add(feature)
    return strong_features


def mark_features(top_node):
    done = {}

    def _mark_features(node):
        if node.uid in done:
            return done[node.uid]
        checked_here = []
        for f1, f2 in node.checked_features:
            if is_positive(f1):
                f1.checks = f2
                f2.checked_by = f1
            else:
                f2.checks = f1
                f1.checked_by = f2
            checked_here.append(f1)
            checked_here.append(f2)
        node.inherited_features = []
        my_strong_features = [f for f in node.features if f.sign == '*']
        my_head_features = [f for f in node.features if f.sign != '*']
        for part in node.parts:
            strong_features, head_features = _mark_features(part)
            if part.head is node.head or node.argument is part:
                my_strong_features += strong_features
                if part.head is node.head:
                    my_head_features += head_features

        node.inherited_features = my_head_features + my_strong_features
        my_strong_features = [f for f in my_strong_features if not strictly_in(f, checked_here)]
        my_head_features = [f for f in my_head_features if not strictly_in(f, checked_here)]
        done[node.uid] = my_strong_features, my_head_features
        return my_strong_features, my_head_features

    _mark_features(top_node)


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


def unsatisfied_mandatory(features, matches):
    for feat in features:
        if feat.sign == '_':
            found = False
            for pos_f, neg_f in matches:
                if neg_f is feat:
                    found = True
                    break
            if not found:
                return True


class State:
    def __init__(self, parent=None, s=None, entry="", state_type=0, stack=None, checked_features=None):
        self.parser = None
        self.state_id = 0
        self.s = s
        if parent and parent.s:
            self.parent = parent
            parent.children.append(self)
        else:
            self.parent = None
        self.entry = entry
        self.children = []
        self.state_type = state_type
        if stack is None and parent:
            self.stack = list(parent.stack)
        else:
            self.stack = stack or []
        self.checked_features = checked_features or []

    def set_id(self, state_id):
        self.state_id = state_id

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def __repr__(self):
        return f'{self.state_id}. {self.print_history()}'

    def print_history(self):
        entries = []
        state = self
        while state:
            if state.entry:
                entries.append(state.entry)
            state = state.parent
        entries.reverse()
        return '.'.join(entries)

    def export(self, msg):
        self.parser.export_to_kataja(self, msg)

    def start(self):
        self.parser.add_state(State())

    # Commands

    def collect_checked_features_with_nodes(self):
        if self.parent:
            return self.parent.collect_checked_features_with_nodes() + [(self.s, self.checked_features)]
        else:
            return [(self.s, self.checked_features)]

    def collect_checked_features(self):
        checked = set()
        for f1, f2 in self.checked_features:
            checked.add(f1)
            checked.add(f2)
        if self.parent:
            return self.parent.collect_checked_features() | checked
        else:
            return checked

    def add(self, word):
        x = Constituent(word)
        x.head = x
        y = Constituent(word, parts=[x, self.s], head=x.head) if self.s else x
        msg = f'add "{word}"'
        return self.new_state(y, msg, f"f('{word}')", ADD)

    def add_const(self, const):
        x = Constituent(const.label, parts=[const, self.s], head=const.head) if self.s else const
        msg = f'add "{const.label}"'
        return self.new_state(x, msg, f"f('{const.label}')", ADD)

    def o_adj(self, other=None):
        const = self.s
        first = const.left
        second = const.right
        trunk = const.right.right or second
        head = first.head if not other else second.head
        x = Constituent(label=f'{first.label}+{second.label}', parts=[second, first],
                        argument=second if not other else first,
                        head=head)
        y = Constituent(label=x.label, parts=[x, trunk], head=x.head)
        msg = f'raise adj: {second}'
        return self.new_state(y, msg, "adj()", ADJUNCT)

    def close_argument(self, checked_features=None):
        const = self.s
        first = const.left
        second = const.right
        trunk = const.right.right or second
        head = second.head
        arg = first
        x = Constituent(label=second.label, parts=[second, first],
                        argument=arg, head=head, checked_features=checked_features)
        y = Constituent(label=x.label, parts=[x, trunk], head=x.head)
        msg = f"CLOSING: set '{arg.label}' as arg for: '{second.label}', when third is {trunk.label} ({checked_features or ''})"
        return self.new_state(y, msg, "r()", CLOSE_ARG, checked_features=checked_features)

    def arg(self, checked_features=None):
        const = self.s
        first = const.left
        second = const.right
        trunk = const.right.right or second
        head = first.head
        arg = second
        x = Constituent(label=first.label, parts=[second, first],
                        argument=arg, head=head, checked_features=checked_features)
        y = Constituent(label=x.label, parts=[x, trunk], head=x.head)
        msg = f"raise '{arg.label}' as arg for: '{first.label}' ({checked_features or ''})"
        return self.new_state(y, msg, "arg()", RAISE_ARG, checked_features=checked_features)

    def put_stack(self):
        const = self.s
        stack = list(self.stack)
        stack.append(const.right)
        msg = f"put '{const.right.label}' into stack for later use"
        return self.new_state(const, msg, "put_stack()", PUT_STACK, stack=stack)

    def from_stack(self, checked_features=None):
        const = self.s
        stack = list(self.stack)
        stack_node = stack.pop()
        x = Constituent(label=const.left.label, parts=[stack_node, const.left],
                        argument=stack_node, head=const.left.head, checked_features=checked_features)
        y = Constituent(label=x.label, parts=[x, const.right], head=x.head)
        msg = f"pull '{stack_node.label}' from stack and merge as argument for: '{const.label}'"

        return self.new_state(y, msg, "from_stack()", FROM_STACK, stack=stack)

    def adj(self, checked_features=None):
        const = self.s
        first = const.left
        second = const.right
        trunk = const.right.right or second
        head = first.head
        adj = second
        x = Constituent(label=f'{adj.label}+{first.label}', parts=[second, first], head=(adj.head, head),
                        checked_features=checked_features)
        y = Constituent(label=x.label, parts=[x, trunk], head=x.head)
        msg = f"raise '{adj.label}' as adj for: '{first.label}' ({checked_features or ''})"
        return self.new_state(y, msg, "adj()", ADJUNCT, checked_features=checked_features)

    def new_state(self, x, msg, entry, state_type, stack=None, checked_features=None):
        state = State(self, x, entry, state_type, stack, checked_features)
        self.parser.add_state(state)
        if self.parser.debug:
            print(f':: {msg}')
            print(f'    ->: {x}')
        state.export(msg)
        return state

    # Aliases

    def r(self):
        return self.close_argument()

    def f(self, word):
        return self.add(word)


class Parser:
    def __init__(self, lexicon, forest=None, debug=True):
        self.forest = forest
        self.results = []
        self.correct = []
        self.lexicon = lexicon or {}
        self.states = []
        self.ids = 0
        self.debug = debug
        self.func_parsing = False
        self.total = 0
        self.state_count = Counter()
        if WEAVE:
            self.web = Web()

    def add_state(self, new_state):
        new_state.state_id = self.ids
        new_state.parser = self
        self.ids += 1
        if self.func_parsing:
            self.states = [new_state]
        self.total += 1
        return new_state

    @staticmethod
    def compute_target_linearization(sentence):
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
            return self.states[0].add(word)
        func_locals = {'f': f}
        self.func_parsing = True
        exec(sentence, globals(), func_locals)
        self.func_parsing = False

    def _string_parse(self, sentence):

        first = True
        for word in sentence.split():
            const = self.get_from_lexicon(word)
            if first:  # the first word will always get focus feature, makes sense at least in finnish
                if not has_focus(const.features):
                    const.features.append(Feature(name='foc', sign='*'))
            states_before_raising = self.states
            self.states = []
            for state in states_before_raising:
                self.states += self.attempt_raising(state, const)
            states_before_addition = self.states
            self.states = []
            for state in states_before_addition:
                new_state = state.add_const(const)
                self.states.append(new_state)
            first = False
        # Finally attempt to raise what can be raised
        states_before_raising = self.states
        self.states = []
        for state in states_before_raising:
            self.states += self.attempt_raising(state)

    def get_from_lexicon(self, word):
        const = self.lexicon[word].copy()
        const.head = const
        return const

    @staticmethod
    def validate_structure(const):
        """ See if there are any constituents that are not connected into each other by head- or argument relation"""
        done = set()
        valid = {const}

        def walk_and_validate(con):
            if con in done:
                return
            done.add(con)
            for child in con.parts:
                if child.head == con.head or con.argument == child:  # argument relation
                    valid.add(child)
                elif isinstance(con.head, tuple) and child.head in con.head:  # adjunct
                    valid.add(child)
                walk_and_validate(child)

        walk_and_validate(const)
        return len(done) == len(valid)

    def parse(self, sentence):
        result_trees = []
        sentence = sentence.strip()
        func_parse = sentence.startswith('f(')

        self.states = []
        self.ids = 0
        self.total = 0
        self.state_count = Counter()
        initial_state = State()
        self.add_state(initial_state)
        self.states.append(initial_state)

        print('--------------')

        if func_parse:
            target_linearization = self.compute_target_linearization(sentence)
            self._func_parse(sentence)
        else:
            target_linearization = sentence
            self._string_parse(sentence)

        print('==============')
        print(f"expecting: '{target_linearization}'")

        for state in list(self.states):
            linear = linearize(state.s)
            print('state n.: ', state)

            if not state.stack and target_linearization == linear and self.validate_structure(state.s):
                state.new_state(state.s, f'done: {linear}', '', DONE_SUCCESS)
                result_trees.append(state.s)
                if not func_parse:
                    print('possible derivation: ', state.print_history())
            else:
                state.new_state(state.s, f'fail: {linear}', '', DONE_FAIL)

        print()
        if self.state_count:
            print(len(self.state_count), self.total, self.total / len(self.state_count))
        if WEAVE:
            self.web.save_as_json(DATA_PATH)

        return result_trees

    @staticmethod
    def _collect_available_features(top_head):
        strong_features = collect_strong_features(top_head)
        head_features = get_head_features(top_head.head)
        return head_features + [f for f in strong_features if f not in head_features]

    @staticmethod
    def _find_match(target, features):
        for feat in features:
            if feat.name == target.name and (feat.value == target.value or not target.value) and is_positive(feat):
                return feat

    @staticmethod
    def _find_matches(pos_features, neg_features, neg_signs='-='):
        matches = []
        for pos_feat in pos_features:
            if is_positive(pos_feat):
                for neg_feat in neg_features:
                    if neg_feat.sign and neg_feat.name == pos_feat.name and neg_feat.sign in neg_signs and \
                            (pos_feat.value == neg_feat.value or not neg_feat.value):
                        matches.append((pos_feat, neg_feat))
        return matches
        # adj raise
        # adj_features = second_features
        # head_features = top_features
        # if are_congruent(head_features, adj_features):
        #     for feat in head_features:
        #         if feat.sign == '+':
        #             match = self._find_match(feat, adj_features)
        #             if match:
        #                 new_state = state.adj(checked_features=[(feat, match)])
        #                 new_state = self.attempt_raising(new_state, next_const=next_const)
        #                 self.states_to_remove.add(state)
        #                 return new_state

    def attempt_raising(self, state, next_const=None):
        if not (state.s and state.s.left and state.s.right):
            return [state]

        states = []
        used_features = state.collect_checked_features()
        # next_features = self._collect_available_features(next_const, set()) if next_const else []
        top_features = [f for f in self._collect_available_features(state.s.left) if not strictly_in(f, used_features)]
        second_features = [f for f in self._collect_available_features(state.s.right) if not strictly_in(f, used_features)]
        next_const_features = next_const.features if next_const else []
        f_string = f'{state.s.left.label}:{top_features},{state.s.right.label}:{second_features}'
        self.state_count[f_string] += 1

        # raise from stack
        if state.stack:
            stack_features = [f for f in self._collect_available_features(state.stack[-1]) if f not in used_features]
            head_features = top_features
            matches = self._find_matches(stack_features, head_features, '_-=')
            if matches:  # and not unsatisfied_mandatory(stack_features, matches):
                new_state = state.from_stack(checked_features=matches)
                states += self.attempt_raising(new_state, next_const=next_const)

        # arg raise (ARG H)
        arg_features = second_features
        head_features = top_features
        matches = self._find_matches(arg_features, head_features, '-')
        if matches:  # and not unsatisfied_mandatory(arg_features, matches):
            new_state = state
            stack_put = False
            for fpos, fneg in matches:
                if fpos.name == 'foc' and not state.stack:
                    new_state = state.put_stack()
                    stack_put = True
            new_state = new_state.arg(checked_features=matches)
            if stack_put and len(matches) > 1:
                new_state.stack.pop()
            return self.attempt_raising(new_state, next_const=next_const)

        # close argument (H ARG)
        if not has_focus(next_const_features):
            arg_features = top_features
            head_features = second_features
            matches = self._find_matches(arg_features, head_features, '_-=')
            if matches:  # and not unsatisfied_mandatory(arg_features, matches):
                new_state = state.close_argument(checked_features=matches)
                states += self.attempt_raising(new_state, next_const=next_const)

        states.append(state)
        return states

    def export_to_kataja(self, state, message):
        if self.forest:
            # print('iteration ', iteration, ' : ', message)
            const = state.s
            include_kataja_data(const)
            if WEAVE:
                self.web.weave_in(const)
            if const.left and const.right and state.state_type != DONE_SUCCESS and state.state_type != DONE_FAIL:
                groups = [('', [const.left]), ('', [const.right])]
            else:
                groups = [('', []), ('', [])]
            groups.append(('', state.stack))
            syn_state = SyntaxState(tree_roots=[const], msg=message, state_id=state.state_id,
                                    parent_id=state.parent and state.parent.state_id,
                                    groups=groups, state_type=state.state_type)
            self.forest.add_step(syn_state)


debug_all = False
debugs = []

if __name__ == '__main__':
    t = time.time()
    lexicon = read_lexicon('lexicon.txt')
    parser = Parser(lexicon)
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
        parser.debug = debug_all or (i in debugs)
        results = parser.parse(in_sentence)
        if results:
            successes += 1

    print('=====================')
    print(f'  {successes}/{i}   ')
    print('=====================')
    print('Parsing sentences took: ', time.time() - t)
    print('Total considerations: ', parser.total)
