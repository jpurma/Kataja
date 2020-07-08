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
debug_parse = True


def filter_checked(features, checked_features):
    flat_list = list(chain(*checked_features))
    return [f for f in features if f not in flat_list], [f for f in features if f in flat_list]


class RouteItem:
    def __init__(self, state, features, parser, used_features=None, long_distance=False):
        self.state = state
        self.features = list(features)
        self.used_features = list(used_features) if used_features else []
        self.parser = parser
        self.parents = []
        self.long_distance = long_distance

    def __str__(self):
        ld = ', long_distance=True' if self.long_distance else ''
        return f'{self.get_head_label()}{self.features}, {self.state.state_type}{ld}'

    def __repr__(self):
        return f'RouteItem({self})'

    def get_head_label(self):
        return self.state.get_head_label()

    def get_label(self):
        return self.state.get_head_label()

    def get_arg_label(self):
        return self.state.get_arg_label()

    def new_route_item(self, head=None, head_ri=None, arg=None, arg_ri=None, msg='', entry='', state_type=None,
                       checked_features=None, features=None, long_distance=False):
        checked_features = checked_features or []
        new_key = State.create_key(state_type, head, arg, checked_features)
        if new_key in self.parser.states:
            state = self.parser.states[new_key]
            debug_state and print('using existing state: ', state.state_id, new_key)
        else:
            state = State(head, arg, entry, state_type, checked_features)
            self.parser.add_state(state)
            debug_state and print('creating new state: ', state.state_id, new_key)
        if features:
            used_features = []
        elif head_ri:
            strong_features = filter_strong(arg_ri.features) if arg_ri else []
            features, used = filter_checked(head_ri.features + strong_features, checked_features)
            used_features = head_ri.used_features + used
        else:
            features, used_features = filter_checked(get_features(head), checked_features)
        new_route_item = RouteItem(state, features, self.parser, used_features=used_features, long_distance=long_distance)
        debug_state and print('creating new route item: ', new_route_item, state.state_id, new_route_item.features)
        self.parser.active_route.append(new_route_item)
        return new_route_item

    # Func parse methods

    @staticmethod
    def create_initial_state(head, parser, feats=None):
        if feats:
            if isinstance(feats, str):
                feats = [feats]
            head.features += [Feature.from_string(f) for f in feats]
        state = State(head, None, f"f('{head.label}')", State.ADD)
        parser.add_state(state)
        debug_state and print('creating new state: ', state.state_id)
        return RouteItem(state, list(head.features), parser)

    def func_add(self, word, *feats):
        head = SimpleConstituent(word)
        if feats:
            if isinstance(feats, str):
                feats = [feats]
            head.features = [Feature.from_string(f) for f in feats]
        msg = f'add "{word}"'
        return self.new_route_item(head=head, msg=msg, entry=f"f('{word}')", state_type=State.ADD)

    def func_complement(self, with_feat=''):
        arg = self.state.head
        arg_label = self.get_head_label()
        long_distance = False
        if with_feat:
            print('doing func complement with feat ', with_feat)
            pos_feat = Feature.from_string(with_feat)
            match = get_route_item_with_feature_match(self.parser.active_route, pos_feat)
            if match:
                head_item, neg_feat = match
                long_distance = head_item is not get_free_precedent_from_route(self.parser.active_route)
                print('found route item for head: ', head_item, head_item.state, neg_feat)
            else:
                raise KeyError(f'No match for feature {pos_feat}')
            head = head_item.state.head
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
            head_item = get_free_precedent_from_route(self.parser.active_route)
            print('free precedent from ', self.parser.active_route, ' is ', head_item)
            if head_item:
                head = head_item.state.head
            else:
                print(f'No free precedent at {self.parser.active_route}')
                return self
            matches = find_matches(self.features, head_item.features)
            if matches:
                arg_feat, head_feat = matches[0]
            else:
                arg_feat, head_feat  = self.parser.speculate_features(head, arg)
                self.parser.add_feat_to_route(head_feat, head)
                self.parser.add_feat_to_route(arg_feat, arg)
            checked_features = [(arg_feat, head_feat)]
        msg = f"CLOSING: set '{arg_label}' as arg for: '{head_item.get_label()}' ({checked_features or ''})"
        print(msg)
        return self.new_route_item(head=head, head_ri=head_item, arg=arg, arg_ri=self, msg=msg, entry="r()",
                                   state_type=State.CLOSE_ARG, checked_features=checked_features, long_distance=long_distance)

    def func_raise_arg(self, with_feat=''):
        head = self.state.head
        long_distance = False
        if with_feat:
            neg_feat = Feature.from_string(with_feat)
            match = get_route_item_with_feature_match(self.parser.active_route, neg_feat)
            if match:
                arg_item, pos_feat = match
                long_distance = arg_item is not get_free_precedent_from_route(self.parser.active_route)
                print('found route item for arg: ', arg_item, arg_item.state, pos_feat)
            else:
                raise KeyError(f'No match for feature {neg_feat} at {self.parser.active_route}')

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
            arg_item = get_free_precedent_from_route(self.parser.active_route)
            if arg_item:
                arg = arg_item.state.head
            else:
                #raise KeyError(f'No free precedent at {self.parser.active_route}')
                print(f'No free precedent at {self.parser.active_route}')
                return self
            matches = find_matches(arg_item.features, self.features)
            if matches:
                arg_feat, head_feat = matches[0]
            else:
                arg_feat, head_feat = self.parser.speculate_features(head, arg)
                self.parser.add_feat_to_route(head_feat, head)
                self.parser.add_feat_to_route(arg_feat, arg)
            checked_features = [(arg_feat, head_feat)]
        if not arg:
            debug_parse and print(f'{self} has no free precedent for argument')
        debug_parse and print(f'raising {arg.label} as argument for {head.label}')
        msg = f"raise '{arg_item.get_head_label()}' as arg for: '{self.get_head_label()}' ({checked_features or ''})"
        return self.new_route_item(head=head, head_ri=self, arg=arg, arg_ri=arg_item, msg=msg, entry="arg()",
                                   state_type=State.RAISE_ARG, checked_features=checked_features, long_distance=long_distance)

    def func_adjunct(self):
        other_head_item = get_free_precedent_from_route(self.parser.active_route)
        other_head = other_head_item.state.head
        head = (other_head, self.state.head)
        #shared_features = list(get_features(other_head))
        #self.state.head.features = list(shared_features)
        msg = f"set '{other_head_item.get_head_label()}' as adjunct for {self.get_head_label()}" # ({shared_features})"
        return self.new_route_item(head=head, head_ri=self, msg=msg, entry="adj()", state_type=State.ADJUNCT)
                                   #features=shared_features)

    ### Parser methods

    def add_const(self, const):
        debug_parse and print(f'adding {const.label}')
        msg = f"add '{const.label}'"
        return self.new_route_item(head=const, msg=msg, entry=f"f('{const.label}')", state_type=State.ADD)

    def raise_arg(self, arg_item, checked_features, long_distance=False):
        head = self.state.head
        arg = arg_item.state.head
        debug_parse and print(f'raising {arg_item.get_head_label()} as argument for {self.get_head_label()}')
        ld = ' (long distance)' if long_distance else ''
        msg = f"raise '{arg_item.get_head_label()}' as arg for: '{self.get_head_label()}' ({checked_features or ''}){ld}"
        return self.new_route_item(head=head, head_ri=self, arg=arg, arg_ri=arg_item, msg=msg, entry="arg()", state_type=State.RAISE_ARG,
                                   checked_features=checked_features, long_distance=long_distance)

    def complement(self, head_item, checked_features, long_distance=False):
        head = head_item.state.head
        arg = self.state.head
        ld = ' (long distance)' if long_distance else ''
        msg = f"set '{self.get_head_label()}' as complement arg for: '{head_item.get_head_label()}' ({checked_features or ''}){ld}"
        return self.new_route_item(head=head, head_ri=head_item, arg=arg, arg_ri=self, msg=msg, entry="r()",
                                   state_type=State.CLOSE_ARG, checked_features=checked_features, long_distance=long_distance)

    def adjunct(self, other_head_item, shared_features):
        other_head = other_head_item.state.head
        head = (other_head, self.state.head)
        msg = f"set '{other_head_item.get_head_label()}' as adjunct for {self.get_head_label()} ({shared_features})"
        return self.new_route_item(head=head, head_ri=self, msg=msg, entry="adj()", state_type=State.ADJUNCT,
                                   features=shared_features)

    # Aliases
    r = func_complement
    arg = func_raise_arg
    f = func_add
    adj = func_adjunct
