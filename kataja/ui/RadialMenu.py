# coding=utf-8
"""
Created on 28.8.2013

@author: purma
"""
import math

from PyQt5 import QtGui, QtCore, QtWidgets

from kataja.singletons import prefs, ctrl
from kataja.ui.ButtonMenuItem import ButtonMenuItem
from kataja.ui.CheckButtonMenuItem import CheckButtonMenuItem
from kataja.ui.MenuItem import MenuItem
from kataja.ui.MovableUI import MovableUI
from kataja.ui.RadioButtonMenuItem import RadioButtonMenuItem
from kataja.ui.TextAreaMenuItem import TextAreaMenuItem
from kataja.utils import to_tuple


class RadialMenu(QtWidgets.QGraphicsItem, MovableUI):
    """ When user clicks a node, a circle of menu items appear. RadialMenu organizes and animates the menu items.  """

    def __init__(self, host, actions=None, shape='ring', radius=100):
        if not actions:
            actions = []
        QtWidgets.QGraphicsItem.__init__(self)
        MovableUI.__init__(self)
        self.hide()
        self.menu_items = []
        self._actions = actions
        self._radius = radius
        self._shape = shape
        self.host = host
        self.draggable = False
        self.focusable = False
        self.setPos(0, 0)
        self._build_menu_items(actions)
        self.radius_pen = QtGui.QPen()

        self.radius_pen.setColor(ctrl.cm.ui())
        self.radius_pen.setWidth(1)
        self._polygon_rect = QtCore.QRectF()
        self._focus_taker = None
        self.setZValue(50)

        self.submit_method = None
        self._assemble_menu_items_around()
        # self.glow_effect=GlowRing(self, self.radius)
        # self.glow_effect.hide() # remove the whole thing if we decide it is better without
        self.grabs_keyboard = False
        for menu in self.menu_items:
            if getattr(menu, 'checked', False):
                self.submit_method = menu.action
                break
        self.update_position(fit=False)


    def _build_menu_items(self, actions):
        """ Creates all MenuItems operating under this radial menu """
        editor = None
        self.menu_items = []
        constructors = {'Button': ButtonMenuItem, 'TextArea': TextAreaMenuItem, 'RadioButton': RadioButtonMenuItem,
                        'CheckButton': CheckButtonMenuItem}
        for action in actions:
            menu_type = action.get('menu_type', 'Button')
            condition = action.get('condition', None)
            constructor = constructors[menu_type]
            new_item = constructor(self, action)
            self.menu_items.append(new_item)
            if condition:
                cond_method = getattr(self.host, condition, None)
                if cond_method:
                    if not cond_method():
                        new_item.setEnabled(False)

        # create list of dependant menus for each menu item, so that when menu item moves
        # it has easy access to those items that should move with it.
        for this_menu, action in zip(self.menu_items, actions):
            pos = action.get('pos', None)
            if pos and isinstance(pos[0], str):
                direction, host_key = pos
                host_menu = None
                for menu in list(self.menu_items):
                    if menu.key == host_key:
                        host_menu = menu
                        break
                if host_menu:
                    host_menu._dependant_menus.append(this_menu)
        self._sorted_menu_items = list(self.menu_items)
        self._sorted_menu_items.sort(key=MenuItem.get_tab_index)


    def _assemble_menu_items(self):
        """ Position menu items """
        menu_items = [menu for menu in self.menu_items if not menu.has_fixed_position]

        total_height = sum([menu.boundingRect().height() + 4 for menu in menu_items])
        y = total_height * -.5
        x = self.radius * 2
        for menu in menu_items:
            menu.relative_position = x, y
            y += menu.boundingRect().height() + 2

    def _assemble_menu_items_around(self):
        """ Position menu items in a circle around the target """
        angle = -0.6 * math.pi
        max_x = max([menu.relative_position[0] + menu._width for menu in self.menu_items if menu.has_fixed_position])
        max_y = max([-menu.relative_position[1] for menu in self.menu_items if menu.has_fixed_position])
        menu_items = [menu for menu in self.menu_items if not menu.has_fixed_position]
        step = (math.pi * 1.2) / (len(self.menu_items) or 1)
        if self._radius < max_y:
            self._radius = max_y + 8
        # menu_positions should be relative to node.
        for menu in menu_items:  # radial positions for menus
            xf = math.cos(angle)
            yf = math.sin(angle)
            # todo: check if previous menu rectangle overlaps with current menu rectangle. If so,
            # move both either left or right until they don't
            menu.relative_position = (xf * self._radius) + (xf * menu.boundingRect().width() * 0.5), yf * self._radius
            angle += step

    # deprecated
    # def _fitting_to_screen_pos(self):
    # ui_view = ctrl.main.ui_view  # @UndefinedVariable
    # min_x = min_y = 100
    # max_x = max_y = dx = dy = 0
    # x, y = self._host_pos
    # for menu in self.menu_items:
    # mx, my = menu.relative_position
    # mw, mh = menu.boundingRect().width() * 0.5, menu.boundingRect().height() * 0.5
    # if mx - mw < min_x:
    #             min_x = mx - mw
    #         if mx + mw > max_x:
    #             max_x = mx + mw
    #         if my - mh < min_y:
    #             min_y = my - mh
    #         if my + mh > min_y:
    #             max_y = my + mh
    #     min_x += x
    #     max_x += x
    #     min_y += y
    #     max_y += y
    #     view_rect = ui_view.sceneRect()
    #     if min_x < view_rect.left():
    #         dx = view_rect.left() - min_x
    #     if max_x > view_rect.right():
    #         dx = view_rect.right() - max_x
    #     if min_y < view_rect.top():
    #         dy = view_rect.top() - min_y
    #     if max_y > view_rect.bottom():
    #         dy = view_rect.bottom() - max_y
    #     return (x + dx, y + dy)



    def selected_radio_menu(self, selected):
        """ If there are radio menus, only one of them can be checked. Uncheck others.
        :param selected:
        """
        for menu in self.menu_items:
            if menu == selected:
                self.submit_method = selected.action
                menu.checked = True
                menu.update()
            elif getattr(menu, 'radio_id', 0) == selected.radio_id:
                menu.checked = False
                menu.update()

    def get_text_input(self):
        """ Return text from currently active (focused) menu item """
        pass
        # if self.editor:
        #    return self.editor.toPlainText()

    def is_open(self):
        """


        :return:
        """
        return self.isVisible()

    def click(self, event=None):
        """

        :param event:
        :return:
        """
        self.close()
        self.update()
        return False  # doesn't consume this click: can click something under menu

    def key_press_enter(self):
        # trigger some default action
        """


        """
        if self.submit_method:
            if isinstance(self.submit_method, QtWidgets.QAction):
                self.submit_method.trigger()
            else:
                self.submit_method(self)
            self.close()
        pass

    def key_press_esc(self):
        """


        """
        self.cancel()

    def cancel(self):
        """


        """
        self.close()


    def update_position(self, drag=False, slide=False, fit=True):
        """

        :param drag:
        :param slide:
        :param fit:
        """
        graph = ctrl.main.graph_view  # @UndefinedVariable
        self._host_pos = to_tuple(self.host.pos())
        if fit and False:
            good_x, good_y = self._fitting_to_screen_pos()
        else:
            good_x, good_y = to_tuple(self.host.pos())
        if self.host:
            if slide:
                self.set_target_position(good_x, good_y)
                # self.set_timer(6, self.move_towards_target_position)
            else:
                self.setPos(good_x, good_y)

    def boundingRect(self):
        """


        :return:
        """
        return self.childrenBoundingRect().united(self._polygon_rect)


    ########### FOCUS ##########

    # Menus have a local focus control system.
    # ctrl.focus is set to menu, but menu has its own menu.focus, that points to
    # certain MenuItem.

    # def move_focus_right(self):
    #     if self.focus:
    #         i= self.menu_items.index(self.focus)
    #         i+=1
    #         if i==len(self.menu_items):
    #             i=0
    #         self.focus=self.menu_items[i]
    #     else:
    #         l=len(self.menu_items)
    #         if l:
    #             self.focus=self.menu_items[l/4]
    #     self.pleaseUpdate()

    # def move_focus_up(self):
    #     l=len(self.menu_items)
    #     if l:
    #         self.focus=self.menu_items[0]
    #     self.pleaseUpdate()

    # def move_focus_down(self):
    #     l=len(self.menu_items)
    #     if l:
    #         self.focus=self.menu_items[l/2]
    #     self.pleaseUpdate()

    # def move_focus_left(self):
    #     if self.focus:
    #         i= self.menu_items.index(self.focus)
    #         i-=1
    #         if i==-1:
    #             i=len(self.menu_items)-1
    #         self.focus=self.menu_items[i]
    #     else:
    #         l=len(self.menu_items)
    #         if l:
    #             self.focus=self.menu_items[int((l/4.0)*3)+1]
    #     self.pleaseUpdate()

    # def trigger_menu(self):
    #     if self.focus:
    #         self.focus.action.trigger()
    #     self.close()

    # # this is not yet used by menus, make them check that this is true!
    # def allowFocus(self):
    #     self.allow_focus=True

    # def denyFocus(self):
    #     self.allow_focus=False


    # open & close

    def open(self, focus=''):
        """

        :param focus:
        """
        self.update_position(slide=True)
        self.show()
        for item in self.menu_items:
            if item.key == focus:
                self._focus_taker = item
            item.appear()
        x, y = to_tuple(self.pos())

        # self.glow_effect.radius = 0
        # self.glow_effect.max_radius = 60
        # self.glow_effect.step_size = self.glow_effect.max_radius / 10.0
        self.set_timer(prefs.ui_speed, self._open_one_step, self._finish_opening)
        ctrl.take_focus(self)

    def _open_one_step(self):
        # self.glow_effect.grow()
        self.prepareGeometryChange()
        for item in self.menu_items:
            item.move_towards_target_position(self._ticks_left, self._ticks)
            item.adjust_opacity(self._ticks_left, self._ticks)
        self.move_towards_target_position(self._ticks_left, self._ticks)

    def _finish_opening(self):
        self.host.hide()
        self.focusable = True
        if self._sorted_menu_items:
            ctrl.take_focus(self._focus_taker)
            self._focus_taker.setFocus()

    def close(self, immediately=False, keep=None):
        """

        :param immediately:
        :param keep:
        :return:
        """
        if not self.isVisible():
            return
        self.focusable = False
        if immediately:
            for item in self.menu_items:
                item.remove()
            self._finish_closing()
        else:
            for item in self.menu_items:
                if item is not keep:
                    item.disappear()
            # self.glow_effect.step_size=self.glow_effect.max_radius/10.0
            self.set_timer(prefs.ui_speed, self._close_one_step, self._finish_closing)
        self.focus = None
        ctrl.release_focus()
        # ctrl.remove_from_selection(self.host)
        self.host.show()
        ctrl.main.ui_manager.main.enable_actions()  # @UndefinedVariable

    def _close_one_step(self):
        # self.glow_effect.shrink()
        self.prepareGeometryChange()
        for item in self.menu_items:
            item.move_towards_target_position(self._ticks_left, self._ticks)
            item.adjust_opacity(self._ticks_left, self._ticks)

    def _finish_closing(self):
        self.hide()
        self.host.remove_menu(self)


    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        """
        pass

        # painter.setPen(self.radius_pen)
        # #for item in self.menu_items:
        # #    px, py = to_tuple(item.center_point_in_scene())
        # #    painter.drawLine(0, 0, px, py)
        # painter.setPen(ctrl.cm.selection())
        # painter.setBrush(ctrl.cm.ui())
        # polygon = QtGui.QPolygon()
        # polygon.append(QtCore.QPoint(0, 0))
        # polygon.append(QtCore.QPoint(20, 0))
        # x, y = to_tuple(self.pos())
        # polygon.append(QtCore.QPoint(self._host_pos[0] - x, self._host_pos[1] - y))
        # polygon.append(QtCore.QPoint(0, 0))
        # self._polygon_rect = QtCore.QRectF(polygon.boundingRect())
        # painter.drawPolygon(polygon)
        # # painter.drawLine(-10, 0, self._host_pos[0] - x, self._host_pos[1] - y)
        # # painter.drawLine(20, 0, self._host_pos[0] - x, self._host_pos[1] - y)
