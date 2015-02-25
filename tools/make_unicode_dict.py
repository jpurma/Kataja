from xml.dom.minidom import parse, parseString
import pprint

MAKE = 1
PREVIEW = 0

operation = MAKE 
#operation = PREVIEW

dom1 = parse('../temp/unicode.xml') # parse an XML file by name

charmap = {}
prep_tables = ['greek', 'latin', 'combining', 'arrows', 'rest']
tables = ['cyrchar', 'ding', 'ElsevierGlyph', 'mathbb', 'mathbf', 'mathbit', 'mathfrak', 'mathmit', 'mathscr', 'mathsfbfsl', 'mathsfbf', 'mathsfsl', 'mathsf', 'mathslbb', 'mathsl', 'mathtt']


manual_additions = {
    "theta": ('θ', 'greek letter theta', 'greek'),
    "Nu": ('N', 'greek capital letter nu', 'greek'),
    "Mu": ('M', 'greek capital letter mu', 'greek'),
    "Omicron": ('O', 'greek capital letter omicron', 'greek'),
    "omicron": ('o', 'greek letter omicron', 'greek'),
}

def getText(nodelist):
    """

    :param nodelist:
    :return:
    """
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def find_characters(dom):
    """

    :param dom:
    """
    b = 0
    c = 0
    d = 0
    characters = dom.getElementsByTagName("character")
    for character in characters:
        d += 1
        latex_element = character.getElementsByTagName("latex")
        #print(latex)
        if latex_element:
            latex = getText(latex_element[0].childNodes)
            latex = latex.strip()
            description = getText(character.getElementsByTagName("description")[0].childNodes).lower()
            if len(latex) > 1:
                char_code = character.getAttribute("dec")
                if char_code.isdigit():
                    unicode_char = chr(int(char_code))
                else:
                    uchars =  char_code.split('-')
                    unicode_char = ''.join([chr(int(c)) for c in uchars]) 
                category = choose_category(latex[1:], description)
                charmap[latex[1:]] = (unicode_char, description, category)
                b += 1
            c += 1 
    print("Found %s characters, where %s latex command and %s had slash-command" % (d, c, b))

def choose_category(key, description):
    """

    :param key:
    :param description:
    :return:
    """
    if 'greek' in description:
        return 'greek'
    elif description.startswith('latin'):
        return 'latin'
    elif description.startswith('combining'):
        return 'combining'
    elif 'left' in description or 'right' in description or 'arrow' in description:
        return 'arrows'
    else:
        for tname in tables:
            if key.startswith(tname):
                return tname
        return 'rest'


find_characters(dom1)
charmap.update(manual_additions)

if operation == MAKE:
    w = open('../kataja/parser/latex_to_unicode.py', 'w')
    w.write("""# This file is created with tools/make_unicode_dict.py from unicode.xml, downloaded from
# http://www.w3.org/TR/unicode-xml/  
""")
    w.write('latex_to_unicode = ')
    pprint.pprint(charmap, stream=w)
    w.write('\n')
    w.close()
else:
    w = open('../temp/latex_to_unicode_preview.txt', 'w')
    keys = list(charmap.keys())
    keys.sort()
    for key in keys:
        w.write('%s\t%s (%s)\n' % (charmap[key][0], key, charmap[key][1]))    

