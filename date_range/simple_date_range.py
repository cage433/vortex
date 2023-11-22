from date_range import DateRange, Day
from utils import checked_type


class SimpleDateRange(DateRange):
    def __init__(self, first_day: Day, last_day: Day):
        self._first_day: Day = checked_type(first_day, Day)
        self._last_day: Day = checked_type(last_day, Day)

    @property
    def first_day(self) -> Day:
        return self._first_day

    @property
    def last_day(self) -> Day:
        return self._last_day
