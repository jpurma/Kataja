# coding=utf-8


def get_ui_container(qt_object):
    """ Traverse up in widget hierarchy until object governed by UIManager is
    found. Return this.
    :param qt_object:
    :return:
    """
    if not qt_object:
        return None
    if getattr(qt_object, 'ui_key', None):
        return qt_object
    else:
        p = qt_object.parent()
        if p:
            return get_ui_container(p)
        else:
            return None


def get_host(sender):
    """ Get the Kataja object that this UI element is about, the 'host' element.
    :param sender:
    :return:
    """
    container = get_ui_container(sender)
    if container:
        return container.host


