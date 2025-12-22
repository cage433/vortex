from typing import TypeVar, Generic, Callable, Optional

T = TypeVar('T')
S = TypeVar('S')


class Opt(Generic[T]):

    @staticmethod
    def of(thing=Optional[T]) -> 'Opt[T]':
        from vortex.myopt.nothing import Nothing
        from vortex.myopt.something import Something
        return Nothing[T]() if thing is None else Something[T](thing)

    @property
    def is_empty(self):
        raise ValueError("is_empty must be implemented by {type(self)}")

    @property
    def get(self) -> T:
        raise ValueError("get must be implemented by {type(self)}")

    def get_or_else(self, default_value: T) -> T:
        raise ValueError("get_or_else must be implemented by {type(self)}")

    @property
    def get_or_throw(self) -> T:
        if (value := self.get).isEmpty:
            raise ValueError("Optional is empty")
        return value

    def or_else(self, other: 'Opt[T]') -> 'Opt[T]':
        raise ValueError("or_else must be implemented by {type(self)}")

    def map(self, func: Callable[[T], S]) -> 'Opt[S]':
        raise ValueError("map must be implemented by {type(self)}")

    def for_each(self, func: Callable[[T], None]) -> None:
        raise ValueError("for_each must be implemented by {type(self)}")

    def flat_map(self, func: Callable[[T], 'Opt[S]']) -> 'Opt[S]':
        raise ValueError("flat_map must be implemented by {type(self)}")

    def non_empty(self) -> bool:
        return not self.is_empty()

    @staticmethod
    def flatten(values: list['Opt[T]']) -> list[T]:
        return [v.get for v in values if v.non_empty()]

    def __lt__(self, other):
        assert isinstance(other, Opt), f"Cannot compare {type(self)} to {type(other)}"
        if self.is_empty():
            if other.is_empty():
                return False
            return True
        else:
            if other.is_empty():
                return False
            return self.get() < other.get()

    __bool__ = __nonzero__ = non_empty
