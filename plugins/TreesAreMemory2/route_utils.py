from collections.abc import Iterable

debug_linearization = False

DONE_SUCCESS = 7
DONE_FAIL = 2
ADD = 0
ADJUNCT = 6
SPECIFIER = 4
COMPLEMENT = 5

# these can adjoin if coordinator is present, but not otherwise
unadjoinable_categories = {'T', 'V', 'rel', 'että', 'v', 'neg', 'ld'}

phase_borders = {'rel'}


def get_label(const):
    if not const:
        return None
    if isinstance(const, tuple):
        return '+'.join([get_label(c) for c in const])
    else:
        return const.label


def get_uid(const):
    if not const:
        return None
    elif isinstance(const, tuple):
        return '+'.join([get_uid(c) for c in const])
    else:
        return str(const.uid)


def filter_strong(feats):
    return [feat for feat in feats if feat.strong]


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


def union(features1, features2):
    return list(set(features1) | set(features2))


def allow_long_distance(features):
    for feature in features:
        if feature.name == 'ld':
            return True


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


def head_precedes(precedent, top):
    for operation in top.as_route():
        if operation.head is precedent.head:
            return True
        elif operation.head is top.head:
            return False


def has_loose_adjoining_feature(features):
    for feat in features:
        if feat.name == 'coord':
            return True


def has_adjunct_licensed(precedent, operation):
    for feat in operation.features:
        if feat.name == 'adjL':
            found = None
            for featp in precedent.features:
                if featp.name == 'a' and featp.value == feat.value:
                    found = (feat, featp)
                elif featp.name == 'adjL' and featp.value == feat.value:
                    return
            if found:
                return found


def find_common_features(a_features, b_features):
    loose_adjoining = has_loose_adjoining_feature(a_features) or has_loose_adjoining_feature(b_features)
    if loose_adjoining:
        l = _loose_find_common_features(a_features, b_features)
        print('loose adjoining: ', l, a_features, b_features)
        return l
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


def print_route_str(route):
    print(f'derivation route, {len(route)} steps')
    for ri in route:
        print(ri)
    print('--------')

def find_shared_heads(route_item_a, route_item_b):
    flatten_a = set(flatten(route_item_a.operation.head))
    flatten_b = set(flatten(route_item_b.operation.head))
    return flatten_a & flatten_b


def find_operation_with_features(feats, route):
    #print('looking for ', feats, ' in ', route)
    assert(len(feats) == 1)
    for operation in reversed(route):
        found_all = True
        for feat in feats:
            if feat not in operation.features:
                found_all = False
                break
        if found_all:
            return operation


def make_path(route):
    return '_'.join(str(op.uid) for op in route)


def route_str(path):
    return [op.uid for op in path]


