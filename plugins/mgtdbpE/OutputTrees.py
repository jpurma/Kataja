# Output trees ########

import io

try:
    from mgtdbpE.Constituent import Constituent
except ImportError:
    from Constituent import Constituent

#try:
#    from nltk.tree import Tree
#except ImportError:
#    Tree = None
Tree = None

def list_tree_to_nltk_tree(listtree):
    """ We can convert a list tree to an NLTK tree with the following: 
    TreeView(list_tree_to_nltk_tree(t))    
    """
    if not Tree:
        return listtree

    if isinstance(listtree, tuple):  # special case for MG lexical items at leaves
        return ' '.join(listtree[0]) + ' :: ' + ' '.join(listtree[1])
    elif isinstance(listtree, str):  # special case for strings at leaves
        return listtree
    elif isinstance(listtree, list) and listtree == []:
        return []
    elif isinstance(listtree, list):
        subtrees = [list_tree_to_nltk_tree(e) for e in listtree[1:]]
        if not subtrees:
            return listtree[0]
        else:
            return Tree(listtree[0], subtrees)
    else:
        raise RuntimeError('list_tree_to_nltk_tree')


def print_results(dnodes, lexicon=None):
        print('attempting to create derivation tree...')
        dt = Constituent.dnodes_to_dtree(dnodes, all_features=True) #False)
        res = {}
        # d -- derivation tree
        res['d'] = list_tree_to_nltk_tree(dt.as_list_tree())
        print('success at creating derivation tree.')
        # pd -- pretty-printed derivation tree
        output = io.StringIO()
        pptree(output, dt.as_list_tree())
        res['pd'] = output.getvalue()
        print(res['pd'])
        output.close()
        # s -- state tree
        print('attempting to create state tree...')
        res['s'] = list_tree_to_nltk_tree(StateTree(dt).as_list_tree())
        print('success at creating state tree.')
        # ps -- pretty-printed state tree
        output = io.StringIO()
        pptree(output, StateTree(dt).as_list_tree())
        res['ps'] = output.getvalue()
        print(res['ps'])
        output.close()
        # b -- bare tree
        print('attempting to create bare tree...')
        res['b'] = list_tree_to_nltk_tree(BareTree(dt).as_list_tree())
        print('success at creating bare tree.')
        # pb -- pretty-printed bare tree
        output = io.StringIO()
        pptree(output, BareTree(dt).as_list_tree())
        res['pb'] = output.getvalue()
        output.close()
        # x -- xbar tree
        print('attempting to create xbar tree...')
        res['x'] = list_tree_to_nltk_tree(XBarTree(dt).as_list_tree())
        print('success at creating xbar tree.')
        # px -- pretty-printed xbar tree
        output = io.StringIO()
        pptree(output, XBarTree(dt).as_list_tree())
        res['px'] = output.getvalue()
        output.close()
        # pg -- print grammar as items
        output = io.StringIO()
        res['pg'] = output.getvalue()
        output.close()
        if lexicon:
            # l -- grammar as tree
            res['l'] = list_tree_to_nltk_tree(['.'] + lex_array_as_list(lexicon))
            # pl -- pretty-printed grammar as tree
            output = io.StringIO()
            pptree(output, ['.'] + lex_array_as_list(lexicon))  # changed EA
            res['pl'] = output.getvalue()
            output.close()
        return res


def _pptree(out, n, t):  # pretty print t indented n spaces
    if isinstance(t, list) and len(t) > 0:
        out.write('\n' + ' ' * n + '[')
        out.write(str(t[0])),  # print root and return
        if len(t[1:]) > 0:
            out.write(',')  # comma if more coming
        for i, subtree in enumerate(t[1:]):  # then print subtrees indented by 4
            _pptree(out, n + 4, subtree)
            if i < len(t[1:]) - 1:
                out.write(',')  # comma if more coming
        out.write(']')
    else:
        out.write('\n' + ' ' * n)
        out.write(str(t))


