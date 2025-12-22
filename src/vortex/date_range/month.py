from datetime import date
from functools import total_ordering

from vortex.date_range import Day
from vortex.date_range.date_range import ContiguousDateRange
from vortex.utils import checked_type


@total_ordering
class Month(ContiguousDateRange):
    def __init__(self, y: int, m: int):
        self.y: int = checked_type(y, int)
        self.m: int = checked_type(m, int)

    def __eq__(self, other):
        return isinstance(other, Month) and self.y == other.y and self.m == other.m

    def __lt__(self, other):
        return self.y < other.y or (self.y == other.y and self.m < other.m)

    def __add__(self, n: int) -> 'Month':
        y = self.y
        m = self.m + n
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        return Month(y, m)

    @property
    def first_day(self) -> 'Day':
        return Day(self.y, self.m, 1)

    @property
    def last_day(self) -> 'Day':
        return (self + 1).first_day - 1

    def __str__(self):
        return f"Month({self.y}, {self.m})"

    @property
    def month_name(self):
        return date(self.y, self.m, 1).strftime("%b %y")

    def __hash__(self):
        return hash((self.y, self.m))

    @property
    def tab_name(self):
        return self.month_name

    @staticmethod
    def containing(day: Day) -> 'Month':
        return Month(day.y, day.m)

