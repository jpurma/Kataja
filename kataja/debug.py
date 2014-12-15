import traceback

__author__ = 'purma'

DEBUG_TIME_ME = True
DEBUG_SYNTAX = False
DEBUG_PRINT_MOUSE_EVENTS = False
DEBUG_PRINT_PARSER_EVENTS = False
DEBUG_FOREST_OPERATION = False
DEBUG_VISUALIZATION = False
DEBUG_KEYPRESS = False
DEBUG_UNDO = False
DEBUG_UI = False


def mouse(*args):
    """ More helpful print, can be toggled on/off through var at the beginning of this file.
    :param args: arguments for print
    """
    if DEBUG_PRINT_MOUSE_EVENTS:
        _debug_print('MOU', *args)

def syntax(*args):
    """ More helpful print, can be toggled on/off through var at the beginning of this file.
    :param args: arguments for print
    """
    if DEBUG_SYNTAX:
        _debug_print('SYN', *args)


def parser(*args):
    """ More helpful print, can be toggled on/off through var at the beginning of this file.
    :param args: arguments for print
    """
    if DEBUG_PRINT_PARSER_EVENTS:
        _debug_print('PAR', *args)


def forest(*args):
    """ More helpful print, can be toggled on/off through var at the beginning of this file.
    :param args: arguments for print
    """
    if DEBUG_FOREST_OPERATION:
        _debug_print('FOR', *args)


def vis(*args):
    """ More helpful print, can be toggled on/off through var at the beginning of this file.
    :param args: arguments for print
    """
    if DEBUG_VISUALIZATION:
        _debug_print('VIS', *args)


def keys(*args):
    """ More helpful print, can be toggled on/off through var at the beginning of this file.
    :param args: arguments for print
    """
    if DEBUG_KEYPRESS:
        _debug_print('KEY', *args)


def undo(*args):
    """ More helpful print, can be toggled on/off through var at the beginning of this file.
    :param args: arguments for print
    """
    if DEBUG_UNDO:
        _debug_print('UNDO', *args)


def ui(*args):
    """ More helpful print, can be toggled on/off through var at the beginning of this file.
    :param args: arguments for print
    """
    if DEBUG_UI:
        _debug_print('UI', *args)


def _debug_print(key, *args):
    path, ln, func, caller = traceback.extract_stack(limit=3)[0]
    path = path.split('/')[-1]
    s = '%s %s:%s: %s/ ' % (key, path, ln, func)
    args = [s] + list(args)
    print(*args)