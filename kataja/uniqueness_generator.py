

type_id = 65536
uid = 1
ui_key = 1


def next_available_type_id():
    global type_id
    type_id += 1
    return type_id


def next_available_uid():
    global uid
    uid += 1
    return uid


def next_available_ui_key():
    global ui_key
    ui_key += 1
    return ui_key