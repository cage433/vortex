import csv
from datetime import date
from numbers import Number
from pathlib import Path
from typing import Optional, Tuple, List

import numpy as np

from date_range import DateRange



def difference(x, y, path: List[str] = None, tol: float = 1e-9) -> Optional[Tuple[str, str, object, object]]:
    if path is None:
        path = []

    if isinstance(x, Number):
        if abs(x - y) > tol:
            return ("/".join(path), "value", x, y)
        return None

    if x.__class__ != y.__class__:
        return ("/".join(path), "class", x.__class__, y.__class__)

    if isinstance(x, np.ndarray):
        try:
            np.testing.assert_array_almost_equal(x, y)
            return None
        except AssertionError:
            return (path, "np.ndarray", x, y)

    if isinstance(x, (list, tuple)):
        if len(x) != len(y):
            return (path, "list length", x, y)
        for i in range(len(x)):
            if result := difference(x[i], y[i], path + [str(i)], tol):
                return result
        return None

    if isinstance(x, (str, DateRange, date, bool, Path, type)):
        if x != y:
            return (path, "object", x, y)
        return None

    if x is None or y is None:
        if x != y:
            return (path, "None", x, y)

    if x is None and y is None:
        return None

    if isinstance(x, dict):
        if len(x) != len(y):
            return (path, "len", x, y)
        for k, v in x.items():
            if result := difference(x.get(k), y.get(k), path + [str(k)], tol):
                return result
        for k, v in y.items():
            if result := difference(x.get(k), y.get(k), path + [str(k)], tol):
                return result
        return None

    for name in vars(x):
        if name.startswith("_"):
            continue
        if result := difference(getattr(x, name), getattr(y, name), path + [name], tol):
            return result

    return None


def assert_almost_equal(x, y, tol=1e-9):
    if result := difference(x, y, tol=tol):
        raise AssertionError(f"Have difference {result}")
