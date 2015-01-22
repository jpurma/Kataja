

# This module has functions for parsing LaTeX QTree structures to generic node-based representations.
# These representations can then be converted to other structures, e.g. Kataja Constituents and ConstituentNodes.

# This module can be run and tested as it is,
#from kataja.utils import time_me


latex_to_rtf = {
    'sup': 'sup', 
    'emph': 'i', 
    'textbf': 'b'    
}

class ParseError(Exception):
    pass


class ITextNode:
    """ Node to represent text that may contain other kinds of nodes. e.g.
    "here is a text \emph{with latexnode} inside."
    This would turn to list of parts, where most of parts are other TextNodes and one CommandNode with TextNode inside.
    self.raw will always contain the original text to be parsed for scope of the node
    """

    def __init__(self):
        self.parts = []
        self.raw = []        

    def add_raw_char(self, c):
        """
        :param c: char (string of length 1)
        """
        self.raw.append(c)

    def add_char(self, c):
        """
        :param c: char (string of length 1)
        """
        self.parts.append(c)

    def add_part(self, node):
        """
        :param node: any kind of INode or string)
        """
        self.parts.append(node)
        self.raw += node.raw


    def parts_as_string(self):
        """ Parts flattened into string, recursively stringifies parts if they contain other INodes
        :return:
        """
        return ''.join([str(x) for x in self.parts])

    def __str__(self):
        return self.parts_as_string()

    @property
    def raw_string(self):
        """
        :return:
        """
        return ''.join(self.raw)

    def structure(self, depth=0):
        """ Pretty printer for debugging
        :param depth:
        :return:
        """
        s = depth * ' '
        for item in self.parts:
            if isinstance(item, ITextNode):
                item.structure(depth + 1)
            else:
                s += item
        print(s)


class ICommandNode(ITextNode):
    """ Node that contains command (like a html tag or a LaTeX command) as a string and where
    the scope of the command is the parts of the node. """

    def __init__(self):
        """ Command is stored as a string in self.command. self.parts are the TextNodes in the scope of command. """  
        ITextNode.__init__(self)
        self.command = ''

    def add_command_char(self, c):
        """
        :param c: char (string of length 1)
        """
        self.command += c

    def __str__(self):
        if self.parts:
            return '(%s)%s(/%s)' % (self.command, self.parts_as_string(), self.command)
        else:
            return '(%s/)' % self.command

    def structure(self, depth=0):
        """ Pretty printer for debugging
        :param depth:
        :return:
        """
        s = depth * ' '
        if self.command:
            s += '(C:%s)' % self.command
        for item in self.parts:
            if isinstance(item, ITextNode):
                item.structure(depth + 1)
            else:
                s += item
        print(s)


class IConstituentNode(ITextNode):
    """ Intermediary Node that contains basic information required for building a linguistic constituent.
    (Except features)
    IConstituentNode has label, alias, index and parts, where parts are IConstituentNodes and other are ITextNodes
    """

    def __init__(self):
        ITextNode.__init__(self)
        self.label = ''
        self.alias = ''
        self.index = ''

    def add_alias(self, node):
        """

        :param node:
        """
        self.alias = node
        self.raw += node.raw

    def add_label(self, node):
        """

        :param node:
        """
        self.label = node
        self.raw += node.raw

    def prepare_index(self):
        """ Check if alias or label contains something that can be used as an index.
        Sets the index (simple string) if so.
        :return: None
        """
        def find_index(node):
            """ Recursively look for index ( _{something} or _c ) in given node / string.
            :param node:
            :return: found index or None
            """
            if isinstance(node, ICommandNode) and node.command == '_':
                return node.parts_as_string()
            elif isinstance(node, ITextNode):
                for part in node.parts:
                    index = find_index(part)
                    if index:
                        return index
        index = find_index(self.alias)
        if index:
            self.index = index
        else:
            index = find_index(self.label)
            if index:
                self.index = index
            else:
                self.index = ''
        if index:
            print ('found index for %s: %s' % (self, self.index))


    def __str__(self):
        if self.parts and self.alias:
            return '[.%s %s]' % (self.alias, self.parts_as_string())
        elif self.parts:
            return '[%s]' % self.parts_as_string()
        elif self.alias:
            return '.{%s}%s' % (self.alias, self.label)
        else:
            return str(self.label)

    def structure(self, depth=0):
        """ Pretty printer for debugging
        :param depth:
        :return:
        """
        s = depth * ' '
        if self.alias:
            s += '(.%s)' % self.alias
        if self.label:
            s += '(L:%s)' % self.label
        for item in self.parts:
            if isinstance(item, ITextNode):
                item.structure(depth + 1)
            else:
                s += item
        print(s)


one_character_commands = ['&', '~', '#', '%', '$', '^', '_']

#@time_me
def parse(text):
    """ Turn text into INodes (intermediary nodes). These can be IConstituentNodes, ICommandNodes or ITextNodes.
    INodes are then, dependent on purpose of parsing turned into Kataja's ConstituentNodes, rich text format
    representations (with NodeToQTextDocument), HTML or flat strings. The nodes also store the original raw string
    (=text that was given to parser).
        :param text: string to parse.
    """
    text = text.strip()
    if not text:
        return None
    feed = list(text)
    node = None
    while feed:
        c = feed[0]
        if c == '[':
            feed, node = parse_brackets(feed)
        elif c == ']':
            feed.pop(0)
        else:
            feed, node = parse_word(feed)
    try:
        assert(node.raw_string == text)
    except AssertionError:
        print('raw string different from given input:')
        print('---- raw string ----')
        print(node.raw_string)
        print('---- input was ----')
        print(text)
        #quit()
    return node


