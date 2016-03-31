# coding=utf-8
from kataja.singletons import ctrl


class UIItem:
    """ UI Items are items that are tracked by UIManager. UIManager can fetch UIItems for
    updating, e.g. change palette colors or update field values.  UI Items can also announce
    signals that they will receive, these signals can be sent by any object.
    """

    def __init__(self, ui_key, host=None):
        self.ui_key = ui_key
        self.host = host
        self.watchlist = []
        self.ui_manager = ctrl.ui

    def watch_alerted(self, obj, signal, field_name, value):
        pass