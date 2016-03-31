# coding=utf-8

class UIItem:

    def __init__(self, ui_key, host=None):
        self.ui_key = ui_key
        self.host = host
        self.watchlist = []