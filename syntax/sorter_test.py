# coding=utf-8
t = ['table', 'ate', 'at', 'the']

d1 = [('ate', 'at'), ('at', 'the'), ('at', 'table'), ('ate', 'the'), ('ate', 'table')]
d2 = [('ate', 'at'), ('at', 'the'), ('at', 'table'), ('ate', 'the'), ('ate', 'table'), ('the', 'table')]


def sort_func(x, y):
    """

    :param x:
    :param y:
    :return:
    """
    for first, second in d2:
        if first == x and second == y:
            return -1
        elif first == y and second == x:
            return 1
    print "failed to sort '%s' and '%s'" % (x, y)
    return 0


def sortlist(first, second, result):
    """

    :param first:
    :param second:
    :param result:
    :return:
    """
    i_max = len(result) - 1
    for i, item in enumerate(result):
        if item == first:
            if i == i_max:
                result.append(second)
            else:
                if isinstance(result[i + 1], list):
                    result[i + 1].append(second)
                else:
                    result[i + 1] = [result[i + 1], second]
    return result


def sorter(dA):
    """

    :param dA:
    """
    result = []
    for (first, second) in dA:
        if not result:
            result = [first, second]
        else:
            result = sortlist(first, second, result)
        print result


print sorted(t, sort_func)

