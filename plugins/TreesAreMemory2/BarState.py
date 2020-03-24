try:
    from plugins.TreesAreMemory2.BarConstituent import BarConstituent
except ImportError:
    from BarConstituent import BarConstituent

debug_state = False
debug_parse = True
debug_linearization = False


def route_str(route):
    return '_'.join(str(state.state_id) for state in route)


def get_free_precedent_from_route(route):
    if not route:
        return None
    first_head = route[-1].head
    connected = {first_head}
    for state in reversed(route):
        if state.arg_ in connected:
            connected.add(state.head)
        elif state.head in connected:
            if state.arg_:
                connected.add(state.arg_)
        elif state.head:
            return state


def get_labeled_head_from_route(route, head_label):
    if not route:
        return None
    for state in reversed(route):
        if state.head and state.head.label == head_label:
            return state


def get_stack_top_from_route(route, used_features):
    if not route:
        return None
    pops = []
    print('...start inspecting route')
    for state in reversed(route):
        if state.state_type == state.FROM_STACK:
            print('has been raised from stack ', state.arg_)
            pops.append(state.arg_)
        elif state.state_type == state.PUT_STACK:
            print('has been put into stack ', state.head)
            if pops and pops[-1] is state.head:
                print('raised and put cancel each other')
                pops.pop()
            else:
                for feature in state.head.features:
                    if not feature.sign and feature.name == 'foc' and feature not in used_features:
                        print('this state has been put up but not yet used: ', state)
                        return state


def simple_route(last_state):
    route = []
    state = last_state
    while state:
        route.append(state)
        state = state.parents[0] if state.parents else None
    return list(reversed(route))


def collect_checked_features_from_route(route):
    head = route.head
    checked = set()
    for state in route:
        if state.head is head or state.arg_ is head:
            for f1, f2 in state.checked_features:
                if f1 in head.features:
                    checked.add(f1)
                if f2 in head.features:
                    checked.add(f2)
    return checked


def collect_strong_features_from_route(route):
    if not route:
        return []
    strong_features = []
    current, *route = route
    heads = {current.head, current.arg_} if current.arg_ else {current.head}
    for state in reversed(route):
        if state.head in heads and state.state_type == state.ADD:
            strong_features += [f for f in state.head.features if f.sign == '*']
        elif state.arg_:
            if state.arg_ in heads:
                heads.add(state.head)
            elif state.head in heads:
                heads.add(state.arg_)
    return strong_features


def linearize(route):
    result = []
    raised = []
    heads = {}
    unused_heads = []
    for state in route:
        if state.state_type == state.ADD:
            heads[state.head.uid] = state.head.label
            unused_heads.append(state.head.uid)
        elif state.state_type == state.PUT_STACK:
            result.append(state.head.uid)
            raised.append(state.head.uid)
        elif state.state_type == state.FROM_STACK:
            if raised:
                arg_uid = raised.pop()
                if arg_uid in unused_heads:
                    unused_heads.remove(arg_uid)
                result.append(state.head.uid)
            else:
                return ''
        elif state.state_type == state.CLOSE_ARG:
            result.append(state.head.uid)
            result.append(state.arg_.uid)
            if state.arg_.uid in unused_heads:
                unused_heads.remove(state.arg_.uid)
        elif state.state_type == state.RAISE_ARG:
            result.append(state.head.uid)
            result.append(state.arg_.uid)
            if state.arg_.uid in unused_heads:
                unused_heads.remove(state.arg_.uid)
        else:
            print('unusable state type: ', state.state_type)
    result_labels = []
    done = set()
    for uid in result:
        if uid not in done:
            result_labels.append(heads[uid])
            done.add(uid)

    str_result = ' '.join(result_labels)
    debug_linearization and print('linearised: ', str_result)
    debug_linearization and print('unused heads: ', [heads[uid] for uid in unused_heads])
    return str_result


def is_fully_connected(route):
    heads = set()
    args = set()
    for state in reversed(route):
        if state.head and state.head not in args:
            heads.add(state.head)
        if state.arg_:
            args.add(state.arg_)
            if state.arg_ in heads:
                heads.remove(state.arg_)
    return len(heads) == 1


