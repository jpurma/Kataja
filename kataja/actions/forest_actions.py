import ast
import gzip
import json
import pickle
import pprint
import time

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

from kataja.KatajaAction import KatajaAction

from kataja.singletons import ctrl, prefs, log
from kataja.ui_support.PreferencesDialog import PreferencesDialog


# ==== Class variables for KatajaActions:
#
# k_action_uid : unique id for calling this action. required, other are optional
# k_command : text used for menu command and log feedback, unless the method returns a fdback string
# k_tooltip : tooltip text for ui element. If not given, uses k_command as tooltip.
# k_undoable : is the action undoable, default is True
# k_shortcut : keyboard shortcut given as string, e.g. 'Ctrl+x'
# k_shortcut_context : can be nothing or 'parent_and_children' if shortcut is active only when the
#                      parent widget is visible and active
# k_checkable : should the action be checkable, default False
#
# ==== Methods:
#
# method : gets called when action is triggered. If it returns a string, this is used as a command
#          feedback string, otherwise k_command is printed to log.
# getter : if there is an UI element that can show state or display value, this method returns the
#          value. These are called quite often, but with values that have to change e.g. when item
#          is dragged, you'll have to update manually.
# enabler : if enabler is defined, the action is active (also reflected into its UI elements) only
#           when enabler returns True
#

class RemoveFromSelection(KatajaAction):
    k_action_uid = 'remove_from_selection'
    k_command = 'Remove from selection'
    k_undoable = False

    def method(self, object_uid):
        """ Add node, edge or other selectable object to selection
        :param object_uid: int or str uid of item to select, or list of uids for adding
         multiple objects. None or empty list does nothingh.
        :return: None
        """
        if not object_uid:
            return
        elif isinstance(object_uid, (list, tuple)):
            objs = []
            for uid in object_uid:
                obj = ctrl.forest.get_object_by_uid(uid)
                if obj:
                    objs.append(obj)
            ctrl.remove_from_selection(objs)
        else:
            obj = ctrl.forest.get_object_by_uid(object_uid)
            ctrl.remove_from_selection(obj)


class AddToSelection(KatajaAction):
    k_action_uid = 'add_to_selection'
    k_command = 'Add to selection'
    k_undoable = False

    def method(self, object_uid):
        """ Add node, edge or other selectable object to selection
        :param object_uid: int or str uid of item to select, or list of uids for adding
         multiple objects. None or empty list does nothingh.
        :return: None
        """
        if not object_uid:
            return
        elif isinstance(object_uid, (list, tuple)):
            objs = []
            for uid in object_uid:
                obj = ctrl.forest.get_object_by_uid(uid)
                if obj:
                    objs.append(obj)
            ctrl.add_to_selection(objs)
        else:
            obj = ctrl.forest.get_object_by_uid(object_uid)
            ctrl.add_to_selection(obj)


class SelectObject(KatajaAction):
    k_action_uid = 'select'
    k_command = 'Select'
    k_undoable = False

    def method(self, object_uid):
        """ Select node, edge or other forest object
        :param object_uid: int or str uid of item to select, or list of uids for selecting
         multiple objects, or None to empty the current selection.
        :return: None
        """
        if object_uid is None:
            ctrl.deselect_objects()
        elif isinstance(object_uid, (list, tuple)):
            objs = []
            for uid in object_uid:
                obj = ctrl.forest.get_object_by_uid(uid)
                if obj:
                    objs.append(obj)
            ctrl.select(objs)
        else:
            obj = ctrl.forest.get_object_by_uid(object_uid)
            ctrl.select(obj)


