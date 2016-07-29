

from html.parser import HTMLParser
from kataja.parser.mappings import html_to_command
from kataja.parser.INodes import ITextNode, ICommandNode, IParserNode


class PlainTextToINode:
    """  Convert HTML to ICommandNodes and ITextNodes to use as field values. Doesn't handle
    brackets or tree parsing, only fields.
    """

    def __init__(self, rows_mode=False):
        self.rows_mode = rows_mode
        self.rows = []

    def process(self, string):
        inrows = string.splitlines()
        if self.rows_mode:
            self.rows = []
            for row in inrows:
                self.rows.append(ITextNode(parts=[row]))
            return self.rows
        else:
            return ITextNode(parts=[string])

    def reset(self):
        pass

