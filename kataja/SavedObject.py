import copy
import sys
import types
from collections import Iterable

from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QPointF, QPoint

from kataja.SavedField import SavedField
from kataja.globals import CREATED, DELETED
from kataja.parser.INodes import ITextNode
from kataja.parser.LatexToINode import LatexFieldToINode
from kataja.singletons import ctrl, classes
from kataja.utils import to_tuple, time_me
from kataja.uniqueness_generator import next_available_uid

__author__ = 'purma'


class SaveError(Exception):
    """ for errors related to storing the model
    """
    # def __init__(self, value):
    # self.value = value
    # def __str__(self):
    # return repr(self.value)


class SavedObject(object):
    """ Make the object to have internal .saved -object where saved data
    should go.
    Also makes it neater to check if item is Savable.
    """
    uid = SavedField("uid")
    class_name = SavedField("class_name")
    syntactic_object = False
    unique = False
    dont_copy = []

    def __init__(self, uid=None, **kw):
        if self.unique:
            uid = self.__class__.__name__
        elif uid is None:
            uid = next_available_uid()
        self._saved = {}
        self._history = {}
        self.uid = uid
        self.class_name = self.__class__.__name__
        self._cd = 0  # / CREATED / DELETED
        self._can_be_deleted_with_undo = True
        self._skip_this = False  # temporary "ghost" objects can use this flag to avoid being stored

    def __str__(self):
        return self.class_name + str(self.uid)

    def copy(self, others=None):
        """ Make a new object of same type and copy its attributes.
        object class can define dont_copy, list of attribute names that shouldn't be copied (
        either because they refer to peers or objects above, or because they are handled
        manually.). Attributes starting with '_' are always ignored, and the copied object is
        assigned a new key.
        :param others:
        :return:
        """
        if self.__class__.unique:
            print('cannot copy unique object')
            return None
        new_obj = self.__class__()
        new_obj.uid = next_available_uid()
        dont_copy = self.__class__.dont_copy
        for key, value in vars(self).items():
            if (not key.startswith('_')) and key not in dont_copy:
                if hasattr(value, 'copy'):
                    new_value = value.copy(others=others)
                else:
                    new_value = copy.copy(value)
                print('copied this: ', key, new_value)
                setattr(new_obj, key, new_value)
        return new_obj



    def poke(self, attribute):
        """ Alert undo system that this (Saved) object is being changed.
        This is used manually for container-type objects in the model before
        changing adding or
        removing objects in them, as these operations would not be catch by
        setters. This doesn't check if
         the new value is different from previous, as this is used manually
         before actions that change
         the list/dict/set.
        :param attribute: string, name of the attribute
        :return: None
        """
        if ctrl.undo_disabled:
            return

        if not self._history:
            ctrl.undo_pile.add(self)
            self._history[attribute] = copy.copy(self._saved[attribute])
        elif attribute not in self._history:
            self._history[attribute] = copy.copy(self._saved[attribute])

    def announce_creation(self):
        """ Flag object to have been created in this undo cycle.
        If the object was created here, when moving to _previous_ cycle
        should launch removal of the object
        from scene.
        :return:None
        """
        if ctrl.undo_disabled:
            return
        self._cd = CREATED
        ctrl.undo_pile.add(self)

    def announce_deletion(self):
        """ Flag object to have been deleted in this undo cycle.
        :return:None
        """
        if ctrl.undo_disabled or not self._can_be_deleted_with_undo:
            return
        self._cd = DELETED
        ctrl.undo_pile.add(self)

    def call_watchers(self, signal, field_name=None, value=None):
        """ Alert (UI) objects that are watching for changes for given field
        in this object
        :param signal:
        :param field_name:
        :param value:
        :return:
        """
        ctrl.call_watchers(self, signal, field_name, value)

    def transitions(self):
        """ Create a dict of changes based on modified attributes of the item.
        result dict has tuples as value, where the first item is value
        before, and second
        item is value after the change.
        :return: (dict of changed attributes, 0=EDITED(default) | 1=CREATED |
        2=DELETED)
        """
        transitions = {}
        # print('item %s history: %s' % (self.uid, self._history))
        for key, old_value in self._history.items():
            new_value = self._saved[key]
            if old_value != new_value:
                if isinstance(new_value, Iterable):
                    transitions[key] = old_value, copy.copy(new_value)
                else:
                    transitions[key] = old_value, new_value
        return transitions, self._cd

    def flush_history(self):
        """ Call after getting storing a set of transitions. Prepare for next
        round of transitions.
        :return: None
        """
        self._history = {}
        self._cd = {}

    # don't know yet what to do with synobjs:
    #                elif attr_name.endswith('_synobj') and getattr(self,
    # attr_name, False):
    #                    transitions[attr_name] = (True, True)

    def revert_to_earlier(self, transitions):
        """ Restore to earlier version with a given changes -dict
        :param transitions: dict of changes, values are tuples of (old,
        new) -pairs
        :return: None
        """
        #print('--- restore to earlier for ', self, ' ----------')
        for key, value in transitions.items():
            old, new = value
            if isinstance(old, Iterable):
                setattr(self, key, copy.copy(old))
            else:
                setattr(self, key, old)

    def move_to_later(self, transitions):
        """ Move to later version with a given changes -dict
        :param transitions: dict of changes, values are tuples of (old,
        new) -pairs
        :return: None
        """
        # print('--- move to later for ', self, ' ----------')
        for key, value in transitions.items():
            old, new = value
            if isinstance(new, Iterable):
                setattr(self, key, copy.copy(new))
            else:
                setattr(self, key, new)

    def after_model_update(self, changed_fields, transition_type):
        """ Override this to update derivative values when restoring objects
        :param changed_fields:
        :param transition_type:
        :return:
        """
        pass

    def after_init(self):
        """ Override this to do preparations necessary for object creation
        :return:
        """
        self.announce_creation()

    def save_object(self, saved_objs, open_refs):
        """ Flatten the object to saveable dict and recursively save the
        objects it contains
        :param saved_objs: dict where saved objects are stored.
        :param open_refs: set of open references. We cannot go jumping to
        save each referred object when one is
        met, as it would soon lead to circular references. Open references
        are stored and cyclically reduced.
        :return: None
        """

        def _simplify(data):
            """ Goes through common iterable datatypes and if common Qt types
            are found, replaces them
            with basic python tuples.

            If object is one of Kataja's own data classes, then save its uid
            """

            if isinstance(data, (int, float, str)):
                return data
            elif isinstance(data, ITextNode):
                r = data.as_latex()
                if r:
                    return 'INode', r
                else:
                    return ''

            elif isinstance(data, dict):
                result = {}
                for k, value in data.items():
                    value = _simplify(value)
                    result[k] = value
                return result
            elif isinstance(data, list):
                result = []
                for o in data:
                    result.append(_simplify(o))
                return result
            elif isinstance(data, tuple):
                result = []
                for o in data:
                    result.append(_simplify(o))
                result = tuple(result)
                return result
            elif isinstance(data, set):
                result = set()
                for o in data:
                    result.add(_simplify(o))
                return result
            elif isinstance(data, types.FunctionType):
                # if functions are stored in the dict, there should be some
                # original
                # version of the same dict, where these
                # are in their original form.
                raise SaveError('trying to save a function at object ', self)
            elif data is None:
                return data
            elif isinstance(data, QPointF):
                return 'QPointF', to_tuple(QPointF)
            elif isinstance(data, QPoint):
                return 'QPoint', to_tuple(QPoint)
            elif isinstance(data, QtGui.QColor):
                return 'QColor', data.red(), data.green(), data.blue(), \
                       data.alpha()
            elif isinstance(data, QtGui.QPen):
                pass
            elif isinstance(data, QtCore.QRectF):
                return 'QRectF', data.x(), data.y(), data.width(), data.height()
            elif isinstance(data, QtCore.QRect):
                return 'QRect', data.x(), data.y(), data.width(), data.height()
            elif isinstance(data, QtGui.QFont):
                raise SaveError("We shouldn't save QFonts!: ", data)
            elif hasattr(data, 'uid'):
                k = getattr(data, 'uid')
                if k not in saved_objs and k not in open_refs:
                    # print('in %s adding open reference %s' % (
                    # self.uid, k))
                    open_refs[k] = data
                return '|'.join(('*r*', str(k)))
            else:
                raise SaveError("simplifying unknown data type:", data,
                                type(data))

        if self.uid in saved_objs:
            return

        obj_data = {}
        for key, item in self._saved.items():
            obj_data[key] = _simplify(item)

        # print('saving obj: ', self.uid, obj_data)
        saved_objs[self.uid] = obj_data
        if self.uid in open_refs:
            del open_refs[self.uid]

    @time_me
    def load_objects(self, data, kataja_main):
        """ Load and restore objects starting from given obj (probably Forest
        or KatajaMain instance)
        :param data:
        :param kataja_main:
        :param self:
        """
        full_map = {}
        restored = {}
        full_data = data

        # First we need a full index of objects that already exist within the
        #  existing objects.
        # This is to avoid recreating those objects. We just want to modify them
        def map_existing(obj):
            """ Take note of existing objects, as undo? will overwrite these.
            :param obj:
            :return:
            """
            if isinstance(obj, dict):
                for item in obj.values():
                    map_existing(item)
                return
            elif isinstance(obj, (list, tuple, set)):
                for item in obj:
                    map_existing(item)
                return
            # objects that support saving

            if getattr(obj, 'unique', False):
                key = getattr(obj, 'uid', '')
                if key and key not in full_map:
                    full_map[key] = obj
                    for item in obj._saved.values():
                        map_existing(item)

        # Restore either takes existing object or creates a new 'stub' object
        #  and then loads it with given data
        map_existing(self)
        self.restore(self.uid, full_data, full_map, restored, kataja_main, root=True)

    def restore(self, obj_key, full_data, full_map, restored, kataja_main, root=False):
        """ Recursively restore objects inside the scope of current obj. Used
        for loading kataja files.
        :param obj_key:
        :param root:
        :return:
        """

        if obj_key.isdigit():
            obj_key = int(obj_key)

        def inflate(data):
            """ Recursively turn QObject descriptions back into actual
            objects and object references
            back into real objects
            :param data:
            :return:
            """
            # print('inflating %s in %s' % (str(data), self))
            if data is None:
                return data
            elif isinstance(data, (int, float)):
                return data
            elif isinstance(data, dict):
                result = {}
                for k, value in data.items():
                    result[k] = inflate(value)
                return result
            elif isinstance(data, list):
                result = []
                for item in data:
                    result.append(inflate(item))
                return result
            elif isinstance(data, str):
                if data.startswith('*r*'):
                    r, uid = data.split('|', 1)
                    return self.restore(uid, full_data, full_map, restored, kataja_main)
                else:
                    return data
            elif isinstance(data, tuple):
                if data and isinstance(data[0], str):
                    data_type = data[0]
                    if data_type == 'INode':
                        parser = LatexFieldToINode(data[1])
                        return parser.node
                    elif data_type == 'QPointF':
                        return QPointF(data[1], data[2])
                    elif data_type == 'QPoint':
                        return QPoint(data[1], data[2])
                    elif data_type == 'QRectF':
                        return QtCore.QRectF(data[1], data[2], data[3], data[4])
                    elif data_type == 'QRect':
                        return QtCore.QRect(data[1], data[2], data[3], data[4])
                    elif data_type == 'QColor':
                        return QtGui.QColor(data[1], data[2], data[3], data[4])
                    elif data_type == 'QFont':
                        f = QtGui.QFont()
                        f.fromString(data[1])
                        return f
                    else:
                        raise SaveError('unknown QObject: %s' % data)
                else:
                    result = []
                    for item in data:
                        result.append(inflate(item))
                    result = tuple(result)
                    return result
            elif isinstance(data, set):
                result = set()
                for item in data:
                    result.add(inflate(item))
                return result
            return data

        # print('restoring %s , %s ' % (obj_key, class_key))
        # Don't restore object several times, even if the object is referred
        # in several places
        if obj_key in restored:
            return restored[obj_key]
        # If the object already exists (e.g. we are doing undo), the loaded
        # values overwrite existing values.

        obj = full_map.get(obj_key, None)

        # new data that the object should have
        new_data = full_data[obj_key]
        class_key = new_data['class_name']

        if not obj:
            #print('creating new ', class_key)
            obj = classes.create(class_key)
            #print('created new ', obj)
        else:
            # print('found obj: ', obj)
            pass
        # when creating/modifying values inside forests, they may refer back
        # to ctrl.forest. That has to be the current

        # forest, or otherwise things go awry
        if class_key == 'Forest':
            kataja_main.forest = obj

        # keep track of which objects have been restored
        restored[obj_key] = obj

        for key, old_value in obj._saved.items():
            new_value = new_data.get(key, None)
            if new_value is not None:
                new_value = inflate(new_value)
            if new_value != old_value:
                setattr(obj, key, new_value)

        # objects need to be finalized after setting values, do this only once per load.
        if root:
            for item in restored.values():
                if hasattr(item, 'after_init'):
                    item.after_init()
        return obj
