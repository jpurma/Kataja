# coding=utf-8
from kataja.singletons import log
from kataja.KatajaAction import KatajaAction


class Help(KatajaAction):
    k_action_uid = 'help'
    k_command = '&Help'
    k_shortcut = 'h'
    k_undoable = False

    def method(self):
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
        log.critical(m)

