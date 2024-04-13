from abc import ABC, abstractmethod

__all__ = ["DateRange", "ContiguousDateRange"]

from enum import Enum
from typing import List, Optional


class SplitType(Enum):
    EXACT = 0
    OUTER = 1
    INNER = 2


class DateRange(ABC):
    @property
    @abstractmethod
    def first_day(self) -> 'Day':
        raise NotImplementedError()

    @property
    @abstractmethod
    def last_day(self) -> 'Day':
        raise NotImplementedError()

    def contains_day(self, day: 'Day') -> bool:
        return self.first_day <= day <= self.last_day

    def contains(self, period: 'DateRange') -> bool:
        return self.first_day <= period.first_day and period.last_day <= self.last_day

    @property
    def num_days(self) -> int:
        return self.last_day.days_since(self.first_day) + 1

    def intersection(self, rhs: 'DateRange') -> 'Optional[DateRange]':
        from date_range.simple_date_range import SimpleDateRange
        first_day = max(self.first_day, rhs.first_day)
        last_day = min(self.last_day, rhs.last_day)
        if first_day > last_day:
            return None
        return SimpleDateRange(first_day, last_day)

    @property
    def days(self) -> list['Day']:
        ds = []
        d = self.first_day
        while d <= self.last_day:
            ds.append(d)
            d += 1
        return ds

    def split_into(self, period_type, split_type: SplitType) -> List['DateRange']:
        c = period_type.containing(self.first_day)
        split = [c]
        while c.last_day < self.last_day:
            c += 1
            split.append(c)

        if split_type == SplitType.OUTER:
            return split
        if split_type == SplitType.EXACT:
            return [c.intersection(self) for c in split]
        if split_type == SplitType.INNER:
            return [c for c in split if self.contains(c)]

        raise ValueError(f"Unknown split type: {split_type}")


class ContiguousDateRange(DateRange, ABC):
    @abstractmethod
    def __add__(self, n) -> 'ContiguousDateRange':
        raise NotImplementedError()

    def __sub__(self, n) -> 'ContiguousDateRange':
        return self + (-n)
