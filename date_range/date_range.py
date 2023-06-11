from abc import ABC, abstractmethod

__all__ = ["DateRange", "ContiguousDateRange"]


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

    @property
    def num_days(self) -> int:
        return self.last_day.days_since(self.first_day) + 1

    @property
    def days(self) -> list['Day']:
        ds = []
        d = self.first_day
        while d <= self.last_day:
            ds.append(d)
            d += 1
        return ds

class ContiguousDateRange(DateRange, ABC):
    @abstractmethod
    def __add__(self, n) -> 'ContiguousDateRange':
        raise NotImplementedError()

    def __sub__(self, n) -> 'ContiguousDateRange':
        return self + (-n)


