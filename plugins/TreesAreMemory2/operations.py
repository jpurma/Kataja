try:
    from plugins.TreesAreMemory2.route_utils import *
    from plugins.TreesAreMemory2.Operation import Operation
    #from plugins.TreesAreMemory2._deprecated_func_support.FuncSupport import FuncSupport
except ImportError:
    from route_utils import *
    from Operation import Operation
    #from FuncSupport import FuncSupport

debug_state = False
debug_parse = False
debug_func_parse = False

DONE_SUCCESS = 7
DONE_FAIL = 2
ADD = 0
ADJUNCT = 6
SPECIFIER = 4
COMPLEMENT = 1
PROMISE_COMPLEMENT = 3
RESOLVE_COMPLEMENT = 5


class Add(Operation):
    sort_order = 3
    state_type = ADD

    def __init__(self, const):
        msg = f"add '{const.label}'"
        Operation.__init__(self, const, msg=msg, entry=f"add('{const.label}')")

    def calculate_free_precedents(self, route_item):
        if route_item.parent:
            return [route_item.parent] + route_item.parent.free_precedents
        return []


class Spec(Operation):
    sort_order = 1
    state_type = SPECIFIER

    def __init__(self, head, spec, checked_features, long_distance=False):
        ld = ' (long distance)' if long_distance else ''
        msg = f"raise '{spec}' as specifier arg for: '{head}' ({checked_features or ''}){ld}"
        entry = f"spec('{spec}')" if long_distance else 'spec()'
        Operation.__init__(self, head, arg=spec, msg=msg, entry=entry, checked_features=checked_features)

    def calculate_features(self, route_item):
        head_item = route_item.find_head_item()
        return [feat for feat in head_item.features if feat not in route_item.flat_checked_features]

    def calculate_free_precedents(self, route_item):
        used = {self.head, self.arg}
        arg_item = route_item.find_arg_item()
        free_precedents = []
        for precedent in arg_item.free_precedents:
            if precedent.operation.head not in used:
                free_precedents.append(precedent)
                used.add(precedent.operation.head)
        return free_precedents


class Comp(Operation):
    sort_order = 2
    state_type = COMPLEMENT

    def __init__(self, head, comp, checked_features, long_distance=False):
        ld = ' (long distance)' if long_distance else ''
        msg = f"set '{comp}' as complement arg for: '{head}' ({checked_features or ''}){ld}"
        entry = f"comp('{head}')" if long_distance else 'comp()'
        Operation.__init__(self, head, arg=comp, entry=entry, msg=msg, checked_features=checked_features)

    def get_as_previous(self):
        return self.previous

    def calculate_features(self, route_item):
        head_item = route_item.find_head_item()
        return [feat for feat in head_item.features if feat not in route_item.flat_checked_features]

    def calculate_free_precedents(self, route_item):
        used = {self.head, self.arg}
        # pitäisi estää se, että pääsana tai tämän pääsanan päässana olisi vapaissa edeltäjissä jotta sitä ei käytetä
        # speccinä tai comppina ja tehdä kehää.
        free_precedents = []
        arg_item = route_item.find_arg_item()
        print('arg_item free precedents: ', arg_item.free_precedents)
        for precedent in [route_item.parent] + arg_item.free_precedents:
            print('used: ', used)
            if precedent.operation.head not in used:
                free_precedents.append(precedent)
                used.add(precedent.operation.head)
        print(f'set free precedents for {route_item}****: {free_precedents}')
        return free_precedents


class Adj(Operation):
    sort_order = 5
    state_type = ADJUNCT

    def __init__(self, head, other_head):
        msg = f"set '{other_head}' as adjunct for {head}"
        Operation.__init__(self, (other_head, head), msg=msg, entry="adj()")

    def calculate_features(self, route_item):
        head, other_head = self.head
        head_op = route_item.parent.find_closest_head(head)
        other_head_op = route_item.parent.find_closest_head(other_head)
        return union(head_op.features, other_head_op.features)

    def calculate_free_precedents(self, route_item):
        free_precedents = []
        for precedent in [route_item.parent] + route_item.parent.free_precedents:
            if precedent.operation.head not in self.head:
                free_precedents.append(precedent)
        return free_precedents


class Done(Operation):
    sort_order = 0
    state_type = DONE_SUCCESS

    def __init__(self, head, msg=""):
        Operation.__init__(self, head, msg=msg, entry="done()")


class Fail(Operation):
    sort_order = 8
    state_type = DONE_FAIL

    def __init__(self, head, msg=""):
        Operation.__init__(self, head, msg, entry="fail()")
