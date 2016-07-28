from kataja.parser.latex_to_unicode import latex_to_unicode
from parser.mappings import latex_to_html, latex_to_command, command_to_latex, html_to_command, \
    command_to_html

__author__ = 'purma'
""" INodes can be used to represent strings that have formatting commands and
to represent constituent structures
They can replace strings for simple comparisons, but common string methods
don't work with them: use str(inode)
instead.
"""


class ITextNode:
    """ Node to represent text that may contain other kinds of nodes. e.g.
    "here is a text \emph{with latexnode} inside."
    This would turn to list of parts, where most of parts are other TextNodes
    and one CommandNode with TextNode inside.
    self.raw will always contain the original text to be parsed for scope of
    the node
    """

    def __init__(self, parts=None):
        if parts is not None:
            self.parts = parts
        else:
            self.parts = []

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)

    def __hash__(self):
        return hash(str(self))

    def __getitem__(self, item):
        return self.parts[item]

    def __setitem__(self, item, value):
        self.parts[item] = value

    def __delitem__(self, item):
        del self.parts[item]

    def __iter__(self):
        return iter(self.parts)

    def __contains__(self, item):
        return item in self.parts

    def __len__(self):
        return len(self.parts)

    def __reversed__(self):
        return reversed(self.parts)

    def __add__(self, other):
        if other:
            if isinstance(other, (ITextNode, str)):
                return ITextNode(parts=[self, other])
            else:
                raise TypeError()

    def __radd__(self, other):
        if other:
            if isinstance(other, ITextNode):
                return ITextNode(parts=[other, self])
            elif isinstance(other, str):
                return other + str(self)
            else:
                raise TypeError()

    def __iadd__(self, other):
        if other:
            if isinstance(other, (ITextNode, str)):
                self.append(other)
                return self
            else:
                raise TypeError('Cannot handle type: %s' % type(other))

    def __bool__(self):
        return not self.is_empty()

    def append(self, node):
        self.parts.append(node)

    def remove(self, node):
        self.parts.remove(node)

    def startswith(self, s):
        return self.parts and self.parts[0].startswith(s)

    def remove_prefix(self, s):
        if self.parts:
            p = self.parts[0]
            if isinstance(p, ITextNode):
                p.remove_prefix(s)
            elif p.startswith(s):
                self.parts[0] = p[len(s):]

    def find_and_remove_part(self, part):
        """ Recursively search and remove part
        :param part: INode or str
        :return:
        """
        if part in self.parts:
            self.remove(part)
        else:
            for p in self.parts:
                if isinstance(p, ITextNode):
                    p.find_and_remove_part(part)

    def tidy(self, keep_node=True):
        """ Join string parts into continuous strings when possible, just to
        help readability
        :return:
        """
        merged_parts = []
        current_section = []
        plain_string = True
        for part in self.parts:
            if isinstance(part, ITextNode):
                part = part.tidy(keep_node=False)
            if isinstance(part, str):
                if part:
                    current_section.append(part)
            elif part:
                plain_string = False
                if current_section:
                    merged_parts.append(''.join(current_section))
                    current_section = []
                merged_parts.append(part)
        if current_section:
            merged_parts.append(''.join(current_section))
        self.parts = merged_parts
        if keep_node:
            return self
        else:
            if plain_string:
                return str(self)
            elif not self.parts:
                return ''
            elif len(self.parts) == 1:
                return self.parts[0]
            else:
                return self

    def is_plain_string(self):
        """ Check if this ITextNode contains only strings or ITextNodes that
        can be represented as plain strings
        if so, it would be easier to replace ITextNode with just a string.
        :return: bool
        """
        for part in self.parts:
            if isinstance(part, ITextNode) and not part.is_plain_string():
                return False
        return True

    def simplified(self):
        """ If ITextNode can be presented as a string without losing
        anything, give that str, else return ITextNode
        :return: str or self
        """
        if self.is_plain_string():
            return str(self)
        elif self.parts and len(self.parts) == 1:
            return self.parts[0]
        else:
            return self

    def is_empty(self):
        return not self.parts

    def is_empty_for_view(self):
        return self.is_empty()

    def as_html(self):
        s = []
        for part in self.parts:
            if isinstance(part, ITextNode):
                s.append(part.as_html())
            else:
                s.append(str(part))
        ss = ''.join(s)
        return ss.replace('\n', '<br/>')

    def as_latex(self):
        s = []
        for part in self.parts:
            if isinstance(part, ITextNode):
                s.append(part.as_latex())
            else:
                s.append(str(part))
        ss = ''.join(s)
        return ss.replace('\n', '\\')

    def __str__(self):
        return ''.join((str(x) for x in self.parts))

    def __repr__(self):
        return 'ITextNode(parts=%r)' % self.parts


