try:
    from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
    from plugins.TreesAreMemory2.Feature import Feature
    from plugins.TreesAreMemory2.route_utils import *
except ImportError:
    from SimpleConstituent import SimpleConstituent
    from Feature import Feature
    from route_utils import *

debug_func_parse = False


class Context:
    def __init__(self):
        self.parser = None
        self.Add = None
        self.Spec = None
        self.Comp = None
        self.Adj = None


context = Context()


def get_features(const):
    if not const:
        return []
    elif isinstance(const, Iterable):
        feat_lists = []
        for item in const:
            feat_lists.append(get_features(item))
        feats = [f for f in feat_lists[0] if all([f in feat_list for feat_list in feat_lists])]
        return feats
    return const.features


def add_feature(const, feat):
    exists = []

    def _find_feature(_const):
        if isinstance(_const, Iterable):
            for item in _const:
                _find_feature(item)
        else:
            if feat in _const.features:
                exists.append(_const)

    def _add_feature(_const):
        if isinstance(_const, Iterable):
            for item in _const:
                _add_feature(item)
        else:
            if feat not in _const.features:
                if exists:
                    fcopy = feat.copy()
                    _const.features.append(fcopy)
                    fcopy.host = _const
                    #print('added feature (copy) ', fcopy, ' to const ', fcopy.host, id(fcopy))
                else:
                    _const.features.append(feat)
                    exists.append(_const)
                    feat.host = _const
                    #print('added feature ', feat, ' to const ', feat.host, id(feat))

    _find_feature(const)
    _add_feature(const)



class FuncSupport:
    """ These are methods for parsing dot-string notations, eg. "f('Pekka').f('loves').spec().f('Merja').comp()"
     These are not required for parser itself, but this class is inserted into operations inheritance """


    @staticmethod
    def add_to_route(new_operation):
        context.parser.active_route.append(new_operation)
        new_operation.calculate_free_precedents(context.parser.active_route)
        return new_operation

    @staticmethod
    def f(word, *feats):
        head = SimpleConstituent(word)
        if feats:
            if isinstance(feats, str):
                feats = [feats]
            head.features = [Feature.from_string(f) for f in feats]
        return FuncSupport.add_to_route(context.Add(context.states, head))

    def get_precedent_with_feature_match(self, feature):
        for operation in self.free_precedents:
            for feat in operation.features:
                if feature_match(feature, feat):
                    return operation, feat

    def comp(self, with_feat=''):
        arg = self.state.head
        long_distance = False
        if with_feat:
            debug_func_parse and print('doing func complement with feat ', with_feat)
            pos_feat = Feature.from_string(with_feat)
            match = self.get_precedent_with_feature_match(pos_feat)
            if match:
                head_op, neg_feat = match
                long_distance = head_op is not self.first_free_precedent()
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
            head_op = self.first_free_precedent()
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
                arg_feat, head_feat = context.parser.speculate_features(head, arg)
                context.parser.add_feat_to_route(head_feat, head)
                context.parser.add_feat_to_route(arg_feat, arg)
            checked_features = [(arg_feat, head_feat)]
        return self.add_to_route(context.Comp(context.states, self, head_op, checked_features, long_distance=long_distance))

    def spec(self, with_feat=''):
        head = self.state.head
        long_distance = False
        if with_feat:
            neg_feat = Feature.from_string(with_feat)
            match = self.get_precedent_with_feature_match(neg_feat)
            if match:
                arg_item, pos_feat = match
                long_distance = arg_item is not self.first_free_precedent()
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
            arg_item = self.first_free_precedent()
            if arg_item:
                arg = arg_item.state.head
            else:
                # raise KeyError(f'No free precedent at {self.parser.active_route}')
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
        return self.add_to_route(context.Spec(context.states, self, arg_item, checked_features, long_distance=long_distance))

    def adj(self):
        other_head_op = self.free_precedents[0] if self.free_precedents else None
        return self.add_to_route(context.Adj(context.states, self, other_head_op, []))

