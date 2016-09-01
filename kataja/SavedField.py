from kataja.singletons import ctrl


class SavedField(object):
    """ This is a descriptor to use together with the BaseModel -class.
    if class variables are created as varname = Saved("varname"),
    when the same variable name is used in instances it will store the
    values in such way that they can be used for saving the data or
    remembering history through undo/redo system

    >class Item(BaseModel):
    >
    >   def __init__(self):
    >       super().__init__()
    >       self.d = 30
    >
    >   d = Saved("d")

    Now instance variable self.d supports Saving, Undo and Redo!

    Rule of thumb is that Kataja classes that describe objects that need to be saved or undoed
    always have __at the end of class__ definitions of its SavedFields.

    Descriptor can be given parameter "before_set", which should be a method of host object that is
    called with provided value if setting a value needs to have some side effect. This is to replace
    property -setters.

    Note that if variable is container e.g. list or dict, the setter doesn't activate when the
    insides are changed. For container, you have to poke them manually to notify that they need
    to save their current state to history.

    This is simple: (implemented in SavedObject)
    before manipulating a container, e.g. append, remove, pop, making [key]=something assignments
    etc. call:

    >self.poke("d")
    >d["oh"] = "my"

    With poke, old items of dict "d" are stored in SavedField's history. The changed value for
    "oh" is the current value.

    Poke is needed only once per container if there are multiple changes in a row.
    Be careful to not put it in a loop where it would be called several times.

    == Watchers ==

    The descriptor also supports announcing the changes in values to arbitrary Kataja objects.
    Usually this will be used to reflect changed value in UI elements, e.g. changing
    numeric values in comboboxes as user drags an element.

    The signaling works by giving a string identifier for 'watcher'. Then, if value is changed,
    Kataja looks into its global dict where Kataja (UI) objects are listed under the identifier.
    If there are objects, all of them are called with method 'watch_alerted', with calling
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


class SavedFieldWithGetter(SavedField):
    """ SavedField, but getter runs the provided after_get -method for the returned
    value. Useful if you want to receive e.g. QPointFs, but you want to store them as
    (x, y)-tuples. Probably bit slower than regular SavedField
    """

    def __init__(self, name, before_set=None, if_changed=None, getter=None):
        super().__init__(name, before_set=before_set, if_changed=if_changed)
        self.getter = getter

    def __get__(self, obj, objtype=None):
        value = obj._saved[self.name]
        if self.getter:
            return self.getter(obj, value)
        else:
            return value


class SavedSynField(SavedField):
    """ Descriptor that delegates attribute requests to syntactic_object.
    It can be given "before_set" parameter, which should be a method in host object that is run
    when value is set. If the property has different name in synobj than here it can be provided
    with parameter "name_in_synobj"
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