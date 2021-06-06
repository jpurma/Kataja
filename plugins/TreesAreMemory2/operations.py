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

    def calculate_top_head(self, route_item):
        return [self]

    def calculate_free_heads(self, route_item):
        if route_item.parent:
            return [route_item] + route_item.parent.free_heads
        return [route_item]

    def calculate_local_heads(self, route_item):
        return [route_item]


class Spec(Operation):
    sort_order = 1
    state_type = SPECIFIER

    def __init__(self, head, spec, checked_features, long_distance=False):
        ld = ' (long distance)' if long_distance else ''
        msg = f"raise '{spec}' as specifier arg for: '{head}' ({checked_features or ''}){ld}"
        #entry = f"spec('{spec}')" if long_distance else 'spec()'
        entry = f"spec('{spec}', '{head}')"
        Operation.__init__(self, head, arg=spec, msg=msg, entry=entry, checked_features=checked_features)

    def calculate_features(self, route_item):
        head_item = route_item.find_head_item()
        return [feat for feat in head_item.features if feat not in route_item.flat_checked_features]

    def calculate_top_head(self, route_item):
        return route_item.find_head_item()

    def calculate_free_heads(self, route_item):
        return [route_item] + [ri for ri in route_item.parent.free_heads if ri.head is not self.head and ri.head is not self.arg]

    def calculate_local_heads(self, route_item):
        head = route_item.head
        parent = route_item.parent
        local_heads = [route_item]
        heads = [route_item.head]
        while parent:
            if parent.arg is head:
                head = parent.head
                if head not in heads:
                    local_heads.append(parent)
                    heads.append(parent.head)
            parent = parent.parent
        return local_heads

    def calculate_local_heads2(self, route_item):
        return [route_item] + [ri for ri in route_item.parent.parent.local_heads if ri.head is not self.head and ri.head is not self.arg]


class Comp(Operation):
    sort_order = 2
    state_type = COMPLEMENT

    def __init__(self, head, comp, checked_features, long_distance=False):
        ld = ' (long distance)' if long_distance else ''
        msg = f"set '{comp}' as complement arg for: '{head}' ({checked_features or ''}){ld}"
        #entry = f"comp('{head}')" if long_distance else 'comp()'
        entry = f"comp('{head}', '{comp}')"
        Operation.__init__(self, head, arg=comp, entry=entry, msg=msg, checked_features=checked_features)

    def calculate_features(self, route_item):
        head_item = route_item.find_head_item()
        return [feat for feat in head_item.features if feat not in route_item.flat_checked_features]

    def calculate_top_head(self, route_item):
        head = route_item.head
        parent = route_item.parent
        heads = []
        while parent:
            if parent.arg is head:
                head = parent.head
                if head not in heads:
                    heads.append(parent)

    def calculate_free_heads(self, route_item):
        return [route_item if ri.head is self.head else ri for ri in route_item.parent.free_heads if ri.head is not self.arg]

    def calculate_local_heads(self, route_item):
        head = route_item.head
        parent = route_item.parent
        local_heads = [route_item.find_arg_item(), route_item]
        heads = [route_item.arg, route_item.head]
        while parent:
            if parent.arg is head:
                head = parent.head
                if head not in heads:
                    local_heads.append(parent)
                    heads.append(parent.head)
            parent = parent.parent
        return local_heads


class Adj(Operation):
    sort_order = 5
    state_type = ADJUNCT

    def __init__(self, head, other_head):
        msg = f"set '{other_head}' as adjunct for {head}"
        # entry = "adj()"
        entry = f"adj('{other_head}', '{head}')"
        Operation.__init__(self, (other_head, head), msg=msg, entry=entry)

    def calculate_features(self, route_item):
        head, other_head = self.head
        head_op = route_item.parent.find_closest_head(head)
        other_head_op = route_item.parent.find_closest_head(other_head)
        return union(head_op.features, other_head_op.features)

    # route itemin free headsin on tarkoitus olla ne route itemit jotka ovat käytettävissä silloin kun tämä on viimeinen
    # route item ja yritetään päättää minkä toisen route itemin kanssa tämä voi yhdistyä. Eli free heads ei sisällä
    # tätä route itemiä itseään, mutta sisältää edeltävän elementin ylimmän pään.
    def calculate_free_heads(self, route_item):
        return [route_item] + [ri for ri in route_item.parent.free_heads if ri.head not in self.head]

    # [.A+B A B]

    def calculate_local_heads(self, route_item):
        return [route_item] + [ri for ri in route_item.parent.free_heads if ri.head not in self.head]


class Done(Operation):
    sort_order = 0
    state_type = DONE_SUCCESS

    def __init__(self, head, msg=""):
        Operation.__init__(self, head, msg=msg, entry="done()")

    def calculate_features(self, route_item):
        return []


class Fail(Operation):
    sort_order = 8
    state_type = DONE_FAIL

    def __init__(self, head, msg=""):
        Operation.__init__(self, head, msg, entry="fail()")

    def calculate_features(self, route_item):
        return []
