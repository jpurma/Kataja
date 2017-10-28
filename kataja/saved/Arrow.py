
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from collections import ChainMap

import kataja.globals as g
from kataja.ArrowLabel import ArrowLabel
from kataja.SavedField import SavedField
from kataja.SavedObject import SavedObject
from kataja.singletons import ctrl, prefs
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import to_tuple, add_xy, time_me
from kataja.FadeInOut import FadeInOut
from kataja.EdgePath import EdgePath
from kataja.Shapes import SHAPE_PRESETS


class Arrow(Movable):
    __qt_type_id__ = next_available_type_id()
    role = 'Arrow'

    def __init__(self, start=None, end=None, start_point=None, end_point=None, text=None):
        FadeInOut.__init__(self)
        Movable.__init__(self)
        QtWidgets.QGraphicsObject.__init__(self)
        self.start = start
        self.end = end
        self.start_point = start_point
        self.end_point = end_point
        self.label_data = {}
        self.label_item = None
        self.text = text or ''

    def drag(self, event):
        """ This is for dragging the whole edge in cases when edge is not
        connected to nodes at any point
        e.g. it is freely floating arrow or divider
        :param event: Drag event?
        """
        # self.draggable = not (self.start or self.end)

        scene_x, scene_y = to_tuple(event.scenePos())
        ex, ey = self.end_point
        sx, sy = self.start_point
        if not self._local_drag_handle_position:
            drag_x, drag_y = to_tuple(event.buttonDownScenePos(QtCore.Qt.LeftButton))
            self._local_drag_handle_position = drag_x - sx, drag_y - sy
        handle_x, handle_y = self._local_drag_handle_position
        start_x = scene_x - handle_x
        start_y = scene_y - handle_y
        if not self.start:
            self.fixed_start_point = start_x, start_y
        if not self.end:
            self.fixed_end_point = start_x + ex - sx, start_y + ey - sy

    def __repr__(self):
        return f'Arrow from {self.start or int(self.start_point[0]), int(self.start_point[1])} to '\
               f'{self.end or int(self.end_point[0]), int(self.end_point[1])}'

    # ## Label data and its shortcut properties

    def update_selection_status(self, selected):
        """ Switch

        :param selected:
        """
        self.selected = selected
        if selected:
            if self.uses_labels():
                if not self.label_item:
                    self.label_item = ArrowLabel('', self, placeholder=True)
                    self.label_item.update_position()
        else:
            if self.label_item:
                if self.label_item.placeholder:
                    scene = self.scene()
                    if scene:
                        scene.removeItem(self.label_item)
                    self.label_item = None
        self.update()


    def get_label_text(self) -> str:
        """ Label text is actually stored in model.label_data, but this is a
        shortcut for it.
        :return:
        """
        return self.label_data.get('text', '')

    def set_label_text(self, value):
        if self.label_item:
            old = self.get_label_text()
            if old != value:
                self.poke('label_data')
                self.label_data['text'] = value
                self.label_item.update_text(value)
        else:
            self.label_item = ArrowLabel(value, parent=self)
            self.poke('label_data')
            self.label_data['text'] = value


    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # Saved properties
    start = SavedField("start")
    end = SavedField("end")
    start_point = SavedField("start_point")
    end_point = SavedField("end_point")
    middle_point = SavedField("middle_point")
    label_data = SavedField("label_data")
