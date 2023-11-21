from numbers import Number
from typing import List

from airtable_db.contracts_and_events import GigsInfo
from bank_statements import BankActivity
from date_range import DateRange
from google_sheets.tab_range import TabCell
from google_sheets.tim_replication.accounts_range import AccountsRange
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type


class BarTakingsRange(AccountsRange):
    NUM_ROWS = 8

    (TITLE, _, SUB_PERIOD, TOTAL, SALES, PURCHASES, EVENING, DELIVERED) = range(NUM_ROWS)

    def __init__(
            self,
            top_left_cell: TabCell,
            sub_periods: List[DateRange],
            sub_period_titles: List[any],
            gigs_info: GigsInfo,
            nominal_ledger: NominalLedger,
            bank_activity: BankActivity,
            vat_rate: float,
    ):
        super().__init__(top_left_cell, self.NUM_ROWS, sub_periods, sub_period_titles, gigs_info.excluding_hires,
                         nominal_ledger, bank_activity)
        self.vat_rate: float = checked_type(vat_rate, Number)

    def format_requests(self):
        return self.common_requests() + [
            # self[self.SALES].border_request(["bottom", "top"]),
            self.tab.group_rows_request(self.i_first_row + self.SALES,
                                        self.i_first_row + self.DELIVERED),
            self.tab.group_rows_request(self.i_first_row + self.EVENING,
                                        self.i_first_row + self.DELIVERED),
            self[self.EVENING:, 0].right_align_text_request(),
        ]

    def values(self):
        values = self.sub_period_values()
        values += [(
            self[:, 0],
            ["Bar Takings (ex. VAT)", "", "Period", "Total", "Sales", "Purchases", "Evening", "Delivered"]
        ), (
            self[self.TOTAL, 1:-1],
            [
                f"=SUM({self[self.SALES:self.PURCHASES + 1, i_col].in_a1_notation})"
                for i_col in range(1, self.num_sub_periods + 1)
            ]
        ), (
            self[self.PURCHASES, 1:-1],
            [
                f"=SUM({self[self.EVENING:self.DELIVERED + 1, i_col].in_a1_notation})"
                for i_col in range(1, self.num_sub_periods + 1)
            ]
        )
        ]

        values += [
            (
                self[self.SALES, 1:-1],
                [gig.bar_takings / (1 + self.vat_rate) for gig in self.gigs_by_sub_period]
            ),
            (
                self[self.EVENING, 1:-1],
                [- gig.evening_purchases / (1 + self.vat_rate) for gig in self.gigs_by_sub_period]
            ),
            (
                self[self.DELIVERED, 1:-1],
                [ledger.bar_stock for ledger in self.ledger_by_sub_period]
            )
        ]

        # To date values
        values += [
            (
                self[i_row, -1],
                f"=SUM({self[i_row, 1:self.num_sub_periods + 1].in_a1_notation})"
            )
            for i_row in range(self.TOTAL, self.DELIVERED + 1)
        ]

        return values
