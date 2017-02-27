from kataja.parser.latex_to_unicode import latex_to_unicode
from kataja.parser.mappings import command_to_latex, command_to_html
import html

__author__ = 'purma'
""" INodes can be used to represent strings that have formatting commands and
to represent constituent structures
They can replace strings for simple comparisons, but common string methods
don't work with them: use str(inode)
instead.
"""


def as_html(item, omit_triangle=False, include_index='') -> str:
    """ INodes to html, or if called on string, string as escaped html.
    :param item: INode or str
    :param omit_triangle: don't include content inside \qroof{ }.
    :param include_index: add <sub>index</sub> at the first line and remove other occurences
    :return: str
    """
    if not item:
        h = ''
    elif isinstance(item, ITextNode):
        h = item.as_html(omit_triangle=omit_triangle)
    else:
        h = html.escape(item).replace('\n', '<br/>\n').replace('\r', '<br/>\r').\
            replace('  ', ' &nbsp;')
    if include_index:
        index_html = f'<sub>{include_index}</sub>'
        if h:
            # Make sure that index is at the end of the first line or somewhere in first line
            # Remove other occurences.
            lines = h.splitlines(keepends=True)
            if len(lines) == 1:
                if index_html in h:
                    return h
                else:
                    return h + index_html
            first_line = lines[0]
            new_lines = []
            if index_html not in first_line:
                first_line.replace('</br>', f'{index_html}<br/>')
            new_lines.append(first_line)
            for line in lines[1:]:
                line.replace(index_html, '')
                new_lines.append(line)
            return ''.join(new_lines)
        else:
            return index_html
    return h


def as_editable_html(item) -> str:
    """ Return contents of a complex text field (INode, probably) as html, but \n instead of
    <br/> and no escaping. This is friendlier to edit and br:s can be added when interpreting the
    result.
    :param item:
    :return:
    """
    if not item:
        return ''
    elif isinstance(item, ITextNode):
        return item.as_editable_html()
    else:
        return str(item)


def as_editable_latex(item) -> str:
    if not item:
        return ''
    elif isinstance(item, ITextNode):
        return item.as_editable_latex()
    else:
        return str(item)


def as_text(item, omit_triangle=False, omit_index=False, omit_outmost=False, single_line=False):
    if isinstance(item, ITextNode):
        if omit_outmost:
            r = []
            ITextNode._as_plain(item, r, omit_triangle=omit_triangle, omit_index=omit_index)
            return ''.join(r)
        s = item.as_plain(omit_triangle=omit_triangle, omit_index=omit_index)
    else:
        s = str(item)
    if single_line:
        return s.replace('\n', ' ')
    else:
        return s


def extract_triangle(item, remove_from_original=False):
    if isinstance(item, ITextNode):
        for part in list(item.parts):
            if isinstance(part, ICommandNode) and part.command == 'qroof':
                if remove_from_original:
                    item.parts.remove(part)
                return part
            found = extract_triangle(part)
            if found:
                return found


def remove_triangle(item):
    """ Turn triangled part of INode back to regular ITextNode """
    if isinstance(item, ITextNode):
        for i, part in enumerate(list(item.parts)):
            if isinstance(part, ICommandNode) and part.command == 'qroof':
                if isinstance(item, ICommandNode):
                    item.parts[i] = ITextNode(parts=part.parts)
                elif len(item.parts) == i + 1:
                    item.parts = item.parts[0:i] + part.parts
                else:
                    item.parts = item.parts[0:i] + part.parts + item.parts[i + 1:]
                break
            else:
                remove_triangle(part)




