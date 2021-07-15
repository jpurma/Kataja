

sentences = [
    'Pekka ui '
]


class Feature:
    simple_signs = {'-', '='}
    def __init__(self, name, sign, value=''):
        self.name = name
        self.sign = sign
        self.value = value

    def __str__(self):
        return f'{self.sign}{self.value}{":" if self.value else ""}{self.value}'

    def __repr__(self):
        return str(self)

    @classmethod
    def from_string(cls, s):
        s = s.strip()
        if not s:
            return
        if s[0] in cls.simple_signs:
            sign = s[0]
            name = s[1:]
        else:
            sign = ''
            name = s
        name, sep, value = name.partition(':')  # 'case:acc' -> name = 'case', subtype = 'acc'
        return cls(name, sign, value)


class Constituent:
    def __init__(self, label=word, features=None):
        self.label = label
        self.feats = features or []


def read_lexicon(lines, lexicon=None):
    if lexicon is None:
        lexicon = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        label, foo, feat_parts = line.partition('::')
        label = label.strip()
        consts = []
        for i, fstring in enumerate(feat_parts.split(',')):
            feats = [Feature.from_string(fs) for fs in fstring.split()]
            const_label = f'({label}{i})' if i else label
            consts.append(Constituent(label=const_label, features=feats))
        if label in lexicon:
            lexicon[label].append(consts)
        else:
            lexicon[label] = [consts]
    return lexicon


my_lexicon = read_lexicon(open('lexicon.txt'))
parser = Parser(my_lexicon)
for sentence in sentences:


