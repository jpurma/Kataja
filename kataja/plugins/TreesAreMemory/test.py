#################################################################################
# This is the highest level script that should be run when testing the algorithm
################################################################################

import time

from TreesAreMemoryParser import TreesAreMemoryParser

t = time.time()

sentences = open('sentences.txt').readlines()
lexicon = open('lexicon.txt').readlines()
# This creates the parser object itself.
# We can later parametrize the parser (e.g. for different languages, UG parameters, etc.)
P = TreesAreMemoryParser(lexicon)  # The arg = number of parses delivered (= 1) see more for testing

# Provide parses for all sentences and show them
for sentence in sentences:
    sentence = sentence.strip()
    if sentence.startswith('#') or not sentence:
        continue

    # Parse one sentence from the list of sentences
    output = P.parse(sentence)

    # Print out the phrase structure
    # Arg = position in the plausibility ranking, i.e. 0 = the most plausible parse
    # If you want to show all, print(P.output)
    print(sentence)
    print(output)
    print(P.spellout(output))

print(time.time() - t)
