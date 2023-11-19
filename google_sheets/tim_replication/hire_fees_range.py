from numbers import Number
from typing import List

from airtable_db.contracts_and_events import GigsInfo
from date_range import DateRange
from google_sheets.tab_range import TabCell
from google_sheets.tim_replication.accounts_range import AccountsRange
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type


class HireFeesRange(AccountsRange):
    NUM_ROWS = 6

    (TITLE, _, SUB_PERIOD, TOTAL, EVENING, DAY) = range(NUM_ROWS)

    def __init__(
            self,
            top_left_cell: TabCell,
            sub_periods: List[DateRange],
            sub_period_titles: List[any],
            gigs_info: GigsInfo,
            nominal_ledger: NominalLedger,
            vat_rate: float,
    ):
        super().__init__(top_left_cell, self.NUM_ROWS, sub_periods, sub_period_titles, gigs_info.excluding_hires,
                         nominal_ledger)
        self.vat_rate: float = checked_type(vat_rate, Number)

    def format_requests(self):
        return [
            self.outline_border_request(),
            self[self.TITLE].merge_columns_request(),
            self[self.TITLE].center_text_request(),
            self[self.TITLE:self.SUB_PERIOD + 1, :].set_bold_text_request(),
            self[self.TOTAL, :].set_bold_text_request(),
            self[self.SUB_PERIOD].border_request(["bottom"]),
            self[self.SUB_PERIOD:, 1].border_request(["left"]),
            self[self.SUB_PERIOD:, -1].border_request(["left", "right"]),
            self[self.SUB_PERIOD, -1:].right_align_text_request(),

            self[self.TOTAL, 0].set_bold_text_request(),
            self[self.TOTAL:, 1:].set_decimal_format_request("#,##0.00"),
            self.tab.group_rows_request(self.i_first_row + self.EVENING,
                                        self.i_first_row + self.DAY),
            self[self.EVENING:, 0].right_align_text_request(),
            self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
        ]

    def values(self):
        # Headings + Week nos + Total weekly ticket sales
        values = [(
            self[:, 0],
            ["Hire Fees (ex. VAT)", "", "Period", "Total", "Evening", "Day"]
        ), (
            self[self.SUB_PERIOD, 1:-1],
            [w for w in self.sub_period_titles]
        ), (
            self[self.SUB_PERIOD, -1:], ["To Date"]
        ), (
            self[self.TOTAL, 1:-1],
            [
                f"=SUM({self[self.EVENING:, i_col].in_a1_notation})"
                for i_col in range(1, self.num_sub_periods + 1)
            ]
        )]

        values += [
            (
                self[self.EVENING, 1:-1],
                [gig.hire_fees / (1 + self.vat_rate) for gig in self.gigs_by_sub_period]
            ),
            (
                self[self.DAY, 1:-1],
                [ledger.total_space_hire for ledger in self.ledger_by_sub_period]
            )
        ]

        # To date values
        values += [
            (
                self[i_row, -1],
                f"=SUM({self[i_row, 1:self.num_sub_periods + 1].in_a1_notation})"
            )
            for i_row in range(self.EVENING, self.DAY + 1)
        ]

        return values