def pptree(out, t):
    if len(t) == 0:  # catch special case of empty tree, lacking even a root
        out.write('\n[]\n')
    else:
        _pptree(out, 0, t)
        out.write('\n')


def lex_array_as_list(lexicon):
    def as_list(node):
        return [str(node.feature)] + [as_list(x) for x in node.subtrees] + node.terminals

    return [as_list(y) for y in lexicon.values()]


class StateTree:
    """
    convert derivation tree to state tree
    """

    def __init__(self, dtree):
        self.features = []
        self.movers = []
        self.part0 = None
        self.part1 = None
        self.const = dtree
        if dtree.features:
            self.features = dtree.features #.copy()
        if dtree.label == '•' or dtree.label == '●' or dtree.label == '*':
            self.part0 = StateTree(dtree.parts[0])
            self.part1 = StateTree(dtree.parts[1])
            self.merge_check()
        elif dtree.label == '◦' or dtree.label == '○' or dtree.label == 'o':
            self.part0 = StateTree(dtree.parts[0])
            self.move_check()

    def merge_check(self):
        headf0, *remainders0 = self.part0.features
        headf1, *remainders1 = self.part1.features
        if headf0.value == '=' and headf1.value == '' and headf0.name == headf1.name:
            self.features = remainders0
            if remainders1:
                self.movers = [remainders1]
            self.movers += self.part0.movers
            self.movers += self.part1.movers
        else:
            raise RuntimeError('merge_check error')

    def move_check(self):
        mover_match, *remaining = self.part0.features
        self.features = remaining
        found = False
        mover = []
        self.movers = []
        assert self.part0.movers
        for mover_f_list in self.part0.movers:
            if mover_f_list[0].name == mover_match.name:
                if found:
                    raise RuntimeError('SMC violation in move_check')
                mover = mover_f_list[1:]
                found = True
            else:
                self.movers.append(mover_f_list)
        assert found
        if mover:
            self.movers.append(mover)

    def as_list_tree(self):
        fss = []
        if self.features:
            fss.append(self.features)
        fss += self.movers
        sfs = ','.join([' '.join([str(f) for f in fs]) for fs in fss])
        if self.part0 and self.part1:  # merge
            return [sfs, self.part0.as_list_tree(), self.part1.as_list_tree()]
        elif self.part0:  # move
            return [sfs, self.part0.as_list_tree()]
        else:  # leaf
            return [sfs]

    def to_constituent(self, done=None):
        """ Overwrite original constituent (self.const) with its state tree version (self). """
        if done is None:
            done = {}
        parts = []
        label = ' '.join([str(f) for f in self.features])
        if self.movers:
            mstrings = ['<i>%s</i>' % ' '.join([str(f) for f in fs]) for fs in self.movers]
            mstring = ', '.join(mstrings)
            label += ', ' + mstring
        if self.part0:
            if self.part0 in done:
                parts.append(done[self.part0])
            else:
                parts.append(self.part0.to_constituent(done))
        if self.part1:
            if self.part1 in done:
                parts.append(done[self.part1])
            else:
                parts.append(self.part1.to_constituent(done))
        self.const.parts = parts
        self.const.label = label
        self.const.features = []
        done[self] = self.const
        return self.const


