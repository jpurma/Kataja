# -*- coding: UTF-8 -*-
import re

string = '''[ {Hei} [ sana\komento{parametri} {pitempi kokonaisuus_{toinen kokonaisuus}}]]'''
# string = ''' [ Jukka [ {Salla vai}{muuta ei} ] ]'''

string = '''[ [.{Acc_i} B [.{Nom} A [.{DP} the grass ] ] ] [ S-Acc [ ... [ [.{GenP_j} C t_i ] [ S-Gen [.{vP\rightarrow\emph{load}} ... [.{v'} v^0 [.{VP} V [.{PP} [.{InsP} E [.{DatP} D t_j ] ] [.{P'} P [.{NP*} the truck ] ] ] ] ] ] ] ] ] ] ]'''

splitter = re.compile('''(
    \\  # slash = command starts
    | [  # [
    | ]  #
    | \ + # space, can be more than one
    | _   # underscore (subscription)
    | ^  # superscription
    | $  # latex math mode
    | (\{.*?\})+ # aaltosulut
    )''', re.X)
# | # or this group:
# \{.*?\})''', re.X)  #

splitter = '([\\\[\]\{\} +_\^\$])'  #

splitter = re.compile(r'(\\|\[|\]|{|}| +)')
words = []


def merge_curlies(s):
    """

    :param s:
    :return:
    """
    merged = ''
    for c in s:
        print(c)
        # if modes[-1] == 'start':
    return s, merged


def find_dot_alias(s):
    """

    :param s:
    :return:
    """
    label_string = ''
    if s[0] == '.':
        s, label_string = merge_curlies(s[1:])
    return s, label_string


def find_constituent(s):
    """

    :param s:
    :return:
    """
    return s, None


def analyze_word(s):
    """

    :param s:
    """
    print(s)
    s, dot_alias = find_dot_alias(s)
    s, constituent = find_constituent(s)
    s, other = find_constituent(s)
    print((s, dot_alias, constituent, other))


def bottom_up_bracket_parser(s):
    """

    :param s:
    :return:
    """
    word = []
    while s:
        c = s.pop()
        if s:
            escape = s[-1] == '\\'
        else:
            escape = False
        if c == ']' and not escape:
            s = bottom_up_bracket_parser(s)
        elif c == '[' and not escape:
            word.reverse()
            words.append(word)
            analyze_word(word)
            return s
        else:
            # process whatever is at s[i]
            word.append(c)
    return s


items = [x for x in re.split(splitter, string) if x]
print('split:', items)
print('original:', string)
bottom_up_bracket_parser(list(items))
print('words:', words)
