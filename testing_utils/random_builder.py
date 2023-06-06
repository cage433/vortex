from abc import abstractmethod, ABCMeta
from typing import Callable

from utils.random_number_generator import RandomNumberGenerator

__all__ = [
    "UNSET",
    "RandomBuilder",
]


class _UnsetRandomBuilderVariable:
    """
    Initial state for random builder parameters. A builder will fail if any of its
    parameters are left in this state

    Note that we couldn't use 'None' for this purpose, as that might be a valid parameter value
    """
    def __str__(self):
        return "UNSET"

    def __repr__(self):
        return str(self)


UNSET = _UnsetRandomBuilderVariable()


class RandomBuilder(metaclass=ABCMeta):

    @classmethod
    def _property(cls, var_name):
        return property(
            fset=lambda obj, new_value: obj._setter_for(var_name)(new_value),
            fget=lambda obj: obj._getter_for(var_name)(),
        )

    def _setter_for(self, var_name):
        def setter_func(new_value):
            if new_value == UNSET:
                attr_name = f"_{var_name}"
                setattr(self, attr_name, new_value)
            else:
                setter_name = f"set_{var_name}"
                assert hasattr(self, setter_name), f"{type(self)} has no method {setter_name}"

                getattr(self, setter_name)(new_value)
            return self

        return setter_func

    def _getter_for(self, var_name):
        """
        Returns a function that takes an abject, and returns the property associated with
        var_name, asserting that it has been set
        """

        def getter_func():
            attr_name = f"_{var_name}"
            assert hasattr(self, attr_name), f"Variable {var_name} is unset "
            value = getattr(self, attr_name)
            # Can't use equality testing as numpy arrays are a little weird with that
            assert not isinstance(value, _UnsetRandomBuilderVariable), f"Variable {var_name} is unset"
            return value

        return getter_func

    def set_remaining_values(self, rng):
        for var_name, var_value in list(vars(self).items()):
            if var_name[0] == "_" and isinstance(var_value, _UnsetRandomBuilderVariable):
                self._setter_for(var_name[1:])(rng)
        return self

    @staticmethod
    def _if_random(value, func_for_random: Callable[[RandomNumberGenerator], object]):
        if isinstance(value, RandomNumberGenerator):
            return func_for_random(value)
        return value

    def build(self, rng_for_unset_values=None):
        """Return the object we are constructing"""
        if rng_for_unset_values is not None:
            self.set_remaining_values(rng_for_unset_values)
        return self._build()

    @abstractmethod
    def _build(self):
        """Return the object we are constructing"""
