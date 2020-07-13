try:
    from plugins.TreesAreMemory2.SimpleConstituent import SimpleConstituent
    from plugins.TreesAreMemory2.State import State
    from plugins.TreesAreMemory2.FuncSupport import context, FuncSupport
    from plugins.TreesAreMemory2.Feature import Feature
    from plugins.TreesAreMemory2.operations import Add, Spec, Comp, Adj
    from plugins.TreesAreMemory2.route_utils import *
except ImportError:
    from SimpleConstituent import SimpleConstituent
    from State import State
    from FuncSupport import context, FuncSupport
    from operations import Add, Spec, Comp, Adj
    from Feature import Feature
    from route_utils import *
from string import ascii_letters


class FuncParser:
    def __init__(self, parser):
        self.active_route = []
        self.last_used_feature = 0
        self.parser = parser
        context.parser = self
        context.states = parser.states
        context.Spec = Spec
        context.Add = Add
        context.Adj = Adj
        context.Comp = Comp

    # Only for _func_parse
    @staticmethod
    def compute_target_linearisation(route):
        words = []
        for operation in route:
            if operation.state.state_type == State.ADD:
                words.append(operation.state.head.label)
        return ' '.join(words)

    def parse(self, sentence):

        def f(word, *feats):
            return FuncSupport.f(word, *feats)

        func_locals = {'f': f}
        self.last_used_feature = 0
        self.active_route = []
        exec(sentence, globals(), func_locals)
        return [self.active_route]

    # Only for _func_parse
    def add_feat_to_route(self, feat, head):
        for operation in self.active_route:
            if operation.state.head is head and feat not in operation.features and feat not in operation.used_features:
                #print('adding missing feat for ', operation.state.head, feat)
                operation.features.append(feat)
                add_feature(operation.state.head, feat)

    # Only for _func_parse
    def speculate_features(self, head, arg):
        pos_feature = Feature(ascii_letters[self.last_used_feature], sign='')
        neg_feature = Feature(ascii_letters[self.last_used_feature], sign='-')
        self.last_used_feature += 1
        add_feature(head, neg_feature)
        add_feature(arg, pos_feature)
        return pos_feature, neg_feature
