from collections.abc import Iterable

debug_linearization = True

DONE_SUCCESS = 7
DONE_FAIL = 2
ADD = 0
ADJUNCT = 6
RAISE_ARG = 4
CLOSE_ARG = 5
FROM_STACK = 3
PUT_STACK = 1

# these can adjoin if coordinator is present, but not otherwise
unadjoinable_categories = {'T', 'V', 'rel'}

def get_free_precedent_from_route_old(route):
    connected_heads = {route[-1].state.head}
    for route_item in reversed(route):
        if route_item.state.head not in connected_heads:
            #print('from route ', route, ' free precedent is ', route_item)
            return route_item
        if route_item.state.arg_ and not route_item.long_distance:
            connected_heads.add(route_item.state.arg_)
        if route_item.state.state_type == ADJUNCT:
            for head in route_item.state.head:
                connected_heads.add(head)

def get_free_precedent_from_route(route):
    connected_heads = {route[-1].state.head}
    for route_item in reversed(route):
        if route_item.state.head not in connected_heads:
            #print('from route ', route, ' free precedent is ', route_item)
            return route_item
        if route_item.state.arg_: # and not route_item.long_distance:
            connected_heads.add(route_item.state.arg_)
        if route_item.state.state_type == ADJUNCT:
            for head in route_item.state.head:
                connected_heads.add(head)


def get_label(const):
    if not const:
        return None
    if isinstance(const, Iterable):
        return '+'.join([get_label(c) for c in const])
    else:
        return const.label


def get_uid(const):
    if not const:
        return None
    elif isinstance(const, Iterable):
        return '+'.join([get_uid(c) for c in const])
    else:
        return str(const.uid)


def filter_strong(feats):
    return [feat for feat in feats if feat.strong]


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
                    print('added feature (copy) ', fcopy, ' to const ', fcopy.host, id(fcopy))
                else:
                    _const.features.append(feat)
                    exists.append(_const)
                    feat.host = _const
                    print('added feature ', feat, ' to const ', feat.host, id(feat))

    _find_feature(const)
    _add_feature(const)


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


def is_positive(feat):
    return feat.sign == '' or feat.sign == '*'


def is_negative(feat):
    return feat.sign == '-' or feat.sign == '=' or feat.sign == '_'


def feature_match(feat, other):
    if feat.name != other.name:
        return False
    if is_positive(feat) and is_negative(other):
        return (not other.value) or feat.value in other.value.split('|')
    elif is_positive(other) and is_negative(feat):
        return (not feat.value) or other.value in feat.value.split('|')


def find_matches(pos_features, neg_features, neg_signs='-='):
    matches = []
    for pos_feat in pos_features:
        if is_positive(pos_feat):
            for neg_feat in neg_features:
                if neg_feat.sign and neg_feat.name == pos_feat.name and neg_feat.sign in neg_signs and \
                        ((not neg_feat.value) or pos_feat.value in neg_feat.value.split('|')):
                    matches.append((pos_feat, neg_feat))
                    break  # one pos feature can satisfy only one neg feature
    return matches


def has_loose_adjoining_feature(features):
    for feat in features:
        if feat.name == 'coord':
            return True


def find_common_features(a_features, b_features):
    loose_adjoining = has_loose_adjoining_feature(a_features) or has_loose_adjoining_feature(b_features)
    if loose_adjoining:
        return _loose_find_common_features(a_features, b_features)
    else:
        return _strict_find_common_features(a_features, b_features)


def _loose_find_common_features(a_features, b_features):
    common = []
    for a in a_features:
        if is_positive(a):
            for b in b_features:
                if is_positive(b):
                    if a == b:
                        common.append(a)
                        break
                    elif a.name == b.name and a.sign == b.sign:
                        common.append(a)
                        common.append(b)
                        break
    return common


def _strict_find_common_features(a_features, b_features):
    common = []
    for a in a_features:
        if is_positive(a):
            if a.name in unadjoinable_categories:
                continue
            for b in b_features:
                if is_positive(b):
                    if a == b:
                        common.append(a)
                        break
                    elif a.name == b.name and a.sign == b.sign and a.value and b.value and a.value != b.value:
                        return []
    return common


def find_shared_features(a_features, b_features):
    return a_features + [b for b in b_features if b not in a_features]


def flatten(head):
    if isinstance(head, Iterable):
        r = []
        for h in head:
            r += flatten(h)
        return r
    else:
        return [head]


def find_shared_heads(a_route_item, b_route_item):
    flatten_a = set(flatten(a_route_item.state.head))
    flatten_b = set(flatten(b_route_item.state.head))
    return flatten_a & flatten_b


def get_route_item_with_feature_match(route, feature):
    for route_item in reversed(route):
        for feat in route_item.features:
            if feature_match(feature, feat):
                return route_item, feat


def find_route_item_with_features(feats, route):
    #print('looking for ', feats, ' in ', route)
    for route_item in reversed(route):
        found_all = True
        for feat in feats:
            if feat not in route_item.features:
                found_all = False
                break
        if found_all:
            return route_item


def make_path(route):
    return '_'.join(str(ri.state.state_id) for ri in route)


def route_str(path):
    return [ri.state.state_id for ri in path]


def linearize(route):
    """ This is a very simple linearisation because route already has elements in correct order.
    To verify that the structure is valid, one should try to linearise the constituent tree """
    result = []
    for route_item in route:
        state = route_item.state
        if state.state_type == state.ADD:
            result.append(state.get_head_label())
    str_result = ' '.join(result)
    debug_linearization and print('linearised: ', str_result)
    return str_result


def is_fully_connected(route):
    heads = set()
    args = set()
    for route_item in route:
        state = route_item.state
        if state.head and state.head not in args:
            heads.add(state.head)
        if state.arg_:
            args.add(state.arg_)
            if state.arg_ in heads:
                heads.remove(state.arg_)
        elif state.state_type == ADJUNCT:
            for item in state.head:
                if item in heads:
                    heads.remove(item)
    print('is_fully_connected: ', len(heads), heads)
    return len(heads) < 2

