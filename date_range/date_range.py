from abc import ABC, abstractmethod

__all__ = ["DateRange"]


class DateRange(ABC):
    @property
    @abstractmethod
    def first_day(self) -> 'Day':
        raise NotImplementedError()

    @property
    @abstractmethod
    def last_day(self) -> 'Day':
        raise NotImplementedError()


class ContiguousDateRange(DateRange, ABC):
    @abstractmethod
    def __add__(self, n) -> 'ContiguousDateRange':
        raise NotImplementedError()

    def __sub__(self, n) -> 'ContiguousDateRange':
        return self + (-n)
