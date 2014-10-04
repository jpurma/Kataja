from PyQt5 import QtWidgets, QtGui
from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.singletons import qt_prefs

__author__ = 'purma'



class NewElementEmbed(UIEmbed):

    def __init__(self, parent, ui_manager, scenePos):
        UIEmbed.__init__(self, parent, ui_manager, scenePos)
        layout = QtWidgets.QVBoxLayout()
        arrowbutton = QtWidgets.QPushButton("Arrow ->")
        self.top_row_layout.addWidget(arrowbutton)
        dividerbutton = QtWidgets.QPushButton("Divider --")
        self.top_row_layout.addWidget(dividerbutton)
        layout.addLayout(self.top_row_layout)
        layout.addSpacing(12)
        text = QtWidgets.QLineEdit(self)
        f = QtGui.QFont(qt_prefs.font)
        f.setPointSize(f.pointSize()*2)
        text.setFont(f)
        layout.addWidget(text)
        hlayout = QtWidgets.QHBoxLayout()
        selector = QtWidgets.QComboBox(self)
        selector.addItems(['guess from input', 'Constituent', 'Feature', 'Gloss', 'Text box'])
        hlayout.addWidget(selector)
        enterbutton = QtWidgets.QPushButton("↩") # U+21A9 &#8617;
        enterbutton.setMaximumWidth(20)
        hlayout.addWidget(enterbutton)
        layout.addLayout(hlayout)
        self.setLayout(layout)


# line = new QFrame(w);
#     line->setObjectName(QString::fromUtf8("line"));
#     line->setGeometry(QRect(320, 150, 118, 3));
#     line->setFrameShape(QFrame::HLine);
#     line->setFrameShadow(QFrame::Sunken);
