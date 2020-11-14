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
        self.uid = operation_ids.get_id()
        self.parent = parent
        self.operation = operation
        self.features = []
        self.free_precedents = []
        self.flat_checked_features = flatten_checked(operation.checked_features)
        self.features = self.operation.calculate_features(self)
        print(f'route item {self} has features: {self.features}')
        self.previous = self.calculate_previous_item()
        self.free_precedents = self.operation.calculate_free_precedents(self)
        self.path = f'{self.parent.path}_{self.uid}' if self.parent else str(self.uid)
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

    def as_route(self):
        route = []
        route_item = self
        while route_item:
            route.append(route_item)
            route_item = route_item.parent
        return list(reversed(route))

    def first_free_precedent(self):
        if self.free_precedents:
            return self.free_precedents[0]

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
        if self.operation.arg:
            return self.parent.find_closest_head(self.operation.arg)

    def find_head_item(self):
        return self.parent.find_closest_head(self.operation.head)

    def find_previous_added_head(self):
        if type(self.operation) is Adj or type(self.operation) is Add:
            return self.operation.head
        elif self.parent:
            return self.parent.find_previous_added_head()

    def calculate_previous_item(self):
        if self.parent:
            prev_added_head = self.parent.find_previous_added_head()
            if prev_added_head:
                found = self.find_closest_head(prev_added_head)
                print(f'for {self} previous item is {found}')
                return found