# (command, html, latex)
commands = {('emph', 'em', 'emph'), ('italic', 'i', 'textit'), ('bold', 'b', 'textbf'),
            ('sup', 'sup', '^'), ('sub', 'sub', '_'), ('underline', 'u', 'underline'),
            ('strikeout', 's', 'strikeout'), ('smallcaps', 'font', 'textsc'), ('code', 'code', 'verb'),
            ('br', 'br', '\\'), ('newline', '', 'newline'), ('small', 'small', ''), ('link', 'a', 'href'),
            ('quote', 'q', 'quote'), ('sample', 'samp', 'verb'), ('qroof', 'roof', 'qroof'),
            ('math', '', '$')}

command_to_html = {}
command_to_latex = {}
latex_to_command = {}
html_to_command = {}

for command, html, latex in commands:
    command_to_html[command] = html
    command_to_latex[command] = latex
    if latex:
        latex_to_command[latex] = command
    if html:
        html_to_command[html] = command

latex_to_html = {
    'emph': ('<em>', '</em>'),
    'textit': ('<i>', '</i>'),
    'textbf': ('<b>', '</b>'),
    '^': ('<sup>', '</sup>'),
    '_': ('<sub>', '</sub>'),
    '$': ('', ''),
    'underline': ('<u>', '</u>'),
    'strikeout': ('<s>', '</s>'),
    'textsc': ('<font face="{textsc}">', '</font>'),
    '\\': ('<br/>', ''),
    'newline': ('<br/>', ''),
    'verb': ('<code>', '</code>')
}

latex_special_chars = {'#', '$', '%', '^', '&', '_', '{', '}', '~', '\\'}

allowed_html = {'i', 'b', 'sup', 'sub', 'u', 's', 'font', 'br', 'a', 'code', 'em', 'q', 's', 'samp',
                'small'}

html_to_latex = {}
for key, tag_tuple in latex_to_html.items():
    html_to_latex[tag_tuple[0]] = key
