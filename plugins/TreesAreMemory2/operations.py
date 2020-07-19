try:
    from plugins.TreesAreMemory2.State import State
    from plugins.TreesAreMemory2.route_utils import *
    from plugins.TreesAreMemory2.Operation import Operation, make_state
    from plugins.TreesAreMemory2.FuncSupport import FuncSupport
except ImportError:
    from State import State
    from route_utils import *
    from Operation import Operation, make_state
    from FuncSupport import FuncSupport

debug_state = False
debug_parse = False
debug_func_parse = False


class Add(Operation, FuncSupport):
    sort_order = 3

    def __init__(self, states, const):
        msg = f"add '{const.label}'"
        state = make_state(states, const, None, f"f('{const.label}')", State.ADD)
        Operation.__init__(self, state, msg, features=state.head.features)


class Spec(Operation, FuncSupport):
    sort_order = 1

    def __init__(self, states, head_op, spec_op, checked_features, long_distance=False):
        head = head_op.state.head
        arg = spec_op.state.head
        ld = ' (long distance)' if long_distance else ''
        msg = f"raise '{spec_op.get_head_label()}' as specifier arg for: '{head_op.get_head_label()}' ({checked_features or ''}){ld}"
        state = make_state(states, head, arg, "spec()", State.SPECIFIER, checked_features)
        Operation.__init__(self, state, msg, head_op=head_op, arg_op=spec_op, long_distance=long_distance)


class Comp(Operation, FuncSupport):
    sort_order = 2

    def __init__(self, states, comp_op, head_op, checked_features, long_distance=False):
        head = head_op.state.head
        arg = comp_op.state.head
        ld = ' (long distance)' if long_distance else ''
        msg = f"set '{comp_op.get_head_label()}' as complement arg for: '{head_op.get_head_label()}' ({checked_features or ''}){ld}"
        state = make_state(states, head, arg, "comp()", State.COMPLEMENT, checked_features)
        Operation.__init__(self, state, msg, head_op=head_op, arg_op=comp_op, long_distance=long_distance)


class Adj(Operation, FuncSupport):
    sort_order = 4

    def __init__(self, states, head_op, other_head_op, shared_features):
        head = head_op.state.head
        other_head = other_head_op.state.head
        msg = f"set '{other_head_op.get_head_label()}' as adjunct for {head_op.get_head_label()} ({shared_features})"
        state = make_state(states, (other_head, head), None, "adj()", State.ADJUNCT)
        Operation.__init__(self, state, msg, head_op=head_op, other_head_op=other_head_op)


class Done(Operation, FuncSupport):
    sort_order = 0

    def __init__(self, states, head_op, msg=""):
        head = head_op.state.head
        state = make_state(states, head, None, "done()", State.DONE_SUCCESS)
        Operation.__init__(self, state, msg, head_op=head_op)


class Fail(Operation, FuncSupport):
    sort_order = 8

    def __init__(self, states, head_op, msg=""):
        head = head_op.state.head
        state = make_state(states, head, None, "fail()", State.DONE_FAIL)
        Operation.__init__(self, state, msg, head_op=head_op)
