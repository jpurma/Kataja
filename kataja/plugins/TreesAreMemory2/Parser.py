try:
    from kataja.plugins.TreesAreMemory2.Constituent import Constituent
    from kataja.plugins.TreesAreMemory2.WebWeaver import Web
    from kataja.syntax.BaseFeature import BaseFeature as Feature
    from kataja.syntax.SyntaxState import SyntaxState
except ImportError:
    from Constituent import Constituent
    from WebWeaver import Web
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
        if x.parts:
            _lin(x.parts[0])
            _lin(x.parts[1])
        else:
            result.append(x.label.replace('+', ' '))

    _lin(const)
    return ' '.join(result)


def has_wh(const):
    for feat in get_head_features(const):
        if feat.name == 'wh' and is_positive(feat):
            return feat


def shallow_find_wh(node):
    wh_feat = has_wh(node)
    if wh_feat:
        return node, wh_feat


# def deep_find_wh(node, at_head=None):
#     wh_feat = has_wh(node.head)
#     if wh_feat:
#         return (at_head or node), wh_feat
#     if node.parts:
#         for part in node.parts:
#             if part is node.argument or part.head is node.head:
#                 found = deep_find_wh(part, at_head=at_head or node)
#             else:
#                 found = deep_find_wh(part)
#             if found:
#                 return found


find_wh = shallow_find_wh


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
        n.inherited_features = []
        heads.add(n.head)
        for part in n.parts:
            _collect_nodes(part)

    _collect_nodes(node)
    for head in heads:
        for feat in get_head_features(head):
            feat.checked_by = None
            feat.checks = None


def collect_checked(const, used_features, done, add_kataja_props=False):
    if const in done:
        return
    done.add(const)
    for part in const.parts:
        collect_checked(part, used_features, done, add_kataja_props=add_kataja_props)
    for f1, f2 in const.checked_features:
        used_features.add(f1)
        used_features.add(f2)

    if add_kataja_props:
        const.inherited_features = [feat for feat in get_head_features(const.head) if feat not in used_features]
        for f1, f2 in const.checked_features:
            if is_positive(f1):
                f1.checks = f2
                f2.checked_by = f1
            else:
                f2.checks = f1
                f1.checked_by = f2


def collect_strong_features(const, strong_features, used_features, done, add_kataja_props=False):
    if const in done:
        return
    done.add(const)
    my_strong_features = set()
    #for part in const.parts:
    #    if part is const.head or part is const.argument or True:
    if const.parts:
        part = const.parts[0]
        if part is const.head or part is const.argument:
            collect_strong_features(part, my_strong_features, used_features, done, add_kataja_props)
    for feature in const.features:
        if feature.sign == '*':
            my_strong_features.add(feature)
    strong_features |= my_strong_features
    if add_kataja_props:
        const.inherited_features += [feat for feat in my_strong_features
                                     if feat not in used_features and feat not in const.inherited_features]


def mark_features(node):
    used_features = set()
    collect_checked(node, used_features, set(), add_kataja_props=True)
    collect_strong_features(node, set(), used_features, set(), add_kataja_props=True)


def are_congruent(feats_a, feats_b):
    for feat_a in feats_a:
        if feat_a.value:
            for feat_b in feats_b:
                if feat_b.name == feat_a.name and feat_a.sign == feat_b.sign and feat_b.value and feat_b.value != feat_a.value:
                    return False
    return True


def is_positive(feat):
    return feat.sign == '' or feat.sign == '*'


