from html.parser import HTMLParser

from kataja.parser.INodes import ITextNode, ICommandNode
from kataja.parser.mappings import html_to_command


class HTMLToINode(HTMLParser):
    """  Convert HTML to ICommandNodes and ITextNodes to use as field values. Doesn't handle
    brackets or tree parsing, only fields.
    """

    def error(self, message):
        print('HTML parse error: ', message)

    def __init__(self, rows_mode=False):
        super().__init__(convert_charrefs=True)
        self.current = ITextNode()
        self.stack = []
        self.rows_mode = rows_mode
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag in html_to_command:
            command = html_to_command[tag]
            self.stack.append(self.current)
            new = ICommandNode(command)
            self.current.append(new)
            self.current = new

    def handle_endtag(self, tag):
        if self.stack:
            self.current = self.stack.pop()

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            if self.rows_mode:
                self.rows.append(self.current)
                # you may want to start again all currently open tags for the next line
                self.stack = []
                self.current = ITextNode()

            command = html_to_command[tag]
            self.current.append(ICommandNode(command))

    def handle_data(self, data):
        """ Brackets and other tree defining structures are only found within data objects.
        If we are entering data to field, just take whatever it is here.
        :param data:
        :return:
        """
        self.current.append(data)

    def process(self, string):
        self.feed(string)
        result = self.current
        self.reset()
        if self.rows_mode:
            self.rows.append(result)
            return self.rows
        else:
            return result

    def reset(self):
        self.current = ITextNode()
        self.stack = []
        super().reset()


if __name__ == '__main__':
    parser = HTMLToINode()
    print(parser.process('<A href="https://github.com">link</a> and <i>italics</i>.'))
    print(parser.process("""row<br/>row<br/>row
    your boat"""))
    print(parser.process("<bonk broken < html> <b> and some</bread> butter</b>"))
