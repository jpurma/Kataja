try:
    from plugins.TreesAreMemory2.route_utils import *
except ImportError:
    from route_utils import *

from itertools import chain


class Operation:
    """ Base class for "operator nodes" used by parser."""
    sort_order = 10
    state_type = 0

    def __init__(self, head, arg=None, msg='', entry='', checked_features=None):
        self.head = head
        self.arg = arg
        self.uid = f'{self.get_head_uid()}{self.get_arg_uid()}S{self.state_type}'
        self.ord = 0
        self.msg = msg
        self.entry = entry
        self.checked_features = checked_features or []

    def __str__(self):
        return repr(self)

    def get_arg_uid(self):
        return get_uid(self.arg)

    def get_head_uid(self):
        return get_uid(self.head)

    def get_arg_label(self):
        return get_label(self.arg)

    def get_head_label(self):
        return get_label(self.head)

    def calculate_previous_item(self, route_item):
        return route_item.parent

    def calculate_features(self, route_item):
        return self.head.features

    def calculate_free_heads(self, route_item):
        return []

    def calculate_local_heads(self, route_item):
        return []

    def __repr__(self):
        checked_feats = ', ' + str(self.checked_features) if self.checked_features else ''
        if self.arg:
            return f'{self.__class__.__name__}({self.get_head_label()}, {self.get_arg_label()}{checked_feats})'
        else:
            return f'{self.__class__.__name__}({self.get_head_label()}{checked_feats})'

    def __lt__(self, other):
        if isinstance(other, Operation):
            if self.sort_order == other.sort_order:
                return self.uid < other.uid
            else:
                return self.sort_order < other.sort_order

    def __eq__(self, other):
        if isinstance(other, Operation):
            return self.uid == other.uid or \
                   (self.head == other.head and self.arg == other.arg and self.checked_features == other.checked_features)
        return False

    def __hash__(self):
        return hash(self.uid)
