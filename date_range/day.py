from datetime import date, timedelta
from functools import total_ordering

from date_range import parse_date
from date_range.date_range import ContiguousDateRange

__all__ = ["Day"]

from utils import checked_type


@total_ordering
class Day(ContiguousDateRange):
    def __init__(self, y: int, m: int, d: int):
        self.y: int = checked_type(y, int)
        self.m: int = checked_type(m, int)
        self.d: int = checked_type(d, int)
        self.date: date = date(y, m, d)


    @property
    def weekday(self) -> int:
        return self.date.weekday()

    @property
    def first_day(self) -> 'Day':
        return self

    @property
    def iso_repr(self) -> str:
        return self.date.isoformat()

    def __str__(self):
        return self.iso_repr

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(self.date)

    @property
    def last_day(self) -> 'Day':
        return self

    def __eq__(self, other: 'Day') -> bool:
        return isinstance(other, Day) and self.date == other.date

    def __lt__(self, other: 'Day') -> bool:
        return self.date < other.date

    def __add__(self, n) -> 'Day':
        return Day.from_date(self.date + timedelta(n))

    @staticmethod
    def from_date(d: date) -> 'Day':
        return Day(d.year, d.month, d.day)

    def days_since(self, rhs: 'Day') -> int:
        return (self.date - rhs.date).days

    @staticmethod
    def parse(text) -> 'Day':
        return Day.from_date(parse_date(text))
