

# This module has functions for parsing LaTeX QTree structures to generic node-based representations.
# These representations can then be converted to other structures, e.g. Kataja Constituents and ConstituentNodes.

# This module can be run and tested as it is,
#from kataja.utils import time_me

from kataja.parser.INodes import ICommandNode, IConstituentNode, ITextNode

class ParseError(Exception):
    pass



one_character_commands = ['&', '~', '#', '%', '$', '^', '_']

#@time_me
def parse(text):
    """ Turn text into INodes (intermediary nodes). These can be IConstituentNodes, ICommandNodes or ITextNodes.
    INodes are then, dependent on purpose of parsing turned into Kataja's ConstituentNodes, rich text format
    representations (with NodeToQTextDocument), HTML or flat strings. The nodes also store the original raw string
    (=text that was given to parser).
        :param text: string to parse.
    """
    if not text:
        return None
    text = text.strip()
    if not text:
        return None
    feed = list(text)
    nodes = []
    while feed:
        c = feed[0]
        if c == '[':
            feed, node = parse_brackets(feed)
            if not node.is_empty():
                nodes.append(node)
        elif c == ']':
            feed.pop(0)
        else:
            feed, node = parse_word(feed)
            if not node.is_empty():
                nodes.append(node)
            else:
                feed.pop(0)
    if len(nodes) == 1:
        return nodes[0]
    else:
        return nodes

#@time_me
def parse_field(text):
    """ Simpler version of parse, turns values of text fields into INodes (intermediary nodes).
    Results are ITextNodes that may contain more ITextNodes and ICommandNodes.
        :param text: string to parse.
    """
    if not text:
        return None
    text = text.strip()
    if not text:
        return None
    feed = list(text)
    while feed:
        feed, node = parse_word(feed)
    return node

def parse_word(feed):
    """ Turn text into ITextNodes. If something special (commands, curlybraces, brackets is found, deal with them by
    creating new Nodes of specific types
        :param feed: list of chars (strings of length 1)
    """

    node = ITextNode()

    def eat_char():
        feed.pop(0)

    while feed:
        c = feed[0]
        if c == '{':
            feed, new_node = parse_curlies(feed)
            node.add_part(new_node)
        elif c == '}':
            return feed, node
        elif c == '\\':
            feed, new_node = parse_command(feed)
            node.add_part(new_node)
        elif c in one_character_commands:
            feed.pop(0)
            feed, new_node = parse_one_character_command(feed, c)
            node.add_part(new_node)
        elif c.isspace():
            eat_char()
            return feed, node
        elif c == ']':
            return feed, node
        elif c == '[':
            return feed, node

        else:
            eat_char()
            node.add_char(c)
    return feed, node


def parse_curlies(feed):
    """ Turn text into ITextNodes, but don't let space end the current ITextNode. Only closing curly brace will end
    the node parsing.
        :param feed: list of chars (strings of length 1)
    """
    node = ITextNode()

    def eat_char():
        feed.pop(0)

    eat_char()

    while feed:
        c = feed[0]
        if c == '{':
            feed, new_node = parse_curlies(feed)
            node.add_part(new_node)
        elif c == '}':
            eat_char()
            return feed, node
        elif c == '\\':
            feed, new_node = parse_command(feed)
            node.add_part(new_node)
        elif c in one_character_commands:
            feed.pop(0)
            feed, new_node = parse_one_character_command(feed, c)
            node.add_part(new_node)
        else:
            eat_char()
            node.add_char(c)
    raise ParseError


def parse_one_character_command(feed, command):
    """ Start a new command node, where the command is just one character and already given as a param.
        e.g. _{subscripted text} or ^{superscript}
        :param feed: list of chars (strings of length 1)
        :param command: one character command recognized by parent parser
    """
    node = ICommandNode()
    node.add_command_char(command)
    node.prefix = '' # now it doesn't start with \

    def eat_char():
        feed.pop(0)

    while feed:
        c = feed[0]
        if c == '{':
            feed, new_node = parse_curlies(feed)
            node.add_part(new_node)
            return feed, node
        elif c == '}':
            # weird situation
            print(" plain '}' after one char command. what to do? ")
            return feed, node
        elif c == '\\':
            if len(node.command) == 1:
                # _\something -- is it possible?
                eat_char()
                node.add_char(c)
                print('backslash after one character command, what to do?')
                return feed, node
            else:
                return feed, node
        elif c.isspace():
            eat_char()
            return feed, node
        elif c == ']':
            print(" plain ']' after one char command. what to do? ")
            return feed, node
        else:
            eat_char()
            node.add_char(c)
            return feed, node


