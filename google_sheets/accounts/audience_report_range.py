from typing import List

from airtable_db.gigs_info import GigsInfo
from airtable_db.table_columns import TicketPriceLevel, TicketCategory
from date_range import DateRange
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type, checked_list_type


class AudienceReportRange(TabRange):
    ROW_HEADINGS = [
        # Headings
        "", "", "",
        # Ticket sales (numbers)
        "Gigs",
        "Audience", "", "", "", "", "", "", "",
    ]
    CAT_1_HEADINGS = [
        "", "", "Breakdown",
        # Ticket sales (numbers)
        "", "",
        "Full Price", "Member", "Conc", "Other", "Guest", "Online", "Walk in",
    ]
    CAT_2_HEADINGS = [
        "", "", "",
        # Ticket sales ()
        "", "",
        "", "", "", "", "", "", "",
    ]
    (TITLE, _, PERIOD,
     NUM_GIGS,
     AUDIENCE_TOTAL, FULL_PRICE_TICKETS, MEMBER_TICKETS, CONC_TICKETS, OTHER_TICKETS, GUEST_TICKETS, ONLINE_TICKETS,
     WALK_IN_TICKETS,

     ) = range(len(ROW_HEADINGS))

    (ROW_TITLE, CAT_1, CAT_2, PERIOD_1) = range(4)

    def __init__(
            self,
            top_left_cell: TabCell,
            title: str,
            periods: List[DateRange],
            period_titles: List[str],
            gigs_info: GigsInfo,
    ):
        super().__init__(top_left_cell, len(self.ROW_HEADINGS), len(periods) + 4)
        self.title = checked_type(title, str)
        self.periods: List[DateRange] = checked_list_type(periods, DateRange)
        self.period_titles: List[str] = checked_list_type(period_titles, str)
        self.num_periods: int = len(self.periods)
        self.gigs_by_sub_period: list[GigsInfo] = [
            gigs_info.restrict_to_period(period)
            for period in self.periods
        ]
        self.LAST_PERIOD = self.PERIOD_1 + self.num_periods - 1
        self.TO_DATE = self.PERIOD_1 + self.num_periods
        self.NUM_ROWS = len(self.ROW_HEADINGS)

    def format_requests(self):
        return [

            # Headings
            self.outline_border_request(),
            self[self.TITLE].merge_columns_request(),
            self[self.TITLE].center_text_request(),
            self[self.PERIOD, self.PERIOD_1:].right_align_text_request(),
            self[self.PERIOD].border_request(["bottom"]),
            self[self.TITLE:self.PERIOD + 1].set_bold_text_request(),
            self[:, self.ROW_TITLE].set_bold_text_request(),
            self[2:, self.CAT_2].border_request(["right"]),
            self[2:, self.TO_DATE].border_request(["left"]),

            # Audience
            self.tab.group_rows_request(self.i_first_row + self.FULL_PRICE_TICKETS,
                                        self.i_first_row + self.WALK_IN_TICKETS),
            self[self.NUM_GIGS:self.WALK_IN_TICKETS + 1, self.PERIOD_1:].set_decimal_format_request("#,##0"),
            self[self.ONLINE_TICKETS].border_request(["top"]),
            self[self.WALK_IN_TICKETS].border_request(["bottom"]),

            # last row
            self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
        ]

    def period_range(self, i_row):
        return self[i_row, self.PERIOD_1:self.LAST_PERIOD + 1]

    def raw_values(self):
        # Dates we want to display as strings
        return [
            (
                self.period_range(self.PERIOD),
                [w for w in self.period_titles]
            ),
            (
                self[self.PERIOD, self.TO_DATE], ["To Date"]
            ),
        ]

    def _heading_values(self):
        values = []

        values.append((self[2:, self.ROW_TITLE], self.ROW_HEADINGS[2:]))
        values.append((self[2:, self.CAT_1], self.CAT_1_HEADINGS[2:]))
        values.append((self[2:, self.CAT_2], self.CAT_2_HEADINGS[2:]))
        values.append((self[self.TITLE], [f"Audience Numbers"]))

        # To date totals
        for i_row in range(self.NUM_GIGS, self.NUM_ROWS):
            week_range = self.period_range(i_row)
            values.append(
                (self[i_row, self.TO_DATE], f"=Sum({week_range.in_a1_notation})")
            )
        return values

    def _audience_values(self):
        values = []
        values.append((
            self.period_range(self.NUM_GIGS),
            [gigs.number_of_gigs for gigs in self.gigs_by_sub_period]
        ))
        for i_row, level in [
            (self.FULL_PRICE_TICKETS, TicketPriceLevel.FULL),
            (self.MEMBER_TICKETS, TicketPriceLevel.MEMBER),
            (self.CONC_TICKETS, TicketPriceLevel.CONCESSION),
            (self.OTHER_TICKETS, TicketPriceLevel.OTHER),
        ]:
            values.append((
                self.period_range(i_row),
                [gigs.num_paid_tickets(price_level=level) for gigs in self.gigs_by_sub_period]
            ))
        values.append(
            (self.period_range(self.GUEST_TICKETS),
             [gigs.num_free_tickets for gigs in self.gigs_by_sub_period])
        )
        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):  # +1 for MTD
            breakdown_values = self[self.FULL_PRICE_TICKETS:self.GUEST_TICKETS + 1, i_col]
            values.append(
                (self[self.AUDIENCE_TOTAL, i_col], f"=Sum({breakdown_values.in_a1_notation})")
            )
        for i_row, category in [
            (self.ONLINE_TICKETS, TicketCategory.ONLINE),
            (self.WALK_IN_TICKETS, TicketCategory.WALK_IN)
        ]:
            values.append((self.period_range(i_row),
                           [gig.num_paid_tickets(category=category) for gig in self.gigs_by_sub_period]))
        return values

    def values(self):
        return self._heading_values() + self._audience_values()
