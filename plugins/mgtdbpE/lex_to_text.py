# Helper to convert list-tuple -based grammars (e.g. mg0.py) to text file grammars

# replace this with grammar you want to convert
grammar_file = 'mg0.py'
grammar_file = grammar_file.rsplit('.', 1)[0]
grammar = __import__(grammar_file, globals=globals(), locals=locals())
outfile_name = grammar_file + '.txt'
out = open(outfile_name, 'w')
fmap = {'cat': '', 'neg': '-', 'pos': '+', 'sel': '='}

for words, feature_tuples in grammar.g:
    w_string = ', '.join(words)
    f_strings = [fmap[value]+name for value, name in feature_tuples]
    out.write('%s :: %s\n' % (w_string, ' '.join(f_strings)))
out.close()

