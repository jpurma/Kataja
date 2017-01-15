# This module has functions for parsing LaTeX QTree structures to generic
# node-based representations.
# These representations can then be converted to other structures, e.g. Kataja
# Constituents and ConstituentNodes.

# This module can be run and tested as it is,
# from kataja.utils import time_me

import html
from kataja.parser.INodes import ICommandNode, ITextNode
from kataja.parser.mappings import latex_to_command


class ParseError(Exception):
    pass


one_character_commands = ['&', '#', '%', '^', '_'] # '~',


class LatexToINode:

    def __init__(self, rows_mode=False):
        """ Turn text into INodes (intermediary nodes). These can be IParserNodes,
         ICommandNodes or ITextNodes. INodes are then, dependent on purpose of
         parsing turned into Kataja's ConstituentNodes, back to LaTeX, HTML or flat strings.
        :param text: string to parse.
        :param lbracket: option to use something else, e.g. '(' as a delimiter
        """
        self.math_mode = False
        self.feed = []
        self.nodes = []
        self.rows = []
        self.rows_mode = rows_mode

    def process(self, string):
        self.feed = list(string)
        self.feed.reverse()
        self.nodes = []
        if self.rows_mode:
            self.rows = self.parse_word(end_on_space=False, return_rows=True)
            # doesn't handle rows well, fix this tomorrow
            return self.rows
        else:
            return self.parse_word(end_on_space=False)

    def parse_word(self, end_on_space=False, return_rows=False):
        """ Turn text into ITextNodes. If something special (commands, curlybraces,
        brackets is found, deal with them by creating new Nodes of specific types
            :param feed: list of chars (strings of length 1)
        """

        node = ITextNode()
        rows = []

        while self.feed:
            c = self.feed[-1]
            if c == '{':
                new_node = self.parse_curlies()
                node.append(new_node)
            elif c == '}':
                break
            elif c == '\\':
                new_node = self.parse_command()
                if return_rows and isinstance(new_node, ICommandNode) and new_node.command == 'br':
                    # fixme: doesn't handle if some style scope continues across line break
                    rows.append(node)
                    node = ITextNode()
                else:
                    node.append(new_node)
            elif c == '$':
                self.toggle_math_mode()
            elif c in one_character_commands:
                new_node = self.parse_one_character_command()
                node.append(new_node)
            elif c.isspace() and end_on_space:
                self.feed.pop()
                break
            #elif c == self.rbracket and not self.math_mode:
            #    break
            #elif c == self.lbracket and not self.math_mode:
            #    break
            #elif c in ['&', '<', '>'] and False:
            #    self.feed.pop()
            #    node.append(html.escape(c))
            else:
                self.feed.pop()
                node.append(c)
        node = node.tidy(keep_node=False)
        if return_rows:
            if node:
                rows.append(node)
            return rows
        else:
            return node

    def parse_curlies(self):
        """ Turn text into ITextNodes, but don't let space end the current
        ITextNode. Only closing curly brace will end the node parsing.
            :param feed: list of chars (strings of length 1)
        """
        node = ITextNode()

        self.feed.pop()  # eat first "{"

        while self.feed:
            c = self.feed[-1]
            if c == '{':
                self.parse_curlies()
                node.append(new_node)
            elif c == '}':
                self.feed.pop()
                break
            elif c == '\\':
                new_node = self.parse_command()
                node.append(new_node)
            elif c == '$':
                self.toggle_math_mode()
            elif c in one_character_commands:
                new_node = self.parse_one_character_command()
                node.append(new_node)
            else:
                self.feed.pop()
                node.append(c)
        return node

    def parse_one_character_command(self):
        """ Start a new command node, where the command is just one character and
        already given as a param.
            e.g. _{subscripted text} or ^{superscript}
            :param feed: list of chars (strings of length 1)
        """
        command = self.feed.pop()
        parts = []

        while self.feed:
            c = self.feed[-1]
            if c == '{':
                new_node = self.parse_curlies()
                parts.append(new_node)
                break
            elif c == '}':
                break
            elif c == '\\':
                if len(command) == 1:
                    # _\something -- is it possible?
                    self.feed.pop()
                    parts.append(c)
                    print('backslash after one character command, what to do?')
                    break
                else:
                    break
            elif c == '$':
                self.toggle_math_mode()
            elif c.isspace():
                break
            #elif c == self.rbracket and not self.math_mode:
            #    print(" plain ']' after one char command. what to do? ")
            #    break
            else:
                self.feed.pop()
                parts.append(c)
                break
        command = latex_to_command.get(command, command)
        node = ICommandNode(command=command, parts=parts)
        return node

    def toggle_math_mode(self):
        """ Switch to math mode, main difference is that brackets are not interpreted as tree
        brackets
        :param feed:
        :param math_mode: new value for math mode, true/false
        :return:
        """
        self.feed.pop()
        self.math_mode = not self.math_mode

    def parse_command(self):
        """ Turn text into ICommandNodes. These are best understood as tags, where
         the tag is the command, and parts of the node are the scope of the tag.
         Reads a word and stores it as a command, and then depending how the word
         ends, either ends the command node or starts reading next entries as a
         nodes inside the ICommandNode.
            :param feed: list of chars (strings of length 1)
        """
        parts = []
        command = ''
        self.feed.pop()  # this is the beginning "\"

        while self.feed:
            c = self.feed[-1]
            if c == '{':
                new_node = self.parse_curlies()
                parts.append(new_node)
            elif c == '}':
                break
            elif c == '\\':
                if not command:
                    # this is a line break in latex, '\\'', two backslashes in row.
                    # not two command words
                    self.feed.pop()
                    command += c
                    break
                else:
                    break
            elif c == ' ':
                break
            #elif c == self.rbracket and not self.math_mode:
            #    break
            elif c in ['<', '>', '&']:
                break
            elif c == '$':
                self.toggle_math_mode()
            else:
                self.feed.pop()
                command += c

        if command and command in latex_to_command:
            command = latex_to_command[command]
        if command:
            node = ICommandNode(command=command, parts=parts)
            return node
        elif parts:
            node = ITextNode(parts=parts)
            return node
        return ''


class LatexFieldToINode(LatexToINode):

    def __init__(self):
        """ Simpler version of parse, turns values of text elements into INodes
        (intermediary nodes).  Results are ITextNodes that may contain more
        ITextNodes and ICommandNodes.
            :param text: string to parse.
        """
        self.math_mode = False
        self.node = None
        self.feed = []

    def process(self, text):
        """ Simpler version of parse, turns values of text elements into INodes
        (intermediary nodes).  Results are ITextNodes that may contain more
        ITextNodes and ICommandNodes.
            :param text: string to parse.
        """
        #print('LatexFieldToINode called with "%s"' % text)
        self.math_mode = False
        self.node = None
        if not text:
            return ""
        text = text.strip()
        if not text:
            return ""
        self.feed = list(text)
        self.feed.reverse()
        nodes = []
        while self.feed:
            feed_progress = len(self.feed)
            node = self.parse_word()
            # ensure that we are not stuck in endless loop
            if len(self.feed) < feed_progress:
                nodes.append(node)
            else:
                self.feed.pop()

        if len(nodes) == 1:
            return nodes[0]
        elif nodes:
            node = ITextNode(parts=nodes)
            return node.tidy()
        else:
            return ""



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

    prsr = LatexToINode()
    print(prsr.process(s))

