try:
    from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
    from plugins.TreesAreMemory2.Feature import Feature
    from plugins.TreesAreMemory2.State import State
    from plugins.TreesAreMemory2.route_utils import *
except ImportError:
    from SimpleConstituent import SimpleConstituent
    from Feature import Feature
    from State import State
    from route_utils import *
from itertools import chain
from collections import Iterable

debug_state = False
debug_parse = False
debug_func_parse = False


def filter_checked(features, checked_features):
    flat_list = list(chain(*checked_features))
    return [f for f in features if f not in flat_list], [f for f in features if f in flat_list]


def make_state(parser, head, arg, entry, state_type, checked_features=None):
    new_key = State.create_key(state_type, head, arg, checked_features or [])
    if new_key in parser.states:
        state = parser.states[new_key]
        debug_state and print('using existing state: ', state.state_id, new_key)
    else:
        state = State(head, arg, entry, state_type, checked_features)
        parser.add_state(state)
        debug_state and print('creating new state: ', state.state_id, new_key, state.key)
    return state


class Context:
    def __init__(self):
        self.context = None


context = Context()


class Operation:
    sort_order = 10

    def __init__(self, state, msg, head_op=None, arg_op=None, features=None, long_distance=False):
        self.state = state
        self.msg = msg
        self.features = []
        self.used_features = []
        if features:
            self.features = features
        elif head_op:
            strong_features = filter_strong(arg_op.features) if arg_op else []
            self.features, used = filter_checked(head_op.features + strong_features, state.checked_features)
            self.used_features = head_op.used_features + used
        self.long_distance = long_distance
        debug_state and print('creating new Operation: ', self)

    def __str__(self):
        ld = ', long_distance=True' if self.long_distance else ''
        return f'{self.get_head_label()}{self.features}, {self.state.state_type}{ld}'

    def __repr__(self):
        return f'{self.__class__.__name__}({self})'

    def __lt__(self, other):
        if isinstance(other, Operation):
            return self.__class__.sort_order < other.__class__.sort_order

    def get_head_label(self):
        return self.state.get_head_label()

    def get_label(self):
        return self.state.get_head_label()

    def get_arg_label(self):
        return self.state.get_arg_label()

    # Func parse methods -- these are only necessary for testing structures with function chain notation
    # eg. "f('Pekka').f('loves').spec().f('Merja').comp()"

    @staticmethod
    def func_add(word, *feats):
        head = SimpleConstituent(word)
        if feats:
            if isinstance(feats, str):
                feats = [feats]
            head.features = [Feature.from_string(f) for f in feats]
        new_operation = Add(context.parser, head)
        context.parser.active_route.append(new_operation)
        return new_operation

    def func_complement(self, with_feat=''):
        arg = self.state.head
        long_distance = False
        if with_feat:
            debug_func_parse and print('doing func complement with feat ', with_feat)
            pos_feat = Feature.from_string(with_feat)
            match = get_operation_with_feature_match(context.parser.active_route, pos_feat)
            if match:
                head_op, neg_feat = match
                long_distance = head_op is not get_free_precedent_from_route(context.parser.active_route)
                debug_func_parse and print('found route item for head: ', head_op, head_op.state, neg_feat)
            else:
                raise KeyError(f'No match for feature {pos_feat}')
            head = head_op.state.head
            arg_feats = get_features(arg)
            if pos_feat in arg_feats:
                for feat in arg_feats:
                    if feat == pos_feat:
                        pos_feat = feat
            else:
                add_feature(arg, pos_feat)
            for feat in get_features(head):
                if feat == neg_feat:
                    neg_feat = feat
            checked_features = [(neg_feat, pos_feat)]
        else:
            head_op = get_free_precedent_from_route(context.parser.active_route)
            debug_func_parse and print('free precedent from ', context.parser.active_route, ' is ', head_op)
            if head_op:
                head = head_op.state.head
            else:
                print(f'No free precedent at {context.parser.active_route}')
                return self
            matches = find_matches(self.features, head_op.features)
            if matches:
                arg_feat, head_feat = matches[0]
            else:
                arg_feat, head_feat  = context.parser.speculate_features(head, arg)
                context.parser.add_feat_to_route(head_feat, head)
                context.parser.add_feat_to_route(arg_feat, arg)
            checked_features = [(arg_feat, head_feat)]
        new_operation = Comp(context.parser, self, head_op, checked_features, long_distance=long_distance)
        context.parser.active_route.append(new_operation)
        return new_operation

    def func_specifier(self, with_feat=''):
        head = self.state.head
        long_distance = False
        if with_feat:
            neg_feat = Feature.from_string(with_feat)
            match = get_operation_with_feature_match(context.parser.active_route, neg_feat)
            if match:
                arg_item, pos_feat = match
                long_distance = arg_item is not get_free_precedent_from_route(context.parser.active_route)
                debug_func_parse and print('found route item for arg: ', arg_item, arg_item.state, pos_feat)
            else:
                raise KeyError(f'No match for feature {neg_feat} at {context.parser.active_route}')

            arg = arg_item.state.head
            if neg_feat in get_features(head):
                for feat in get_features(head):
                    if feat == neg_feat:
                        neg_feat = feat
            else:
                add_feature(head, neg_feat)
            for feat in get_features(arg):
                if feat == pos_feat:
                    pos_feat = feat
            checked_features = [(pos_feat, neg_feat)]
        else:
            arg_item = get_free_precedent_from_route(context.parser.active_route)
            if arg_item:
                arg = arg_item.state.head
            else:
                #raise KeyError(f'No free precedent at {self.parser.active_route}')
                print(f'No free precedent at {context.parser.active_route}')
                return self
            matches = find_matches(arg_item.features, self.features)
            if matches:
                arg_feat, head_feat = matches[0]
            else:
                arg_feat, head_feat = context.parser.speculate_features(head, arg)
                context.parser.add_feat_to_route(head_feat, head)
                context.parser.add_feat_to_route(arg_feat, arg)
            checked_features = [(arg_feat, head_feat)]
        if not arg:
            debug_func_parse and print(f'{self} has no free precedent for argument')
        new_operation = Spec(context.parser, self, arg_item, checked_features, long_distance=long_distance)
        context.parser.active_route.append(new_operation)
        return new_operation

    def func_adjunct(self):
        other_head_op = get_free_precedent_from_route(context.parser.active_route)
        new_operation = Adj(context.parser, self, other_head_op, [])
        context.parser.active_route.append(new_operation)
        return new_operation

    # Aliases
    comp = func_complement
    spec = func_specifier
    f = func_add
    adj = func_adjunct


