hierarchies = [
    ['V', 'v', 'Pass', 'Prog', 'Perf', 'Mod', 'Neg', 'T', 'Fin', 'C'],
    ['N', 'n', 'Poss', 'Num', 'D', 'Q']
]

lex = {
    'him': [('D', 5), None, ('acc', '+')],
    'kiss': [('V', 1), ('D', None)],
    'v': [('v', 2), ('D', None), ('acc', None)],
    'he': [('D', 5), None, ('nom', '+')],
    'T': [('T', 8), ('D', None), ('nom', None), ('tense', 'past')],
}

parts = ['kiss', 'him', 'v', 'he', 'T']


class Feature:
    def __init__(self, name, value, family=''):
        self.name = name
        self.value = value
        self.family = family
        self.union_with = None

    def __str__(self):
        if self.value is None:
            v = '∅'
        else:
            v = self.value
        return f'<{self.name}, {v}>'

    def satisfy(self, other):
        self.union_with = other
        other.union_with = self


class Constituent:

    def __init__(self, data_key='', copy_of=None):
        self.label = data_key
        self.category = None
        self.selects = None
        self.feats = []
        self.parts = {}
        if data_key:
            cat, sel, *feats = lex[data_key]
            self.category = Feature(*cat)
            if sel:
                self.selects = Feature(*sel)
            self.feats = [Feature(*f) for f in feats]
        elif copy_of:
            self.label = copy_of.label
            self.category = copy_of.category
            self.selects = copy_of.selects
            self.feats = copy_of.feats[:]
            self.parts = copy_of.parts

    def __str__(self):
        l = [self.category]
        if self.selects:
            if self.selects.value:
                l.append(self.selects)
            elif self.selects.union_with:
                pass
                # l.append(self.selects.union_with)
            else:
                l.append(self.selects)
        for f in self.feats:
            if f.value:
                l.append(f)
            elif f.union_with:
                l.append(f.union_with)
            else:
                l.append(f)
        s = ', '.join([str(p) for p in l])
        return f'{self.label} = {{{s}}}'

    def SelectMerge(self, selected):
        if self.selects and self.selects.value is None:
            if isinstance(selected, str):
                selected = Constituent(selected)
            if self.selects.name == selected.category.name and selected.category is not None:
                selected.category.satisfy(self.selects)
                merged = Constituent(copy_of=self)
                merged.parts = {self, selected}
                return merged, True
        return self, False

    def HoPMerge(self, other: str or Constituent) -> tuple:
        if isinstance(other, str):
            other = Constituent(other)
        my_cat = self.category.name
        new_cat = other.category.name
        for hierarchy in hierarchies:
            if my_cat in hierarchy and new_cat in hierarchy:
                if hierarchy.index(new_cat) > hierarchy.index(my_cat):
                    merged = Constituent(copy_of=other)
                    merged.parts = {self, other}
                    return merged, True
        return self, False

    def Agree(self):
        def seek_value(fname, host):
            for feat in host.feats:
                if feat.name == fname and feat.value:
                    return feat
            for child in host.parts:
                found = seek_value(fname, child)
                if found:
                    return found

        for feat in self.feats:
            if feat and feat.value is None:
                value_giver = seek_value(feat.name, self)
                if value_giver:
                    value_giver.satisfy(feat)
                    return self, True
        return self, False

    def InternalMerge(self):
        def seek_value(cat_name, host):
            if host.category.name == cat_name and host.category.value:
                return host
            for child in host.parts:
                found = seek_value(cat_name, child)
                if found:
                    return found

        if self.selects and self.selects.value is None:
            mover = seek_value(self.selects.name, self)
            if mover:
                # self.selects = mover.category
                merged = Constituent(copy_of=self)
                mover.category.satisfy(self.selects)
                merged.parts = {mover, self}
                return merged, True
        return self, False


s = Constituent('kiss')
print(s)
s, ok = s.SelectMerge('him')
print('SelectMerge: ', s, ok)
# noinspection PyTypeChecker
s, ok = s.HoPMerge('v')
print('HoPMerge: ', s, ok)
s, ok = s.Agree()
print('Agree: ', s, ok)
s, ok = s.SelectMerge('he')
print('SelectMerge: ', s, ok)
s, ok = s.HoPMerge('T')
print('HoPMerge: ', s, ok)
s, ok = s.Agree()
print('Agree: ', s, ok)
s, ok = s.InternalMerge()
print('InternalMerge: ', s, ok)
print('------------Automatic for the people------------')
part = None
s = Constituent(parts[0])
for part in parts[1:]:
    new = Constituent(part)
    s, ok = s.SelectMerge(new)
    if ok:
        print(part, ' SelectMerge: ', s)
    else:
        s, ok = s.HoPMerge(new)
        if ok:
            print(part, ' HoPMerge: ', s)
        else:
            s, ok = s.InternalMerge()
            if ok:
                print(part, ' InternalMerge: ', s)
            else:
                print(part, ' no merges available')
    s, ok = s.Agree()
    if ok:
        print(part, ' Agree: ', s)
s, ok = s.InternalMerge()
if ok:
    print(part, ' InternalMerge: ', s)
