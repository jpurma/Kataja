try:
    from plugins.TreesAreMemory2.route_utils import *
    from plugins.TreesAreMemory2.operations import Add, Adj
except ImportError:
    from route_utils import *
    from operations import Add, Adj

from itertools import chain

debug_state = False


class OperationIds:
    def __init__(self):
        self.count = 0

    def reset(self):
        self.count = 0

    def get_id(self):
        i = self.count
        self.count += 1
        return i


operation_ids = OperationIds()


def filter_checked(features, checked_features):
    flat_list = list(chain(*checked_features))
    return [f for f in features if f not in flat_list], [f for f in features if f in flat_list]


def flatten_checked(checked_features):
    return list(chain(*checked_features))


class RouteItem:

    def __init__(self, parent, operation):
        self.parent = parent
        self.operation = operation
        self.path = f'{self.parent.path}_{self.operation.ord}' if self.parent else str(self.operation.ord)
        self.uid = self.operation.ord
        self.features = []
        self.free_heads = []
        self.local_heads = []
        self.flat_checked_features = flatten_checked(operation.checked_features)
        self.features = self.operation.calculate_features(self)
        self.previous = self.calculate_previous_item()
        self.used_features = self.calculate_used_features()
        self.free_heads = self.operation.calculate_free_heads(self)
        self.local_heads = self.operation.calculate_local_heads(self)
        self.consts = []
        debug_state and print('creating new RouteItem: ', self)

    def __str__(self):
        return str(self.operation)

    def __repr__(self):
        return str(self.operation)
        #return f'RouteItem({self.operation})'

    def __lt__(self, other):
        return self.operation < other.operation

    def __eq__(self, other):
        return self.uid == other.uid

    def __hash__(self):
        return self.uid

    @property
    def head(self):
        return self.operation.head

    @property
    def arg(self):
        return self.operation.arg

    @property
    def label(self):
        return self.operation.get_head_label()

    def as_route(self):
        route = []
        route_item = self
        while route_item:
            route.append(route_item)
            route_item = route_item.parent
        return list(reversed(route))

    def is_phase_border(self):
        for feat in self.features:
            if feat.name in phase_borders and is_positive(feat):
                return True

    def find_closest_head(self, head):
        if self.operation.head is head:
            return self
        elif self.parent:
            return self.parent.find_closest_head(head)

    def find_arg_item(self):
        if self.operation.arg and self.parent:
            return self.parent.find_closest_head(self.operation.arg)

    def find_head_item(self):
        if self.parent:
            return self.parent.find_closest_head(self.operation.head)

    def find_top_head(self):
        head = self.head
        top_ri = self
        prev = self.parent
        while prev:
            if prev.operation.arg is head:
                head = prev.head
                top_ri = prev
            prev = prev.parent
        return top_ri

    def find_previous_added_head(self, excluded):
        if type(self.operation) is Adj or type(self.operation) is Add and self.operation.head is not excluded:
            return self.operation.head
        elif self.parent:
            return self.parent.find_previous_added_head(excluded)

    def calculate_previous_item(self):
        if self.parent:
            prev_added_head = self.parent.find_previous_added_head(self.operation.head)
            if prev_added_head:
                found = self.find_closest_head(prev_added_head)
                return found

    def find_closest_merging_item(self, head):
        if self.operation.checked_features and (self.operation.head is head or self.operation.arg is head):
            return self
        elif self.parent:
            return self.parent.find_closest_head(head)

    def calculate_used_features(self):
        feats = list(self.flat_checked_features)
        route_item = self.parent
        relevant_heads = {self.operation.head}
        while route_item:
            if route_item.flat_checked_features:
                if route_item.operation.head in relevant_heads:
                    feats += route_item.flat_checked_features
                elif route_item.operation.arg in relevant_heads:
                    feats += route_item.flat_checked_features
                    relevant_heads.add(route_item.operation.head)
            route_item = route_item.parent
        return feats

    def not_used(self, features):
        return [f for f in features if f not in self.used_features]