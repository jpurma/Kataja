
class TestConstituent:
    def __init__(self, label=''):
        self.label = label
        self.parts = []

    def __str__(self):
        return f"[ {' '.join([str(child) for child in self.parts])} ]" if self.parts else self.label


def simple_bracket_tree_parser(sentence, const_model=None):
    """ Handles simple bracket trees where only leaves have text, and spaces cannot be escaped"""

    def finish_const(const):
        if const and const.label:
            c_stack[-1].parts.append(const)
            return None
        return const

    Constituent = const_model or TestConstituent
    c_stack = []
    sentence = list(reversed(sentence))
    const = None
    parent = None

    while sentence:
        c = sentence.pop()
        if c == '[':
            const = finish_const(const)
            c_stack.append(Constituent(''))
        elif c == ']':
            const = finish_const(const)
            if c_stack:
                parent = c_stack.pop()
                if c_stack:
                    c_stack[-1].parts.append(parent)
        elif c == ' ':
            const = finish_const(const)
        else:
            if not const:
                const = Constituent('')
            const.label += c
    return parent


s = "[ [ the [ nice letter ] ] [ from [ the [ smart lady ] ] ] ]"
print(simple_bracket_tree_parser(s))
s = "[[the[nice letter]][from[the[smart lady]]]]"
print(simple_bracket_tree_parser(s))
