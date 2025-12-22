from functools import total_ordering

from date_range import ContiguousDateRange
from date_range import Day
from date_range.accounting_year import AccountingYear
from date_range.month import Month
from utils import checked_type


@total_ordering
class AccountingMonth(ContiguousDateRange):
    # First month of the accounting year is September
    def __init__(self, year: AccountingYear, m: int):
        self.year: AccountingYear = checked_type(year, AccountingYear)
        self.m: int = checked_type(m, int)

    def __eq__(self, other):
        return isinstance(other, AccountingMonth) and self.year == other.year and self.m == other.m

    def __lt__(self, other):
        assert isinstance(other, AccountingMonth), f"Cannot compare {self} to {other}"
        return self.first_day < other.first_day

    def __add__(self, n) -> 'AccountingMonth':
        y = self.year.y
        m = self.m + n
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        return AccountingMonth(AccountingYear(y), m)

    def __hash__(self):
        return hash((self.year, self.m))

    def __str__(self):
        return self.month_name

    def months_since(self, other: 'AccountingMonth') -> int:
        return (self.year.y - other.year.y) * 12 + self.m - other.m

    @property
    def month_name(self):
        return self.corresponding_calendar_month.month_name

    def __repr__(self):
        return str(self)

    @property
    def first_day(self) -> 'Day':
        if self in TIMS_FIRST_DAY_OF_ACCOUNTING_MONTH:
            return TIMS_FIRST_DAY_OF_ACCOUNTING_MONTH[self]
        calendar_month = self.corresponding_calendar_month
        return calendar_month.first_day - calendar_month.first_day.weekday

    @property
    def last_day(self) -> 'Day':
        return (self + 1).first_day - 1

    @property
    def tab_name(self):
        return self.corresponding_calendar_month.first_day.date.strftime("%b %y")

    @property
    def corresponding_calendar_month(self) -> 'Month':
        m1 = Month(self.year.y - 1, 9)
        return m1 + self.m - 1

    @staticmethod
    def from_calendar_month(month: Month):
        if month.m >= 9:
            return AccountingMonth(AccountingYear(month.y + 1), month.m - 8)
        return AccountingMonth(AccountingYear(month.y), month.m + 4)

    @property
    def weeks(self) -> list['Week']:
        from date_range.week import Week
        ws = []
        w = Week.containing(self.first_day)
        while w.last_day <= self.last_day:
            ws.append(w)
            w += 1
        return ws

    @property
    def num_weeks(self):
        return len(self.weeks)

    @staticmethod
    def containing(day: Day) -> 'AccountingMonth':
        calendar_month = Month.containing(day)
        accounting_month = AccountingMonth.from_calendar_month(calendar_month)
        if accounting_month.last_day < day:
            return accounting_month + 1
        if accounting_month.first_day > day:
            return accounting_month - 1
        return accounting_month


