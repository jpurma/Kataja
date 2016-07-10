
import sys
#sys.setrecursionlimit(10000)

original = open('../PoP/ignore/deriveModel10.log', 'r')
new = open('deriveG.log', 'r')


originals = []
for line in original.readlines():
    originals.append(eval(line))

news = []
for line in new.readlines():
    news.append(eval(line))

def norm_feature(feat):
    """ Remove number from the end """
    fl = list(feat)
    while fl[-1].isdigit() or fl[-1] == ':':
        fl.pop()
    return ''.join(fl)

def norm_so(so):
    new_so = []
    if any(isinstance(x, list) for x in so):
        # not a feature set
        for item in so:
            if isinstance(item, str):
                new_so.append(norm_feature(item))
            else:
                new_so.append(norm_so(item))
        return new_so
    else:
        fs = set()
        for item in so:
            fs.add(norm_feature(item))
        fs = sorted(list(fs))
        return fs


def normalise(synlist):
    new_list = []
    for so in synlist:
        new_list.append(norm_so(so))
    return new_list

norm_orig = normalise(originals)
norm_news = normalise(news)


def featureless(so):
    if isinstance(so, str):
        return so
    if len(so) == 2 and isinstance(so[0], str) and isinstance(so[1], list):
        return so[0]
    else: 
        return [featureless(o) for o in so]


def copyless(so):
    if isinstance(so, str):
        return so
    if len(so) == 2 and isinstance(so[0], str) and isinstance(so[1], list):
        if 'Copy' in so[1]:
            so[1].remove('Copy')
        return so
    else:
        return [copyless(o) for o in so]


def rec_diff(item_one, item_two):
    for i1, i2 in zip(item_one, item_two):
        if i1 and i2 and i1 != i2 and isinstance(i1, list) and isinstance(i2, list):
            if not any(isinstance(x, list) for x in i1):
                print('old: ', i1)
                print('new: ', i2)
            if isinstance(i1, list) and isinstance(i2, list):
                rec_diff(i1, i2) 
        elif (not i1) or (not i2):
            print('missing')
        elif isinstance(i1, list):
            print('ok ', i1)
c = 0
success = 0
for item1, item2 in zip(norm_orig, norm_news):
    c += 1
    fless_item1 = featureless(item1)
    fless_item2 = featureless(item2)
    item1 = copyless(item1)
    item2 = copyless(item2)
    if item1 == item1:
        print('%s: Match' % c)
        success += 1
    else:
        print('*********')
        print('original: ', item1)
        print('my version: ', item2)
        rec_diff(item1, item2)
        if fless_item1 != fless_item2:
            print('structural mismatch:')
            print(fless_item1)
            print(fless_item2)
        else:
            print('structure ok')
        print('%s: Feature mismatch' % c)
        print(fless_item1)
        input()

print('-------------------- success: ', success)