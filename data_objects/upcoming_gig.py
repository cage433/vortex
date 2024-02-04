from typing import Optional

from date_range import Day
from utils import checked_type
from utils.type_checks import checked_opt_type


class UpcomingGig:
    def __init__(self, date: Day, door_time: Optional[str], title: str, gig_type: Optional[str]):
        self.date = checked_type(date, Day)
        self.door_time = checked_opt_type(door_time, str)
        self.title = checked_type(title, str)
        self.gig_type = checked_opt_type(gig_type, str)