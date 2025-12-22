from unittest import TestCase

from date_range.fixtures import random_day
from vortex.date_range import Day
from testing_utils import RandomisedTest


class RandomNumberGeneratorTestCase(TestCase):

    @RandomisedTest(number_of_runs=100)
    def test_random_date(self, rng):
        first_date = Day(2000, 1, 1)
        last_date = Day(2000, 12, 31)
        rand_date = random_day(rng, first_date, last_date)
        self.assertTrue(first_date <= rand_date <= last_date)  # Bounded inclusively

        rand_date = random_day(rng)
        self.assertIsInstance(rand_date, Day)

    @RandomisedTest(number_of_runs=100)
    def test_choice(self, rng):
        possible_values = ["A", 1, object()]
        choice = rng.choice(possible_values)
        self.assertIn(choice, possible_values)

        choice = rng.choice(*possible_values)  # Alternative style of call
        self.assertIn(choice, possible_values)

    @RandomisedTest(number_of_runs=100)
    def test_maybe(self, rng):
        possible_value = 1
        choice = rng.maybe(possible_value)
        self.assertIn(choice, [possible_value, None])
