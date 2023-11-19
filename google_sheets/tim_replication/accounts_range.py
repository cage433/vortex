from typing import Callable, List

from airtable_db.contracts_and_events import GigsInfo
from date_range import DateRange
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type, checked_list_type


class AccountsRange(TabRange):
    def __init__(self,
                 top_left_cell: TabCell, num_rows: int,
                 sub_periods: List[DateRange],
                 sub_period_titles: List[any],
                 gigs_info: GigsInfo):
        super().__init__(top_left_cell, num_rows, len(sub_periods) + 2)
        if len(sub_periods) == 0:
            raise ValueError("Must have at least one sub-period")
        self.sub_periods: List[DateRange] = checked_list_type(sub_periods, DateRange)
        self.sub_period_titles: List[any] = sub_period_titles
        if len(sub_periods) != len(sub_period_titles):
            raise ValueError("Must have same number of sub-periods and sub-period titles")
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.num_sub_periods: int = len(self.sub_periods)
        self.gigs_by_sub_period: list[GigsInfo] = [self.gigs_info.restrict_to_period(w) for w in self.sub_periods]

    def sub_period_gigs_row(self, gig_func: Callable[[GigsInfo], int]) -> list[any]:
        return [gig_func(gigs) for gigs in self.gigs_by_sub_period]
