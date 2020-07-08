try:
    from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
    from plugins.TreesAreMemory2.route_utils import *
except ImportError:
    from SimpleConstituent import SimpleConstituent
    from route_utils import *


class State:
    # State types
    DONE_SUCCESS = 7
    DONE_FAIL = 2
    ADD = 0
    ADJUNCT = 6
    RAISE_ARG = 4
    CLOSE_ARG = 5
    FROM_STACK = 3
    PUT_STACK = 1

    @staticmethod
    def create_key(state_type, head, arg_, checked_features):
        return f'{state_type}_{get_uid(head)}_{get_uid(arg_)}_{checked_features}'

    def __init__(self, head=None, arg=None, entry="", state_type=-1, checked_features=None):
        self.parser = None
        self.state_id = 0
        self.head = head
        self.arg_ = arg
        self.entry = entry
        self.state_type = state_type
        self.checked_features = checked_features or []
        self.key = ''
        self.update_key()

    def set_id(self, state_id):
        self.state_id = state_id

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def __repr__(self):
        return f'{self.state_id}. {self.key}'

    def __str__(self):
        return f'State(state_id={self.state_id}, head={self.get_head_label()}, arg={self.get_arg_label()}, ' \
               f'state_type={self.state_type}, checked_features={self.checked_features})'

    def update_key(self):
        self.key = self.create_key(self.state_type, self.head, self.arg_, self.checked_features)

    def get_arg_uid(self):
        return get_uid(self.arg_)

    def get_head_uid(self):
        return get_uid(self.head)

    def get_arg_label(self):
        return get_label(self.arg_)

    def get_head_label(self):
        return get_label(self.head)
