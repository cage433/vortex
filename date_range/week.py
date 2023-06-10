from functools import total_ordering

from date_range import ContiguousDateRange, Day
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
class Week(ContiguousDateRange):
    def __init__(self, y: int, week_no: int):
        self.y = checked_type(y, int)
        self.week_no = checked_type(week_no, int)
        if week_no < 1 or week_no > Week.num_weeks_in_accounting_year(y):
            raise ValueError(f"Week number for {y} must be between 1 and {Week.first_monday_of_accounting_year(y)}")

    def __eq__(self, other):
        return isinstance(other, Week) and self.y == other.y and self.week_no == other.week_no

    def __lt__(self, other):
        return self.first_day < other.first_day

    def __add__(self, n) -> 'ContiguousDateRange':
        week_no = self.week_no + n
        y = self.y
        while week_no < 1:
            y -= 1
            week_no += Week.num_weeks_in_accounting_year(y)
        while week_no > Week.num_weeks_in_accounting_year(y):
            week_no -= Week.num_weeks_in_accounting_year(y)
            y += 1
        return Week(y, week_no)

    @property
    def first_day(self):
        return Week.first_monday_of_accounting_year(self.y) + (self.week_no - 1) * 7

    @property
    def last_day(self):
        return self.first_day + 6

    @staticmethod
    def num_weeks_in_accounting_year(y: int) -> int:
        d1 = Week.first_monday_of_accounting_year(y)
        d2 = Week.first_monday_of_accounting_year(y + 1)
        return d2.days_since(d1) // 7

    @staticmethod
    def first_monday_of_accounting_year(y: int) -> Day:
        if y in TIMS_FIRST_MONDAYS_OF_ACCOUNTING_YEAR:
            return TIMS_FIRST_MONDAYS_OF_ACCOUNTING_YEAR[y]
        sep_1 = Day(y - 1, 9, 1)
        return sep_1 - sep_1.weekday
