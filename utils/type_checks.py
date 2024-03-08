__all__ = [
    "checked_type",
    "checked_list_type",
    "checked_optional_type",
    "checked_dict_type",
    "checked_opt_type",
]

from myopt.opt import Opt


def checked_type(obj, expected_type):
    assert isinstance(obj, expected_type), f"{obj} is of type {type(obj)}, expected {expected_type}"
    return obj


def checked_set_type(obj, expected_type):
    assert isinstance(obj, set), f"{obj} is of type {type(obj)}, expected set"
    for x in obj:
        checked_type(x, expected_type)
    return obj

def checked_list_type(obj, expected_type):
    assert isinstance(obj, list), f"{obj} is of type {type(obj)}, expected list"
    for x in obj:
        checked_type(x, expected_type)
    return obj


def checked_optional_type(obj, expected_type):
    if obj is None:
        return None
    return checked_type(obj, expected_type)


def checked_opt_type(obj, expected_type):
    if not isinstance(obj, Opt):
        print("here")
    checked_type(obj, Opt)
    obj.for_each(lambda x: checked_type(x, expected_type))
    return obj


def checked_dict_type(obj, key_type, value_type):
    assert isinstance(obj, dict), f"{obj} is of type {type(obj)}, expected dict"
    for k, v in obj.items():
        checked_type(k, key_type)
        checked_type(v, value_type)
    return obj
