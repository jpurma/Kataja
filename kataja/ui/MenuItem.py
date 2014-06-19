# coding=utf-8
"""
Created on 28.8.2013

@author: purma
"""
from PyQt5 import QtGui, QtCore

from kataja.Controller import qt_prefs
from kataja.ui.MovableUI import MovableUI


class MenuItem(MovableUI):
    """ MenuItems are UI objects that are created dynamically as needed. They are not stored in save files. """

    def __init__(self, parent, args):
        """ Base class of buttons, textareas etc. Provides aligning elements
        compared to each others.
        This has to be used together with some kind of QGraphicsItem,
        which should be initialized before this. """
        MovableUI.__init__(self)
        self._label_text = args['name']
        self.key = args['name']
        shortcut = args.get('local_shortcut', '')
        if shortcut:
            self._label_text += ' (' + shortcut + ')'
        self.method = args['method']
        self.condition = args.get('condition', None)
        self._tab_index = args.get('tab_index', 999)
        self.host_node = parent.host
        self._parent_menu = parent
        self._cached_bounding_rect = None
        self._dependant_menus = []
        self._font = qt_prefs.menu_font  # @UndefinedVariable
        self.focusable = True
        self.draggable = False


        # f = QtGui.QFontMetrics(self._font)

        self._label_width = 80  # f.width(self._label_text) + 6
        self._label_height = 17  # f.lineSpacing() + 4
        print('font metrics: ', self._label_width, self._label_height)
        if 'size' in args:
            self._width, self._height = args['size']
        else:
            self._width = self._label_width
            self._height = self._label_height
        if 'pos' in args:
            self.has_fixed_position = True
            if isinstance(args['pos'][0], str):
                # position is relative to some other element. there are few
                # preset keywords to calculate this:
                direction, target_name = args['pos']
                target = None
                for item in parent.menu_items:
                    if item.key == target_name:
                        target = item
                        break
                if not target:
                    print("couldn't find target menu called ", target_name)
                if direction == 'bottom-right':
                    tx, ty = target.relative_position
                    target_br = target.boundingRect()
                    x = tx + target_br.width() + 4
                    y = ty + target_br.height() / 2
                elif direction == 'top-right':
                    tx, ty = target.relative_position
                    target_br = target.boundingRect()
                    x = tx + target_br.width() + 4
                    y = ty - (target_br.height() / 2) - 4
                elif direction == 'bottom':
                    tx, ty = target.relative_position
                    target_br = target.boundingRect()
                    x = tx + target_br.width() / 2 - self._width / 2
                    y = ty + target_br.height() + 4
                elif direction == 'top':
                    tx, ty = target.relative_position
                    target_br = target.boundingRect()
                    x = tx + target_br.width() / 2 - self._width / 2
                    y = ty - target_br.height() + 4

                else:
                    x = 0
                    y = 0
                self.relative_position = x, y
            else:
                x, y = args['pos']
                self.relative_position = x, y
        else:
            self.has_fixed_position = False
            self.relative_position = 0, 0

        self.enabled = True
        self.activated = False

        # ### Qt parts <-- this has to inherit QGraphicsItem to work

        # self.setFlag(QtGui.QGraphicsWidget.ItemIsMovable)
        # self.setFlag(QtGui.QGraphicsTextItem.ItemIsSelectable)

        # self.setText(self.text)
        self.setAcceptHoverEvents(True)
        self.hide()
        self.setZValue(50)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self._inner_bounding_rect = self.boundingRect().adjusted(2, 2, -2, -2)
        # initial position is in the middle of the menu circle
        x, y = self.centered(0, 0)
        self.setPos(x, y)

        # Typically subclass will override some of these

    def get_tab_index(self):
        """


        :return:
        """
        return self._tab_index

    def get_value(self):
        """


        :return:
        """
        return True

    def move_by(self, dx, dy):
        """

        :param dx:
        :param dy:
        """
        x, y = self.relative_position
        self.relative_position = (x + dx, y + dy)
        self.moveBy(dx, dy)  # setPos(menu_item.x()+x_adjust, menu_item.y())
        for item in self._dependant_menus:
            item.move_by(dx, dy)


    def cancel(self):
        """ Close, don't save, delete if delete_on_cancel """
        self._parent_menu.cancel()


    def center_point_in_scene(self):
        """


        :return:
        """
        return self.pos() + self.boundingRect().center()

    def centered(self, x, y):
        """

        :param x:
        :param y:
        :return:
        """
        br = self.boundingRect()
        return x - (br.width() - 15) / 2, y - br.height() / 2

    def condition(self, event=None):
        """ Menu items may have a condition method attached to them to decide if the menu item should be available
        :param event:
        """
        if hasattr(self.host, self.condition):
            return getattr(self.host, self.condition)(event)  # calls method w. event as argument
        return True

    def boundingRect(self):
        """


        :return:
        """
        if not self._cached_bounding_rect:
            self._cached_bounding_rect = QtCore.QRectF(-5, -5, self._width + 10, self._height + 10)
        return self._cached_bounding_rect

    # let's try to keep UI elements out from the main animation timer.
    # UIRadialMenu has its own timer
    def appear(self):
        """


        """
        self.show()
        x, y = self.centered(0, 0)
        self.setPos(x, y)
        self.setOpacity(0.0)
        self._target_opacity = 1.0
        x, y = self.centered(self.relative_position[0], self.relative_position[1])
        self.set_target_position(x, y)


    def remove(self, ui):
        """

        :param ui:
        """
        self.hide()
        ui.moving_things.discard(self)

    def disappear(self, after_move_function=None):
        """

        :param after_move_function:
        """
        self._target_opacity = .0
        x, y = self.centered(0, 0)
        self.set_target_position(x, y)

    # ######### MOUSE ##############

    def click(self, event):
        """

        :param event:
        :return:
        """
        self.method(caller=self, event=event)
        self._parent_menu.close(keep=self)
        self.activated = True
        return True  # consumes the click

    # def mouseReleaseEvent(self, event):
    # ctrl.pressed.remove(self)
    # event.ui_released = self

    def hoverEnterEvent(self, event):
        """

        :param event:
        """
        self._hovering = True

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        self._hovering = False