class Add(Operation):
    sort_order = 3

    def __init__(self, parser, const):
        msg = f"add '{const.label}'"
        state = make_state(parser, const, None, f"f('{const.label}')", State.ADD)
        Operation.__init__(self, state, msg, features=state.head.features)


class Spec(Operation):
    sort_order = 1

    def __init__(self, parser, head_op, spec_op, checked_features, long_distance=False):
        head = head_op.state.head
        arg = spec_op.state.head
        ld = ' (long distance)' if long_distance else ''
        msg = f"raise '{spec_op.get_head_label()}' as specifier arg for: '{head_op.get_head_label()}' ({checked_features or ''}){ld}"
        state = make_state(parser, head, arg, "spec()", State.SPECIFIER, checked_features)
        Operation.__init__(self, state, msg, head_op=head_op, arg_op=spec_op, long_distance=long_distance)


class Comp(Operation):
    sort_order = 2

    def __init__(self, parser, comp_op, head_op, checked_features, long_distance=False):
        head = head_op.state.head
        arg = comp_op.state.head
        ld = ' (long distance)' if long_distance else ''
        msg = f"set '{comp_op.get_head_label()}' as complement arg for: '{head_op.get_head_label()}' ({checked_features or ''}){ld}"
        state = make_state(parser, head, arg, "comp()", State.COMPLEMENT, checked_features)
        Operation.__init__(self, state, msg, head_op=head_op, arg_op=comp_op, long_distance=long_distance)


class Adj(Operation):
    sort_order = 4

    def __init__(self, parser, head_op, other_head_op, shared_features):
        head = head_op.state.head
        other_head = other_head_op.state.head
        msg = f"set '{other_head_op.get_head_label()}' as adjunct for {head_op.get_head_label()} ({shared_features})"
        state = make_state(parser, (other_head, head), None, "adj()", State.ADJUNCT)
        Operation.__init__(self, state, msg, head_op=head_op)


class Done(Operation):
    sort_order = 0

    def __init__(self, parser, head_op, msg=""):
        head = head_op.state.head
        state = make_state(parser, head, None, "done()", State.DONE_SUCCESS)
        Operation.__init__(self, state, msg, head_op=head_op)


class Fail(Operation):
    sort_order = 8

    def __init__(self, parser, head_op, msg=""):
        head = head_op.state.head
        state = make_state(parser, head, None, "fail()", State.DONE_FAIL)
        Operation.__init__(self, state, msg, head_op=head_op)
