from typing import List

from airtable_db.contracts_and_events import GigsInfo
from airtable_db.table_columns import TicketPriceLevel, TicketCategory
from date_range import DateRange
from google_sheets.tab_range import TabCell
from google_sheets.tim_replication.accounts_range import AccountsRange


class AudienceNumbersRange(AccountsRange):
    NUM_ROWS = 11
    TITLE, _, SUB_PERIOD, TOTAL, FULL_PRICE, MEMBERS, CONCS, OTHER, GUEST, ONLINE, WALK_IN = range(NUM_ROWS)

    def __init__(self, top_left_cell: TabCell,
                 sub_periods: List[DateRange],
                 sub_period_titles: List[any],
                 gigs_info: GigsInfo):
        super().__init__(top_left_cell, self.NUM_ROWS, sub_periods, sub_period_titles, gigs_info)

    def format_requests(self):
        return [
            self.outline_border_request(),
            self[self.TITLE:self.TOTAL + 1, :].set_bold_text_request(),
            self[self.TITLE].merge_columns_request(),
            self[self.TITLE].center_text_request(),
            self[self.SUB_PERIOD, -1].right_align_text_request(),
            self[self.FULL_PRICE:, 0].right_align_text_request(),
            self[self.FULL_PRICE:, 1:].set_decimal_format_request("#,0"),
            self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),

            self[self.SUB_PERIOD:, 1].border_request(["left"]),
            self[self.SUB_PERIOD:, -1].border_request(["left"]),
            self[self.TOTAL].border_request(["top", "bottom"]),
            self[-2:].border_request(["top"]),
            self.tab.group_rows_request(self.i_first_row + self.FULL_PRICE,
                                        self.i_last_row)
        ]

    def values(self):
        # Headings
        values = [(
            self[:, 0],
            ["Audience", "", "", "Total", "Full Price", "Members", "Concessions", "Other", "Guest", "Online",
             "Walk-in"]
        ), (
            self[self.SUB_PERIOD, 1:-1],
            [str(w) for w in self.sub_period_titles]
        ), (
            self[self.SUB_PERIOD, -1], "To Date"
        )]

        # Week Nos

        # Tickets by level
        for i_level, level in enumerate([
            TicketPriceLevel.FULL,
            TicketPriceLevel.MEMBER,
            TicketPriceLevel.CONCESSION,
            TicketPriceLevel.OTHER,
        ]):
            func = lambda gigs: gigs.num_paid_tickets(price_level=level)
            week_range = self[self.FULL_PRICE + i_level, 1:self.num_sub_periods + 1]
            values.append((week_range, self.sub_period_gigs_row(func)))

        # Guests
        values.append(
            (self[self.GUEST, 1:self.num_sub_periods + 1], self.sub_period_gigs_row(lambda x: x.num_free_tickets))
        )

        # Online/Walk-in
        for i_category, category in enumerate([TicketCategory.ONLINE, TicketCategory.WALK_IN]):
            func = lambda gigs: gigs.num_paid_tickets(category=category)
            week_range = self[self.ONLINE + i_category, 1:self.num_sub_periods + 1]
            values.append((week_range, self.sub_period_gigs_row(func)))

        # Top totals
        for i_sub_period in range(self.num_sub_periods + 1):  # +1 for MTD
            breakdown_values = self[self.FULL_PRICE:self.GUEST + 1, i_sub_period + 1]
            values.append(
                (self[self.TOTAL, i_sub_period + 1], f"=Sum({breakdown_values.in_a1_notation})")
            )
        # Side totals
        for i_row in range(self.TOTAL, self.WALK_IN + 1):
            week_range = self[i_row, 1:self.num_sub_periods + 1]
            total_cell = self[i_row, self.num_sub_periods + 1]
            values.append(
                (total_cell, f"=Sum({week_range.in_a1_notation})")
            )

        return values