class State:
    # State types
    DONE_SUCCESS = 7
    DONE_FAIL = 2
    ADD = 0
    ADJUNCT = 6
    RAISE_ARG = 4
    CLOSE_ARG = 5
    FROM_STACK = 3
    PUT_STACK = 1

    @staticmethod
    def create_key(state_type, head, arg_, checked_features):
        return f'{state_type}_{head.uid if head else None}_{arg_.uid if arg_ else None}_{checked_features}'

    def __init__(self, parents=None, head=None, arg=None, entry="", state_type=-1, checked_features=None):
        self.parser = None
        self.state_id = 0
        self.head = head
        self.arg_ = arg
        if parents:
            self.parents = list(parents)
            for parent in parents:
                parent.children.append(self)
        else:
            self.parents = []
        self.entry = entry
        self.children = []
        self.state_type = state_type
        self.checked_features = checked_features or []
        self.key = ''
        self.update_key()

    def set_id(self, state_id):
        self.state_id = state_id

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def __repr__(self):
        return f'{self.state_id}. {self.key}'

    def __str__(self):
        return f'State(state_id={self.state_id}, parents={[p.state_id for p in self.parents]}, head={self.head and self.head.label}, arg={self.arg_ and self.arg_.label}, state_type={self.state_type}' + \
               f', checked_features={self.checked_features})'

    def update_key(self):
        self.key = self.create_key(self.state_type, self.head, self.arg_, self.checked_features)

    def start(self):
        self.parser.add_state(State())

    def fbuild_valid_routes(self, used_features=None, route=None, stack=None):
        # A good route doesn't have same state twice
        if route and self in route:
            return []
        used_features = used_features or set()
        route = route or []
        stack = stack or []
        # A good route doesn't use same feature twice
        for f0, f1 in self.checked_features:
            if f0 in used_features or f1 in used_features:
                #print('cancel route, features already used: ', f0, f1, used_features)
                return []
            used_features.add(f0)
            used_features.add(f1)
        # A good route doesn't raise from stack if the raised is not on top of the stack
        # Since we are traversing the route backwards, FROM_STACK and PUT_STACK are reversed in effect
        if self.state_type == self.FROM_STACK:
            stack.append(self.arg_)
        elif self.state_type == self.PUT_STACK:
            if stack and stack.pop() is not self.head:
                #print('cancel route, putting to stack something incompatible with latest FROM_STACK')
                return []

        route.append(self)
        if self.parents:
            routes = []
            for parent in self.parents:
                routes += parent.build_valid_routes(set(used_features), list(route), list(stack))
            return routes
        elif stack:  # route that starts with items already in stack is impossible
            #print('items in stack, bad branch')
            return []
        return [route]

    def build_single_route(self):
        route = [self]
        if self.parents:
            state = self.parents[0]
            while state:
                route.append(state)
                state = self.parents and self.parents[0]
        return route

    def free_precedents(self, used_features=None, connected=None):
        if used_features is None:
            used_features = set()
        if connected is None:
            connected = {self.head}
        for f0, f1 in self.checked_features:
            if f0 in used_features or f1 in used_features:
                return []
            used_features.add(f0)
            used_features.add(f1)
        if self.arg_ in connected:
            connected.add(self.head)
        elif self.head in connected:
            if self.arg_:
                connected.add(self.arg_)
        elif self.head:
            return [self]
        found_frees = []
        for parent in self.parents:
            found_frees += parent.free_precedents(set(used_features), set(connected))
        return found_frees

    # Commands

    def add(self, word):
        head = BarConstituent(word)
        msg = f'add "{word}"'
        print(msg)
        return self.new_state(head, None,  msg, f"f('{word}')", State.ADD)

    def add_const(self, head):
        msg = f'add "{head.label}"'
        debug_parse and print(msg)
        return self.new_state(head, None, msg, f"f('{head.label}')", State.ADD)

    @staticmethod
    def add_initial_const(head, parser):
        null_state = State()
        null_state.parser = parser
        msg = f'add "{head.label}"'
        return null_state.new_state(head, None, msg, f"f('{head.label}')", State.ADD, initial_state=True)

    def get_head_features(self):
        def _get_head_features(head):
            if isinstance(head, tuple):
                feats = []
                for h in head:
                    feats += [feat for feat in _get_head_features(h) if feat not in feats]
                return feats
            else:
                return head.features
        return _get_head_features(self.head)

    def collect_available_features(self, route):
        if not self.head:
            return []
        strong_features = collect_strong_features_from_route(route[:route.index(self)])
        head_features = self.get_head_features()
        return head_features + [f for f in strong_features if f not in head_features]

    # def o_adj(self, other=None):
    #     const = self.s
    #     first = const.left
    #     second = const.right
    #     trunk = const.right.right or second
    #     head = first.head if not other else second.head
    #     x = Constituent(label=f'{first.label}+{second.label}', parts=[second, first],
    #                     argument=second if not other else first,
    #                     head=head)
    #     y = Constituent(label=x.label, parts=[x, trunk], head=x.head)
    #     msg = f'raise adj: {second}'
    #     return self.new_state(y, msg, "adj()", ADJUNCT)

    def close_argument(self, head=None, checked_features=None, free_precedent=None):
        if head:
            route = simple_route(self)
            free_precedent = get_labeled_head_from_route(route, head)
        if not free_precedent:
            route = simple_route(self)
            used_features = collect_checked_features_from_route(route)
            free_precedent = get_free_precedent_from_route(route, used_features)
        head = free_precedent.head
        arg = self.head
        assert(arg and head)
        if not checked_features:
            checked_features = self.parser.speculate_features(head, arg)
        debug_parse and print(f"using '{arg.label}' as argument for previous head '{head.label}'")
        msg = f"CLOSING: set '{arg.label}' as arg for: '{head.label}' ({checked_features or ''})"
        return self.new_state(head, arg, msg, "r()", State.CLOSE_ARG, checked_features=checked_features)

    def arg(self, arg=None, checked_features=None, free_precedent=None):
        if arg:
            route = simple_route(self)
            free_precedent = get_labeled_head_from_route(route, arg)
        if not free_precedent:
            route = simple_route(self)
            used_features = collect_checked_features_from_route(route)
            free_precedent = get_free_precedent_from_route(route, used_features)
        arg = free_precedent.head
        head = self.head
        assert(arg and head)
        if not checked_features:
            checked_features = self.parser.speculate_features(head, arg, arg_first=True)
        if not arg:
            debug_parse and print(f'{self} has no free precedent for argument')
        debug_parse and print(f'raising {arg.label} as argument for {head.label}')
        msg = f"raise '{arg.label}' as arg for: '{head.label}' ({checked_features or ''})"
        return self.new_state(head, arg, msg, "arg()", State.RAISE_ARG, checked_features=checked_features)

    def put_stack(self):
        head = self.head
        msg = f"put '{head.label}' (state_id={self.state_id}) into stack for later use"
        debug_parse and print(msg)
        return self.new_state(self.head, None, msg, "put_stack()", State.PUT_STACK)

    def from_stack(self, checked_features=None, arg_state=None):
        head = self.head
        if not arg_state:
            route = self.build_single_route()
            arg_state = get_stack_top_from_route(route)
        arg = arg_state.head
        assert(arg and head)
        if not checked_features:
            checked_features = self.parser.speculate_features(head, arg, arg_first=True)
        msg = f"pull '{arg.label}' (state_id={arg_state.state_id}) from stack and merge as argument for: '{head.label}' ({checked_features or ''})"
        debug_parse and print(msg)
        return self.new_state(head, arg, msg, "from_stack()", State.FROM_STACK, checked_features=checked_features)

    # def adj(self, checked_features=None):
    #     const = self.s
    #     first = const.left
    #     second = const.right
    #     trunk = const.right.right or second
    #     head = first.head
    #     adj = second
    #     x = Constituent(label=f'{adj.label}+{first.label}', parts=[second, first], head=(adj.head, head),
    #                     checked_features=checked_features)
    #     y = Constituent(label=x.label, parts=[x, trunk], head=x.head)
    #     msg = f"raise '{adj.label}' as adj for: '{first.label}' ({checked_features or ''})"
    #     return self.new_state(y, msg, "adj()", ADJUNCT, checked_features=checked_features)

    def new_state(self, head, arg, msg, entry, state_type, checked_features=None, initial_state=False):
        parent = None if initial_state else self
        new_key = State.create_key(state_type, head, arg, checked_features or [])
        if new_key in self.parser.states:
            state = self.parser.states[new_key]
            if parent in state.parents:
                return state
            state.parents.append(parent)
            debug_state and print('using existing state: ', state.state_id, new_key)
        else:
            state = State([parent] if parent else [], head, arg, entry, state_type, checked_features)
            self.parser.add_state(state)
            debug_state and print('creating new state: ', state.state_id, new_key)
        #print('new state:', state)
        return state

    # Aliases

    def r(self, **kwargs):
        return self.close_argument(**kwargs)

    def f(self, word):
        return self.add(word)

