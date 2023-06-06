from datetime import date, timedelta
from functools import total_ordering

from date_range.date_range import DateRange

__all__ = ["Day"]


@total_ordering
class Day(DateRange):
    def __init__(self, y: int, m: int, d: int):
        self._date: date = date(y, m, d)

    @property
    def first_day(self) -> 'Day':
        return self

    @property
    def last_day(self) -> 'Day':
        return self

    def __eq__(self, other: 'Day') -> bool:
        return isinstance(other, Day) and self._date == other._date

    def __lt__(self, other: 'Day') -> bool:
        return self._date < other._date

    def __add__(self, n) -> 'Day':
        return Day.from_date(self._date + timedelta(n))

    @staticmethod
    def from_date(d: date) -> 'Day':
        return Day(d.year, d.month, d.day)

    def __sub__(self, n) -> 'Day':
        return self + (-n)

    def days_since(self, rhs: 'Day') -> int:
        return (self._date - rhs._date).days
