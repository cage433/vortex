from datetime import date
from functools import total_ordering
from typing import List

from date_range import Day
from date_range.date_range import ContiguousDateRange
from date_range.month import Month
from utils import checked_type


@total_ordering
class Quarter(ContiguousDateRange):
    def __init__(self, y: int, q: int):
        self.y: int = checked_type(y, int)
        self.q: int = checked_type(q, int)
        if self.q < 1 or self.q > 4:
            raise ValueError(f"Quarter number must be between 1 and 4, not {q}")

    def __eq__(self, other):
        return isinstance(other, Quarter) and self.y == other.y and self.q == other.q

    def __lt__(self, other):
        return self.y < other.y or (self.y == other.y and self.q < other.q)

    def __add__(self, n: int) -> 'Quarter':
        y = self.y
        q = self.q + n
        while q < 1:
            q += 4
            y -= 1
        while q > 4:
            q -= 4
            y += 1
        return Quarter(y, q)

    @property
    def first_month(self) -> Month:
        return Month(self.y, 3 * self.q - 2)

    @property
    def last_month(self) -> Month:
        return self.first_month + 2

    @property
    def months(self) -> 'List[Month]':
        return [self.first_month, self.first_month + 1, self.first_month + 2]

    @property
    def first_day(self) -> 'Day':
        return self.first_month.first_day

    @property
    def last_day(self) -> 'Day':
        return self.last_month.last_day

    def __str__(self):
        return self.tab_name

    def __repr__(self):
        return self.tab_name

    @property
    def tab_name(self):
        return f"Q{self.q}-{self.y % 100}"

    @staticmethod
    def containing(day: Day) -> 'Quarter':
        m = Month.containing(day)
        return Quarter(day.y, (m.m - 1) // 3 + 1)

