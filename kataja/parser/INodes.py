__author__ = 'purma'


class ITextNode:
    """ Node to represent text that may contain other kinds of nodes. e.g.
    "here is a text \emph{with latexnode} inside."
    This would turn to list of parts, where most of parts are other TextNodes and one CommandNode with TextNode inside.
    self.raw will always contain the original text to be parsed for scope of the node
    """

    def __init__(self, parts=None):
        if parts is not None:
            self.parts = parts
        else:
            self.parts = []

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

    def split_lines(self):
        lines = []
        line = ITextNode()
        max_splits = 2
        splits = 0
        for part in self.parts:
            if splits <= max_splits and isinstance(part, ICommandNode) and part.command == '\\':
                lines.append(line)
                line = ITextNode()
            else:
                line.add_part(part)
        lines.append(line)
        return lines

    def parts_as_string(self):
        """ Parts flattened into string, recursively stringifies parts if they contain other INodes
        :return:
        """
        return ''.join([str(x) for x in self.parts])

    def tidy(self):
        """ Join string parts into continuous strings when possible, just to help readability
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

    def is_plain_string(self):
        """ Check if this ITextNode contains only strings or ITextNodes that can be represented as plain strings
        if so, it would be easier to replace ITextNode with just a string.
        :return: bool
        """
        for part in self.parts:
            if isinstance(part, ITextNode) and not part.is_plain_string():
                return False
        return True

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
    """ Node that contains command (like a html tag or a LaTeX command) as a string and where
    the scope of the command is the parts of the node. """

    def __init__(self, command='', prefix='\\', parts=None):
        """ Command is stored as a string in self.command. self.parts are the TextNodes in the scope of command. """
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
            return '(%s)%s(/%s)' % (self.command, self.parts_as_string(), self.command)
        else:
            return '(%s/)' % self.command

    def is_empty(self):
        return not (self.command or self.parts)

    def __repr__(self):
        return 'ICommandNode(command=%s, prefix=%s, parts=%s)' % (repr(self.command), repr(self.prefix), repr(self.parts))


class INode(ITextNode):
    """ INode that contains Node (feature or other Kataja node) with "label" as the field for displayable value. """

    def __init__(self, label='', parts=None):
        """ Command is stored as a string in self.command. self.parts are the TextNodes in the scope of command. """
        ITextNode.__init__(self, parts=parts)
        self.label = label

    def add_label(self, node):
        """

        :param node:
        """
        self.label = node

    def is_plain_string(self):
        """ Cannot be represented with just a string.
        :return: bool
        """
        return False

    def __str__(self):
        if self.parts:
            return ':%s %s' % (self.label, self.parts_as_string())
        else:
            return ':%s' % self.label

    def is_empty(self):
        return not (self.label or self.parts)

    def __repr__(self):
        return 'INode(label=%s, parts=%s)' % (repr(self.label), repr(self.parts))


class IConstituentNode(ITextNode):
    """ Intermediary Node that contains basic information required for building a linguistic constituent.
    (Except features)
    IConstituentNode has label, alias, index and parts, where parts are IConstituentNodes and other are ITextNodes
    """

    def __init__(self, label='', index='', features=None, alias='', gloss='', parts=None):
        ITextNode.__init__(self, parts=parts)
        self.label = label
        self.index = index
        if features is not None:
            self.features = features
        else:
            self.features = []
        self.alias = alias
        self.gloss = gloss
        self._label_complex = []

    def add_label(self, node):
        """

        :param node:
        """
        self.label = node

    def add_feature(self, node):
        self.features.append(node)

    def add_index(self, index):
        self.index = index

    def add_alias(self, node):
        self.alias = node

    def add_gloss(self, node):
        self.gloss = node

    def add_label_complex(self, node):
        self._label_complex.append(node)

    def is_plain_string(self):
        """ Cannot be represented with just a string.
        :return: bool
        """
        return False

    def sort_out_label_complex(self):
        """ Go through label complex and fill alias, label, index, gloss and features if provided.
        :return: None
        """
        row_i = 0
        rows = []
        if not self._label_complex:
            return
        container = ITextNode()
        is_leaf = not bool(self.parts)
        index_found = False
        for node in self._label_complex:
            #print(type(node), node)
            #print('--------------')
            for part in node.parts:
                #print(type(part), part)
                if isinstance(part, ICommandNode):
                    # Linebreak --
                    if part.command == '\\':
                        rows.append(container)
                        container = ITextNode()
                        row_i += 1
                    # Index --
                    elif part.command == '_' and not index_found:
                        self.index = part.parts_as_string()
                        index_found = True
                    # Anything else --
                    else:
                        container.add_part(part)
                else:
                    container.add_part(part)
        rows.append(container)
        row_i += 1
        if row_i == 1:
            if is_leaf:
                self.add_label(container)
            else:
                self.add_alias(container)
        else:
            for i, node in enumerate(rows):
                if i == 0:
                    self.add_alias(node)
                elif i == 1:
                    self.add_label(node)
                elif i == 2:
                    self.add_gloss(node)
                elif i > 2:
                    self.add_feature(node)
        print('Guessed about constituent: alias: %s, label: %s, index: %s, gloss: %s, features: %s ' % (self.alias, self.label, self.index, self.gloss, self.features))

    def __str__(self):
        if self.parts and self.label:
            return '[.%s %s]' % (self.label, self.parts_as_string())
        elif self.parts:
            return '[%s]' % self.parts_as_string()
        else:
            return str(self.label)

    def is_empty(self):
        return not (self.label or self.parts or self.index or self.alias or self.features)

    def __repr__(self):
        return 'IConstituentNode(alias=%s, label=%s, index=%s, gloss=%s, features=%s, parts=%s)' % (repr(self.alias),
            repr(self.label),
            repr(self.index),
            repr(self.gloss),
            repr(self.features),
            repr(self.parts))
