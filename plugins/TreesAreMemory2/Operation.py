try:
    from plugins.TreesAreMemory2.State import State
    from plugins.TreesAreMemory2.route_utils import *
except ImportError:
    from State import State
    from route_utils import *

from itertools import chain

debug_state = False


def filter_checked(features, checked_features):
    flat_list = list(chain(*checked_features))
    return [f for f in features if f not in flat_list], [f for f in features if f in flat_list]


def make_state(states, head, arg, entry, state_type, checked_features=None):
    new_key = State.create_key(state_type, head, arg, checked_features or [])
    if new_key in states:
        state = states[new_key]
        debug_state and print('using existing state: ', state.state_id, new_key)
    else:
        state = State(head, arg, entry, state_type, checked_features)
        state.state_id = len(states)
        states[state.key] = state
        debug_state and print('creating new state: ', state.state_id, new_key, state.key)
    return state


class Operation:
    """ Base class for "operator nodes" used by parser."""
    sort_order = 10

    def __init__(self, parent, state, msg, head_op=None, arg_op=None, other_head_op=None, features=None, long_distance=False):
        self.parent = parent
        self.state = state
        self.msg = msg
        self.features = []
        self.used_features = []
        self.free_precedents = []
        if features:
            self.features = features
        elif head_op:
            strong_features = filter_strong(arg_op.features) if arg_op else []
            self.features, used = filter_checked(head_op.features + strong_features, state.checked_features)
            self.used_features = head_op.used_features + used
        self.long_distance = long_distance
        self.head_op = head_op
        self.arg_op = arg_op
        self.other_head_op = other_head_op
        self.calculate_free_precedents()
        debug_state and print('creating new Operation: ', self)

    def __str__(self):
        ld = ', long_distance=True' if self.long_distance else ''
        return f'{self.get_head_label()}{self.features}, {self.state.state_type}{ld}'

    def __repr__(self):
        return f'{self.__class__.__name__}({self})'

    def __lt__(self, other):
        if isinstance(other, Operation):
            sd = self.sort_order + 10 if self.long_distance else self.sort_order
            od = other.sort_order + 10 if other.long_distance else other.sort_order
            if sd == od:
                return self.state.state_id < other.state.state_id
            else:
                return sd < od

    def __eq__(self, other):
        if isinstance(other, Operation):
            return self.state == other.state and self.features == other.features and self.free_precedents == other.free_precedents
        return False

    def __hash__(self):
        return hash(str(self.state) + str(self.features) + str(self.free_precedents))

    def get_head_label(self):
        return self.state.get_head_label()

    def get_label(self):
        return self.state.get_head_label()

    def get_arg_label(self):
        return self.state.get_arg_label()

    def calculate_free_precedents(self):
        if not self.parent:
            self.free_precedents = []
            return
        used = {self.state.head}
        if self.state.arg_:
            used.add(self.state.arg_)
        elif self.other_head_op:
            used.add(self.state.head[0])
            used.add(self.state.head[1])
        self.free_precedents = [op for op in [self.parent] + self.parent.free_precedents if op.state.head not in used]

    def as_route(self):
        route = []
        operation = self
        while operation:
            route.append(operation)
            operation = operation.parent
        return list(reversed(route))

    def first_free_precedent(self):
        if self.free_precedents:
            return self.free_precedents[0]

    def is_phase_border(self):
        for feat in self.features:
            if feat.name in phase_borders and is_positive(feat):
                return True
