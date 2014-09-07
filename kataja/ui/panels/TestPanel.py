from PyQt5 import QtWidgets

from kataja.ui.ColorBox import ColorBox
from kataja.ui.panels.UIPanel import UIPanel


__author__ = 'purma'


class TestPanel(UIPanel):
    """
        Panel for rapid testing of various UI elements that otherwise may be hidden behind complex screens or logic.
    """

    def __init__(self, name, key, default_position='right', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        boxes = [('drawing', "Drawing"), ('text', "Text"), ('paper', "Paper"), ('ui', "UI"), ('ui_paper', "UI paper"),
                 ('secondary', "Secondary"), ('selection', "Selection")]
        for box_base, box_text in boxes:
            color_button = ColorBox(box_base, box_text)
            layout.addWidget(color_button)
        #layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        #layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        inner.setLayout(layout)
        print(layout.sizeConstraint(), layout.sizeHint(), layout.contentsRect())
        self.setWidget(inner)
        self.finish_init()



   # def secondary(self):
   #  def selection(self):
   #  def ui_hover(self):
   #  def ui_active(self):
   #  def ui_selected(self):