class BareTree:
    """ Temporary node to convert constituents from derivation trees to bare tree style
    """

    def __init__(self, dtree):
        self.features = []
        self.movers = []
        self.moving = []
        self.label = ''
        self.part0 = None
        self.part1 = None
        self.const = None
        if dtree:
            self.label = dtree.label
            self.const = dtree
            if dtree.features:
                self.features = dtree.features
            if dtree.label == '•' or dtree.label == '●' or dtree.label == '*':
                self.part0 = BareTree(dtree.parts[0])
                self.part1 = BareTree(dtree.parts[1])
                self.moving = [] + self.part0.moving + self.part1.moving
                self.merge_check()
            elif dtree.label == '◦' or dtree.label == '○' or dtree.label == 'o':
                self.part1 = BareTree(dtree.parts[0])
                self.move_check()

    def merge_check(self):
        if self.part0.features and self.part1.features:
            headf0, *remainders0 = self.part0.features
            headf1, *remainders1 = self.part1.features
            if headf0.value == '=' and headf1.value == '' and headf0.name == headf1.name:
                self.features = remainders0
                self.movers = self.part0.movers + self.part1.movers
                if remainders1:
                    self.movers.append(remainders1)
                    self.moving.append((remainders1, self.part1))
                    #self.part1 = BareTree(None)  # trace
            else:
                raise RuntimeError('merge_check error')
        if not (self.part0.part0 or self.part0.part1):  # is it leaf?
            self.label = '<'
        else:
            self.label = '>'  # switch order to part1, part0
            temp = self.part0
            self.part0 = self.part1
            self.part1 = temp

    def move_check(self):
        if self.part1.features:
            mover_match, *remaining = self.part1.features
            self.features = remaining
            found = False
            mover = []
            self.movers = []
            for mover_f_list in self.part1.movers:
                if mover_f_list[0].name == mover_match.name:
                    if found:
                        raise RuntimeError('SMC violation in move_check')
                    mover = mover_f_list[1:]
                    found = True
                else:
                    self.movers.append(mover_f_list)
            #assert found
            self.moving = []
            for (fs, moving_tree) in self.part1.moving:
                if fs[0].name == mover_match.name:
                    self.part0 = moving_tree
                else:
                    self.moving.append((fs, moving_tree))
            if mover:
                self.movers.append(mover)
                self.moving.append((mover, self.part0))
        self.label = '>'
        #assert self.part0

    def as_list_tree(self):
        if not (self.part0 or self.part1):
            if isinstance(self.label, list):
                w = ' '.join(self.label)
            else:
                w = self.label
            return '%s::%s' % (w, ' '.join([str(f) for f in self.features]))
        elif self.part0 and self.part1:  # merge
            return [self.label, self.part0.as_list_tree(), self.part1.as_list_tree()]
        else:
            raise RuntimeError('BareTree.as_list_tree')

    def to_constituent(self, done=None):
        """ Overwrite original constituent (self.const) with its bare tree version (self). """
        if done is None:
            done = {}
        parts = []
        if self.part0:
            if self.part0 in done:
                parts.append(done[self.part0])
            else:
                parts.append(self.part0.to_constituent(done))
        if self.part1:
            if self.part1 in done:
                parts.append(done[self.part1])
            else:
                parts.append(self.part1.to_constituent(done))
        self.const.label = self.label
        if parts:
            if self.label == '<':
                self.const.heads = [parts[0]]
            elif self.label == '>':
                if len(parts) > 1:
                    self.const.heads = [parts[1]]
                else:
                    self.const.heads = []
        self.const.parts = parts
        if not parts:
            self.const.features = self.features
        else:
            self.const.features = []
        done[self] = self.const
        return self.const

