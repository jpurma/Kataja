try:
    from plugins.TreesAreMemory3.route_utils import *
    from plugins.TreesAreMemory3.Operation import Operation
    #from plugins.TreesAreMemory3._deprecated_func_support.FuncSupport import FuncSupport
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

    def calculate_available_heads(self, route_item):
        if route_item.parent:
            return [route_item] + route_item.parent.available_heads
        return [route_item]


class Spec(Operation):
    sort_order = 1
    state_type = SPECIFIER

    def __init__(self, head, spec, checked_features):
        msg = f"raise '{spec}' as specifier arg for: '{head}' ({checked_features or ''})"
        entry = f"spec('{spec}', '{head}')"
        Operation.__init__(self, head, arg=spec, msg=msg, entry=entry, checked_features=checked_features)

    def calculate_available_heads(self, route_item):
        return [route_item] + [ri for ri in route_item.parent.available_heads
                               if ri.head is not self.head and ri.head is not self.arg]


class Comp(Operation):
    sort_order = 2
    state_type = COMPLEMENT

    def __init__(self, head, comp, checked_features):
        msg = f"set '{comp}' as complement arg for: '{head}' ({checked_features or ''})"
        entry = f"comp('{head}', '{comp}')"
        Operation.__init__(self, head, arg=comp, entry=entry, msg=msg, checked_features=checked_features)

    def calculate_available_heads(self, route_item):
        return [route_item if ri.head is self.head else ri for ri in route_item.parent.available_heads
                if ri.head is not self.arg]


class Adj(Operation):
    sort_order = 5
    state_type = ADJUNCT

    def __init__(self, head, other_head, checked_features):
        msg = f"set '{other_head}' as adjunct for {head}"
        entry = f"adj('{other_head}', '{head}')"
        Operation.__init__(self, (other_head, head), msg=msg, entry=entry, checked_features=checked_features)

    # route itemin free headsin on tarkoitus olla ne route itemit jotka ovat käytettävissä silloin kun tämä on viimeinen
    # route item ja yritetään päättää minkä toisen route itemin kanssa tämä voi yhdistyä. Eli free heads ei sisällä
    # tätä route itemiä itseään, mutta sisältää edeltävän elementin ylimmän pään.
    def calculate_available_heads(self, route_item):
        return [route_item] + [ri for ri in route_item.parent.available_heads if ri.head not in self.head]


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
