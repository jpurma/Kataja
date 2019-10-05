from kataja.parser.latex_to_unicode import latex_to_unicode

greek = []
latin = []
combining = []
rest = []
keys = list(latex_to_unicode.keys())
keys.sort()
d = {}

tables = ['cyrchar', 'ding', 'ElsevierGlyph', 'mathbb', 'mathbf', 'mathbit', 'mathfrak', 'mathmit', 'mathscr',
          'mathsfbfsl', 'mathsfbf', 'mathsfsl', 'mathsf', 'mathslbb', 'mathsl', 'mathtt']

for table in tables:
    d[table] = []

for key in keys:
    char, description = latex_to_unicode[key]
    if 'greek' in description:
        greek.append(key)
    elif description.startswith('latin'):
        latin.append(key)
    elif description.startswith('combining'):
        combining.append(key)
    else:
        found = False
        for tname in tables:
            if key.startswith(tname):
                d[tname].append(key)
                found = True
                break
        if not found:
            rest.append(key)

print(len(greek), greek)
print(len(latin), latin)
for table in tables:
    print(len(d[table]), d[table])
print(len(rest), rest)
