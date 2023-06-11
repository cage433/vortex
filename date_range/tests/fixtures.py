from typing import Optional

from date_range import Day, DateRange
from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from date_range.month import Month
from date_range.week import Week
from utils import RandomNumberGenerator

__all__ = [
    "random_day",
]


def random_day(
        rng: RandomNumberGenerator,
        first_day_inclusive: Optional[Day] = None,
        last_day_inclusive: Optional[Day] = None,
        containing_range: Optional[DateRange] = None
) -> Day:
    if containing_range is not None:
        assert first_day_inclusive is None and last_day_inclusive is None, "first/last or containing only"
        first_day_inclusive = containing_range.first_day
        last_day_inclusive = containing_range.last_day

    if first_day_inclusive is not None and last_day_inclusive is not None:
        return first_day_inclusive + \
            rng.randint((last_day_inclusive.days_since(first_day_inclusive)) + 1)
    if first_day_inclusive is not None:
        return first_day_inclusive + rng.randint(1000)
    if last_day_inclusive is not None:
        return last_day_inclusive - rng.randint(1000)
    return random_day(rng, first_day_inclusive=Day(2010, 1, 1), last_day_inclusive=Day(2030, 12, 31))


def random_month(rng: RandomNumberGenerator) -> Month:
    return Month.containing(random_day(rng))


def random_week(rng: RandomNumberGenerator) -> Week:
    return Week.containing(random_day(rng))


def random_accounting_month(rng: RandomNumberGenerator) -> AccountingMonth:
    return AccountingMonth.containing(random_day(rng))


def random_accounting_year(rng: RandomNumberGenerator) -> AccountingYear:
    return AccountingYear.containing(random_day(rng))
