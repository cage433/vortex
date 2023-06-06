from date_range import DateRange, Day
from utils import checked_type


class Month(DateRange):
    def __init__(self, y: int, m: int):
        self.y: int = checked_type(y, int)
        self.m: int = checked_type(m, int)

    def __add__(self, n: int) -> 'Month':
        y = self.y
        m = self.m + n
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        return Month(y, m)

    @property
    def first_day(self) -> 'Day':
        return Day(self.y, self.m, 1)

    @property
    def last_day(self) -> 'Day':
        return (self + 1).first_day - 1

