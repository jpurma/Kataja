# This module has functions for parsing LaTeX QTree structures to generic
# node-based representations.
# These representations can then be converted to other structures, e.g. Kataja
# Constituents and ConstituentNodes.

# This module can be run and tested as it is,
# from kataja.utils import time_me

import html
from kataja.parser.INodes import ICommandNode, ITextNode, IParserNode


class ParseError(Exception):
    pass


one_character_commands = ['&', '#', '%', '^', '_'] # '~',


class LatexToINode:

    def __init__(self, text):
        """ Turn text into INodes (intermediary nodes). These can be ITemplateNodes,
         ICommandNodes or ITextNodes. INodes are then, dependent on purpose of
         parsing turned into Kataja's ConstituentNodes, rich text format
         representations (with NodeToQTextDocument), HTML or flat strings. The
         nodes also store the original raw string (=text that was given to parser).
            :param text: string to parse.
        """
        self.math_mode = False
        if not text:
            return None
        text = text.strip()
        if not text:
            return None
        self.feed = list(text)
        self.nodes = []
        while self.feed:
            c = self.feed[0]
            if c == '[':
                node = self.parse_brackets()
                if node:
                    self.nodes.append(node)
            elif c == ']':
                self.feed.pop(0)
            else:
                node = self.parse_word(end_on_space=True)
                if node:
                    self.nodes.append(node)
                else:
                    self.feed.pop(0)

    def parse_word(self, end_on_space=False):
        """ Turn text into ITextNodes. If something special (commands, curlybraces,
        brackets is found, deal with them by creating new Nodes of specific types
            :param feed: list of chars (strings of length 1)
        """

        node = ITextNode()

        while self.feed:
            c = self.feed[0]
            if c == '{':
                new_node = self.parse_curlies()
                node.append(new_node)
            elif c == '}':
                break
            elif c == '\\':
                new_node = self.parse_command()
                node.append(new_node)
            elif c == '$':
                self.parse_math_mode()
            elif c in one_character_commands:
                new_node = self.parse_one_character_command()
                node.append(new_node)
            elif c.isspace() and end_on_space:
                self.feed.pop(0)
                break
            elif c == ']' and not self.math_mode:
                break
            elif c == '[' and not self.math_mode:
                break
            elif c in ['&', '<', '>']:
                self.feed.pop(0)
                node.append(html.escape(c))
            else:
                self.feed.pop(0)
                node.append(c)
        node.tidy()
        return node

    def parse_curlies(self):
        """ Turn text into ITextNodes, but don't let space end the current
        ITextNode. Only closing curly brace will end the node parsing.
            :param feed: list of chars (strings of length 1)
        """
        node = ITextNode()

        self.feed.pop(0)  # eat first "{"

        while self.feed:
            c = self.feed[0]
            if c == '{':
                self.parse_curlies()
                node.append(new_node)
            elif c == '}':
                self.feed.pop(0)
                break
            elif c == '\\':
                new_node = self.parse_command()
                node.append(new_node)
            elif c == '$':
                self.parse_math_mode()
            elif c in one_character_commands:
                new_node = self.parse_one_character_command()
                node.append(new_node)
            else:
                self.feed.pop(0)
                node.append(c)
        node.tidy()
        return node

    def parse_one_character_command(self):
        """ Start a new command node, where the command is just one character and
        already given as a param.
            e.g. _{subscripted text} or ^{superscript}
            :param feed: list of chars (strings of length 1)
        """
        node = ICommandNode(command=self.feed.pop(0), prefix='')

        while self.feed:
            c = self.feed[0]
            if c == '{':
                new_node = self.parse_curlies()
                node.append(new_node)
                break
            elif c == '}':
                break
            elif c == '\\':
                if len(node.command) == 1:
                    # _\something -- is it possible?
                    self.feed.pop(0)
                    node.append(c)
                    print('backslash after one character command, what to do?')
                    break
                else:
                    break
            elif c == '$':
                self.parse_math_mode()
            elif c.isspace():
                break
            elif c == ']' and not self.math_mode:
                print(" plain ']' after one char command. what to do? ")
                break
            else:
                self.feed.pop(0)
                node.append(c)
                break
        node.tidy()
        return node

    def parse_math_mode(self):
        """ Switch to math mode, main difference is that brackets are not interpreted as tree
        brackets
        :param feed:
        :param math_mode: new value for math mode, true/false
        :return:
        """
        self.feed.pop(0)
        self.math_mode = not self.math_mode

    def parse_command(self):
        """ Turn text into ICommandNodes. These are best understood as tags, where
         the tag is the command, and parts of the node are the scope of the tag.
         Reads a word and stores it as a command, and then depending how the word
         ends, either ends the command node or starts reading next entries as a
         nodes inside the ICommandNode.
            :param feed: list of chars (strings of length 1)
        """
        node = ICommandNode()

        self.feed.pop(0)  # this is the beginning "\"

        while self.feed:
            c = self.feed[0]
            if c == '{':
                new_node = self.parse_curlies()
                node.append(new_node)
            elif c == '}':
                break
            elif c == '\\':
                if not node.command:
                    # this is a line break in latex, '\\'', two backslashes in row.
                    # not two command words
                    self.feed.pop(0)
                    node.add_command_char(c)
                    break
                else:
                    break
            elif c == ' ':
                break
            elif c == ']' and not self.math_mode:
                break
            elif c in ['<', '>', '&']:
                break
            elif c == '$':
                self.parse_math_mode()
            else:
                self.feed.pop(0)
                node.add_command_char(c)
        node.tidy()
        return node

    def parse_brackets(self):
        """ Turn text into IConstituentNodes. Constituents are expected to contain
        aliases, labels and other constituents and these are read as
        IConstituentNodes or ITextNodes.
            :param feed: list of chars (strings of length 1)
        """
        parsernode = IParserNode()
        assert (self.feed[0] == '[')

        self.feed.pop(0)

        while self.feed:
            c = self.feed[0]
            if c == '[' and not self.math_mode:
                new_parsernode = self.parse_brackets()
                parsernode.append(new_parsernode)
            elif c == ']' and not self.math_mode:
                # Finalize merger
                self.feed.pop(0)
                # if closing bracket continues with . ( "[ ... ].NP " )
                # it is treated as label
                if self.feed and self.feed[0] == '.':
                    self.feed.pop(0)
                    new_node = self.parse_word()
                    parsernode.unanalyzed = new_node
                break
            elif c == '$':
                self.parse_math_mode()
            elif c.isspace():
                self.feed.pop(0)
            elif c == '.':
                self.feed.pop(0)
                new_node = self.parse_word(end_on_space=True)
                parsernode.unanalyzed = new_node
            else:
                # Make a new constituent
                new_parsernode = IParserNode()
                # Read simple constituent e.g. A or B in [ A B ]
                new_node = self.parse_word(end_on_space=True)
                # What we just read was label for that constituent
                new_parsernode.unanalyzed = new_node
                new_parsernode.analyze_label_data()
                parsernode.append(new_parsernode)
        parsernode.analyze_label_data()
        parsernode.tidy()
        return parsernode


class LatexFieldToINode(LatexToINode):

    def __init__(self, text):
        """ Simpler version of parse, turns values of text elements into INodes
        (intermediary nodes).  Results are ITextNodes that may contain more
        ITextNodes and ICommandNodes.
            :param text: string to parse.
        """
        #print('LatexFieldToINode called with "%s"' % text)
        self.math_mode = False
        self.node = None
        if not text:
            return None
        text = text.strip()
        if not text:
            return None
        self.feed = list(text)
        nodes = []
        while self.feed:
            feed_progress = len(self.feed)
            node = self.parse_word()
            if len(self.feed) < feed_progress:
                nodes.append(node)
            else:
                # ensure that we are not stuck in endless loop
                self.feed.pop(0)

        if len(nodes) == 1:
            self.node = nodes[0]
        elif nodes:
            self.node = ITextNode(parts=nodes)
            self.node.tidy()
        else:
            self.node = ""
        #print(self.node)

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

    n = LatexToINode(s)

    print(n.nodes)

