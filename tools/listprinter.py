lines = open('sentences.txt').readlines()


def to_string(listy):
    l = []
    for item in listy:
        if isinstance(item, list):
            l.append(to_string(item))
        elif item:
            l.append(item)
    return f"[ {' '.join(l)} ]"


w = open('sent_out.txt', 'w')

for line in lines:
    if line.strip():
        lists = eval(line)
        ss = to_string(lists)
        w.write(ss)
        w.write('\n\n')

w.close()
