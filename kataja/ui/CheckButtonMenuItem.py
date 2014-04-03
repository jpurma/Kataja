from kataja.ui.MenuItem import MenuItem

########################################################
class CheckButtonMenuItem(MenuItem):
    def __init__(self, parent, action):
        # menu item size should be size of the menu text + some.
        MenuItem.__init__(self, parent, action)