def parse_command(feed):
    """ Turn text into ICommandNodes. These are best understood as tags, where the tag is the command, and parts of the
     node are the scope of the tag. Reads a word and stores it as a command, and then depending how the word ends,
        either ends the command node or starts reading next entries as a nodes inside the ICommandNode.
        :param feed: list of chars (strings of length 1)
    """
    node = ICommandNode()

    def eat_char():
        feed.pop(0)

    eat_char() # this is the beginning "\"

    while feed:
        c = feed[0]
        if c == '{':
            include_space = False
            feed, new_node = parse_curlies(feed)
            node.add_part(new_node)
        elif c == '}':
            return feed, node
        elif c == '\\':
            if not node.command:
                # this is an line break in latex, '\\'', two backslashes in row --
                # not two command words
                eat_char()
                node.add_command_char(c)
                return feed, node
            else:
                return feed, node
        elif c == ' ':
            eat_char()
            return feed, node
        elif c == ']':
            return feed, node
        else:
            eat_char()
            node.add_command_char(c)
    return feed, node


def parse_brackets(feed):
    """ Turn text into IConstituentNodes. Constituents are expected to contain aliases, labels and other constituents
    and these are read as IConstituentNodes or ITextNodes.
        :param feed: list of chars (strings of length 1)
    """
    node = IConstituentNode()
    assert(feed[0] == '[')

    def eat_char():
        feed.pop(0)

    eat_char()

    while feed:
        c = feed[0]
        if c == '[':
            feed, new_cnode = parse_brackets(feed)
            node.add_part(new_cnode)
        elif c == ']':
            # Finalize merger
            eat_char()
            # if closing bracket continues with . ( "[ ... ].NP " ) it is treated as label
            if feed and feed[0] == '.':
                eat_char()
                feed, new_node = parse_word(feed)
                node.add_label_complex(new_node)
            node.sort_out_label_complex()
            return feed, node
        elif c.isspace():
            eat_char()
        elif c == '.':
            eat_char()
            feed, new_node = parse_word(feed)
            node.add_label_complex(new_node)
        else:
            # Make a new constituent
            new_cnode = IConstituentNode()
            feed, new_node = parse_word(feed) # Read simple constituent e.g. A or B in [ A B ]
            # What we just read was label for that constituent
            new_cnode.add_label_complex(new_node)
            new_cnode.sort_out_label_complex()
            node.add_part(new_cnode)
    node.sort_out_label_complex()
    return feed, node

# ### Test cases
if __name__ == "__main__":

    s = r"""[.{AspP} [.{Asp} Ininom] [.{vP} [.{KP} [.{K} ng] [.{DP} [.{D´} [.{D} {} ] [.{NP} lola ]] [.{KP} [.{K} ng] [.{DP} [.{D´} [.{D} {} ] [.{NP} alila] ] [.{KP} {ni Maria} ]]]]] [.{v´} [.{v} {} ] [.{VP} [.{V} {} ] [.{KP} {ang tubig}]]]]]"""

    s = r"""[ [.{Acc_i} B [.{Nom} A [.{DP} the grass ] ] ] [ S–Acc [ … [ [.{GenP_j} C t_i ] [ S–Gen [.{vP\rightarrow\emph{load}} … [.{v´} v^0 [.{VP} V [.{PP} [.{InsP} E [.{DatP} D t_j ] ] [.{P´} P [.{NP*} the truck ] ] ] ] ] ] ] ] ] ] ]"""

    s = r"""[.{EvidP} Part-Evid^0 [.{EvidP} [.{NegP} Part-Neg [.{NegP_j} [.{vP_i} Args Verb] [.{Neg} Neg^0 t_i ]]] [.{Evid} Evid0 t_k ]]]
    """


    s = r"""[.TP
[.AdvP [.Adv\\usually ] ]
          [.TP
             [.DP [.D\\{\O} ] [.NP\\John ] ]
             [.T\1
               [.T\\\emph{PRESENT} ]
               [.VP [.VP
                 [.V\\goes ] [.PP [.P\\to ]
                                  [.DP [.D\\the ] [.NP\\park ] ]
] ]
                     [.PP [.P\\on ]
                          [.DP [.D\\{\O} ] [.NP\\Tuesdays ] ]
] ]
] ]
]
"""

    s = r"""[.TP [.AdvP [.Adv\\usually ] ] [.TP [.DP [.D\\{\O} ] [.NP\\John ] ] [.T\1 [.T\\\emph{PRESENT} ] [.VP [.VP [.V\\goes ] [.PP [.P\\to ] [.DP [.D\\the ] [.NP\\park ] ] ] ] [.PP [.P\\on ] [.DP [.D\\{\O} ] [.NP\\Tuesdays ] ] ] ] ] ] ] ]"""



    n = parse(s)


    print(n)

