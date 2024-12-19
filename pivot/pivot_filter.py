from typing import Callable

from date_range import DateRange
from pivot.pivot_field import PivotField
from pivot.pivot_table import PivotRow
from pivot.pivot_value import PivotValue, StringPivotValue, DayPivotValue
from utils import checked_type


class PivotFilter:
    def __init__(self, field: PivotField, predicate: Callable[[PivotValue], bool]):
        self.field: PivotField = checked_type(field, PivotField)
        self.predicate: Callable[[PivotValue], bool] = predicate

    def include(self, row: PivotRow):
        assert self.field in row.fields, f"Field {self.field} not in {row.fields}"
        return self.predicate(row.value(self.field))

    @staticmethod
    def value_matches(field: PivotField, value: PivotValue) -> 'PivotFilter':
        def check_value(x: PivotValue):
            if isinstance(x, StringPivotValue):
                print(f"Comparing {x.value} to {value}")
            return x == value
        return PivotFilter(field, check_value)

    @staticmethod
    def date_range_filter(pivot_field: PivotField, dr: DateRange):
        def predicate(x: PivotValue):
            if isinstance(x, DayPivotValue):
                return dr.contains_day(x.value)
            raise ValueError(f"Expected a day pivot value, got {x}")
        return PivotFilter(pivot_field, predicate)