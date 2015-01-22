from xml.dom.minidom import parse, parseString

MAKE = 1
PREVIEW = 0

#operation = MAKE 
operation = PREVIEW

dom1 = parse('../temp/unicode.xml') # parse an XML file by name

charmap = {}

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def find_characters(dom):
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
            description = getText(character.getElementsByTagName("description")[0].childNodes).lower()
            if len(latex) > 1:
                char_code = character.getAttribute("dec")
                if char_code.isdigit():
                    unicode_char = chr(int(char_code))
                else:
                    uchars =  char_code.split('-')
                    unicode_char = ''.join([chr(int(c)) for c in uchars]) 

                charmap[latex[1:]] = (unicode_char, description)
                b += 1
            c += 1 
    print("Found %s characters, where %s latex command and %s had slash-command" % (d, c, b))
find_characters(dom1)

if operation == MAKE:
    w = open('../kataja/parser/latex_to_unicode.py', 'w')
    w.write("""# This file is created with tools/make_unicode_dict.py from unicode.xml, downloaded from
    # http://www.w3.org/TR/unicode-xml/  
    """)
    w.write('latex_to_unicode = ' + str(charmap))
    w.write('\n')
    w.close()
else:
    w = open('../temp/latex_to_unicode_preview.txt', 'w')
    keys = list(charmap.keys())
    keys.sort()
    for key in keys:
        w.write('%s\t%s (%s)\n' % (charmap[key][0], key, charmap[key][1]))    

