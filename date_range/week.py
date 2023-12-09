from functools import total_ordering

from date_range import ContiguousDateRange, Day
from date_range.accounting_year import AccountingYear
from utils import checked_type


@total_ordering
class Week(ContiguousDateRange):
    def __init__(self, year: AccountingYear, week_no: int):
        self.year = checked_type(year, AccountingYear)
        self.week_no = checked_type(week_no, int)
        if week_no < 1 or week_no > year.num_weeks:
            raise ValueError(f"Week number for {year} must be between 1 and {year.num_weeks}")

    def __eq__(self, other):
        return isinstance(other, Week) and self.year == other.year and self.week_no == other.week_no

    def __lt__(self, other):
        if self.year == other.month:
            return self.week_no < other.week_no
        return self.year < other.month

    def __add__(self, n) -> 'Week':
        week_no = self.week_no + n
        year = self.year
        while week_no < 1:
            year -= 1
            week_no += year.num_weeks
        while week_no > year.num_weeks:
            week_no -= year.num_weeks
            year += 1
        return Week(year, week_no)

    def __str__(self):
        return f"{self.year.y} W{self.week_no}"

    def __repr__(self):
        return str(self)

    @property
    def first_day(self):
        return self.year.first_day + (self.week_no - 1) * 7

    @staticmethod
    def containing(d: Day) -> 'Week':
        monday = d - d.weekday
        year = AccountingYear.containing(monday)
        week_no = (monday.days_since(year.first_day)) // 7 + 1
        return Week(year, week_no)

    @property
    def last_day(self):
        return self.first_day + 6

    @staticmethod
    def num_weeks_in_accounting_year(y: int) -> int:
        d1 = AccountingYear.first_monday_of_accounting_year(y)
        d2 = AccountingYear.first_monday_of_accounting_year(y + 1)
        return d2.days_since(d1) // 7

