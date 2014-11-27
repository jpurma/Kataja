from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import types
from PyQt5.QtCore import QPointF, QPoint
from kataja.utils import to_tuple

__author__ = 'purma'


class Savable:
    """ Make the object to have internal .saved -object where saved data should go.
    Also makes it neater to check if item is Savable.
    """

    def __init__(self, unique=False, restore=None):
        if unique:
            key = self.__class__.__name__
        else:
            key = str(id(self)) + '|' + self.__class__.__name__
        self.saved = Saved()
        self.saved.key = key
        sys.intern(self.saved.key)

    @property
    def save_key(self):
        return self.saved.key

    @save_key.setter
    def save_key(self, value):
        self.saved.key = value


    def save_object(self, saved_objs, open_refs):
        """

        :param self:
        :param saved_objs:
        :param open_refs:
        :param ignore:
        :return: :raise:
        """

        def _simplify(data):
            """ Goes through common iterable datatypes and if common Qt types are found, replaces them
            with basic python tuples.

            If object is one of Kataja's own data classes, then save its save_key
            """

            if isinstance(data, (int, float, str)):
                return data
            elif isinstance(data, dict):
                result = {}
                for key, value in data.items():
                    value = _simplify(value)
                    result[key] = value
                return result
            elif isinstance(data, list):
                result = []
                for item in data:
                    result.append(_simplify(item))
                return result
            elif isinstance(data, tuple):
                result = []
                for item in data:
                    result.append(_simplify(item))
                result = tuple(result)
                return result
            elif isinstance(data, set):
                result = set()
                for item in data:
                    result.add(_simplify(item))
                return result
            elif isinstance(data, types.FunctionType):
                # if functions are stored in the dict, there should be some original version of the same dict, where these
                # are in their original form.
                print('saving function in undo, at object ', self)
                return None
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
                print("We shouldn't save QFonts!: ", data)
                return 'QFont', data.toString()
            elif hasattr(data, 'save_key'):
                key = getattr(data, 'save_key')
                if key not in saved_objs and key not in open_refs:
                    open_refs[key] = data
                return '|'.join(('*r*', str(key)))
            elif hasattr(data.__class__, 'singleton_key'):
                key = getattr(data.__class__, 'singleton_key')
                if key not in saved_objs and key not in open_refs:
                    open_refs[key] = data
                return '|'.join(('*r*', str(key)))
            else:
                print("simplifying unknown data type:", data, type(data))

        if self.save_key in saved_objs:
            return
        obj_data = {}
        for key, item in vars(self.saved).items():
            obj_data[key] = _simplify(item)

        saved_objs[self.save_key] = obj_data
        if self.save_key in open_refs:
            del open_refs[self.save_key]

    def load_objects(self, data):
        """ Load and restore objects starting from given obj (probably Forest or KatajaMain instance)
        :param self:
        :param full_data:
        """

        global full_map, restored, full_data
        full_map = {}
        restored = {}
        full_data = data

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
            key = getattr(obj, 'save_key', '') or getattr(obj.__class__, 'singleton_key', '')
            if key and key not in full_map:
                full_map[key] = obj
                for item in vars(obj.saved).values():
                    map_existing(item)

        # Restore either takes existing object or creates a new 'stub' object and then loads it with given data

        map_existing(self)
        self.restore(self.save_key)

    def restore(self, obj_key, class_key=''):
        """

        :param obj_key:
        :param class_key:
        :return:
        """
        global full_map, restored, full_data
        if obj_key in restored:
            return restored[obj_key]
        obj = full_map.get(obj_key, None)
        restored[obj_key] = obj
        if not obj:
            # needs to create a stub object
            # how can we reach the constructor?
            pass
        obj_data = full_data[obj_key]
        changes = {}
        for key, value in obj_data.items():
            new_value = obj.inflate(value)
            old_value = getattr(obj, key)
            if new_value != old_value:
                changes[key] = (old_value, new_value)
                setattr(obj, key, new_value)
                #print '  in %s set %s to %s, was %s' % (obj_key, key, new_value, old_value)
                #else:
                #    print 'in %s keep %s value %s' % (obj_key, key, old_value)
        #  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # !!! object needs to be finalized after this !!!
        #  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if hasattr(obj, 'after_restore'):
            obj.after_restore(changes)
        else:
            print(' *obj %s (%s) after_restore -method missing *' % (obj, type(obj)))
        return obj


    def inflate(self, data):
        """ Recursively turn QObject descriptions back into actual objects and object references back into real objects
        :param data:
        :param self:
        :return:
        """
        if isinstance(data, (int, float, str)):
            return data
        elif isinstance(data, dict):
            result = {}
            for key, value in data.items():
                value = self.inflate(value)
                result[key] = value
            return result
        elif isinstance(data, list):
            result = []
            for item in data:
                result.append(self.inflate(item))
            return result
        elif isinstance(data, str):
            if data.startswith('*r*'):
                ref, key, class_name = tuple(data.split('|'))
                return self.restore(key+'|'+class_name, class_name)
        elif isinstance(data, tuple):
            if data and isinstance(data[0], str) and data[0].startswith('Q'):
                data_type = data[0]
                if data_type == 'QPointF':
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
                    print('unknown QObject: ', data)
            else:
                result = []
                for item in data:
                    result.append(self.inflate(item))
                result = tuple(result)
                return result
        elif isinstance(data, set):
            result = set()
            for item in data:
                result.add(self.inflate(item))
            return result
        elif data is None:
            return data
        return data



class Saved:
    """ Everything about object that needs to be saved should be put inside instance of Saved, inside the object.
    eg. for Node instance:  self.saved.syntactic_object = ...

    This class takes care of translating the data to storage format and back.
    """

    def __init__(self):
        pass



