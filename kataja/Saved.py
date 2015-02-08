from PyQt5 import QtGui, QtCore, QtWidgets
import sys
import types
from PyQt5.QtCore import QPointF, QPoint
from kataja.utils import to_tuple
from kataja.parser.INodes import ITextNode
from kataja.parser.INodeToLatex import parse_inode_for_field
from kataja.parser.LatexToINode import parse_field

__author__ = 'purma'

class SaveError(Exception):
    pass
    #def __init__(self, value):
    #    self.value = value
    #def __str__(self):
    #    return repr(self.value)

class Savable:
    """ Make the object to have internal .saved -object where saved data should go.
    Also makes it neater to check if item is Savable.
    """

    def __init__(self, unique=False):
        if unique:
            key = self.__class__.__name__
        else:
            key = str(id(self)) + '|' + self.__class__.__name__
        self.saved = Saved()
        self.saved.save_key = key
        sys.intern(self.saved.save_key)

    @property
    def save_key(self):
        return self.saved.save_key

    @save_key.setter
    def save_key(self, value):
        self.saved.save_key = value


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
            elif isinstance(data, ITextNode):
                return 'INode', parse_inode_for_field(data)

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
                key = getattr(data, 'save_key')
                if key not in saved_objs and key not in open_refs:
                    open_refs[key] = data
                return '|'.join(('*r*', str(key)))
            else:
                raise SaveError("simplifying unknown data type:", data, type(data))

        if self.save_key in saved_objs:
            return
        obj_data = {}
        for key, item in vars(self.saved).items():
            if item:
                obj_data[key] = _simplify(item)

        saved_objs[self.save_key] = obj_data
        if self.save_key in open_refs:
            del open_refs[self.save_key]

    def load_objects(self, data, kataja_main):
        """ Load and restore objects starting from given obj (probably Forest or KatajaMain instance)
        :param self:
        :param full_data:
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
            if key and key not in full_map:
                full_map[key] = obj
                for item in vars(obj.saved).values():
                    map_existing(item)

        # Restore either takes existing object or creates a new 'stub' object and then loads it with given data

        map_existing(self)
        print('full_map:', full_map)
        self.restore(self.save_key)

    def restore(self, obj_key, class_key=''):
        """

        :param obj_key:
        :param class_key:
        :return:
        """
        global full_map, restored, full_data, main
        def inflate(data):
            """ Recursively turn QObject descriptions back into actual objects and object references back into real objects
            :param data:
            :param self:
            :return:
            """
            #print('inflating %s in %s' % (str(data), self))
            if data is None:
                return data
            elif isinstance(data, (int, float)):
                return data
            elif isinstance(data, dict):
                result = {}
                for key, value in data.items():
                    value = inflate(value)
                    result[key] = value
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
                        return self.restore(parts[1]+'|'+parts[2], parts[2])
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

        #print('restoring %s , %s ' % (obj_key, class_key))
        if obj_key in restored:
            return restored[obj_key]
        obj = full_map.get(obj_key, None)
        if not obj:
            #print('creeating new ', class_key)
            obj = main.object_factory.create(class_key)
        if class_key == 'Forest':
            main.forest = obj
        restored[obj_key] = obj
        obj_data = full_data[obj_key]
        for key, old_value in vars(obj.saved).items():
            new_value = obj_data.get(key, None)
            if new_value is not None:
                new_value = inflate(new_value)
            if new_value != old_value and (bool(new_value) or bool(old_value)):
                #changes[key] = (old_value, new_value)
                #print('set: %s.%s = %s (old value: %s)' % (obj, key, new_value, old_value))
                setattr(obj, key, new_value)
                #print '  in %s set %s to %s, was %s' % (obj_key, key, new_value, old_value)
                #else:
                #    print 'in %s keep %s value %s' % (obj_key, key, old_value)
        # !!! object needs to be finalized after this !!!
        if hasattr(obj, 'after_init'):
            obj.after_init()
        return obj





class Saved:
    """ Everything about object that needs to be saved should be put inside instance of Saved, inside the object.
    eg. for Node instance:  self.saved.syntactic_object = ...

    This class takes care of translating the data to storage format and back.
    """

    def __init__(self):
        pass