#
# class XBarTree:
#     """
#     convert derivation tree to X-bar tree -
#       similar to the bare tree conversion
#     """
#
#     def __init__(self, dtree, cntr=0, top=True):
#         self.features = []
#         self.movers = []
#         self.label = ''
#         self.part0 = None
#         self.part1 = None
#         self.moving = []
#         self.category = ''
#         self.cntr = cntr
#         self.lexical = False
#         if dtree:
#             self.label = dtree.label
#             if dtree.features:
#                 self.features = dtree.features
#                 self.lexical = True
#                 for f in dtree.features:
#                     if f.value == '':
#                         self.category = f.name
#                         break
#                 assert self.category
#
#             if dtree.label == '•' or dtree.label == '●' or dtree.label == '*':
#                 self.part0 = XBarTree(dtree.parts[0], self.cntr, top=False)
#                 self.part1 = XBarTree(dtree.parts[1], self.part0.cntr, top=False)
#                 self.moving = [] + self.part0.moving + self.part1.moving
#                 self.merge_check()
#             elif dtree.label == '◦' or dtree.label == '○' or dtree.label == 'o':
#                 self.part1 = XBarTree(dtree.parts[0], self.cntr, top=False)
#                 self.cntr = self.part1.cntr
#                 self.move_check()
#         if top:
#             self.label = self.category + 'P'
#
#     def merge_check(self):
#         headf0, *remainders0 = self.part0.features
#         headf1, *remainders1 = self.part1.features
#         if headf0.value == '=' and headf1.value == '' and headf0.name == headf1.name:
#             self.features = remainders0  # copy remaining head1 features
#             self.movers = self.part0.movers + self.part1.movers  # add movers1 and 2
#             self.cntr = self.part1.cntr
#             if remainders1:
#                 self.movers.append(remainders1)
#                 new_label = '%sP(%s)' % (self.part1.category, self.part1.cntr)
#                 trace = XBarTree(None, top=False)
#                 trace.category = self.part1.category
#                 trace.label = new_label
#                 self.part1.label = new_label
#                 self.cntr += 1
#                 self.moving.append((remainders1, self.part1))
#                 self.part1 = trace
#             elif self.part1.lexical:
#                 self.part1.category += 'P'
#             else:
#                 self.part1.label = self.part1.category + 'P'
#         else:
#             raise RuntimeError('merge_check error')
#         self.category = self.part0.category
#         self.label = self.category + "'"
#         if not self.part0.lexical:
#             temp = self.part0
#             self.part0 = self.part1
#             self.part1 = temp
#
#     def move_check(self):
#         mover_match, *remaining = self.part1.features
#         self.features = remaining
#         found = False
#         mover = []
#         self.movers = []
#         for mover_f_list in self.part1.movers:
#             if mover_f_list[0].name == mover_match.name:
#                 if found:
#                     raise RuntimeError('SMC violation in move_check')
#                 mover = mover_f_list[1:]
#                 found = True
#             else:
#                 self.movers.append(mover_f_list)
#         assert found
#         self.moving = []
#         for (fs, moving_tree) in self.part1.moving:
#             if fs[0].name == mover_match.name:
#                 self.part0 = moving_tree
#             else:
#                 self.moving.append((fs, moving_tree))
#         if mover:
#             self.movers.append(mover)
#             self.moving.append((mover, self.part0))
#         self.category = self.part1.category
#         self.label = self.category + "'"
#         assert self.part0
#
#     def as_list_tree(self):
#         if not (self.part0 or self.part1):
#             if self.lexical:
#                 if self.label and isinstance(self.label, str):
#                     # this is creating ["D'" [ "which" ] ] -trees as lists which we don't want
#                     return [self.category, [self.label]]
#                 else:
#                     return [self.category, [self.label]]
#             else:
#                 return [self.label], []
#         elif self.part0 and self.part1:  # merge
#             return [self.label, self.part0.as_list_tree(), self.part1.as_list_tree()]
#         else:
#             raise RuntimeError('XBarTree.as_list_tree')
#
#     def to_constituent(self):
#         parts = []
#         if self.part0:
#             parts.append(self.part0.to_constituent())
#         if self.part1:
#             parts.append(self.part1.to_constituent())
#         if parts:
#             return Constituent(label=self.label, parts=parts)
#         else:
#             if self.lexical:
#                 head = Constituent(label=self.label, features=self.features)
#                 return Constituent(label=self.category, parts=[head])
#             else:
#                 return Constituent(label=self.label, features=self.features)


