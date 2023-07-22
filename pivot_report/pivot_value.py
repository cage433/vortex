from abc import ABC, abstractmethod
from functools import total_ordering
from numbers import Number

from myopt.nothing import Nothing
from myopt.opt import Opt
from myopt.something import Something
from utils import checked_type
from utils.type_checks import checked_opt_type


class PivotValue(ABC):
    @property
    @abstractmethod
    def display_value(self) -> any:
        pass


@total_ordering
class StringPivotValue(PivotValue):
    def __init__(self, value: str):
        self.value = checked_type(value, str)
        self.__hash = hash(self.value)

    @property
    def display_value(self) -> any:
        return self.value

    def __str__(self):
        return f"String({self.value})"

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.value < other.value

    def __eq__(self, other):
        return self.value == other.value

    def __hash__(self):
        return self.__hash


@total_ordering
class OptionalStringPivotValue(PivotValue):
    def __init__(self, value: Opt[str]):
        self.value: Opt[str] = checked_opt_type(value, str)
        self._hash = hash(self.value)

    def __str__(self):
        return f"Optional({self.value})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __hash__(self):
        return self._hash

    @property
    def display_value(self) -> any:
        return self.value.get_or_else("None")


class NumericValue(PivotValue):
    def __init__(self, value: Number):
        self.value: float = checked_type(value, Number)

    @property
    def display_value(self) -> any:
        return self.value
