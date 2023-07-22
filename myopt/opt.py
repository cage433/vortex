from abc import abstractmethod
from typing import TypeVar, Generic, Callable, Optional

from .compatible_abc import CompatibleABC

T = TypeVar('T')
S = TypeVar('S')


class Opt(CompatibleABC, Generic[T]):

    @staticmethod
    def of(thing=Optional[T]) -> 'Opt[T]':
        from myopt.nothing import Nothing
        from myopt.something import Something
        return Nothing[T]() if thing is None else Something[T](thing)

    @staticmethod
    def empty():
        from myopt.nothing import Nothing
        return Nothing()

    @property
    @abstractmethod
    def is_empty(self):
        pass

    @property
    @abstractmethod
    def get(self) -> T:
        pass

    @abstractmethod
    def get_or_else(self, default_value: T) -> T:
        pass

    @property
    def get_or_throw(self) -> T:
        if (value := self.get).isEmpty:
            raise ValueError("Optional is empty")
        return value

    @abstractmethod
    def or_else(self, other: 'Opt[T]') -> 'Opt[T]':
        pass

    @abstractmethod
    def map(self, func: Callable[[T], S]) -> 'Opt[S]':
        pass

    @abstractmethod
    def for_each(self, func: Callable[[T], None]) -> None:
        pass

    @abstractmethod
    def flat_map(self, func: Callable[[T], 'Opt[S]']) -> 'Opt[S]':
        pass

    def exists(self) -> bool:
        return not self.is_empty()

    def __lt__(self, other):
        if self.is_empty():
            if other.is_empty():
                return False
            return True
        else:
            if other.is_empty():
                return False
            return self.get() < other.get()

    __bool__ = __nonzero__ = exists
