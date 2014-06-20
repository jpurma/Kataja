# coding=utf-8
"""
Created on 28.8.2013

@author: purma
"""
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QGraphicsItem

from kataja.Controller import ctrl
from kataja.ui.MenuItem import MenuItem


# Note that TextAreaMenuItem inherits QGraphicsTextItem while the other menuitems inherit QGraphicsSimpleTextItem
# ######
class TextAreaMenuItem(MenuItem, QtWidgets.QGraphicsTextItem):
    """ This is an editable text field that stays centered in position and stretches when necessary """

    def __init__(self, parent: QGraphicsItem, args):
        QtWidgets.QGraphicsTextItem.__init__(self)
        MenuItem.__init__(self, parent, args)
        self.setParentItem(parent)
        self.setZValue(53)
        # self.setFont(args.get('font', qt_prefs.font))
        self.setCursor(QtCore.Qt.IBeamCursor)
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.setTabChangesFocus(True)
        if 'get_method' in args:
            self.set_text(args['get_method']())

    def set_text(self, text):
        """

        :param text:
        """
        self.setPlainText(text)
        cursor = self.textCursor()
        cursor.setPosition(len(text))
        self.setTextCursor(cursor)

    def get_value(self):
        """


        :return:
        """
        return self.toPlainText()

    def set_target_position(self, x, y):
        """ Since we cannot center the drawing of textitem, we adjust every try to move it so
        :param x:
        :param y:
        """
        self._target_position = (x, y - self._label_height)

    # We need different appear/disappear here because of set_target_position.

    def appear(self):
        """


        """
        self.show()
        x, y = self.centered(0, 0)
        self.setPos(x, y)
        self.setOpacity(0.0)
        self._target_opacity = 1.0
        self.set_target_position(self.relative_position[0], self.relative_position[1])
        # if self._tab_index == 0:
        # self.setFocus()
        # print 'focus to me: ', self

    def disappear(self, after_move_function=None):
        """

        :param after_move_function:
        """
        self._target_opacity = .0
        x, y = self.centered(0, 0)
        self.set_target_position(x, y)

    # ########## KEYBOARD ##########

    def keyPressEvent(self, event):
        """ Special keys: Enter - submit, Esc - abort
        :param event:
        """
        key = event.key()
        if (key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter) and event.nativeModifiers() != 512:
            self.submit(event)
            # self._parent_menu.key_press_enter()
        elif key == QtCore.Qt.Key_Escape:
            self._parent_menu.key_press_esc()
        else:
            # old=self.toPlainText()
            QtWidgets.QGraphicsTextItem.keyPressEvent(self, event)
            # if self.toPlainText()!=old:
            # pass
            # self.parentItem().method(event)
        x_adjust = self.boundingRect().width() - self._width
        if x_adjust != 0:
            self._width = self.boundingRect().width()
            for menu_item in self._dependant_menus:
                menu_item.move_by(x_adjust, 0)

    def boundingRect(self):
        """


        :return:
        """
        return QtCore.QRectF(0, -self._label_height + 2, self._label_width, self._label_height).united(
            QtWidgets.QGraphicsTextItem.boundingRect(self))

    # def mousePressEvent(self, event):
    # ctrl.ui_pressed.append(self)

    # def mouseReleaseEvent(self, event):
    # ctrl.ui_pressed.remove(self)


    def click(self, event):
        """

        :param event:
        :return:
        """
        self.setFocus()
        print('clicked on textarea ', self)
        return True  # consumes click

    def submit(self, event):
        """

        :param event:
        """
        self.method(caller=self, event=event)
        self._parent_menu.close(keep=self)
        self.activated = True


    def focusInEvent(self, event):
        """

        :param event:
        """
        self._parent_menu.focus = self
        ctrl.focus = self._parent_menu
        self._parent_menu.grabs_keyboard = True
        QtWidgets.QGraphicsTextItem.focusInEvent(self, event)

    def focusOutEvent(self, event):
        # self._parent_menu.grabs_keyboard=False
        """

        :param event:
        """
        self.method(caller=self, event=event)
        QtWidgets.QGraphicsTextItem.focusOutEvent(self, event)

    def shape(self):
        """


        :return:
        """
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path


    def paint(self, painter, option, widget):
        # some kind of colored rectangle for background.
        # if self.has_focus():
        # painter.setBrush(prefs.white)
        # else:
        # painter.setBrush(prefs.lighter_color)
        """

        :param painter:
        :param option:
        :param widget:
        """
        painter.setBrush(ctrl.cm().ui_paper())
        if ctrl.has_focus(self):
            painter.setPen(ctrl.cm().ui())
        else:
            painter.setPen(ctrl.cm().ui_inactive())

        # painter.setFont(qt_prefs.menu_font)
        painter.drawRect(self.boundingRect())
        # self.setBrush(colors.ui)
        painter.drawText(2, -2, self._label_text)
        QtWidgets.QGraphicsTextItem.paint(self, painter, option, widget)


    # ######### MOUSE ##############

    def hoverEnterEvent(self, event):
        """

        :param event:
        """
        MenuItem.hoverEnterEvent(self, event)
        QtWidgets.QGraphicsTextItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        MenuItem.hoverLeaveEvent(self, event)
        QtWidgets.QGraphicsTextItem.hoverLeaveEvent(self, event)

