__author__ = 'purma'

from kataja.parser.LatexToINode import LatexFieldToINode

# INode-based parsers are tested by converting latex qtrees into INodes, then back to qtrees.

fields = [
    "hello",
    "two words",
    """ spaced
        thing""",
    "\\emph{italic word}",
    "\\rightarrow here",
    "in \\emph{middle \emph{another}}",
    "\\textbf{broken command"
]

for field in fields:
    print("Entered: ", field)
    parser = LatexFieldToINode()
    node = parser.process(field)
    print("As node: ", repr(node))
    text = node.as_latex()
    print("Turned back: ", text)
    print("------------------")

