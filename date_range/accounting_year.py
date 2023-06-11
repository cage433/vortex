from functools import total_ordering

from date_range import DateRange, Day, ContiguousDateRange
from utils import checked_type

TIMS_FIRST_MONDAYS_OF_ACCOUNTING_YEAR = {
    2013: Day(2012, 9, 3),
    2014: Day(2013, 9, 2),
    2015: Day(2014, 9, 1),
    2016: Day(2015, 8, 31),
    2017: Day(2016, 8, 29),
    2018: Day(2017, 8, 28),
    2019: Day(2018, 9, 3),
    2020: Day(2019, 9, 2),
    2021: Day(2020, 8, 31),
    2022: Day(2021, 8, 30),
    2023: Day(2022, 8, 29),
    2024: Day(2023, 9, 4),
}


@total_ordering
class AccountingYear(ContiguousDateRange):
    def __init__(self, y: int):
        self.y = checked_type(y, int)

    @property
    def first_day(self) -> 'Day':
        from date_range.accounting_month import AccountingMonth
        return AccountingMonth(self, 9).first_day

    @property
    def last_day(self) -> 'Day':
        from date_range.accounting_month import AccountingMonth
        return AccountingMonth(self, 8).last_day

    def __eq__(self, other):
        return isinstance(other, AccountingYear) and self.y == other.y

    def __lt__(self, other):
        return self.y < other.y

    def __add__(self, n) -> 'AccountingYear':
        return AccountingYear(self.y + n)

    def __hash__(self):
        return hash(self.y)

    def __str__(self):
        return f"AccYear {self.y}"

    def __repr__(self):
        return str(self)

    @staticmethod
    def first_monday_of_accounting_year(y: int) -> Day:
        if y in TIMS_FIRST_MONDAYS_OF_ACCOUNTING_YEAR:
            return TIMS_FIRST_MONDAYS_OF_ACCOUNTING_YEAR[y]
        sep_1 = Day(y - 1, 9, 1)
        return sep_1 - sep_1.weekday

    @property
    def num_weeks(self) -> int:
        return (self.last_day + 1).days_since(self.first_day) // 7

    @staticmethod
    def containing(day: Day) -> 'AccountingYear':
        year = AccountingYear(day.y)
        if year.contains_day(day):
            return year
        year = year + 1
        assert year.contains_day(day), f"Day {day} is not in an accounting year"
        return year
