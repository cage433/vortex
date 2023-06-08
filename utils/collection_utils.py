def group_into_dict(iterable, key_constructor):
    """Builds a dict whose values are disjoint sub-lists of `iterable`, which share the same `property` value, the
    latter being the associated key.

    The sub-lists constructed preserve order to the extent the original iterable does

    Equivalent to `groupBy` in the Scala collections library. Note that this is _not_ equivalent to `itertools.group_by`
    """
    result = {}
    for item in iterable:
        key = key_constructor(item)
        result[key] = result.get(key, []) + [item]

    return result


def flatten(things):
    result = []
    for thing in things:
        if isinstance(thing, list):
            result.extend(flatten(thing))
        else:
            result.append(thing)
    return result
