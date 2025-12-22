from vortex.date_range import DateRange, Day
from vortex.utils import checked_type


class Year(DateRange):
    def __init__(self, y: int):
        self.y: int = checked_type(y, int)

    @property
    def first_day(self) -> 'Day':
        return Day(self.y, 1, 1)

    @property
    def last_day(self) -> 'Day':
        return Day(self.y, 12, 31)