class State:
    def __init__(self, parser, parent=None, s=None, state_id=0, entry="", state_type=0):
        self.state_id = state_id
        self.s = s
        self.parent = parent
        self.parser = parser
        self.entry = entry
        self.children = []
        self.state_type = state_type
        self.stack = []

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
        self.parser.export_to_kataja(self.s, msg, self.state_id, self.parent and self.parent.state_id, self.state_type)

    # end / start

    def start(self):
        self.parser.add_state(self)

    def crash(self):
        self.parser.remove_state(self)

    # Commands

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

    def new_state(self, x, msg, entry, state_type, stack=None):
        state = self.parser.add_state(self, x, entry, state_type, stack)
        #print('creating state ', state.state_id, ' w. parent ', state.parent and state.parent.state_id, ' , ', msg)
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
        self.states_to_remove = set()
        self.ids = 0
        self.debug = debug
        self.expanding = False
        if WEAVE:
            self.web = Web()

    def add_state(self, parent=None, const=None, entry="", state_type=0, stack=None):
        if parent and not parent.s:
            parent = None
        new_state = State(parser=self, s=const, parent=parent, state_id=self.ids, entry=entry, state_type=state_type)
        if stack is not None:
            new_state.stack = stack
        elif parent:
            new_state.stack = parent.stack
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

        def f(word):
            return self.states[0].add(word)

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
            old_states = self.states
            self.states = []
            for state in old_states:
                if state not in self.states_to_remove:
                    state.add_const(const)
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
            print('state n.: ', state)

            if not state.stack and target_linearization == linear and self.validate_structure(state.s):
                state.new_state(state.s, f'done: {linear}', '', DONE_SUCCESS)
                result_trees.append(state.s)
                if not func_parse:
                    print('possible derivation: ', state.print_history())
            else:
                state.new_state(state.s, f'fail: {linear}', '', DONE_FAIL)

        print()
        if WEAVE:
            self.web.save_as_json(DATA_PATH)

        return result_trees

    @staticmethod
    def _collect_available_features(top_head, used_features):
        strong_features = set()
        collect_strong_features(top_head, strong_features, used_features, set())
        head_features = get_head_features(top_head.head)
        head_features += [f for f in strong_features if f not in head_features]

        res = [feat for feat in head_features if feat not in used_features]
        if strong_features:
            print(top_head.label, res, strong_features, used_features)
        return res

    @staticmethod
    def _find_match(target, features):
        for feat in features:
            if feat.name == target.name and (feat.value == target.value or not target.value) and is_positive(feat):
                return feat

    def attempt_raising(self, state, next_const=None):
        if not (state.s and state.s.left and state.s.right):
            self.states_to_remove.remove(state)
            return state


        used_features = set()

        collect_checked(state.s, used_features, set())
        next_features = self._collect_available_features(next_const, set()) if next_const else []
        top_features = self._collect_available_features(state.s.left, used_features)
        second_features = self._collect_available_features(state.s.right, used_features)
        # next_const_features = next_const.features if next_const else []

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

        # arg raise
        arg_features = second_features
        head_features = top_features
        for feat in head_features:
            if feat.sign == '-' or feat.sign == '=':
                match = self._find_match(feat, arg_features)
                if match:
                    important = feat.sign == '-' or True
                    if feat.name == 'foc' and not state.stack:
                        new_state = state.put_stack()
                        if important:
                            self.states_to_remove.add(state)
                    else:
                        new_state = state
                    if important:
                        self.states_to_remove.add(new_state)
                    new_state = new_state.arg(checked_features=[(feat, match)])
                    new_state = self.attempt_raising(new_state, next_const=next_const)
                    if important:
                        return new_state

        # raise from stack
        stack_features = self._collect_available_features(state.stack[-1], used_features) if state.stack else []
        head_features = top_features
        for feat in head_features:
            if feat.sign == '-' or feat.sign == '=':
                match = self._find_match(feat, stack_features)
                if match:
                    new_state = state.from_stack(checked_features=[(feat, match)])
                    self.attempt_raising(new_state, next_const=next_const)

        # close argument
        arg_features = top_features
        head_features = second_features
        for feat in head_features:
            if feat.sign == '-' or feat.sign == '=':
                match = self._find_match(feat, arg_features)
                if match:
                    new_state = state.close_argument(checked_features=[(feat, match)])
                    self.attempt_raising(new_state, next_const=next_const)

        if state in self.states_to_remove:
            self.states_to_remove.remove(state)
        return state

    def export_to_kataja(self, const, message, state_id, parent_id, state_type):
        if self.forest:
            # print('iteration ', iteration, ' : ', message)
            include_kataja_data(const)
            if WEAVE:
                self.web.weave_in(const)
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
