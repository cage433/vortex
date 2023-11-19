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
            self.tab.group_rows_request(self.i_first_row + self.FULL,
                                        self.i_first_row + self.OTHER),
            self[self.FULL:self.OTHER + 1, 0].right_align_text_request(),
            self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
        ]

    def values(self):
        # Headings + Week nos + Total weekly ticket sales
        values = [(
            self[:, 0],
            ["Ticket Sales", "", "Period", "Total", "Full Price", "Members", "Student", "Other", ]
        ), (
            self[self.SUB_PERIOD, 1:-1],
            [w for w in self.sub_period_titles]
        ), (
            self[self.SUB_PERIOD, -1:], ["To Date"]
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
