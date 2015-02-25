class ObjectFactory:
    """

    """

    def __init__(self):
        pass


    def create(self, object_class_name, *args, **kwargs):
        class_object = globals().get(object_class_name, None)
        if class_object:
            # print('creating obj %s with args %s and kwargs %s ' % (object_class_name, str(args), str(kwargs)))
            new_object = class_object(*args, **kwargs)
            # new_object = object.__new__(class_object, *args, **kwargs)
            # print(new_object)
            return new_object
        else:
            # print('class missing: ', object_class_name)
            raise TypeError('class missing: %s ' % object_class_name)
            # print(globals().keys())
