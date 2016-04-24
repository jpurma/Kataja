from kataja.singletons import ctrl


class SavedField(object):
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
    Usually this will be used to reflect changed value in UI elements,
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


class SavedFieldWithGetter(SavedField):
    """ Saved, but getter runs the provided after_get -method for the returned
    value. Probably bit slower than regular Saved
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