def join_lines(lines):
    """ Flatten rows of label into one string/ITextNode/ICommandNode
    It gets bit complicated, because str+ITextNode, str+str, ITextNode+ITextNode and
    ICommandNode + ... all need different ways to join them. This is reverse to INode's splitlines.
    :param lines: list of INodes and/or strings
    :return: INode or str 
    """
    if not lines:
        return ''
    elif len(lines) == 1:
        return lines[0]
    else:
        last_row = None
        while lines:
            row = lines.pop()
            if last_row is not None:
                if isinstance(row, ICommandNode):
                    # commandnode + commandnode, commandnode + str
                    if isinstance(last_row, ICommandNode) or isinstance(last_row, str):
                        last_row = ITextNode(parts=[row, '\n', last_row])
                    # commandnode + textnode
                    else:
                        last_row.parts = [row, '\n'] + last_row.parts
                elif isinstance(row, ITextNode):
                    # textnode + commandnode, textnode + str
                    if isinstance(last_row, ICommandNode) or isinstance(last_row, str):
                        row.parts.append('\n')
                        row.parts.append(last_row)
                        last_row = row
                    # textnode + textnode
                    else:
                        row.parts.append('\n')
                        row.parts += last_row.parts
                        last_row = row
                # str + commandnode
                elif isinstance(last_row, ICommandNode):
                    row = ITextNode(parts=[row, '\n', last_row])
                    last_row = row
                # str + textnode
                elif isinstance(last_row, ITextNode):
                    last_row.parts = [row, '\n'] + last_row.parts
                # str + str
                else:
                    last_row = row + '\n' + last_row
            else:
                last_row = row
        return last_row


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
        return repr(self) == repr(other)

    def __ne__(self, other):
        return repr(self) != repr(other)

    def __hash__(self):
        return hash(repr(self))

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

    def splitlines(self):
        """ This is shallow splitline, it doesn't go inside other INodes to look for linebreaks
        :return:
        """
        lines = []
        line = []
        for part in self.parts:
            if part == '\n' or part == '\r':
                if len(line) > 1:
                    lines.append(ITextNode(parts=line))
                elif line:
                    lines.append(line[0])
                else:
                    lines.append('')
                line = []
            else:
                line.append(part)
        if len(line) > 1:
            lines.append(ITextNode(parts=line))
        elif line:
            lines.append(line[0])
        else:
            lines.append('')
        return lines

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

    def _as_html(self, s, omit_triangle=False):
        for part in self.parts:
            if isinstance(part, ITextNode):
                part._as_html(s, omit_triangle=omit_triangle)
            else:
                s.append(str(html.escape(part)))

    def _as_editable_html(self, s):
        for part in self.parts:
            if isinstance(part, ITextNode):
                part._as_editable_html(s)
            else:
                s.append(str(part))

    def as_html(self, omit_triangle=False) -> str:
        """ INodes to html
        :param omit_triangle: don't include content inside \qroof{ }.
        :return: str
        """
        s = []
        self._as_html(s, omit_triangle=omit_triangle)
        return ''.join(s).replace('\n', '<br/>\n').replace('\r', '<br/>\r')

    def as_editable_html(self) -> str:
        """ Return contents of a complex text field as html, but \n instead of
        <br/> and no escaping. This is friendlier to edit and br:s can be added when interpreting
        the result.
        :param item:
        :return:
        """
        s = []
        self._as_editable_html(s)
        return ''.join(s)

    def _as_latex(self, s, inside_math=False, in_math=False):
        for part in self.parts:
            if isinstance(part, ITextNode):
                part._as_latex(s, inside_math=inside_math)
            else:
                s.append(str(part))
        return inside_math

    def _as_editable_latex(self, s):
        for part in self.parts:
            if isinstance(part, ITextNode):
                part._as_editable_latex(s)
            else:
                s.append(str(part))

    def as_latex(self):
        s = []
        in_math = self._as_latex(s)
        if in_math:
            s.append('$')
        return ''.join(s).replace('\n', '\\\\\n').replace('\r', '\\\\\r')

    def as_editable_latex(self):
        s = []
        self._as_editable_latex(s)
        return ''.join(s)

    def _as_plain(self, s, omit_triangle=False, omit_index=False):
        for part in self.parts:
            if isinstance(part, ITextNode):
                part._as_plain(s, omit_triangle=omit_triangle, omit_index=omit_index)
            else:
                s.append(str(part))

    def as_plain(self, omit_triangle=False, omit_index=False):
        r = []
        self._as_plain(r, omit_triangle=omit_triangle, omit_index=omit_index)
        return ''.join(r)

    def __str__(self):
        return ''.join((str(x) for x in self.parts))

    def __repr__(self):
        return f'ITextNode(parts={self.parts})'


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

    def _as_html(self, s, omit_triangle=False):
        if omit_triangle and self.command == 'qroof':
            if s and s[-1] == '\n':
                s.pop()
            return
        if self.command in command_to_html:
            tag = command_to_html[self.command]
            if tag and self.parts:
                s.append('<%s>' % tag)
                ITextNode._as_html(self, s, omit_triangle=omit_triangle)
                s.append('</%s>' % tag)
            elif tag:
                s.append('<%s/>\n' % tag)
            else:
                ITextNode._as_html(self, s, omit_triangle=omit_triangle)
        elif self.command in latex_to_unicode:
            s.append(latex_to_unicode[self.command][0])
        else:
            ITextNode._as_html(self, s, omit_triangle=omit_triangle)

    def _as_editable_html(self, s):
        if self.command in command_to_html:
            tag = command_to_html[self.command]
            if tag and self.parts:
                s.append('<%s>' % tag)
                ITextNode._as_editable_html(self, s)
                s.append('</%s>' % tag)
            elif tag:
                s.append('<%s/>' % tag)
            else:
                ITextNode._as_editable_html(self, s)
        elif self.command in latex_to_unicode:
            s.append(latex_to_unicode[self.command][0])
        else:
            ITextNode._as_editable_html(self, s)

    def _as_latex(self, s, after_math=False, inside_math=False):
        command = self.command
        if command: # in command_to_latex:
            in_math = False
            if self.requires_math_mode():
                if not (after_math or inside_math):
                    s.append('$')
                    in_math = True
            elif after_math:
                s.append('$')
            if command in command_to_latex:
                command = command_to_latex[command]
            if command and self.parts:
                s.append('\%s{' % command)
                ITextNode._as_latex(self, s, inside_math=inside_math or in_math)
                s.append('}')
            elif command:
                s.append('\%s ' % command)
            else:
                ITextNode._as_latex(self, s)
            return in_math
        else:
            if after_math and not inside_math:
                s.append('$')
            ITextNode._as_latex(self, s)
            return inside_math

    def _as_editable_latex(self, s):
        command = self.command
        if command: # in command_to_latex:
            if command in command_to_latex:
                command = command_to_latex[command]
            if command and self.parts:
                s.append('\%s{' % command)
                ITextNode._as_editable_latex(self, s)
                s.append('}')
            elif command:
                s.append('\%s ' % command)
            else:
                ITextNode._as_editable_latex(self, s)
        else:
            ITextNode._as_editable_latex(self, s)

    def _as_plain(self, s, omit_triangle=False, omit_index=False):
        if not self.parts:
            unic = latex_to_unicode.get(self.command, None)
            if unic:
                s.append(unic[0])
        else:

            if self.command == 'qroof':
                if omit_triangle:
                    return
                s.append('△')
            elif self.command == 'sub':
                if omit_index:
                    return
                s.append('_')
            elif self.command == 'sup':
                s.append('^')
            for part in self.parts:
                if isinstance(part, ITextNode):
                    part._as_plain(s, omit_triangle=omit_triangle, omit_index=omit_index)
                else:
                    s.append(str(part))

    def tidy(self, keep_node=True):
        """ Tidy insides, but always maintain identity so that the command remains even if it has
        empty scope
        :param keep_node:
        :return:
        """
        # editing buttons put and remove styles to words, leaving style settings for spaces
        # between untouched. Try to get rid of commands that have ' ' or
        if not keep_node:
            if self.parts and len(self.parts) == 1:
                part = self.parts[0]
                if part and isinstance(part, str) and part.isspace():
                    return part
        return ITextNode.tidy(self, keep_node=True)

    def scope(self):
        """ Return the content of command (parts), simplified if possible.
        :return:
        """
        new = ITextNode(self.parts)
        return new.tidy(keep_node=False)

    def is_empty(self):
        return not (self.command or self.parts)

    def __repr__(self):
        return f'ICommandNode(command={repr(self.command)}, parts={self.parts})'

    def requires_math_mode(self):
        return self.command in latex_to_unicode

    def splitlines(self):
        """ This is shallow splitline, it doesn't go inside other INodes to look for linebreaks
        :return:
        """
        lines = []
        line = []
        for part in self.parts:
            if part == '\n' or part == '\r':
                if len(line) > 1:
                    lines.append(ICommandNode(command=self.command, parts=line))
                elif line:
                    lines.append(line[0])
                else:
                    lines.append('')
                line = []
            else:
                line.append(part)
        if len(line) > 1:
            lines.append(ICommandNode(command=self.command, parts=line))
        elif line:
            lines.append(line[0])
        else:
            lines.append('')
        return lines


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
        self.index = None
        self.has_triangle = False

    def is_empty(self):
        return not (self.label_rows or self.parts)

    def check_for_index(self):
        """ Tries to find value for index from within this parsernode. Saves it to self.index
        :return:
        """
        def find_index(part):
            if isinstance(part, ICommandNode) and part.command == 'sub':
                return as_text(part, omit_outmost=True)
            elif isinstance(part, ITextNode):
                for p in part.parts:
                    found = find_index(p)
                    if found:
                        return found

        found = None
        self.index = None
        for row in self.label_rows:
            if isinstance(row, ITextNode):
                for rpart in row.parts:
                    found = find_index(rpart)
                if found:
                    self.index = found
                    break

    def tidy(self, keep_node=True):
        """ Tidy insides, but always maintain identity so that the template node remains even if it
        has empty scope
        :param keep_node:
        :return:
        """
        #print('tidying parsernode')
        #t = ITextNode.tidy(self, keep_node=True)
        #print(repr(t.label_rows))
        #return t
        return ITextNode.tidy(self, keep_node=True)

    def is_plain_string(self):
        """ Cannot be represented with just a string.
        :return: bool
        """
        return False

    def __repr__(self):
        return f'IParserNode(parts={self.parts}, label_rows={self.label_rows}, ' \
               f'index={repr(self.index)})'

