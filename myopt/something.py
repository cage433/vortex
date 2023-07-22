from typing import TypeVar, Generic, Callable

from .opt import Opt
from .exceptions import FlatMapFunctionDoesNotReturnOptionalException

T = TypeVar('T')
S = TypeVar('S')

class Something(Opt, Generic[T]):
    def __init__(self, value):
        if value is None:
            raise ValueError('Invalid value for Something: None')

        self.__value = value
        self._hash = hash(value)

    def is_empty(self) -> bool:
        return False

    def get(self) -> T:
        return self.__value

    def get_or_else(self, default_value):
        return self.get()

    def or_else(self, other: Opt[T]):
        return self

    def map(self, func: Callable[[T], S]) -> Opt[S]:
        return Something(func(self.get()))

    def for_each(self, func: Callable[[T], None]) -> None:
        func(self.get())

    def flat_map(self, func: Callable[[T], Opt[S]]) -> Opt[S]:
        res = func(self.get())
        if not isinstance(res, Opt):
            raise FlatMapFunctionDoesNotReturnOptionalException(
                f"Mapping function to flat_map must return Optional., got [{res}] of type {type(res)}"
            )

        return res

    def __eq__(self, other):
        return isinstance(other, Something) and self.get() == other.get()

    def __repr__(self):
        return 'Optional.of({!r})'.format(self.get())

    def __hash__(self):
        return self._hash