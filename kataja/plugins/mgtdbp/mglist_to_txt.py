mg0 = [([], [('=', 'V'), ('', 'C')]), ([], [('=', 'V'), ('+', 'wh'), ('', 'C')]),
       (['the'], [('=', 'N'), ('', 'D')]), (['which'], [('=', 'N'), ('', 'D'), ('-', 'wh')]),
       (['king'], [('', 'N')]), (['queen'], [('', 'N')]), (['wine'], [('', 'N')]),
       (['beer'], [('', 'N')]), (['drinks'], [('=', 'D'), ('=', 'D'), ('', 'V')]),
       (['prefers'], [('=', 'D'), ('=', 'D'), ('', 'V')]),
       (['knows'], [('=', 'C'), ('=', 'D'), ('', 'V')]),
       (['says'], [('=', 'C'), ('=', 'D'), ('', 'V')])]

mg1 = [([], [('=', 'V'), ('', 'C')]),  # = mg0 but without wh features, so no move
       (['the'], [('=', 'N'), ('', 'D')]), (['king'], [('', 'N')]), (['queen'], [('', 'N')]),
       (['wine'], [('', 'N')]), (['beer'], [('', 'N')]),
       (['drinks'], [('=', 'D'), ('=', 'D'), ('', 'V')]),
       (['prefers'], [('=', 'D'), ('=', 'D'), ('', 'V')]),
       (['knows'], [('=', 'C'), ('=', 'D'), ('', 'V')]),
       (['says'], [('=', 'C'), ('=', 'D'), ('', 'V')])]

mg2 = [([], [('=', 'V'), ('', 'C')]),  # = mg1 but without specs, so no merge2
       (['the'], [('=', 'N'), ('', 'D')]), (['king'], [('', 'N')]), (['queen'], [('', 'N')]),
       (['wine'], [('', 'N')]), (['beer'], [('', 'N')]), (['drinks'], [('=', 'D'), ('', 'V')]),
       (['prefers'], [('=', 'D'), ('', 'V')]), (['knows'], [('=', 'C'), ('', 'V')]),
       (['says'], [('=', 'C'), ('', 'V')])]

# mgxx defines the copy language {ww| w\in{a,b}*}
# this grammar has lots of local ambiguity, and does lots of movement
#  (more than in any human language, I think)
#  so it gives the parser a good workout.

mgxx = [([], [('', 'T'), ('-', 'r'), ('-', 'l')]),
        ([], [('=', 'T'), ('+', 'r'), ('+', 'l'), ('', 'T')]),
        (['a'], [('=', 'T'), ('+', 'r'), ('', 'A'), ('-', 'r')]),
        (['b'], [('=', 'T'), ('+', 'r'), ('', 'B'), ('-', 'r')]),
        (['a'], [('=', 'A'), ('+', 'l'), ('', 'T'), ('-', 'l')]),
        (['b'], [('=', 'B'), ('+', 'l'), ('', 'T'), ('-', 'l')])
        ]


def mglist_to_txt(mg):
    for words, features in mg:
        if not words:
            words = ['∅']
        for word in words:
            fstring = ' '.join(['%s%s' % (sign, name) for sign, name in features])
            print('%s:: %s' % (word, fstring))


mglist_to_txt(mg0)
print('--------------')
mglist_to_txt(mg1)
print('--------------')
mglist_to_txt(mg2)
print('--------------')
mglist_to_txt(mgxx)
