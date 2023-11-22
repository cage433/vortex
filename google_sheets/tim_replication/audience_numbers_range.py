from typing import List

from airtable_db.contracts_and_events import GigsInfo
from airtable_db.table_columns import TicketPriceLevel, TicketCategory
from bank_statements import BankActivity
from date_range import DateRange
from google_sheets.tab_range import TabCell
from google_sheets.tim_replication.accounts_range import AccountsRange
from kashflow.nominal_ledger import NominalLedger


class AudienceNumbersRange(AccountsRange):
    NUM_ROWS = 11
    TITLE, _, SUB_PERIOD, TOTAL, FULL_PRICE, MEMBERS, CONCS, OTHER, GUEST, ONLINE, WALK_IN = range(NUM_ROWS)

    def __init__(self, top_left_cell: TabCell,
                 sub_periods: List[DateRange],
                 sub_period_titles: List[any],
                 gigs_info: GigsInfo,
                 nominal_ledger: NominalLedger,
                 bank_activity: BankActivity,
                 ):
        super().__init__(top_left_cell, self.NUM_ROWS, sub_periods, sub_period_titles, gigs_info, nominal_ledger,
                         bank_activity)

    def format_requests(self):
        return super().common_requests() + [
            self[self.ONLINE].border_request(["top"]),
            self.tab.group_rows_request(self.i_first_row + self.FULL_PRICE,
                                        self.i_last_row),
            self[self.TOTAL:, 1:].set_decimal_format_request("#,##0"),
        ]

    def values(self):
        # Headings
        values = (super().sub_period_values() +
                  [
                      (
                          self[:, 0],
                          ["Audience", "", "",
                           "Total", "Full Price", "Members", "Concessions", "Other", "Guest",
                           "Online", "Walk-in"]
                      )
                  ])

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
