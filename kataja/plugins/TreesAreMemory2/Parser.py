try:
    from kataja.plugins.TreesAreMemory2.Constituent import Constituent
    from kataja.syntax.BaseFeature import BaseFeature as Feature
    from kataja.syntax.SyntaxState import SyntaxState
except ImportError:
    from Constituent import Constituent
    from Feature import Feature
    SyntaxState = None
import time

# State types
DONE_SUCCESS = 7
DONE_FAIL = 2
ADD = 0
ADJUNCT = 3
RAISE_ARG = 4
CLOSE_ARG = 5
WH_RAISE_ARG = 6


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
        if x.parts:
            _lin(x.parts[0])
            _lin(x.parts[1])
        else:
            result.append(x.label.replace('+', ' '))

    _lin(const)
    return ' '.join(result)


def has_wh(const):
    for feat in get_head_features(const):
        if feat.name == 'wh' and not feat.sign:
            return feat


def find_wh(node):
    wh_feat = has_wh(node.head)
    if wh_feat:
        return node, wh_feat
    if node.parts:
        for part in node.parts:
            found = find_wh(part)
            if found:
                return found


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
    heads = {node.head}

    def _collect_nodes(n):
        if n in done:
            return
        done.add(n)
        heads.add(n.head)
        for part in n.parts:
            _collect_nodes(part)

    _collect_nodes(node)
    for head in heads:
        for feat in get_head_features(head):
            feat.checked_by = None
            feat.checks = None


def collect_checked(const, used_features, done, inherit=False):
    if const in done:
        return
    done.add(const)
    for part in const.parts:
        collect_checked(part, used_features, done, inherit=inherit)
    for f1, f2 in const.checked_features:
        used_features.add(f1)
        used_features.add(f2)
    if inherit:
        const.inherited_features = [feat for feat in get_head_features(const.head) if feat not in used_features]


def mark_features(node):
    collect_checked(node, set(), set(), inherit=True)


def are_congruent(feats_a, feats_b):
    for feat_a in feats_a:
        if feat_a.value:
            for feat_b in feats_b:
                if feat_b.name == feat_a.name and feat_a.sign == feat_b.sign and feat_b.value and feat_b.value != feat_a.value:
                    return False
    return True


class State:
    def __init__(self, parser, parent=None, s=None, state_id=0, entry="", state_type=0):
        self.state_id = state_id
        self.s = s
        self.parent = parent
        self.parser = parser
        self.entry = entry
        self.children = []
        self.state_type = state_type

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def __repr__(self):
        return str(self.state_id)

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
        self.parser.export_to_kataja(self.s, msg, self.state_id, self.parent and self.parent.state_id, self.state_type)

    # end / start

    def start(self):
        self.parser.add_state(self)

    def crash(self):
        self.parser.remove_state(self)

    # Commands

    def wharg(self, checked_features=None):
        const = self.s
        wh_tup = find_wh(const)
        if not wh_tup:
            return self
        wh, wh_feat = wh_tup
        if checked_features:
            checked_features.append((wh_feat, wh_feat))
        else:
            checked_features = [(wh_feat, wh_feat)]
        x = Constituent(label=get_label(const.head), parts=[const, wh], head=const.head,
                        argument=wh, checked_features=checked_features)
        y = Constituent(label=x.label, parts=[x, const.right], head=x.head)

        msg = f"wh-raise : '{wh.label}' as argument for '{const.label}' ({checked_features or ''})"
        return self.new_state(y, msg, "wharg()", WH_RAISE_ARG)

    def add(self, word, wh=False):
        x = Constituent(word)
        if wh:
            wh_feat = Feature('wh')
            x.features.append(wh_feat)
            wh_feat.host = x
        x.head = x
        y = Constituent(word, parts=[x, self.s], head=x.head) if self.s else x
        msg = f'add "{word}"'
        has_wh = ', wh=True' if wh else ''
        return self.new_state(y, msg, f"f('{word}'{has_wh})", ADD)

    def add_const(self, const):
        x = Constituent(const.label, parts=[const, self.s], head=const.head) if self.s else const
        msg = f'add "{const.label}"'
        has_wh = ', wh=True' if [f for f in const.features if f.name == 'wh' and not f.sign] else ''
        return self.new_state(x, msg, f"f('{const.label}'{has_wh})", ADD)

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
        return self.new_state(y, msg, "r()", CLOSE_ARG)

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
        return self.new_state(y, msg, "arg()", RAISE_ARG)

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
        return self.new_state(y, msg, "adj()", ADJUNCT)


    def new_state(self, x, msg, entry, state_type):
        state = self.parser.add_state(self, x, entry, state_type)
        #print('creating state ', state.state_id, ' w. parent ', state.parent and state.parent.state_id, ' , ', msg)
        if self.parser.debug:
            print(f':: {msg}')
            print(f'    ->: {x}')
        state.export(msg)
        return state

    # Aliases

    def r(self):
        return self.close_argument()

    def f(self, word, wh=False):
        return self.add(word, wh=wh)


