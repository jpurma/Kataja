try:
    from plugins.TreesAreMemory3.route_utils import *
    from plugins.TreesAreMemory3.operations import Add, Adj
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
    """ RouteItems are elements of attempted parses. Each RouteItem hosts one operation -- same operation can be hosted
      in many RouteItems if the same operation appears in different stages in parses. RouteItems form parse trees,
        each RouteItem (except first) has a parent item for 'previous step' and children for its possible next steps.
        RouteItems store parser's state at that point.
        """

    def __init__(self, parent, operation):
        self.parent = parent
        self.children = []
        self.operation = operation
        self.path = f'{self.parent.path}_{self.operation.ord}' if self.parent else str(self.operation.ord)
        self.uid = self.operation.ord
        self._features = None
        self._local_heads = None
        self._available_heads = None
        self.consts = []
        self.const = None
        if parent and self not in parent.children:
            parent.children.append(self)
        self.head_trees = None
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

    @property
    def features(self):
        return self.collect_available_features()

    def collect_available_features(self):
        if self._features is not None:
            return self._features
        heads = {self.head}
        removed = set()
        route_item = self
        feats = []
        while route_item and heads:
            if route_item.head in heads:
                removed |= {checked for checkee, checked in self.operation.checked_features if checked.sign}
                removed |= {checkee for checkee, checked in self.operation.checked_features if checked.sign}
                if route_item.operation.state_type == ADJUNCT:
                    heads.remove(route_item.head)
                    heads.add(route_item.head[0])
                    heads.add(route_item.head[1])
                elif route_item.operation.state_type == ADD:
                    heads.remove(route_item.head)
                    feats += [f for f in route_item.head.features if f not in feats]
            route_item = route_item.parent
        self._features = [f for f in feats if f not in removed]
        return self._features

    def find_available_heads(self):
        if self._available_heads is not None:
            return self._available_heads

        def add_unavailable(const, unavailable):
            if not isinstance(const, tuple) and const.complex_parts:
                unavailable |= set(const.complex_parts)
            else:
                unavailable.add(const)

        def add_banned_argument(const, banned_arguments):
            if not isinstance(const, tuple) and const.complex_parts:
                banned_arguments |= set(const.complex_parts)
            else:
                banned_arguments.add(const)

        unavailable = set()
        banned_arguments = set()
        add_unavailable(self.head, unavailable)
        add_banned_argument(self.head, banned_arguments)
        self._available_heads = []
        item = self
        print('starting from ', item)
        print('unavailable: ', unavailable, ' banned_arguments: ', banned_arguments)
        while item:
            print('doing item ', item)
            if item.arg:
                print('adding unavailable arg: ', item.arg)
                add_unavailable(item.arg, unavailable)
                if item.arg in banned_arguments:
                    print('adding banned argument: ', item.head)
                    add_banned_argument(item.head, banned_arguments)
            elif item.operation.state_type == ADJUNCT:
                print("at adjunct, add unavailable: ", item.head[0], item.head[1])
                add_unavailable(item.head[0], unavailable)
                add_unavailable(item.head[1], unavailable)
                if item.head in banned_arguments:
                    add_banned_argument(item.head[0], banned_arguments)
                    add_banned_argument(item.head[1], banned_arguments)
                    print('added banned arguments: ', item.head[0], item.head[1])
            # Myös jos nykyinen on osa elementin argumenttia
            if item.arg and item.arg in banned_arguments:
                print('skipping ', item, ' because of banned arguments ', banned_arguments)
                add_unavailable(item.head, unavailable)
                print('add ', item.head, ' to unavailables')
                pass
            elif item.head not in unavailable:
                print('add ', item, ' to available heads')
                self._available_heads.append(item)
                add_unavailable(item.head, unavailable)
                print('add ', item.head, ' to unavailables')
            item = item.parent
        print('------ done, ', self, ' available heads: ', self._available_heads)
        return self._available_heads

    def find_local_heads(self):
        if self._local_heads is not None:
            return self._local_heads
        unavailable = {self.head}
        item = self
        self._local_heads = []
        while item:
            if item.operation.state_type in {ADJUNCT, ADD}:
                if item.head in unavailable:
                    if item.operation.complex_parts:
                        for op in item.operation.complex_parts:
                            unavailable.add(op.head)
                else:
                    self._local_heads.append(item)
                    break
            if item.head in unavailable and item.arg:
                unavailable.add(item.arg)
            elif item.arg and item.arg in unavailable:
                unavailable.add(item.head)
            elif item.head in unavailable and item.operation.state_type is ADJUNCT:
                head0, head1 = item.head
                unavailable.add(head0)
                unavailable.add(head1)
            item = item.parent
        return self._local_heads

    def as_route(self):
        route = []
        route_item = self
        while route_item:
            route.append(route_item)
            route_item = route_item.parent
        return list(reversed(route))

    def find_closest_head(self, head):
        if self.operation.head is head:
            return self
        elif self.parent:
            return self.parent.find_closest_head(head)
