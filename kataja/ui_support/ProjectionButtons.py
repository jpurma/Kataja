from PyQt5 import QtWidgets

from kataja.singletons import ctrl


class ProjectionButton(QtWidgets.QPushButton):

    def __init__(self, text, value, tooltip):
        QtWidgets.QPushButton.__init__(self, text)
        self.setCheckable(True)
        self.setFlat(False)
        self.my_value = value
        self.k_tooltip = tooltip

    def enterEvent(self, event):
        node = ctrl.forest.nodes.get(self.my_value)
        if node:
            for n in node.heads:
                n.toggle_halo(True)

    def leaveEvent(self, event):
        node = ctrl.forest.nodes.get(self.my_value)
        if node:
            for n in node.heads:
                n.toggle_halo(False)


class ProjectionButtons(QtWidgets.QWidget):
    """

    :param parent:
    :param tip:
    :param options:
    """

    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        self.empty = True
        self.bgroup = QtWidgets.QButtonGroup(self)
        self.bgroup.setExclusive(False)
        self.my_layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.my_layout)
        self.update_selections()
        self.my_layout.setContentsMargins(0, 0, 0, 0)
        self.connect_slot = self.bgroup.buttonToggled

    def update_selections(self):
        """ Redraw all buttons
        :param options: iterable of (text, value, is_checked, disabled,
        tooltip) -dictionaries
        :return:
        """
        host = self.parent().host
        current_heads = host.heads
        for button in self.bgroup.buttons():
            self.bgroup.removeButton(button)
            self.my_layout.removeWidget(button)
            button.destroy()
        self.empty = True
        children = host.get_children(similar=True, visible=False)
        for child in children:
            child_heads = child.heads
            if not child_heads:
                continue
            text = ', '.join([x.short_str() for x in child_heads])
            tt = f'project from {child_heads}'
            checked = current_heads and (child_heads == current_heads or child_heads in
                      current_heads)
            button = ProjectionButton(text, child.uid, tt)
            button.setChecked(checked)
            button.setEnabled(bool(child_heads))
            self.bgroup.addButton(button)
            self.my_layout.addWidget(button)
            self.empty = False
            button.setMinimumHeight(40)

