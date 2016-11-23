# Output trees ########


#from ... import nltktreeport # (Tree)
import io

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
        dt = DTree.dnodes_to_dtree(dnodes, all_features=False)
        res = {}
        # d -- derivation tree
        res['d'] = list_tree_to_nltk_tree(dt.as_list_tree())
        # pd -- pretty-printed derivation tree
        output = io.StringIO()
        pptree(output, dt.as_list_tree())
        res['pd'] = output.getvalue()
        output.close()
        # s -- state tree
        res['s'] = list_tree_to_nltk_tree(StateTree(dt).as_list_tree())
        # ps -- pretty-printed state tree
        output = io.StringIO()
        pptree(output, StateTree(dt).as_list_tree())
        res['ps'] = output.getvalue()
        output.close()
        # b -- bare tree
        res['b'] = list_tree_to_nltk_tree(BareTree(dt).as_list_tree())
        # pb -- pretty-printed bare tree
        output = io.StringIO()
        pptree(output, BareTree(dt).as_list_tree())
        res['pb'] = output.getvalue()
        output.close()
        # x -- xbar tree
        res['x'] = list_tree_to_nltk_tree(XBarTree(dt).as_list_tree())
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


class DTree:
    """ Basic constituent tree, base for other kinds of trees. """

    def __init__(self, label='', features=None, parts=None):
        self.label = label or []
        self.features = features or []
        self.parts = parts or []

    def __repr__(self):
        return '[%r:%r, %r]' % (self.label, self.features, self.parts)

    def build_from_dnodes(self, parent_path, dnodes, terminals, all_features=False):
        if terminals and terminals[0].path == parent_path:
            leaf = terminals.pop(0)
            self.label = ' '.join(leaf.label)
            self.features = list(leaf.features)
            self.features.reverse()
            # s = ''
            # for char in leaf.path:
            #     if char == '0':
            #         s += 'L'
            #     else:
            #         s += 'R'
            # s += ':' + self.label
            # print(s)
        elif dnodes and dnodes[0].path.startswith(parent_path):
            root = dnodes.pop(0)
            if all_features:
                self.features = list(root.features)
                self.features.reverse()

            child0 = DTree()
            child0.build_from_dnodes(root.path, dnodes, terminals, all_features=all_features)
            self.parts.append(child0)
            if dnodes and dnodes[0].path.startswith(parent_path):
                self.label = '*'
                root1 = dnodes.pop(0)
                child1 = DTree()
                child1.build_from_dnodes(root1.path, dnodes, terminals, all_features=all_features)
                self.parts.append(child1)
            else:
                self.label = 'o'
                # s = ''
                # for char in parent_path:
                #     if char == '0':
                #         s += 'L'
                #     else:
                #         s += 'R'
                # s += ':' + self.label
                # print(s)

    def as_list_tree(self):
        if len(self.parts) == 2:
            return [self.label, self.parts[0].as_list_tree(), self.parts[1].as_list_tree()]
        elif len(self.parts) == 1:
            return [self.label, self.parts[0].as_list_tree()]
        elif self.features:
            if self.label:
                label = [self.label]
            else:
                label = []
            return label, [str(f) for f in self.features]

    @staticmethod
    def dnodes_to_dtree(dnodes, all_features=False):
        nonterms = []
        terms = []
        for dn in dnodes:
            if dn.terminal:
                terms.append(dn)
            else:
                nonterms.append(dn)
        terms.sort()
        nonterms.sort()
        root = nonterms.pop(0)
        dtree = DTree()
        dtree.build_from_dnodes(root.path, nonterms, terms, all_features=all_features)
        if terms or nonterms:
            print('dnodes_to_dtree error: unused derivation steps')
            print('terms=' + str(terms))
            print('nonterms=' + str(nonterms))
        return dtree


class StateTree:
    """
    convert derivation tree to state tree
    """

    def __init__(self, dtree):
        self.features = []
        self.movers = []
        self.part0 = None
        self.part1 = None
        if dtree.features:
            self.features = dtree.features
        elif dtree.label == '*':
            self.part0 = StateTree(dtree.parts[0])
            self.part1 = StateTree(dtree.parts[1])
            self.merge_check()
        elif dtree.label == 'o':
            self.part0 = StateTree(dtree.parts[0])
            self.move_check()

    def merge_check(self):
        headf0, *remainders0 = self.part0.features
        headf1, *remainders1 = self.part1.features
        if headf0.value == 'sel' and headf1.value == 'cat' and headf0.name == headf1.name:
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


