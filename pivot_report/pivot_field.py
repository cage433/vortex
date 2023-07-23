from abc import ABC, abstractmethod
from numbers import Number

from pivot_report.pivot_value import PivotValue, NumericValue
from utils import checked_type
from utils.type_checks import checked_opt_type


class PivotField():
    def __init__(self, name: str):
        self.name: str = checked_type(name, str)

    def value_type_check(self, value):
        raise NotImplementedError()


class DimensionField(PivotField):
    pass


class CategoryField(DimensionField):
    def __init__(self, level: int):
        super().__init__(f"Level {level}")
        self.level: int = checked_type(level, int)
        self.__hash = hash(self.level)

    def value_type_check(self, value):
        checked_opt_type(value, str)

    def __eq__(self, other):
        return isinstance(other, CategoryField) and self.level == other.level

    def __hash__(self):
        return self.__hash


class TimsDescriptionField(DimensionField):
    def __init__(self):
        super().__init__("Tims Description")
        self.__hash = hash(self.name)

    def value_type_check(self, value):
        checked_opt_type(value, str)

    def __eq__(self, other):
        return isinstance(other, TimsDescriptionField)

    def __hash__(self):
        return self.__hash


class MeasureField(PivotField):
    @abstractmethod
    def merge(self, values: list[PivotValue]) -> PivotValue:
        pass


class TransactionValueField(MeasureField):
    def __init__(self):
        super().__init__("Transaction Value")
        self.__hash = hash(self.name)

    def value_type_check(self, value):
        checked_type(value, Number)

    def merge(self, values: list[PivotValue]) -> PivotValue:
        sum = 0
        for value in values:
            checked_type(value, NumericValue)
            sum += value.value
        return sum

    def __eq__(self, other):
        return isinstance(other, TransactionValueField)

    def __hash__(self):
        return self.__hash

LEVEL_1 = CategoryField(1)
LEVEL_2 = CategoryField(2)
LEVEL_3 = CategoryField(3)
LEVEL_4 = CategoryField(4)
LEVEL_5 = CategoryField(5)
TIMS_DESCRIPTION = TimsDescriptionField()
TRANSACTION_VALUE = TransactionValueField()
