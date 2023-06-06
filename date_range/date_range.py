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
