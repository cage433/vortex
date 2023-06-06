from contextlib import redirect_stdout
from io import StringIO
from unittest import TestCase

import numpy as np

from testing_utils import SeedGenerator, RandomisedTest


class RandomisedTestCase(TestCase):

    def test_seed_gen_creates_reproducible_seeds(self):
        seed_gen1 = SeedGenerator(12345)
        seeds1 = []

        seed_gen2 = SeedGenerator(12345)
        seeds2 = []

        seed_gen3 = SeedGenerator(54321)
        seeds3 = []

        @RandomisedTest(number_of_runs=100, seed_gen=seed_gen1)
        def f1(rng):
            seeds1.append(rng.randint(10))

        @RandomisedTest(number_of_runs=100, seed_gen=seed_gen2)
        def f2(rng):
            seeds2.append(rng.randint(10))

        @RandomisedTest(number_of_runs=100, seed_gen=seed_gen3)
        def f3(rng):
            seeds3.append(rng.randint(10))

        f1()
        f2()
        f3()

        self.assertEqual(seeds1, seeds2)
        self.assertNotEqual(seeds1, seeds3)

    @RandomisedTest(number_of_runs=100)
    def test_random_choice(self, rng):
        choices = [1, 2, 3]
        self.assertIn(rng.choice(choices), choices)
        self.assertIn(rng.choice(*choices), choices)
        self.assertIn(rng.choice(1, 2, 3), choices)

    @RandomisedTest(number_of_runs=100, num_allowed_failures=3)
    def test_num_allowed_failures(self, rng):
        """Shows typical use of num_allowed_failures. When results are random, but we have an idea of the distribution
        they come from, then we can assert (e.g.) the sample mean is with in a number of standard errors of the expected
        mean
        This will fail (hopefully rarely), however if we increase the number of allowed failures then we can make the
        chance of a false negative astronomically small.
        """

        np.random.seed(rng.randint(100000))
        N = 100
        array = np.random.normal(size=N)
        std_err = 1.0 / np.sqrt(N)

        # These will fail roughly one in every 30000 runs, the chances of getting more than three failures out of 100 runs
        # is of the order of 1e-12
        self.assertLessEqual(array.mean(), 4.0 * std_err)
        self.assertLessEqual(-4.0 * std_err, array.mean())

    def test_fails_after_breaching_allowed_failure_limit(self):
        @RandomisedTest(number_of_runs=10, num_allowed_failures=5)
        def test_should_fail(rng):
            self.assertEqual(1, 2)

        stream = StringIO()
        with redirect_stdout(stream):
            with self.assertRaises(AssertionError):
                test_should_fail()
            self.assertTrue(stream.getvalue())
