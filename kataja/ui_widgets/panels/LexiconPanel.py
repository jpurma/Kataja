from PyQt5 import QtWidgets, QtCore

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.OverlayButton import PanelButton
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.SelectionBox import SelectionBox

__author__ = 'purma'


class LexiconPanel(Panel):
    """ Browse and build the lexicon """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, default_position, parent, folded)
        inner = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        self.lextree = QtWidgets.QTreeWidget()
        self.lextree.setColumnCount(1)
        #tree.preferred_size = QtCore.QSize(220, 240)
        #tree.sizeHint = self.sizeHint
        self.watchlist = ['forest_changed']
        #self.preferred_size = tree.preferred_size
        layout.addWidget(self.lextree)
        self.info = QtWidgets.QLabel('info text here')
        layout.addWidget(self.info)
        inner.setLayout(layout)
        self.lextree.itemEntered.connect(self.item_entered)
        self.lextree.itemClicked.connect(self.item_clicked)

        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.prepare_lexicon()
        self.finish_init()

    def prepare_lexicon(self):
        self.lextree.clear()
        fk = ctrl.main.forest_keeper
        if not fk:
            return
        print('preparing lexicon panel')
        structures = QtWidgets.QTreeWidgetItem(self.lextree, ['Structures'])
        constituents = QtWidgets.QTreeWidgetItem(self.lextree, ['Constituents'])
        features = QtWidgets.QTreeWidgetItem(self.lextree, ['Features'])
        for parent, sourcedict in [(structures, fk.structures),
                                   (constituents, fk.constituents),
                                   (features, fk.features)]:
            for key, value in sourcedict.items():
                item = QtWidgets.QTreeWidgetItem(parent, [key + value])
                if ctrl.main.use_tooltips:
                    item.setToolTip(value)
                item.setData(55, {'key': key, 'description': value})
                self.lextree.addItem(item)

    def item_entered(self, item):
        self.info.setText(item.data(55).get('description', 'No description'))
        self.info.update()

    def item_clicked(self, item):
        """ Clicked on a symbol: launch activity that tries to insert it to focused text field
        :param item:
        :return:
        """
        focus = ctrl.get_focus_object() or ctrl.main.graph_view.focusWidget()
        print('clicketi click on ', item, item.data(55))

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        print('bop', signal)
        if signal == 'forest_changed':
            print('bip')
            self.prepare_lexicon()

