
import ast
import time

from kataja.parser.HTMLToINode import HTMLToINode
from kataja.parser.LatexToINode import LatexToINode
from kataja.parser.INodes import IParserNode, ITextNode
from kataja.utils import time_me

class SuperParser:

    def __init__(self, string, bracket='', html=None, latex=None, dot_label=None):
        """ SuperParser attempts to use some (really) rough heuristics to guess how the input is
        formatted: does it use parenthesis, brackets, curly braces etc to express embedding,
        does it use html, latex or nothing for internal formatting of each node and does it use
        dot-labeling. Heuristics can be avoided by giving these things as parameters.

        SuperParser can also accept inputs that are already well-formatted python iterables.

        :param string:
        :param bracket:
        :param html:
        :param latex:
        :param dot_label:
        """
        try:
            parts_list = ast.literal_eval(string)
        except SyntaxError:
            parts_list = []
        except ValueError:
            parts_list = []
        ss = string.strip()
        #print('stripped input:', ss)
        if not bracket:
            if ss[0] in '[({':
                bracket = ss[0]
            elif ss[-1] == ']':
                bracket = '['
            elif ss[-1] == '}':
                bracket = '{'
            elif ss[-1] == ')':
                bracket = '('
        self.lbracket = bracket
        if bracket == '[':
            self.rbracket = ']'
        elif bracket == '(':
            self.rbracket = ')'
        elif bracket == '{':
            self.rbracket = '}'
        else:
            self.rbracket = ''
        #print('assuming brackets to be ', self.lbracket, self.rbracket)
        self.latex = latex
        self.html = html
        if self.latex is None and self.html is None:
            latex_prob = 0.1
            html_prob = 0
            if "</" in ss:
                html_prob += 0.5
            if "<i>" in ss:
                html_prob += 0.5
            if "<a href" in ss:
                html_prob += 1.0
            if self.lbracket != "{" and "{" in ss:
                latex_prob += 0.5
            if ss.count('$') > 2:
                latex_prob += 0.5
            if latex_prob < 0.5 and html_prob < 0.5:
                self.latex = False
                self.html = False
            elif latex_prob > html_prob:
                self.latex = True
                self.html = False
            else:
                self.latex = False
                self.html = True
        if dot_label is None:
            if ss.count('.') > 4 or ss.count('[.') > 2:
                self.dot_label = True
            else:
                self.dot_label = False
        else:
            self.dot_label = dot_label
        #print('assuming to be LaTeX: %s, HTML: %s, dot_label: %s ' % (self.latex, self.html,
        #                                                              self.dot_label))
        #print(ss)

        if self.html:
            self.ltag = "<"
            self.rtag = ">"
            self.bitag = ""
            self.escape = ""
            self.divider = " "
            self.row_parser = HTMLToINode(rows_mode=True)
        elif self.latex:
            self.ltag = "{"
            self.rtag = "}"
            self.bitag = "$"
            self.escape = "\\"
            self.divider = " "
            self.row_parser = LatexToINode(rows_mode=True)
        else:
            self.ltag = ""
            self.rtag = ""
            self.bitag = '"'
            self.escape = ""
            self.divider = " "
            self.row_parser = None
        if self.lbracket == '(' and not self.html and not self.latex:  # treebank format
            self.treebank = True
            self.dot_label = False
            #print('** assuming treebank format **')
        else:
            self.treebank = False

        if not parts_list:
            string_lists = self.chop_into_parts(ss)
            parts_list = self.stringify_and_split(string_lists)
            if len(parts_list) == 1 and isinstance(parts_list[0], list) and len(parts_list[0]) == 1:
                parts_list = parts_list[0]  # treebank trees have unnecessary () around them
        self.tree = self.parse_parts(parts_list)
        self.nodes = self.tree

    def chop_into_parts(self, string):
        """ First thing in actual parsing is to find the separate constituents from the string.
        The challenge is that the brackets that sign the start and end of constituent can also be
        found within style definitions, e.g. inside html tags, or as escaped characters that
        should be used literally.

        A structure of embedded lists is built that respects the structure given as string.
        :param string:
        :return:
        """
        open_tags = 0
        open_bitag = False
        stack = []
        current = []
        escaped = False
        for char in string:
            if escaped:
                escaped = False
                current.append(char)
            elif char == self.escape:
                escaped = True
                current.append(char)
            elif char == self.bitag:
                open_bitag = not open_bitag
                current.append(char)
            elif char == self.ltag:
                open_tags += 1
                current.append(char)
            elif char == self.rtag:
                open_tags -= 1
                if open_tags < 0:
                    open_tags = 0
                current.append(char)
            elif not (open_tags or open_bitag):
                if char == self.lbracket:
                    stack.append(current)
                    new = []
                    current.append(new)
                    current = new
                elif char == self.rbracket:
                    if stack:
                        current = stack.pop()
                else:
                    current.append(char)
            else:
                current.append(char)
        return current

    def stringify_and_split(self, charlist):
        """ Stringify and split tries to extract strings that form the labels or and
        other information about the node. Depending on tree style, a word end (space) means end
        of the label and then there are various ways around the rule.
        :param charlist:
        :return:
        """
        s = ''
        parts = []
        open_tags = 0
        open_bitag = False
        escaped = False
        splits = 0
        if self.treebank:
            max_splits = 1
        else:
            max_splits = 0

        for item in charlist:
            if escaped:
                if isinstance(item, str):
                    s += item
                escaped = False
            elif item == self.escape:
                escaped = True
                s += item
            elif item == self.bitag:
                open_bitag = not open_bitag
                s += item
            elif item == self.ltag:
                open_tags += 1
                s += item
            elif item == self.rtag:
                open_tags -= 1
                s += item
            elif isinstance(item, str):
                if open_tags == 0 and (not open_bitag) \
                        and ((self.divider == ' ' and item.isspace()) or item == self.divider) \
                        and (max_splits == 0 or max_splits > splits):
                    splits += 1
                    s = s.strip()
                    if s:
                        parts.append(s)
                    s = ''
                else:
                    s += item

            elif isinstance(item, list):
                s = s.strip()
                if s:
                    parts.append(s)
                s = ''
                parts.append(self.stringify_and_split(item))
        s = s.strip()
        if s:
            parts.append(s)
        return parts

    def parse_parts(self, parts_list, tidy_up=True):
        """ Turn text into IParserNodes. IParserNodes are flexible pre-constituents that have
        the field texts converted to ITextNodes or ICommandNodes.
            :param parts_list: list of strings or lists
            :tidy_up: tidy all contained inodes, do it once
        """
        node = IParserNode()
        deep = any([isinstance(part, list) for part in parts_list])

        for part in parts_list:
            if isinstance(part, list):
                node.parts.append(self.parse_parts(part, tidy_up=False))
            else:
                result = self.parse_word(part)
                tidy_rows = []
                for row in result:
                    if isinstance(row, ITextNode):
                        row = row.tidy(keep_node=False)
                    tidy_rows.append(row)
                if result and self.dot_label and str(tidy_rows[0]).startswith('.'):
                    node.label_rows = tidy_rows
                elif (not node.label_rows) and tidy_rows and (self.treebank or deep):
                    node.label_rows = tidy_rows
                else:
                    new_part = IParserNode()
                    new_part.label_rows = tidy_rows
                    new_part.check_for_index()
                    node.parts.append(new_part)
        if tidy_up:
            node = node.tidy(keep_node=True)
        node.check_for_index()
        return node

    def parse_word(self, string):
        """ Parse string of label text into ITextNodes or ICommandNodes. Relies on HtmlToINode,
        LatexToINode or other row_parser implementation. """
        if self.latex or self.html:
            return self.row_parser.process(string)
        else:
            return string.split('\n')
