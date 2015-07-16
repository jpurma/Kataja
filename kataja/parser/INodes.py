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
        if isinstance(other, (ITextNode, str)):
            return ITextNode(parts=[self, other])
        else:
            raise TypeError()

    def __radd__(self, other):
        if isinstance(other, ITextNode):
            return ITextNode(parts=[other, self])
        elif isinstance(other, str):
            return other + str(self)
        else:
            raise TypeError()

    def __iadd__(self, other):
        if isinstance(other, (ITextNode, str)):
            self.append(other)
            return self
        else:
            raise TypeError()

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

    def parts_as_string(self):
        """ Parts flattened into string, recursively stringifies parts if
        they contain other INodes
        :return:
        """
        return ''.join([str(x) for x in self.parts])

    def tidy(self):
        """ Join string parts into continuous strings when possible, just to
        help readability
        :return:
        """
        new_part = []
        new_parts = []
        for part in self.parts:
            if isinstance(part, ITextNode):
                if new_part:
                    new_parts.append(''.join(new_part))
                    new_part = []
                new_parts.append(part)
            else:
                new_part.append(part)
        if new_part:
            new_parts.append(''.join(new_part))
        self.parts = new_parts
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
        else:
            return self

    def is_empty(self):
        return not self.parts

    def __str__(self):
        return self.parts_as_string()

    def __repr__(self):
        if self.is_plain_string():
            return repr(self.parts_as_string())
        else:
            return 'ITextNode(parts=%s)' % repr(self.parts)


class ICommandNode(ITextNode):
    """ Node that contains command (like a html tag or a LaTeX command) as a
    string and where
    the scope of the command is the parts of the node. """

    def __init__(self, command='', prefix='\\', parts=None):
        """ Command is stored as a string in self.command. self.parts are the
        TextNodes in the scope of command. """
        ITextNode.__init__(self, parts=parts)
        self.command = command
        self.prefix = prefix

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

    def __str__(self):
        if self.parts:
            return '(%s)%s(/%s)' % (
            self.command, self.parts_as_string(), self.command)
        else:
            return '(%s/)' % self.command

    def scope(self):
        """ Return the content of command (parts), simplified if possible.
        :return:
        """
        new = ITextNode(self.parts)
        new.tidy()
        return new.simplified()

    def is_empty(self):
        return not (self.command or self.parts)

    def __repr__(self):
        return 'ICommandNode(command=%s, prefix=%s, parts=%s)' % (
        repr(self.command), repr(self.prefix), repr(self.parts))


class ITemplateNode(ITextNode):
    """ Node used for complex visible labels, allowing a template be given
    for the node that
    describes the displayed fields and their positioning and another for
    parsing nodes
    """

    def __init__(self, parts=None):
        """

        :param parts:
        :return:
        """
        ITextNode.__init__(self, parts=parts)
        self.rows = []
        self.indices = []
        self.unanalyzed = None
        self.view_order = []
        self.values = {}

    def analyze_label_data(self):
        """ Go through label complex and make rows out of it, also pick
        indices to separate list.
        :return: None
        """

        def find_index(inode):
            if isinstance(inode, ICommandNode) and inode.command == '_':
                return inode
            elif isinstance(inode, ITextNode):
                for n in reversed(inode):
                    found = find_index(n)
                    if found:
                        return found

        self.rows = []
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
                    if part.command == '\\':
                        self.rows.append(container.simplified())
                        container = ITextNode()
                    # Anything else --
                    else:
                        container.append(part)
                else:
                    container.append(part)
            final_row = container.simplified()
            self.rows.append(final_row)

    def is_plain_string(self):
        """ Cannot be represented with just a string.
        :return: bool
        """
        return False

    def __str__(self):
        if self.values:
            vals = ';'.join([str(x['value']) for x in self.values.values() if
                             x.get('value', False)])
        else:
            vals = '|'.join([str(x) for x in self.rows])
        if self.parts:
            return '[.%s %s]' % (vals, self.parts_as_string())
        else:
            return vals

    def is_empty(self):
        """
        :return:
        """
        return not (self.values or self.rows)

    def __repr__(self):
        return 'ITemplateNode(rows=%s, values=%s)' % (
        repr(self.rows), repr(self.values))
