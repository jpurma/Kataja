

from html.parser import HTMLParser
from kataja.parser.mappings import html_to_command
from kataja.parser.INodes import ITextNode, ICommandNode, IParserNode


class QDocumentToINode:
    """  Convert QDocument to ICommandNodes and ITextNodes to use as field values. Doesn't handle
    brackets or tree parsing, only fields.
    """

    def process(self, doc):

        def removed(stack, command):
            for item in reversed(stack):
                if isinstance(item, ICommandNode) and item.command == command:
                    stack.remove(item)
                    break
            return stack[-1]

        def continue_on_new_line(stack):
            new_stack = [ITextNode()]
            for item in stack:
                if isinstance(item, ICommandNode):
                    new_command = ICommandNode(item.command)
                    if new_stack:
                        new_stack[-1].append(new_command)
                    new_stack.append(new_command)
            return new_stack

        b = doc.firstBlock()
        end = doc.end()
        count = 0
        rows = []
        while b:
            result = ITextNode()
            stack = [result]
            cf = b.charFormat()
            #b.blockFormat().alignment(),
            caps = cf.fontCapitalization()
            family = cf.fontFamily()
            italic = cf.fontItalic()
            overline = cf.fontOverline()
            strikeout = cf.fontStrikeOut()
            weight = cf.fontWeight()
            underline = cf.fontUnderline()
            vertalign = cf.verticalAlignment()
            for frange in b.textFormats():
                #print('---- block %s ----' % count)
                #print(b.text())
                #print(frange.start, frange.length)
                cf = frange.format
                if caps != cf.fontCapitalization():
                    caps = cf.fontCapitalization()
                    if caps == 3:
                        command = ICommandNode('smallcaps')
                        stack.append(command)
                        result.append(command)
                        result = command
                        #print('cap: ', caps)
                    else:
                        result = removed(stack, 'smallcaps')
                if family != cf.fontFamily():
                    family = cf.fontFamily()
                    #command = ICommandNode('paa')
                    #stack.append(command)
                    #result.append(command)
                    #result = command
                    #print('family: ', family)
                if italic != cf.fontItalic():
                    italic = cf.fontItalic()
                    if italic:
                        command = ICommandNode('italic')
                        stack.append(command)
                        result.append(command)
                        result = command
                        #print('italic: ', cf.fontItalic())
                    else:
                        result = removed(stack, 'emph')
                        result = removed(stack, 'italic')
                if overline != cf.fontOverline():
                    pass
                    #command = ICommandNode('overline')
                    #stack.append(command)
                    #result.append(command)
                    #result = command
                    #print('overline: ', overline)
                if strikeout != cf.fontStrikeOut():
                    strikeout = cf.fontStrikeOut()
                    if strikeout:
                        command = ICommandNode('strikeout')
                        stack.append(command)
                        result.append(command)
                        result = command
                        #print('strikeout: ', strikeout)
                    else:
                        result = removed(stack, 'strikeout')
                if weight != cf.fontWeight():
                    weight = cf.fontWeight()
                    if weight > 50:
                        command = ICommandNode('bold')
                        stack.append(command)
                        result.append(command)
                        result = command
                        #print('weight: ', weight)
                    else:
                        result = removed(stack, 'bold')
                if underline != cf.fontUnderline():
                    underline = cf.fontUnderline()
                    if underline:
                        command = ICommandNode('underline')
                        stack.append(command)
                        result.append(command)
                        result = command
                        #print('underline: ', underline)
                    else:
                        result = removed(stack, 'underline')
                if vertalign != cf.verticalAlignment():
                    if vertalign == 1:
                        result = removed(stack, 'sup')
                    elif vertalign == 2:
                        result = removed(stack, 'sub')
                    vertalign = cf.verticalAlignment()
                    if vertalign == 1:
                        command = ICommandNode('sup')
                        stack.append(command)
                        result.append(command)
                        result = command
                        #print('vertical align: ', vertalign)
                    elif vertalign == 2:
                        command = ICommandNode('sub')
                        stack.append(command)
                        result.append(command)
                        result = command
                        #print('vertical align: ', vertalign)
                text_piece = b.text()[frange.start:frange.start + frange.length]
                lines = text_piece.splitlines()
                if len(lines) > 1:
                    for text_piece in lines:
                        result.append(text_piece)
                        base = stack[0].tidy(keep_node=False)
                        stack = continue_on_new_line(stack)

                        result = stack[-1]
                        rows.append(base)
                else:
                    result.append(text_piece)

            base = stack[0].tidy(keep_node=False)
            if base or b != end: # omit last empty line
                rows.append(base)
            if b == end:
                b = None
            else:
                b = b.next()
                count += 1
        # Return one node or one string instead of rows
        has_nodes = False
        for row in rows:
            if isinstance(row, ITextNode):
                has_nodes = True
                break
        if has_nodes:
            parts = []
            for row in rows:
                parts.append(row)
                parts.append('\n')
            return ITextNode(parts=parts)
        else:
            return '\n'.join(rows)