class ICommandNode(ITextNode):
    """ Node that contains command (like a html tag or a LaTeX command) as a
    string and where
    the scope of the command is the parts of the node. """

    def __init__(self, command='', parts=None):
        """ Command is stored as a string in self.command. self.parts are the
        TextNodes in the scope of command. """
        ITextNode.__init__(self, parts=parts)
        self.command = command

    def add_command_char(self, c):
        """
        :param c: char (string of length 1)
        """
        self.command += c

    def is_plain_string(self):
        """ Cannot be represented with just a string.
        :return: bool
        """
        return False

    def as_html(self):
        s = []
        if self.command in command_to_html:
            tag = command_to_html[self.command]
            if tag and self.parts:
                s.append('<%s>' % tag)
                s.append(ITextNode.as_html(self))
                s.append('</%s>' % tag)
            elif tag:
                s.append('<%s/>' % tag)
            else:
                s.append(ITextNode.as_html(self))
        elif self.command in latex_to_unicode:
            s.append(latex_to_unicode[self.command][0])
        return ''.join(s)

    def as_latex(self):
        s = []
        if self.command in command_to_latex:
            command = command_to_latex[self.command]
            if command and self.parts:
                s.append('\%s{' % command)
                s.append(ITextNode.as_latex(self))
                s.append('}')
            elif command:
                s.append('\%s ' % command)
            else:
                s.append(ITextNode.as_latex())
        return ''.join(s)

    def tidy(self, keep_node=True):
        """ Tidy insides, but always maintain identity so that the command remains even if it has
        empty scope
        :param keep_node:
        :return:
        """
        return ITextNode.tidy(self, keep_node=True)

    def scope(self):
        """ Return the content of command (parts), simplified if possible.
        :return:
        """
        new = ITextNode(self.parts)
        return new.tidy(keep_node=False)

    def is_empty(self):
        return not (self.command or self.parts)

    def __str__(self):
        return self.as_html()

    def __repr__(self):
        return 'ICommandNode(command=%r, parts=%r)' % (self.command,
                                                       self.parts)


# class ILabelNode(ITextNode):
#     """ Node for containing multiple lines of text. Just a list of ITextNodes/ICommandNodes """
#
#     def __init__(self, rows=None):
#         super().__init__()
#         self.rows = rows or []



class IParserNode(ITextNode):
    """ Node used temporarily for parsing latex-style trees. It represents ConstituentNode while
    parsing, but it is mostly agnostic for what to do with the data about the constituent it has
    parsed from the bracket structure: when it finds a new row in label complex, it adds it to
    'rows' and when it finds subscript parts, it adds them to 'indices'. It remains for
    ConstituentNode implementation to map these rows and indices to fields.

    If IParserNodes are found after the parsing, it is probably an error somewhere.
    """

    def __init__(self, parts=None, label_rows=None, indices=None):
        """

        :param parts:
        :return:
        """
        ITextNode.__init__(self, parts=parts)
        self.label_rows = label_rows or []
        self.indices = indices or []
        self.unanalyzed = None

    def is_empty(self):
        return not (self.label_rows or self.parts)

    def analyze_label_data(self):
        """ Go through label complex and make rows out of it, also pick
        indices to separate list.
        :return: None
        """
        # fixme: use inode command format instead of latex commands
        def find_index(inode):
            if isinstance(inode, ICommandNode) and inode.command == 'sub':
                return inode
            elif isinstance(inode, ITextNode):
                for n in reversed(inode):
                    found = find_index(n)
                    if found:
                        return found

        self.label_rows = []
        if not self.unanalyzed:
            return
        container = ITextNode()

        if isinstance(self.unanalyzed, ITextNode):
            index_found = find_index(self.unanalyzed)
            if index_found:
                self.unanalyzed.find_and_remove_part(index_found)
                self.indices.append(index_found.scope())

            for part in self.unanalyzed:
                if isinstance(part, ICommandNode):
                    # Linebreak --
                    if part.command == 'br':
                        container = container.simplified()
                        if container:
                            self.label_rows.append(container)
                        container = ITextNode()
                    # Anything else --
                    else:
                        container.append(part)
                else:
                    container.append(part)
            final_row = container.simplified()
            if final_row:
                self.label_rows.append(final_row)

    def tidy(self, keep_node=True):
        """ Tidy insides, but always maintain identity so that the template node remains even if it
        has empty scope
        :param keep_node:
        :return:
        """
        return ITextNode.tidy(self, keep_node=True)

    def is_plain_string(self):
        """ Cannot be represented with just a string.
        :return: bool
        """
        return False

    def __repr__(self):
        return 'IParserNode(parts=%r, label_rows=%r, indices=%r)' % (self.parts, self.label_rows,
                                                                     self.indices)
