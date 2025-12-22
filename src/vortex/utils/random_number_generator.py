from collections.abc import Iterable
from copy import copy

import numpy as np

__all__ = [
    "RandomNumberGenerator",
]


class RandomNumberGenerator:
    """A wrapper around numpy's `random` with additional methods"""

    def __init__(self, seed):
        self.seed = seed
        self._random = np.random.RandomState(seed)

    def shuffle(self, a):
        b = copy(a)
        self._random.shuffle(b)
        return b

    def choice(self, *a):
        """Can be called with wither a single list, or else a number of arguments"""
        if len(a) == 1 and isinstance(a[0], Iterable):
            choices = list(a[0])
        else:
            choices = a
        return choices[self._random.randint(len(choices))]

    def is_heads(self) -> bool:
        return self._random.randint(2) != 0

    def maybe(self, x):
        return self.choice(x, None)

    def randint(self, n1, n2=None) -> int:
        return self._random.randint(n1, n2)

    def random_seed(self):
        return self.randint(10 * 1000 * 1000)

    def uniform(self, low=0.0, high=1.0):
        return self._random.uniform(low, high)
