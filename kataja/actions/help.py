# coding=utf-8
from kataja.singletons import ctrl

a = {}


def show_help_message():
    """ Dump keyboard shortcuts to console. At some point, make this to use
    dialog window instead.
    :return: None
    """
    m = """(h):------- KatajaMain commands ----------
    (left arrow/,):previous structure   (right arrow/.):next structure
    (1-9, 0): switch between visualizations
    (f):fullscreen/windowed mode
    (p):print trees to file
    (b):show/hide labels in middle of edges
    (q):quit"""
    ctrl.main.add_message(m)


a['help'] = {'command': '&Help', 'method': show_help_message, 'shortcut': 'h'}

