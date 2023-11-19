from typing import Callable, List

from airtable_db.contracts_and_events import GigsInfo
from date_range import DateRange
from google_sheets.tab_range import TabRange, TabCell
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type, checked_list_type


class AccountsRange(TabRange):
    (TITLE, _, SUB_PERIOD, TOTAL) = range(4)

    def __init__(self,
                 top_left_cell: TabCell, num_rows: int,
                 sub_periods: List[DateRange],
                 sub_period_titles: List[any],
                 gigs_info: GigsInfo,
                 nominal_ledger: NominalLedger = None
                 ):
        super().__init__(top_left_cell, num_rows, len(sub_periods) + 2)
        if len(sub_periods) == 0:
            raise ValueError("Must have at least one sub-period")
        self.sub_periods: List[DateRange] = checked_list_type(sub_periods, DateRange)
        self.sub_period_titles: List[any] = sub_period_titles
        if len(sub_periods) != len(sub_period_titles):
            raise ValueError("Must have same number of sub-periods and sub-period titles")
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.nominal_ledger: NominalLedger = checked_type(nominal_ledger or NominalLedger.empty(), NominalLedger)
        self.num_sub_periods: int = len(self.sub_periods)
        self.gigs_by_sub_period: list[GigsInfo] = [self.gigs_info.restrict_to_period(w) for w in self.sub_periods]
        self.ledger_by_sub_period: list[NominalLedger] = [self.nominal_ledger.restrict_to_period(w) for w in
                                                          self.sub_periods]

    def common_requests(self):
        return [
            self.outline_border_request(),
            self[self.TITLE].merge_columns_request(),
            self[self.TITLE].center_text_request(),
            self[self.TITLE:self.SUB_PERIOD + 1, :].set_bold_text_request(),
            self[self.TOTAL, :].set_bold_text_request(),
            self[self.TOTAL].border_request(["bottom"]),
            self[self.SUB_PERIOD].border_request(["bottom"]),
            self[self.SUB_PERIOD:, 1].border_request(["left"]),
            self[self.SUB_PERIOD:, -1].border_request(["left"]),
            self[self.SUB_PERIOD, -1:].right_align_text_request(),

            self[self.TOTAL, 0].set_bold_text_request(),
            self[self.TOTAL:, 1:].set_decimal_format_request("#,##0.00"),
            self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
        ]

    def sub_period_values(self):
        return [
            (
                self[self.SUB_PERIOD, 1:-1],
                [w for w in self.sub_period_titles]
            ),
            (
                self[self.SUB_PERIOD, -1:], ["To Date"]
            ),
        ]

    def sub_period_gigs_row(self, fund: Callable[[GigsInfo], int]) -> list[any]:
        return [fund(gigs) for gigs in self.gigs_by_sub_period]

    def sub_period_ledger_row(self, func: Callable[[NominalLedger], int]) -> list[any]:
        return [func(ledger) for ledger in self.ledger_by_sub_period]
