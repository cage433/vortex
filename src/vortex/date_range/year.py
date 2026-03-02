from vortex.date_range import DateRange, Day, ContiguousDateRange
from vortex.utils import checked_type


class Year(ContiguousDateRange):
    def __init__(self, y: int):
        self.y: int = checked_type(y, int)

    def __add__(self, n) -> 'Year':
        return Year(self.y + n)

    @property
    def excel_format(self) -> str:
        return f"Year {self.y}"

    @property
    def first_day(self) -> 'Day':
        return Day(self.y, 1, 1)

    @property
    def last_day(self) -> 'Day':
        return Day(self.y, 12, 31)

    @staticmethod
    def containing(day: Day):
        return Year(day.y)