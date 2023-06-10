from unittest import TestCase

from date_range.month import Month
from date_range.tests.fixtures import random_day, random_month
from date_range.week import Week
from testing_utils import RandomisedTest


class DateRangeTests(TestCase):
    @RandomisedTest(number_of_runs=100)
    def test_addition(self, rng):
        d = random_day(rng)
        n = rng.randint(1, 1000)
        d1 = d + n
        self.assertEqual(d1.days_since(d), n)
        d2 = d1 - n
        self.assertEqual(d2, d)

    @RandomisedTest(number_of_runs=10)
    def test_sort(self, rng):
        n_days = rng.randint(1, 100)
        days = [random_day(rng) for _ in range(n_days)]
        sorted_days = sorted(days)
        for d0, d1 in zip(sorted_days, sorted_days[1:]):
            self.assertLessEqual(d0, d1)


class MonthTests(TestCase):
    def test_tab_name(self):
        m = Month(2023, 4)
        self.assertEqual(m.tab_name, "Apr 23")

    @RandomisedTest(number_of_runs=100)
    def test_addition(self, rng):
        m1 = random_month(rng)
        n = rng.randint(-30, 30)
        m2 = m1 + n
        m3 = m2 - n
        self.assertEqual(m3, m1)


class WeekTests(TestCase):
    @RandomisedTest(number_of_runs=100)
    def test_addition(self, rng):
        y = rng.randint(2010, 2030)
        week_no = rng.randint(1, Week.num_weeks_in_accounting_year(y))
        w1 = Week(y, week_no)
        n = rng.randint(-200, 200)
        w2 = w1 + n
        w3 = w2 - n
        self.assertEqual(w3, w1)