class Parser:
    def __init__(self, lexicon, forest=None, debug=True):
        self.forest = forest
        self.results = []
        self.correct = []
        self.lexicon = lexicon or {}
        self.states = []
        self.states_to_remove = set()
        self.ids = 0
        self.debug = debug
        self.expanding = False

    def add_state(self, parent=None, const=None, entry="", state_type=0):
        if parent and not parent.s:
            parent = None
        new_state = State(parser=self, s=const, parent=parent, state_id=self.ids, entry=entry, state_type=state_type)
        if parent and self.expanding:
            parent.children.append(new_state)
            self.states.append(new_state)
        else:
            self.states = [new_state]
        self.ids += 1
        return new_state

    def remove_state(self, state):
        if state in self.states:
            self.states.remove(state)

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
        self.expanding = False

        def f(word, wh=False):
            return self.states[0].add(word, wh=wh)

        func_locals = {'f': f}
        exec(sentence, globals(), func_locals)

    def _string_parse(self, sentence):
        self.expanding = True
        for word in sentence.split():
            const = self.get_from_lexicon(word)
            # May create new states to represent different parses
            self.states_to_remove = set(self.states)
            #print('==== starting attempt cycle, states to remove: ', self.states_to_remove)
            for state in list(self.states):
                self.attempt_raising(state, const)
            #print('==== ended attempt cycle, states to remove: ', self.states_to_remove)
            for state in self.states_to_remove:
                self.states.remove(state)
            for state in list(self.states):
                state.add_const(const)
                if state in self.states:
                    self.states.remove(state)
        # Finally attempt to raise what can be raised
        for state in list(self.states):
            #print('final attempts:', state.state_id)
            self.attempt_raising(state)

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
        self.add_state()

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
            print(state)

            if target_linearization == linear and self.validate_structure(state.s):
                state.new_state(state.s, f'done: {linear}', '', DONE_SUCCESS)
                result_trees.append(state.s)
                print(state.s)
                if not func_parse:
                    print(state.print_history())
            else:
                state.new_state(state.s, f'fail: {linear}', '', DONE_FAIL)

        print()
        return result_trees

    @staticmethod
    def _collect_available_features(top_head, used_features):
        return [feat for feat in get_head_features(top_head.head) if feat not in used_features]

    @staticmethod
    def _collect_wh_features(top, used_features):
        wh_tup = find_wh(top)
        if wh_tup:
            wh, wh_feat = wh_tup
            return Parser._collect_available_features(wh, used_features)
        return []

    @staticmethod
    def _find_match(target, features):
        for feat in features:
            if feat.name == target.name and (feat.value == target.value or not target.value) and not feat.sign:
                return feat

    def attempt_raising(self, state, next_const=None):
        # options are close_argument, arg, wharg and do nothing. Features of the current state may block some of these
        if not (state.s and state.s.left and state.s.right):
            self.states_to_remove.remove(state)
            return state

        used_features = set()

        collect_checked(state.s, used_features, set())

        top_features = self._collect_available_features(state.s.left, used_features)
        second_features = self._collect_available_features(state.s.right, used_features)
        # next_const_features = next_const.features if next_const else []

        # adj raise
        adj_features = second_features
        head_features = top_features
        if are_congruent(head_features, adj_features):
            for feat in head_features:
                if feat.sign == '+':
                    print('looking for match for ', feat)
                    match = self._find_match(feat, adj_features)
                    if match:
                        new_state = state.adj(checked_features=[(feat, match)])
                        new_state = self.attempt_raising(new_state, next_const=next_const)
                        self.states_to_remove.add(state)
                        return new_state

        # arg raise
        arg_features = second_features
        head_features = top_features
        for feat in head_features:
            if feat.sign == '-' or feat.sign == '=':
                match = self._find_match(feat, arg_features)
                if match:
                    new_state = state.arg(checked_features=[(feat, match)])
                    new_state = self.attempt_raising(new_state, next_const=next_const)
                    if feat.sign == '-':
                        self.states_to_remove.add(state)
                        return new_state

        # close argument
        arg_features = top_features
        head_features = second_features
        for feat in head_features:
            if feat.sign == '-' or feat.sign == '=':
                match = self._find_match(feat, arg_features)
                if match:
                    new_state = state.close_argument(checked_features=[(feat, match)])
                    self.attempt_raising(new_state, next_const=next_const)

        # wharg raise
        wh_features = self._collect_wh_features(state.s, used_features)
        head_features = top_features
        for feat in head_features:
            if feat.sign == '-' or feat.sign == '=':
                match = self._find_match(feat, wh_features)
                if match:
                    new_state = state.wharg(checked_features=[(feat, match)])
                    self.attempt_raising(new_state, next_const=next_const)
        if state in self.states_to_remove:
            self.states_to_remove.remove(state)
        return state

    def export_to_kataja(self, const, message, state_id, parent_id, state_type):
        if self.forest:
            # print('iteration ', iteration, ' : ', message)
            include_kataja_data(const)
            if const.left and const.right and state_type != DONE_SUCCESS and state_type != DONE_FAIL:
                groups = [('', [const.left]), ('', [const.right])]
            else:
                groups = []
            syn_state = SyntaxState(tree_roots=[const], msg=message, state_id=state_id, parent_id=parent_id,
                                    groups=groups, state_type=state_type)
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