class BareTree:
    """
    convert derivation tree to bare tree
    """

    def __init__(self, dtree):
        self.features = []
        self.movers = []
        self.moving = []
        self.label = ''
        self.part0 = None
        self.part1 = None
        if dtree:
            self.label = dtree.label
            if dtree.features:
                self.features = dtree.features
            elif dtree.label == '*':
                self.part0 = BareTree(dtree.parts[0])
                self.part1 = BareTree(dtree.parts[1])
                self.moving = [] + self.part0.moving + self.part1.moving
                self.merge_check()
            elif dtree.label == 'o':
                self.part1 = BareTree(dtree.parts[0])
                self.move_check()

    def merge_check(self):
        headf0, *remainders0 = self.part0.features
        headf1, *remainders1 = self.part1.features
        if headf0.value == 'sel' and headf1.value == 'cat' and headf0.name == headf1.name:
            self.features = remainders0
            self.movers = self.part0.movers + self.part1.movers
            if remainders1:
                self.movers.append(remainders1)
                self.moving.append((remainders1, self.part1))
                self.part1 = BareTree(None)  # trace
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
        assert found
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
        assert self.part0

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


class XBarTree:
    """
    convert derivation tree to X-bar tree -
      similar to the bare tree conversion
    """

    def __init__(self, dtree, cntr=0, top=True):
        self.features = []
        self.movers = []
        self.label = ''
        self.part0 = None
        self.part1 = None
        self.moving = []
        self.category = ''
        self.cntr = cntr
        self.lexical = False
        if dtree:
            self.label = dtree.label
            if dtree.features:
                self.features = dtree.features
                self.lexical = True
                for f in dtree.features:
                    if f.value == 'cat':
                        self.category = f.name
                        break
                assert self.category

            elif dtree.label == '*':
                self.part0 = XBarTree(dtree.parts[0], self.cntr, top=False)
                self.part1 = XBarTree(dtree.parts[1], self.part0.cntr, top=False)
                self.moving = [] + self.part0.moving + self.part1.moving
                self.merge_check()
            elif dtree.label == 'o':
                self.part1 = XBarTree(dtree.parts[0], self.cntr, top=False)
                self.cntr = self.part1.cntr
                self.move_check()
        if top:
            self.label = self.category + 'P'

    def merge_check(self):
        headf0, *remainders0 = self.part0.features
        headf1, *remainders1 = self.part1.features
        if headf0.value == 'sel' and headf1.value == 'cat' and headf0.name == headf1.name:
            self.features = remainders0  # copy remaining head1 features
            self.movers = self.part0.movers + self.part1.movers  # add movers1 and 2
            self.cntr = self.part1.cntr
            if remainders1:
                self.movers.append(remainders1)
                new_label = '%sP(%s)' % (self.part1.category, self.part1.cntr)
                trace = XBarTree(None, top=False)
                trace.category = self.part1.category
                trace.label = new_label
                self.part1.label = new_label
                self.cntr += 1
                self.moving.append((remainders1, self.part1))
                self.part1 = trace
            elif self.part1.lexical:
                self.part1.category += 'P'
            else:
                self.part1.label = self.part1.category + 'P'
        else:
            raise RuntimeError('merge_check error')
        self.category = self.part0.category
        self.label = self.category + "'"
        if not self.part0.lexical:
            temp = self.part0
            self.part0 = self.part1
            self.part1 = temp

    def move_check(self):
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
        assert found
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
        self.label = self.category + "'"
        assert self.part0

    def as_list_tree(self):
        if not (self.part0 or self.part1):
            if self.lexical:
                if self.label and isinstance(self.label, str):
                    return [self.category, [self.label]]
                else:
                    return [self.category, [self.label]]
            else:
                return [self.label], []
        elif self.part0 and self.part1:  # merge
            return [self.label, self.part0.as_list_tree(), self.part1.as_list_tree()]
        else:
            raise RuntimeError('XBarTree.as_list_tree')

