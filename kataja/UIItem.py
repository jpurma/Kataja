# coding=utf-8
from kataja.singletons import ctrl
from kataja.uniqueness_generator import next_available_ui_key


class UIItem:
    """ UI Items are items that are tracked by UIManager. UIManager can fetch UIItems for
    updating, e.g. change palette colors or update field values.  UI Items can also announce
    signals that they will receive, these signals can be sent by any object.
    """
    permanent_ui = False
    unique = False

    def __init__(self, host=None, ui_key=None, role=None):
        if ui_key:
            self.ui_key = ui_key
        elif self.unique:
            self.ui_key = self.__class__.__name__
        else:
            self.ui_key = next_available_ui_key()
        self.ui_type = self.__class__.__name__
        self.ui_manager = ctrl.ui
        self.role = role  # optional way to identify if cannot be distinguished w. class
        self.host = host
        self.watchlist = []

    def watch_alerted(self, obj, signal, field_name, value):
        pass

    def update_position(self):
        pass

    def update_colors(self):
        pass