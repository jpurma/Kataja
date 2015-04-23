import sys
import traceback
import types

from PyQt5 import QtGui, QtCore

from PyQt5.QtCore import QPointF, QPoint
from kataja.utils import to_tuple
from kataja.parser.INodes import ITextNode
from kataja.parser.INodeToLatex import parse_inode_for_field
from kataja.parser.LatexToINode import parse_field
from kataja.singletons import ctrl

__author__ = 'purma'

# Creation/Deletion flags
CREATED = 1
DELETED = 2

class SaveError(Exception):
    """ for errors related to storing the model
    """
    # def __init__(self, value):
    # self.value = value
    # def __str__(self):
    # return repr(self.value)


class BaseModel:
    """ Make the object to have internal .saved -object where saved data should go.
    Also makes it neater to check if item is Savable.
    """

    def __init__(self, host, unique=False):
        if unique:
            key = self.__class__.__name__
        else:
            key = str(id(self)) + '|' + self.__class__.__name__
        self.save_key = key
        self._host = host
        self._cd = 0 # / CREATED / DELETED
        sys.intern(self.save_key)

    def touch(self, attribute, value):
        """ Prepare a permanency-supporting attribute for being changed: if the new value would change it,
          store its current value in _x_history, raise the _x_touched -flag and announce controller to check
          this object when the undo cycle is finished.

           The idea is that modified values between undo cycles are easy to collect, and thus we can create a diff from
           global kataja state or diff in forest.

        :param attribute: string, the name of attribute being set
        :param value: new value
        :return: True if set operation would change the value, False if not
        """
        if ctrl.disable_undo:
            return True
        old_value = getattr(self, attribute, None)
        if old_value != value:
            touched_name = '_' + attribute + '_touched'
            touched = getattr(self, touched_name, False)
            if not touched:
                # print('(touch) adding to undo_pile %s for attribute %s (%s, %s)' %
                # (self._host, attribute, old_value, value))
                ctrl.undo_pile.add(self._host)
                setattr(self, '_' + attribute + '_history', old_value)
                setattr(self, touched_name, True)
            return True
        return False

    def poke(self, attribute):
        """ Like "touch", to alert undo system that this object is being changed.
        This is used manually for container-type objects in the model before changing adding or
        removing objects in them, as these operations would not be catch by setters. This doesn't check if
         the new value is different from previous, as this is used manually before actions that change
         the list/dict/set.
        :param attribute: string, name of the attribute
        :return: None
        """
        if ctrl.disable_undo:
            return
        touched_name = '_' + attribute + '_touched'
        touched = getattr(self, touched_name, False)
        if not touched:
            # print('(poke) adding to undo_pile', self._host)
            ctrl.undo_pile.add(self._host)
            setattr(self, '_' + attribute + '_history', getattr(self, attribute, None))
            setattr(self, touched_name, True)

    def announce_creation(self):
        """ Flag object to have been created in this undo cycle.
        If the object was created here, when moving to _previous_ cycle should launch removal of the object
        from scene.
        :return:None
        """
        if ctrl.disable_undo:
            return
        self._cd = CREATED
        ctrl.undo_pile.add(self._host)

    def announce_deletion(self):
        """ Flag object to have been deleted in this undo cycle.
        :return:None
        """
        if ctrl.disable_undo:
            return
        self._cd = DELETED
        ctrl.undo_pile.add(self._host)


    def transitions(self):
        """ Create a dict of changes based on touched attributes of the item.
        After creation, reset the touched attributes so that the attribute can
        record the next changes.
        result dict has tuples as value, where the first item is value before, and second
        item is value after the change.
        :return: (dict of changed attributes, 0=EDITED(default) | 1=CREATED | 2=DELETED)
        """
        transitions = {}
        for attr_name in dir(self):
            if attr_name.startswith('_'):
                if attr_name.endswith('_touched'):
                    if getattr(self, attr_name, False):
                        attr_base = attr_name[1:-8]
                        hist_name = '_%s_history' % attr_base
                        old = getattr(self, hist_name)
                        new = getattr(self, attr_base)
                        transitions[attr_base] = (old, new)
                        setattr(self, hist_name, None)
                        setattr(self, attr_name, False)
                elif attr_name.endswith('_synobj') and getattr(self, attr_name, False):
                    transitions[attr_name] = (True, True)
        created_or_deleted = self._cd
        self._cd = 0
        return transitions, created_or_deleted

    def revert_to_earlier(self, transitions):
        """ Restore to earlier version with a given changes -dict
        :param transitions: dict of changes, values are tuples of (old, new) -pairs
        :return: None
        """
        for key, value in transitions.items():
            if key.startswith('_') and key.endswith('_synobj'):
                continue
            old, new = value
            setattr(self, key, old)

    def move_to_later(self, transitions):
        """ Move to later version with a given changes -dict
        :param transitions: dict of changes, values are tuples of (old, new) -pairs
        :return: None
        """
        for key, value in transitions.items():
            if key.startswith('_') and key.endswith('_synobj'):
                continue
            old, new = value
            setattr(self, key, new)

    def update(self, changed_fields):
        """ Runs the after_model_update that should do the necessary derivative calculations and graphical updates
        after the model has been changed by redo/undo.
        updates are run as a batch after all of the objects have had their model values updated.
        :param changes: dict of changes, same as in revert/move
        :return:
        """
        updater = getattr(self._host, 'after_model_update', None)
        if updater:
            updater(changed_fields)

    def save_object(self, saved_objs, open_refs):
        """ Flatten the object to saveable dict and recursively save the objects it contains
        :param saved_objs: dict where saved objects are stored.
        :param open_refs: set of open references. We cannot go jumping to save each referred object when one is
        met, as it would soon lead to circular references. Open references are stored and cyclically reduced.
        :return: None
        """

        def _simplify(data):
            """ Goes through common iterable datatypes and if common Qt types are found, replaces them
            with basic python tuples.

            If object is one of Kataja's own data classes, then save its save_key
            """

            if isinstance(data, (int, float, str)):
                return data
            elif isinstance(data, ITextNode):
                r = parse_inode_for_field(data)
                if r:
                    return 'INode', parse_inode_for_field(data)
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
                # if functions are stored in the dict, there should be some original
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
                return 'QColor', data.red(), data.green(), data.blue(), data.alpha()
            elif isinstance(data, QtGui.QPen):
                pass
            elif isinstance(data, QtCore.QRectF):
                return 'QRectF', data.x(), data.y(), data.width(), data.height()
            elif isinstance(data, QtCore.QRect):
                return 'QRect', data.x(), data.y(), data.width(), data.height()
            elif isinstance(data, QtGui.QFont):
                raise SaveError("We shouldn't save QFonts!: ", data)
            elif hasattr(data, 'save_key'):
                k = getattr(data, 'save_key')
                if k not in saved_objs and k not in open_refs:
                    # print('in %s adding open reference %s' % (self.save_key, k))
                    open_refs[k] = data
                return '|'.join(('*r*', str(k)))
            else:
                raise SaveError("simplifying unknown data type:", data, type(data))

        if self.save_key in saved_objs:
            return

        obj_data = {}
        for key, item in vars(self).items():
            if not key.startswith('_') and item and not callable(item):
                obj_data[key] = _simplify(item)

        saved_objs[self.save_key] = obj_data
        if self.save_key in open_refs:
            del open_refs[self.save_key]

    def load_objects(self, data, kataja_main):
        """ Load and restore objects starting from given obj (probably Forest or KatajaMain instance)
        :param data:
        :param kataja_main:
        :param self:
        """

        global full_map, restored, full_data, main
        full_map = {}
        restored = {}
        full_data = data
        main = kataja_main

        # First we need a full index of objects that already exist within the existing objects.
        # This is to avoid recreating those objects. We just want to modify them
        def map_existing(obj):
            # containers
            """

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
            key = getattr(obj, 'save_key', '')
            try:
                print(getattr(obj, 'save_key', ''), obj.save_key)
            except AttributeError:
                pass
            if key and key not in full_map:
                full_map[key] = obj
                print(type(obj))
                for item in vars(obj).values():
                    map_existing(item)

        # Restore either takes existing object or creates a new 'stub' object and then loads it with given data

        map_existing(self)
        print('full_map has %s items' % len(full_map))
        self.restore(self.save_key)
        del full_map, restored, full_data, main

    def restore(self, obj_key, class_key=''):
        """ Recursively restore objects inside the scope of current obj. Used for loading kataja files.
        :param obj_key:
        :param class_key:
        :return:
        """
        global full_map, restored, full_data, main

        def inflate(data):
            """ Recursively turn QObject descriptions back into actual objects and object references
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
                    parts = data.split('|')
                    if len(parts) > 2:
                        return self.restore(parts[1] + '|' + parts[2], parts[2])
                    else:
                        return self.restore(parts[1], parts[1])
                else:
                    return data
            elif isinstance(data, tuple):
                if data and isinstance(data[0], str) and data[0].startswith('Q'):
                    data_type = data[0]
                    if data_type == 'INode':
                        return parse_field(data[1])
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
        # Don't restore object several times, even if the object is referred in several places
        if obj_key in restored:
            return restored[obj_key]
        # If the object already exists (e.g. we are doing undo), the loaded values overwrite existing values.
        obj = full_map.get(obj_key, None)
        if not obj:
            # print('creating new ', class_key)
            obj = main.object_factory(class_key)
        # when creating/modifying values inside forests, they may refer back to ctrl.forest. That has to be the current
        # forest, or otherwise things go awry
        if class_key == 'Forest':
            main.forest = obj

        # keep track of which objects have been restored
        restored[obj_key] = obj

        # new data that the object should have
        new_data = full_data[obj_key]
        # only values that can be replaced are those defined inside the obj.model -instance.
        for key, old_value in vars(obj.model).items():
            new_value = new_data.get(key, None)
            if new_value is not None:
                new_value = inflate(new_value)
            if new_value != old_value and (new_value or old_value):
                # changes[key] = (old_value, new_value)
                # print('set: %s.%s = %s (old value: %s)' % (obj, key, new_value, old_value))
                setattr(obj, key, new_value)
        # object needs to be finalized after setting values
        if hasattr(obj, 'after_init'):
            obj.after_init()
        return obj