def parse_word(feed):
    """ Turn text into ITextNodes. If something special (commands, curlybraces, brackets is found, deal with them by
    creating new Nodes of specific types
        :param feed: list of chars (strings of length 1)
    """

    node = ITextNode()

    def eat_char():
        """ Remove char from the feed and remember it in raw form.
        If everything goes right, sum of nodes' raw forms should be the original string"""
        node.add_raw_char(feed.pop(0))

    while feed:
        c = feed[0]
        if c == '{':
            eat_char()
            feed, new_node = parse_curlies(feed)
            node.add_part(new_node)
        elif c == '}':
            return feed, node
        elif c == '\\':
            eat_char()
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
        """ Remove char from the feed and remember it in raw form.
        If everything goes right, sum of nodes' raw forms should be the original string"""
        node.add_raw_char(feed.pop(0))

    while feed:
        c = feed[0]
        if c == '{':
            eat_char()
            feed, new_node = parse_curlies(feed)
            node.add_part(new_node)
        elif c == '}':
            eat_char()
            return feed, node
        elif c == '\\':
            eat_char()
            feed, new_node = parse_command(feed)
            node.add_part(new_node)
        elif c in one_character_commands:
            feed.pop(0)
            feed, new_node = parse_one_character_command(feed, c)
            node.add_part(new_node)
        else:
            eat_char()
            node.add_char(c)
    print('CurlyBuilder finished')
    raise ParseError


def parse_one_character_command(feed, command):
    """ Start a new command node, where the command is just one character and already given as a param.
        e.g. _{subscripted text} or ^{superscript}
        :param feed: list of chars (strings of length 1)
        :param command: one character command recognized by parent parser
    """
    node = ICommandNode()
    node.add_command_char(command)
    node.add_raw_char(command)

    def eat_char():
        """ Remove char from the feed and remember it in raw form.
        If everything goes right, sum of nodes' raw forms should be the original string"""
        node.add_raw_char(feed.pop(0))

    while feed:
        c = feed[0]
        if c == '{':
            eat_char()
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
    orig = ''.join(feed)
    #print('in command, parsing "%s"' % orig)

    def eat_char():
        """ Remove char from the feed and remember it in raw form.
        If everything goes right, sum of nodes' raw forms should be the original string"""
        node.add_raw_char(feed.pop(0))

    while feed:
        c = feed[0]
        if c == '{':
            eat_char()
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
        elif c.isspace():
            eat_char()
            return feed, node
        elif c == ']':
            return feed, node
        else:
            eat_char()
            node.add_command_char(c)
    return feed, node
    print('word ended: ', node, orig, node.command)
    raise ParseError(orig)


def parse_brackets(feed):
    """ Turn text into IConstituentNodes. Constituents are expected to contain aliases, labels and other constituents
    and these are read as IConstituentNodes or ITextNodes.
        :param feed: list of chars (strings of length 1)
    """
    node = IConstituentNode()
    assert(feed[0] == '[')

    def eat_char():
        """ Remove char from the feed and remember it in raw form.
        If everything goes right, sum of nodes' raw forms should be the original string"""
        node.add_raw_char(feed.pop(0))

    eat_char()

    while feed:
        c = feed[0]
        if c == '[':
            feed, new_cnode = parse_brackets(feed)
            node.add_part(new_cnode)
        elif c == ']':
            # Finalize merger
            eat_char()
            node.prepare_index()
            return feed, node
        elif c.isspace():
            eat_char()
        elif c == '.':
            eat_char()
            feed, new_node = parse_word(feed)
            node.add_alias(new_node)
        else:
            feed, new_node = parse_word(feed) # Read simple constituent e.g. A or B in [ A B ]
            # Make a new constituent
            new_cnode = IConstituentNode()
            # What we just read was label for that constituent
            new_cnode.add_label(new_node)
            node.add_part(new_cnode)
            #node.add_label(new_node)
    node.prepare_index()
    return feed, node

# ### Test cases
if __name__ == "__main__":
    i = r"""[.{AspP} [.{Asp} Ininom] [.{vP} [.{KP} [.{K} ng] [.{DP} [.{D´} [.{D} {} ] [.{NP} lola ]] [.{KP} [.{K} ng] [.{DP} [.{D´} [.{D} {} ] [.{NP} alila] ] [.{KP} {ni Maria} ]]]]] [.{v´} [.{v} {} ] [.{VP} [.{V} {} ] [.{KP} {ang tubig}]]]]]"""

    i = r"""[ [.{Acc_i} B [.{Nom} A [.{DP} the grass ] ] ] [ S–Acc [ … [ [.{GenP_j} C t_i ] [ S–Gen [.{vP\rightarrow\emph{load}} … [.{v´} v^0 [.{VP} V [.{PP} [.{InsP} E [.{DatP} D t_j ] ] [.{P´} P [.{NP*} the truck ] ] ] ] ] ] ] ] ] ] ]"""

    i = r"""[.{EvidP} Part-Evid^0 [.{EvidP} [.{NegP} Part-Neg [.{NegP_j} [.{vP_i} Args Verb] [.{Neg} Neg^0 t_i ]]] [.{Evid} Evid0 t_k ]]]
    """


    i = r"""[.TP
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

    n = parse(i)


    print(i)
    print(n)
    #print(n.raw_string)

