from unittest import TestCase

from vortex.testing_utils import RandomisedTest
from vortex.utils.collection_utils import group_into_dict, flatten


class CollectionUtilsTestCase(TestCase):
    @RandomisedTest()
    def test_group_into_dict(self, rng):
        values = [rng.randint(100) for _ in range(1000)]
        grouped = group_into_dict(values, lambda x: x % 10)
        for key, group in grouped.items():
            self.assertEqual(key, group[0] % 10)
            for value in group:
                self.assertEqual(value % 10, key)

    def test_flatten(self):
        self.assertEqual([], flatten([]))
        self.assertEqual([1, 2, 3], flatten([1, 2, 3]))
        self.assertEqual([1, 2, 3], flatten([[1, 2, 3]]))
        self.assertEqual([1, 2, 3], flatten([[1], [2], [3]]))
        self.assertEqual([1, 2, 3], flatten([[], [[1]], [2, 3]]))
