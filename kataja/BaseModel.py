import copy
import sys
import types

from PyQt5 import QtGui, QtCore

from PyQt5.QtCore import QPointF, QPoint

from kataja.utils import to_tuple
from kataja.parser.INodes import ITextNode
from kataja.parser.INodeToLatex import parse_inode_for_field
from kataja.parser.LatexToINode import parse_field
from kataja.singletons import ctrl
from kataja.globals import CREATED, DELETED

__author__ = 'purma'


class SaveError(Exception):
    """ for errors related to storing the model
    """
    # def __init__(self, value):
    # self.value = value
    # def __str__(self):
    # return repr(self.value)


class Saved(object):
    """ Descriptor to use together with the BaseModel -class.
    if class variables are created as varname = Saved("varname"),
    when the same variable name is used in instances it will store the
    values in such way that they can be used for saving the data or
    remembering history
    through undo/redo system

    >class Item(BaseModel):
    >    d = Saved("d")
    >
    >    def __init__(self):
    >       super().__init__()
    >       self.d = 30
    Now instance variable d supports Saving, Undo and Redo!

    Descriptor can be assigned a before_set, a method of object that is
    called with provided value
    if setting a value needs to have some side effect. This is to replace
    property -setters.

    Note that if variable is container e.g. list or dict,
    the setter doesn't activate when the insides are changed. For container,
    you have
    to poke them manually to notify that they need to save their current
    state to history.

    This is simple: (implemented in BaseModel)
    before manipulating a container, e.g. append, remove, pop,
    [key]=something assignments etc.
    call

    self.poke("d")
    d["oh"] = "my"

    since common Undo round, the old variable is stored only before the
    changes begin, you need
    to poke container only once if there are many changes incoming. e.g. if
    you are doing a loop
    that will write to a list or dictionary, poke the container before the
    loop, not inside it.

    == Watchers ==

    The descriptor also supports announcing the changes in values to
    arbitrary Kataja objects.
    Usually this will be used to reflect changed value in UI fields,
    e.g. changing
    numeric values in comboboxes as user drags an element.

    The signaling works by giving a string identifier for 'watcher'. Then,
    if value is changed,
    Kataja looks into its global dict where Kataja (UI) objects are listed
    under the identifier.
    If there are objects, all of them are called with method 'watch_alerted',
    with calling
    object, field name, and new value as arguments.


     """

    def __init__(self, name, before_set=None, if_changed=None, watcher=None):
        self.name = name
        self.before_set = before_set
        self.if_changed = if_changed
        self.watcher = watcher

    def __get__(self, obj, objtype=None):
        return obj._saved.get(self.name, None)

    def __set__(self, obj, value):
        if self.before_set:
            value = self.before_set(obj, value)
        if ctrl.undo_disabled:
            if self.name in obj._saved:
                old_value = obj._saved[self.name]
                obj._saved[self.name] = value
                if old_value != value:
                    if self.if_changed:
                        self.if_changed(obj, value)
                    if self.watcher:
                        obj.call_watchers(self.watcher, self.name, value)
            else:
                obj._saved[self.name] = value
                if self.if_changed:
                    self.if_changed(obj, value)
                if self.watcher:
                    obj.call_watchers(self.watcher, self.name, value)
        elif self.name in obj._saved:
            old = obj._saved[self.name]
            if old != value:
                if not obj._history:
                    ctrl.undo_pile.add(obj)
                    obj._history[self.name] = old
                elif self.name not in obj._history:
                    obj._history[self.name] = old
                obj._saved[self.name] = value
                if self.if_changed:
                    self.if_changed(obj, value)
                if self.watcher:
                    obj.call_watchers(self.watcher, self.name, value)
        else:
            obj._saved[self.name] = value
            if self.if_changed:
                self.if_changed(obj, value)
            if self.watcher:
                obj.call_watchers(self.watcher, self.name, value)


class SavedAndGetter(Saved):
    """ Saved, but getter runs provided after_get -method for the returned
    value. Probably bit slower
    than regular Saved
    """

    def __init__(self, name, before_set=None, if_changed=None, after_get=None):
        super().__init__(name, before_set=before_set, if_changed=if_changed)
        self.after_get = after_get

    def __get__(self, obj, objtype=None):
        value = obj._saved[self.name]
        if self.after_get:
            return self.after_get(obj, value)
        else:
            return value


class Synobj(Saved):
    """ Descriptor that delegates attribute requests to syntactic_object.
    can be given before_set, a method in object that is run when value is set
    and if property has different name in synobj than here it can be provided as
    name_in_synobj
    """

    def __init__(self, name, before_set=None, if_changed=None,
                 name_in_synobj=None):
        super().__init__(name, before_set=before_set, if_changed=if_changed)
        self.name_in_synobj = name_in_synobj or name

    def __get__(self, obj, objtype=None):
        synob = obj._saved.get("syntactic_object")
        if synob:
            return getattr(synob, self.name_in_synobj)
        else:
            return obj._saved.get(self.name, None)

    def __set__(self, obj, value):
        if self.before_set:
            value = self.before_set(obj, value)
        synob = obj._saved.get("syntactic_object")
        if synob:
            if self.before_set:
                value = self.before_set(obj, value)
            old_value = getattr(synob, self.name_in_synobj)
            setattr(synob, self.name_in_synobj, value)
            if self.if_changed and value != old_value:
                self.if_changed(obj, value)
        else:
            super().__set__(obj, value)