TIMS_FIRST_DAY_OF_ACCOUNTING_MONTH = {

    AccountingMonth(AccountingYear(2013), 1): Day(2012, 9, 3),
    AccountingMonth(AccountingYear(2013), 2): Day(2012, 10, 1),
    AccountingMonth(AccountingYear(2013), 3): Day(2012, 10, 29),
    AccountingMonth(AccountingYear(2013), 4): Day(2012, 11, 26),
    AccountingMonth(AccountingYear(2013), 5): Day(2012, 12, 31),
    AccountingMonth(AccountingYear(2013), 6): Day(2013, 1, 28),
    AccountingMonth(AccountingYear(2013), 7): Day(2013, 2, 25),
    AccountingMonth(AccountingYear(2013), 8): Day(2013, 4, 1),
    AccountingMonth(AccountingYear(2013), 9): Day(2013, 4, 29),
    AccountingMonth(AccountingYear(2013), 10): Day(2013, 5, 27),
    AccountingMonth(AccountingYear(2013), 11): Day(2013, 7, 1),
    AccountingMonth(AccountingYear(2013), 12): Day(2013, 7, 29),

    AccountingMonth(AccountingYear(2014), 1): Day(2013, 9, 2),
    AccountingMonth(AccountingYear(2014), 2): Day(2013, 9, 30),
    AccountingMonth(AccountingYear(2014), 3): Day(2013, 10, 28),
    AccountingMonth(AccountingYear(2014), 4): Day(2013, 11, 25),
    AccountingMonth(AccountingYear(2014), 5): Day(2013, 12, 30),
    AccountingMonth(AccountingYear(2014), 6): Day(2014, 1, 27),
    AccountingMonth(AccountingYear(2014), 7): Day(2014, 2, 24),
    AccountingMonth(AccountingYear(2014), 8): Day(2014, 3, 31),
    AccountingMonth(AccountingYear(2014), 9): Day(2014, 4, 28),
    AccountingMonth(AccountingYear(2014), 10): Day(2014, 5, 26),
    AccountingMonth(AccountingYear(2014), 11): Day(2014, 6, 30),
    AccountingMonth(AccountingYear(2014), 12): Day(2014, 7, 28),

    AccountingMonth(AccountingYear(2015), 1): Day(2014, 9, 1),
    AccountingMonth(AccountingYear(2015), 2): Day(2014, 9, 29),
    AccountingMonth(AccountingYear(2015), 3): Day(2014, 10, 27),
    AccountingMonth(AccountingYear(2015), 4): Day(2014, 11, 24),
    AccountingMonth(AccountingYear(2015), 5): Day(2014, 12, 29),
    AccountingMonth(AccountingYear(2015), 6): Day(2015, 1, 26),
    AccountingMonth(AccountingYear(2015), 7): Day(2015, 3, 2),
    AccountingMonth(AccountingYear(2015), 8): Day(2015, 3, 30),
    AccountingMonth(AccountingYear(2015), 9): Day(2015, 4, 27),
    AccountingMonth(AccountingYear(2015), 10): Day(2015, 6, 1),
    AccountingMonth(AccountingYear(2015), 11): Day(2015, 6, 29),
    AccountingMonth(AccountingYear(2015), 12): Day(2015, 8, 3),

    AccountingMonth(AccountingYear(2016), 1): Day(2015, 8, 31),
    AccountingMonth(AccountingYear(2016), 2): Day(2015, 9, 28),
    AccountingMonth(AccountingYear(2016), 3): Day(2015, 11, 2),
    AccountingMonth(AccountingYear(2016), 4): Day(2015, 11, 30),
    AccountingMonth(AccountingYear(2016), 5): Day(2015, 12, 28),
    AccountingMonth(AccountingYear(2016), 6): Day(2016, 2, 1),
    AccountingMonth(AccountingYear(2016), 7): Day(2016, 2, 29),
    AccountingMonth(AccountingYear(2016), 8): Day(2016, 3, 28),
    AccountingMonth(AccountingYear(2016), 9): Day(2016, 5, 2),
    AccountingMonth(AccountingYear(2016), 10): Day(2016, 5, 30),
    AccountingMonth(AccountingYear(2016), 11): Day(2016, 6, 27),
    AccountingMonth(AccountingYear(2016), 12): Day(2016, 8, 1),

    AccountingMonth(AccountingYear(2017), 1): Day(2016, 8, 29),
    AccountingMonth(AccountingYear(2017), 2): Day(2016, 9, 26),
    AccountingMonth(AccountingYear(2017), 3): Day(2016, 10, 31),
    AccountingMonth(AccountingYear(2017), 4): Day(2016, 11, 28),
    AccountingMonth(AccountingYear(2017), 5): Day(2017, 1, 2),
    AccountingMonth(AccountingYear(2017), 6): Day(2017, 1, 30),
    AccountingMonth(AccountingYear(2017), 7): Day(2017, 2, 27),
    AccountingMonth(AccountingYear(2017), 8): Day(2017, 3, 27),
    AccountingMonth(AccountingYear(2017), 9): Day(2017, 5, 1),
    AccountingMonth(AccountingYear(2017), 10): Day(2017, 5, 29),
    AccountingMonth(AccountingYear(2017), 11): Day(2017, 6, 26),
    AccountingMonth(AccountingYear(2017), 12): Day(2017, 7, 31),

    AccountingMonth(AccountingYear(2018), 1): Day(2017, 8, 28),
    AccountingMonth(AccountingYear(2018), 2): Day(2017, 10, 2),
    AccountingMonth(AccountingYear(2018), 3): Day(2017, 10, 30),
    AccountingMonth(AccountingYear(2018), 4): Day(2017, 11, 27),
    AccountingMonth(AccountingYear(2018), 5): Day(2018, 1, 1),
    AccountingMonth(AccountingYear(2018), 6): Day(2018, 1, 29),
    AccountingMonth(AccountingYear(2018), 7): Day(2018, 2, 26),
    AccountingMonth(AccountingYear(2018), 8): Day(2018, 3, 26),
    AccountingMonth(AccountingYear(2018), 9): Day(2018, 4, 30),
    AccountingMonth(AccountingYear(2018), 10): Day(2018, 5, 28),
    AccountingMonth(AccountingYear(2018), 11): Day(2018, 7, 2),
    AccountingMonth(AccountingYear(2018), 12): Day(2018, 7, 30),

    AccountingMonth(AccountingYear(2019), 1): Day(2018, 9, 3),
    AccountingMonth(AccountingYear(2019), 2): Day(2018, 10, 1),
    AccountingMonth(AccountingYear(2019), 3): Day(2018, 10, 29),
    AccountingMonth(AccountingYear(2019), 4): Day(2018, 12, 3),
    AccountingMonth(AccountingYear(2019), 5): Day(2018, 12, 31),
    AccountingMonth(AccountingYear(2019), 6): Day(2019, 1, 28),
    AccountingMonth(AccountingYear(2019), 7): Day(2019, 2, 25),
    AccountingMonth(AccountingYear(2019), 8): Day(2019, 4, 1),
    AccountingMonth(AccountingYear(2019), 9): Day(2019, 4, 29),
    AccountingMonth(AccountingYear(2019), 10): Day(2019, 5, 27),
    AccountingMonth(AccountingYear(2019), 11): Day(2019, 7, 1),
    AccountingMonth(AccountingYear(2019), 12): Day(2019, 7, 29),

    AccountingMonth(AccountingYear(2020), 1): Day(2019, 9, 2),
    AccountingMonth(AccountingYear(2020), 2): Day(2019, 9, 30),
    AccountingMonth(AccountingYear(2020), 3): Day(2019, 11, 4),
    AccountingMonth(AccountingYear(2020), 4): Day(2019, 12, 2),
    AccountingMonth(AccountingYear(2020), 5): Day(2019, 12, 30),
    AccountingMonth(AccountingYear(2020), 6): Day(2020, 2, 3),
    AccountingMonth(AccountingYear(2020), 7): Day(2020, 3, 2),
    AccountingMonth(AccountingYear(2020), 8): Day(2020, 3, 30),
    AccountingMonth(AccountingYear(2020), 9): Day(2020, 5, 4),
    AccountingMonth(AccountingYear(2020), 10): Day(2020, 6, 1),
    AccountingMonth(AccountingYear(2020), 11): Day(2020, 6, 29),
    AccountingMonth(AccountingYear(2020), 12): Day(2020, 8, 3),

    AccountingMonth(AccountingYear(2021), 1): Day(2020, 8, 31),
    AccountingMonth(AccountingYear(2021), 2): Day(2020, 9, 28),
    AccountingMonth(AccountingYear(2021), 3): Day(2020, 11, 2),
    AccountingMonth(AccountingYear(2021), 4): Day(2020, 11, 30),
    AccountingMonth(AccountingYear(2021), 5): Day(2020, 12, 28),
    AccountingMonth(AccountingYear(2021), 6): Day(2021, 2, 1),
    AccountingMonth(AccountingYear(2021), 7): Day(2021, 3, 1),
    AccountingMonth(AccountingYear(2021), 8): Day(2021, 3, 29),
    AccountingMonth(AccountingYear(2021), 9): Day(2021, 4, 26),
    AccountingMonth(AccountingYear(2021), 10): Day(2021, 5, 31),
    AccountingMonth(AccountingYear(2021), 11): Day(2021, 6, 28),
    AccountingMonth(AccountingYear(2021), 12): Day(2021, 8, 2),

    AccountingMonth(AccountingYear(2022), 1): Day(2021, 8, 30),
    AccountingMonth(AccountingYear(2022), 2): Day(2021, 9, 27),
    AccountingMonth(AccountingYear(2022), 3): Day(2021, 11, 1),
    AccountingMonth(AccountingYear(2022), 4): Day(2021, 11, 29),
    AccountingMonth(AccountingYear(2022), 5): Day(2022, 1, 3),
    AccountingMonth(AccountingYear(2022), 6): Day(2022, 1, 31),
    AccountingMonth(AccountingYear(2022), 7): Day(2022, 2, 28),
    AccountingMonth(AccountingYear(2022), 8): Day(2022, 3, 28),
    AccountingMonth(AccountingYear(2022), 9): Day(2022, 5, 2),
    AccountingMonth(AccountingYear(2022), 10): Day(2022, 5, 30),
    AccountingMonth(AccountingYear(2022), 11): Day(2022, 7, 4),
    AccountingMonth(AccountingYear(2022), 12): Day(2022, 8, 1),

    AccountingMonth(AccountingYear(2023), 1): Day(2022, 8, 29),
    AccountingMonth(AccountingYear(2023), 2): Day(2022, 10, 3),
    AccountingMonth(AccountingYear(2023), 3): Day(2022, 10, 31),
    AccountingMonth(AccountingYear(2023), 4): Day(2022, 11, 28),
    AccountingMonth(AccountingYear(2023), 5): Day(2023, 1, 2),
    AccountingMonth(AccountingYear(2023), 6): Day(2023, 1, 30),
    AccountingMonth(AccountingYear(2023), 7): Day(2023, 2, 27),
    AccountingMonth(AccountingYear(2023), 8): Day(2023, 3, 27),
    AccountingMonth(AccountingYear(2023), 9): Day(2023, 5, 1),
    AccountingMonth(AccountingYear(2023), 10): Day(2023, 5, 29),
    AccountingMonth(AccountingYear(2023), 11): Day(2023, 7, 3),
    AccountingMonth(AccountingYear(2023), 12): Day(2023, 7, 31),

    AccountingMonth(AccountingYear(2024), 1): Day(2023, 9, 4),
    AccountingMonth(AccountingYear(2024), 2): Day(2023, 10, 2),
    AccountingMonth(AccountingYear(2024), 3): Day(2023, 10, 30),
    AccountingMonth(AccountingYear(2024), 4): Day(2023, 12, 4),
    AccountingMonth(AccountingYear(2024), 5): Day(2024, 1, 1),
    AccountingMonth(AccountingYear(2024), 6): Day(2024, 1, 29),
    AccountingMonth(AccountingYear(2024), 7): Day(2024, 3, 4),
    AccountingMonth(AccountingYear(2024), 8): Day(2024, 4, 1),
}