class TracelessXBarTree:
    """
    Temporary node to help convert derivation trees to X-bar trees -
      similar to the bare tree conversion
    """

    def __init__(self, dtree, top=True):
        self.features = []
        self.movers = []
        self.label = ''
        self.part0 = None
        self.part1 = None
        self.head = None
        self.moving = []
        self.category = ''
        self.const = None
        if dtree:
            self.const = dtree
            self.label = dtree.label
            assert isinstance(dtree.label, str)
            if dtree.features:
                self.features = dtree.features
                for f in dtree.features:
                    if f.value == '':
                        self.category = f.name
                        break
                assert self.category

            if dtree.label == '•' or dtree.label == '●' or dtree.label == '*':
                self.part0 = TracelessXBarTree(dtree.parts[0], top=False)
                self.part1 = TracelessXBarTree(dtree.parts[1], top=False)
                self.moving = [] + self.part0.moving + self.part1.moving
                self.merge_check()
            elif dtree.label == '◦' or dtree.label == '○' or dtree.label == 'o':
                self.part1 = TracelessXBarTree(dtree.parts[0], top=False)
                self.move_check()
        if top:
            self.label = self.category + 'P'

    def merge_check(self):
        if self.part0.features and self.part1.features:
            headf0, *remainders0 = self.part0.features
            headf1, *remainders1 = self.part1.features
            if headf0.value == '=' and headf1.value == '' and headf0.name == headf1.name:
                self.features = remainders0  # copy remaining head1 features
                self.movers = self.part0.movers + self.part1.movers
                if remainders1:
                    self.movers.append(remainders1)
                    self.moving.append((remainders1, self.part1))
                else:
                    #pass
                    self.part1.category += 'P'
            else:
                # raise RuntimeError('merge_check error')
                # we are ok with having broken/not ready derivations
                pass
        self.category = self.part0.category
        self.head = self.part0
        self.label = self.category + "'"

        if self.part0.part0 or self.part0.part1:  # is it leaf?
            temp = self.part0
            self.part0 = self.part1
            self.part1 = temp

    def move_check(self):
        if self.part1.features:
            mover_match, *remaining = self.part1.features
            self.features = remaining
            found = False
            mover = []
            self.movers = []
            for mover_f_list in self.part1.movers:
                if mover_f_list[0].name == mover_match.name:
                    if found:
                        raise RuntimeError('SMC violation in move_check')
                    mover = mover_f_list[1:]
                    found = True
                else:
                    self.movers.append(mover_f_list)
            #assert found
            self.moving = []
            for (fs, moving_tree) in self.part1.moving:
                if fs[0].name == mover_match.name:
                    self.part0 = moving_tree
                else:
                    self.moving.append((fs, moving_tree))
            if mover:
                self.movers.append(mover)
                self.moving.append((mover, self.part0))
        self.category = self.part1.category
        self.head = self.part1
        self.label = self.category + "'"
        #assert self.part0

    def as_list_tree(self):
        if not (self.part0 or self.part1):
            if self.label and isinstance(self.label, str):
                # this is creating ["D'" [ "which" ] ] -trees as lists which we don't want
                return [self.category, [self.label]]
            else:
                return [self.category, [self.label]]
        elif self.part0 and self.part1:  # merge
            return [self.label, self.part0.as_list_tree(), self.part1.as_list_tree()]
        else:
            raise RuntimeError('XBarTree.as_list_tree')

    def to_constituent(self, done=None):
        """  Overwrite original constituent (self.const) with its xbar version (self). """
        if done is None:
            done = {}
        parts = []
        if self.part0:
            if self.part0 in done:
                p0 = done[self.part0]
            else:
                p0 = self.part0.to_constituent(done)
            parts.append(p0)
        if self.part1:
            if self.part1 in done:
                p1 = done[self.part1]
            else:
                p1 = self.part1.to_constituent(done)
            parts.append(p1)
        if parts:
            self.const.label = self.label
            self.const.features = []
            self.const.parts = parts
            if self.head:
                if self.head == self.part0:
                    self.const.heads = [self.part0.const]
                elif self.head == self.part1:
                    self.const.heads = [self.part1.const]
        else:
            head = Constituent(label=self.label, features=self.features)
            self.const.label = self.category
            self.const.features = []
            self.const.parts = [head]

        done[self] = self.const
        return self.const

    # def __hash__(self):
    #     return id(self)