class BaseModel(object):
    """ Make the object to have internal .saved -object where saved data
    should go.
    Also makes it neater to check if item is Savable.
    """
    short_name = "Override this!"
    _sk = Saved("_sk")

    def __init__(self, unique=False, save_key='', **kw):
        if save_key:
            key = save_key
        elif unique:
            key = self.__class__.short_name
        else:
            key = str(id(self))[-6:] + '|' + self.__class__.short_name
        self._saved = {}
        self._history = {}
        self._sk = key
        self._cd = 0  # / CREATED / DELETED
        sys.intern(key)

    @property
    def save_key(self):
        """ Unique key for retrieving the object and identifying it in
        save/load/undo systems
        :return:
        """
        return self._sk

    def __str__(self):
        return self._sk

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
        if ctrl.undo_disabled:
            return
        self._cd = DELETED
        ctrl.undo_pile.add(self)

    def call_watchers(self, signal, field_name, value):
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
        # print('item %s history: %s' % (self.save_key, self._history))
        for key, old_value in self._history.items():
            new_value = self._saved[key]
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
        # print('--- restore to earlier for ', self, ' ----------')
        for key, value in transitions.items():
            # if key.startswith('_') and key.endswith('_synobj'):
            #    continue
            old, new = value
            setattr(self, key, old)
            if len(str(new)) < 80:
                print('%s  %s: %s <- %s' % (self.save_key, key, old, new))
            else:
                print('%s %s: (long) <- (long)' % (self.save_key, key))

    def move_to_later(self, transitions):
        """ Move to later version with a given changes -dict
        :param transitions: dict of changes, values are tuples of (old,
        new) -pairs
        :return: None
        """
        # print('--- move to later for ', self, ' ----------')
        for key, value in transitions.items():
            # if key.startswith('_') and key.endswith('_synobj'):
            #    continue
            old, new = value
            setattr(self, key, new)
            if len(str(new)) < 80:
                print('%s  %s: %s -> %s' % (self.save_key, key, old, new))
            else:
                print('%s %s: (long) -> (long)' % (self.save_key, key))

    def update_model(self, changed_fields, transition_type, doing_undo=True):
        """ Runs the after_model_update that should do the necessary
        derivative calculations and graphical updates
        after the model has been changed by redo/undo.
        updates are run as a batch after all of the objects have had their
        model values updated.
        :param changed_fields: dict of changes, same as in revert/move
        :param transition_type: 0:edit, 1:CREATED, 2:DELETED
        :param doing_undo: bool - are we doing undo (True) or redo (False),
        affects how transition_type is
        interpreted
        :return:
        """
        updater = getattr(self, 'after_model_update', None)
        # a little piece of stupidity here
        if transition_type == CREATED and doing_undo:
            transition_type = DELETED
        elif transition_type == DELETED and doing_undo:
            transition_type = CREATED
        if updater:
            updater(changed_fields, transition_type)

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

            If object is one of Kataja's own data classes, then save its
            save_key
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
            elif hasattr(data, 'save_key'):
                k = getattr(data, 'save_key')
                if k not in saved_objs and k not in open_refs:
                    # print('in %s adding open reference %s' % (
                    # self.save_key, k))
                    open_refs[k] = data
                return '|'.join(('*r*', str(k)))
            else:
                raise SaveError("simplifying unknown data type:", data,
                                type(data))

        if self.save_key in saved_objs:
            return

        obj_data = {}
        for key, item in self._saved.items():
            obj_data[key] = _simplify(item)

        # print('saving obj: ', self.save_key, obj_data)
        saved_objs[self.save_key] = obj_data
        if self.save_key in open_refs:
            del open_refs[self.save_key]

    def load_objects(self, data, kataja_main):
        """ Load and restore objects starting from given obj (probably Forest
        or KatajaMain instance)
        :param data:
        :param kataja_main:
        :param self:
        """

        global full_map, restored, full_data, main
        full_map = {}
        restored = {}
        full_data = data
        main = kataja_main

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
            key = getattr(obj, 'save_key', '')
            if key and key not in full_map:
                full_map[key] = obj
                for item in obj._saved.values():
                    map_existing(item)

        # Restore either takes existing object or creates a new 'stub' object
        #  and then loads it with given data
        map_existing(self)
        self.restore(self.save_key)
        del full_map, restored, full_data, main

    def restore(self, obj_key, class_key=''):
        """ Recursively restore objects inside the scope of current obj. Used
        for loading kataja files.
        :param obj_key:
        :param class_key:
        :return:
        """
        global full_map, restored, full_data, main

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
                    parts = data.split('|')
                    if len(parts) > 2:
                        return self.restore(parts[1] + '|' + parts[2], parts[2])
                    else:
                        return self.restore(parts[1], parts[1])
                else:
                    return data
            elif isinstance(data, tuple):
                if data and isinstance(data[0], str):
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
        # Don't restore object several times, even if the object is referred
        # in several places
        if obj_key in restored:
            return restored[obj_key]
        # If the object already exists (e.g. we are doing undo), the loaded
        # values overwrite existing values.
        obj = full_map.get(obj_key, None)
        if not obj:
            # print('creating new ', class_key)
            obj = main.object_factory.create(class_key)
            # print('created new ', obj)
        else:
            # print('found obj: ', obj)
            pass
        # when creating/modifying values inside forests, they may refer back
        # to ctrl.forest. That has to be the current

        # forest, or otherwise things go awry
        if class_key == 'Forest':
            main.forest = obj

        # keep track of which objects have been restored
        restored[obj_key] = obj

        # new data that the object should have
        new_data = full_data[obj_key]
        for key, old_value in obj._saved.items():
            new_value = new_data.get(key, None)
            if new_value is not None:
                new_value = inflate(new_value)
            if new_value != old_value:
                setattr(obj, key, new_value)
        # object needs to be finalized after setting values
        if hasattr(obj, 'after_init'):
            obj.after_init()
        return obj
