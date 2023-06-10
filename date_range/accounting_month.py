from date_range import ContiguousDateRange
from date_range.month import Month
from utils import checked_type


class AccountingMonth(ContiguousDateRange):
    def __init__(self, y: int, m: int):
        self.y = checked_type(y, int)
        self.m = checked_type(m, int)

    def __add__(self, n) -> 'ContiguousDateRange':
        cal_month = Month(self.y, self.m) + n
        return AccountingMonth(cal_month.y, cal_month.m)

    @property
    def first_day(self) -> 'Day':
        pass

    @property
    def last_day(self) -> 'Day':
        pass

