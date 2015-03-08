__author__ = 'purma'
""" INodes can be used to represent strings that have formatting commands and to represent constituent structures
They can replace strings for simple comparisons, but common string methods don't work with them: use str(inode)
instead.
"""


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

    def __radd__(self, other):
        if isinstance(other, ITextNode):
            return ITextNode(parts=[other, self])
        elif isinstance(other, str):
            return other + str(self)

    def __iadd__(self, other):
        if isinstance(other, (ITextNode, str)):
            self.append(other)

    def append(self, node):
        self.parts.append(node)

    def remove(self, node):
        self.parts.remove(node)

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

    def simplified(self):
        """ If ITextNode can be presented as a string without losing anything, give that str, else return ITextNode
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

    def __bool__(self):
        return bool(self.parts or self.command)

    def is_empty(self):
        return not (self.command or self.parts)

    def __repr__(self):
        return 'ICommandNode(command=%s, prefix=%s, parts=%s)' % (repr(self.command),
                                                                  repr(self.prefix),
                                                                  repr(self.parts))




class IFeatureNode(ITextNode):
    """ INode that contains Node (feature or other Kataja node) with "label" as the field for displayable value. """

    def __init__(self, key='', value='', family='', parts=None):
        """ Command is stored as a string in self.command. self.parts are the TextNodes in the scope of command. """
        ITextNode.__init__(self, parts=parts)
        self.key = key
        self.value = value
        self.family = family

    def is_plain_string(self):
        """ Cannot be represented with just a string.
        :return: bool
        """
        return False

    def __bool__(self):
        return not self.is_empty()

    def __str__(self):
        part_part = ''
        family_part = ''
        if self.parts:
            part_part = ' ' + self.parts_as_string()
        if self.family:
            family_part = '%s:' % self.family
        return '%s%s:%s%s' % (family_part, self.key, self.value, part_part)

    def is_empty(self):
        return not (self.parts or self.key or self.value or self.family)

    def __repr__(self):
        return 'IFeatureNode(key=%s, value=%s, family=%s, parts=%s)' % (repr(self.key),
                                                                        repr(self.value),
                                                                        repr(self.family),
                                                                        repr(self.parts))

    @staticmethod
    def create_inode_from(feature):
        ifeature = IFeatureNode(feature.key, feature.value, feature.family)
        return ifeature

class IConstituentNode(ITextNode):
    """ Intermediary Node that contains basic information required for building a linguistic constituent.
    (Except features)
    IConstituentNode has label, alias, index and parts, where parts are IConstituentNodes and other are ITextNodes
    """

    def __init__(self, label='', index='', features=None, alias='', gloss='', parts=None):
        """

        :param label:
        :param index:
        :param features:
        :param alias:
        :param gloss:
        :param parts:
        """
        ITextNode.__init__(self, parts=parts)
        self.label = label
        self.index = index
        if features:
            print('setting IConstituentNode features to', features)
            ifeatures = []
            if isinstance(features, dict):
                for key, value in features.items():
                    if hasattr(value, 'as_inode'):
                        ifeatures.append(value.as_inode)
                    else:
                        IFeatureNode.create_inode_from(value)
                self.features = ifeatures
            elif isinstance(features, list) and isinstance(features[0], IFeatureNode):
                self.features = features
        else:
            self.features = []
        self.alias = alias
        self.gloss = gloss
        self._label_complex = []

    def __bool__(self):
        return bool(self.parts or self.label or self.index or self.features or self.alias or self.gloss)


    def add_feature(self, node):
        if not isinstance(node, IFeatureNode):
            node = node.as_inode
        self.features.append(node)

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

        def find_index(node):
            if isinstance(node, ICommandNode) and node.command == '_':
                return ITextNode(parts=node.parts).simplified(), node
            elif isinstance(node, ITextNode):
                for n in reversed(node):
                    found = find_index(n)
                    if found:
                        if isinstance(found, tuple):
                            index, icommand = found
                            node.remove(icommand)
                            return index
                        else:
                            return found

        row_i = 0
        rows = []
        if not self._label_complex:
            return
        container = ITextNode()

        index_found = False
        for node in self._label_complex:
            if not index_found:
                index_found = find_index(node)
        if index_found:
            if isinstance(index_found, tuple):
                self.index, icommand = index_found
                self.remove(icommand)
            else:
                self.index = index_found

        for node in self._label_complex:
            for part in node:
                if isinstance(part, ICommandNode):
                    # Linebreak --
                    if part.command == '\\':
                        rows.append(container.simplified())
                        container = ITextNode()
                        row_i += 1
                    # Anything else --
                    else:
                        container.append(part)
                else:
                    container.append(part)

        final_row = container.simplified()
        row_i += 1
        if row_i == 1:
            if self.parts:
                self.alias = final_row
            else:
                self.label = final_row
        else:
            rows.append(final_row)
            for i, node in enumerate(rows):
                if i == 0:
                    self.alias = node
                elif i == 1:
                    self.label = node
                elif i == 2:
                    self.gloss = node
                elif i > 2:
                    self.add_feature(node)

    def __str__(self):
        if self.parts and self.label:
            return '[.%s %s]' % (self.label, self.parts_as_string())
        elif self.parts:
            return '[%s]' % self.parts_as_string()
        else:
            return str(self.label)

    def is_empty(self):
        """


        :return:
        """
        return not (self.label or self.parts or self.index or self.alias or self.features)

    def __repr__(self):
        return 'IConstituentNode(alias=%s, label=%s, index=%s, gloss=%s, features=%s, parts=%s)' % (repr(self.alias),
                                                                                                    repr(self.label),
                                                                                                    repr(self.index),
                                                                                                    repr(self.gloss),
                                                                                                    repr(self.features),
                                                                                                    repr(self.parts))
