from typing import TypeVar, Generic, Callable

from .opt import Opt
from .exceptions import OptionalAccessOfEmptyException

T = TypeVar('T')
S = TypeVar('S')


class Nothing(Opt, Generic[T]):
    def __init__(self):
        self._hash = hash(None)

    def is_empty(self) -> bool:
        return True

    def get(self) -> T:
        raise OptionalAccessOfEmptyException(
            "You cannot call get on an empty optional"
        )

    def get_or_else(self, default_value: T) -> T:
        return default_value

    def or_else(self, other: 'Opt[T]') -> 'Opt[T]':
        return other

    def map(self, func: Callable[[T], S]) -> 'Opt[S]':
        return Nothing[S]()

    def flat_map(self, func: Callable[[T], 'Opt[S]']) -> 'Opt[S]':
        return Nothing[S]()

    def for_each(self, func: Callable[[T], None]) -> None:
        pass

    def __eq__(self, other):
        return isinstance(other, Nothing)

    def __repr__(self):
        return 'Optional.empty()'

    def __hash__(self):
        return self._hash
