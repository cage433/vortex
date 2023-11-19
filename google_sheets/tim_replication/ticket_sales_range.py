from typing import List

from airtable_db.contracts_and_events import GigsInfo
from airtable_db.table_columns import TicketPriceLevel
from date_range import DateRange
from google_sheets.tab_range import TabCell
from google_sheets.tim_replication.accounts_range import AccountsRange


class TicketSalesRange(AccountsRange):
    NUM_ROWS = 8

    (TITLE, _, SUB_PERIOD, TOTAL, FULL, MEMBER, CONCS, OTHER) = range(NUM_ROWS)

    def __init__(
            self,
            top_left_cell: TabCell,
            sub_periods: List[DateRange],
            sub_period_titles: List[any],
            gigs_info: GigsInfo,
    ):
        super().__init__(top_left_cell, self.NUM_ROWS, sub_periods, sub_period_titles, gigs_info.excluding_hires)

    def format_requests(self):
        return super().common_requests() + [
            self.tab.group_rows_request(self.i_first_row + self.FULL,
                                        self.i_first_row + self.OTHER),
        ]

    def values(self):
        values = self.sub_period_values()
        values += [(
            self[:, 0],
            ["Ticket Sales", "", "Period", "Total", "Full Price", "Members", "Student", "Other", ]
        ), (
            self[self.TOTAL, 1:-1],
            [
                f"=SUM({self[self.FULL:self.OTHER + 1, i_col].in_a1_notation})"
                for i_col in range(1, self.num_sub_periods + 1)
            ]
        )]

        # Regular ticket sales
        values += [
            (self[self.FULL + i, 1:-1], [w.ticket_sales(level) for w in self.gigs_by_sub_period])
            for i, level in enumerate([TicketPriceLevel.FULL, TicketPriceLevel.MEMBER, TicketPriceLevel.CONCESSION])
        ]

        # Other ticket sales
        values.append(
            (self[self.OTHER, 1:-1], [w.other_ticket_sales for w in self.gigs_by_sub_period])
        )

        # MTD values
        values += [
            (
                self[i_row, -1],
                f"=SUM({self[i_row, 1:self.num_sub_periods + 1].in_a1_notation})"
            )
            for i_row in range(self.TOTAL, self.OTHER + 1)
        ]

        return values
