from unittest import TestCase

from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from date_range.month import Month
from date_range.tests.fixtures import random_day, random_month, random_week, random_accounting_year, \
    random_accounting_month
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

    @RandomisedTest()
    def test_containing(self, rng):
        month = random_month(rng)
        for day in month.days:
            self.assertEqual(Month.containing(day), month)


class WeekTests(TestCase):
    @RandomisedTest(number_of_runs=10)
    def test_addition(self, rng):
        y = rng.randint(2010, 2030)
        week_no = rng.randint(1, Week.num_weeks_in_accounting_year(y))
        w1 = Week(AccountingYear(y), week_no)
        n = rng.randint(-200, 200)
        w2 = w1 + n
        w3 = w2 - n
        self.assertEqual(w3, w1)

    def test_contiguity(self):
        w = Week(AccountingYear(2017), 1)
        for n in range(1, 1000):
            self.assertEqual(w.last_day + 1, (w + 1).first_day)
            w += 1

    @RandomisedTest()
    def test_containing(self, rng):
        week = random_week(rng)
        for day in week.days:
            self.assertEqual(Week.containing(day), week)


class AccountingYearTests(TestCase):
    @RandomisedTest(number_of_runs=10)
    def test_containing(self, rng):
        year = random_accounting_year(rng)
        for day in year.days:
            self.assertEqual(AccountingYear.containing(day), year)


class AccountingMonthTests(TestCase):
    @RandomisedTest(number_of_runs=10, seed=71102509)
    def test_addition(self, rng):
        am = random_accounting_month(rng)
        n = rng.randint(-20, 20)
        am2 = am + n
        am3 = am2 - n
        self.assertEqual(am3, am)

    def test_contiguity(self):
        am = AccountingMonth(AccountingYear(2010), 1)
        for n in range(1, 200):
            self.assertEqual(am.last_day + 1, (am + 1).first_day)
            am += 1

    @RandomisedTest(seed=12987897)
    def test_containing(self, rng):
        month = random_accounting_month(rng)
        for day in month.days:
            self.assertEqual(AccountingMonth.containing(day), month)

    def test_explicit_increments(self):
        self.assertEqual(AccountingMonth(AccountingYear(2017), 12) + 1, AccountingMonth(AccountingYear(2018), 1))
        self.assertEqual(AccountingMonth(AccountingYear(2018), 1) - 1, AccountingMonth(AccountingYear(2017), 12))
        self.assertEqual(AccountingMonth(AccountingYear(2018), 12) + 1, AccountingMonth(AccountingYear(2019), 1))
        self.assertEqual(AccountingMonth(AccountingYear(2018), 1) - 1, AccountingMonth(AccountingYear(2017), 12))

    @RandomisedTest(number_of_runs=10)
    def test_weeks(self, rng):
        am = random_accounting_month(rng)
        weeks = am.weeks
        self.assertEqual(weeks[0].first_day, am.first_day)
        self.assertEqual(weeks[-1].last_day, am.last_day)
        for w0, w1 in zip(weeks, weeks[1:]):
            self.assertEqual(w0.last_day + 1, w1.first_day)
