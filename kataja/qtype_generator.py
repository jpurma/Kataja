

type_id = 65536


def next_available_type_id():
    global type_id
    type_id += 1
    return type_id
