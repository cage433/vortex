from numbers import Number
from typing import Callable

from airtable_db import VortexDB
from airtable_db.contracts_and_events import GigsInfo
from airtable_db.table_columns import TicketPriceLevel, TicketCategory
from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from date_range.week import Week
from env import TEST_SHEET_ID
from google_sheets import Workbook, Tab
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type


class MonthAccountsRange(TabRange):
    def __init__(self, top_left_cell: TabCell, num_rows: int, num_cols: int, month: AccountingMonth,
                 gigs_info: GigsInfo):
        super().__init__(top_left_cell, num_rows, num_cols)
        self.month: AccountingMonth = checked_type(month, AccountingMonth)
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.weeks: list[Week] = month.weeks
        self.num_weeks: int = len(self.weeks)
        self.gigs_by_week: list[GigsInfo] = [self.gigs_info.restrict_to_period(w) for w in self.weeks]


    def week_gigs_row(self, gig_func: Callable[[GigsInfo], int]) -> list[any]:
        return [gig_func(gigs) for gigs in self.gigs_by_week]


class TicketsSoldRange(MonthAccountsRange):
    NUM_ROWS = 11
    TITLE, _, WEEK, TOTAL, FULL_PRICE, MEMBERS, CONCS, OTHER, GUEST, ONLINE, WALK_IN = range(NUM_ROWS)

    def __init__(self, top_left_cell: TabCell, month: AccountingMonth, gigs_info: GigsInfo):
        super().__init__(top_left_cell, self.NUM_ROWS, month.num_weeks + 3, month, gigs_info)

    def format_requests(self):
        return [
            self.outline_border_request(),
            self[:self.TOTAL, :].set_bold_text_request(),
            self[self.TITLE].merge_columns_request(),
            self[self.TITLE].center_text_request(),
            self[self.WEEK, -1].right_align_text_request(),
            self[self.FULL_PRICE:, 0].right_align_text_request(),
            self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),

            self[self.WEEK:, 1].border_request(["left"]),
            self[self.WEEK:, -1].border_request(["left"]),
            self[self.TOTAL].border_request(["top", "bottom"]),
            self[-2:].border_request(["top"]),
            self.tab.group_rows_request(self.i_first_row + self.FULL_PRICE,
                                        self.i_last_row)
        ]

    def values(self):
        # Headings
        values = [
            (
                self[:, 0],
                ["Audience", "", "Week", "Total", "Full Price", "Members", "Concessions", "Other", "Guest", "Online",
                 "Walk-in"]
            )
        ]

        # Week Nos
        values.append(
            (
                self[self.WEEK, 1:-1],
                [w.week_no for w in self.weeks]
            )
        )

        values.append(
            (
                self[self.WEEK, 5], "MTD"
            )
        )

        # Tickets by level
        for i_level, level in enumerate([
            TicketPriceLevel.FULL,
            TicketPriceLevel.MEMBER,
            TicketPriceLevel.CONCESSION,
            TicketPriceLevel.OTHER,
        ]):
            func = lambda gigs: gigs.num_paid_tickets(price_level=level)
            week_range = self[self.FULL_PRICE + i_level, 1:self.num_weeks + 1]
            values.append((week_range, self.week_gigs_row(func)))

        # Guests
        values.append(
            (self[self.GUEST, 1:self.num_weeks + 1], self.week_gigs_row(lambda x: x.num_free_tickets))
        )

        # Online/Walk-in
        for i_category, category in enumerate([TicketCategory.ONLINE, TicketCategory.WALK_IN]):
            func = lambda gigs: gigs.num_paid_tickets(category=category)
            week_range = self[self.ONLINE + i_category, 1:self.num_weeks + 1]
            values.append((week_range, self.week_gigs_row(func)))

        # Top totals
        for i_week in range(self.num_weeks + 1):  # +1 for MTD
            breakdown_values = self[self.FULL_PRICE:self.GUEST + 1, i_week + 1]
            values.append(
                (self[self.TOTAL, i_week + 1], f"=Sum({breakdown_values.in_a1_notation})")
            )
        # Side totals
        for i_row in range(self.TOTAL, self.WALK_IN + 1):
            week_range = self[i_row, 1:self.num_weeks + 1]
            values.append(
                (week_range.top_right_cell.offset(cols=1), f"=Sum({week_range.in_a1_notation})")
            )

        return values


class MonthlyAccounts(Tab):
    def __init__(
            self,
            workbook: Workbook,
            month: AccountingMonth,
            vat_rate: Number,
            gigs_info: GigsInfo
    ):
        super().__init__(workbook, month.tab_name)
        self.month = checked_type(month, AccountingMonth)
        self.vat_rate: float = checked_type(vat_rate, Number)
        self._gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self._weeks: list[Week] = month.weeks
        self._num_weeks: int = len(self._weeks)
        self._gigs_by_week: list[GigsInfo] = [self._gigs_info.restrict_to_period(w) for w in self._weeks]
        self._month_heading_range: TabRange = TabRange.from_range_name(self, "B2:C4")
        self._vat_cell = self._month_heading_range[-1, 1]
        self.ticket_numbers_range = TicketsSoldRange(self.cell("B6"), month, gigs_info)
        self._income_range: TabRange = TabRange(self.cell("B19"), num_rows=14, num_cols=month.num_weeks + 3)
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _workbook_format_requests(self):
        return self.delete_all_row_groups_requests() + [
            self.set_column_width_request(i_col=0, width=20),
            self.set_column_width_request(i_col=1, width=150),
        ]

    def _month_headings_format_requests(self):
        return [
            self._month_heading_range.outline_border_request(),
            self._month_heading_range[0, 1].date_format_request("mmm-yy"),
            self._month_heading_range[1, 1].date_format_request("d mmm yy"),
            self._month_heading_range[2, 1].percentage_format_request(),
            self._month_heading_range[:, 0].set_bold_text_request(),
        ]

    def _month_headings_values(self) -> list[tuple[TabRange, list[list[any]]]]:
        return [
            (self._month_heading_range[:, 0], ["Month", "Start Date", "VAT Rate"]),
            (self._month_heading_range[:, 1],
             [self.month.corresponding_calendar_month.first_day, self.month.first_day, self.vat_rate]),
        ]


    def _week_gigs_row(self, gig_func: Callable[[GigsInfo], int]) -> list[any]:
        return [gig_func(gigs) for gigs in self._gigs_by_week]


    def _income_format_requests(self):
        return [
            self._income_range.outline_border_request(),
            self._income_range[0].merge_columns_request(),
            self._income_range[0].center_text_request(),
            self._income_range[0:3, :].set_bold_text_request(),
            self._income_range[-1, :].set_bold_text_request(),
            self._income_range[8:10, 0].set_bold_text_request(),
            self._income_range[13, 0].set_bold_text_request(),
            self._income_range[2].border_request(["bottom"]),
            self._income_range[2:, 1].border_request(["left"]),
            self._income_range[2:, -2].border_request(["left", "right"]),
            self.group_rows_request(self._income_range.i_first_row + 4,
                                    self._income_range.i_first_row + 7),
            self.group_rows_request(self._income_range.i_first_row + 10,
                                    self._income_range.i_first_row + 12),
            self._income_range[2, -2:].right_align_text_request(),
            self._income_range[4:8, 0].right_align_text_request(),
            self._income_range[10:13, 0].right_align_text_request(),
            self._income_range[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
            self._income_range[3:, 1:].set_decimal_format_request("#,##0.00")
        ]

    def _income_values(self):
        # Headings + Week nos + Total weekly ticket sales
        values = [(
            self._income_range[:, 0],
            ["Incoming", "", "Week", "Ticket Sales", "Full Price", "Members", "Student", "Other",
             "Hire Fees", "Bar Takings", "Total CC Takings", "CC Ticket Sales", "CC Artist Merch", "Total"]
        ), (
            self._income_range[2, 1:-2],
            [w.week_no for w in self._weeks]
        ), (
            self._income_range[2, -2:], ["MTD", "VAT Estimate"]
        ), (
            self._income_range[3, 1:-2],
            [
                f"=SUM({self._income_range[4:8, i_col].in_a1_notation})"
                for i_col in range(1, self._num_weeks + 1)
            ]
        )]

        # Ticket values
        values += [
            (self._income_range[i + 4, 1:-2], [w.ticket_sales(level) for w in self._gigs_by_week])
            for i, level in enumerate([TicketPriceLevel.FULL, TicketPriceLevel.MEMBER, TicketPriceLevel.CONCESSION])
        ]

        for i, func in enumerate([
            lambda w: w.other_ticket_sales,
            lambda w: w.hire_fees,
            lambda w: w.bar_takings
        ]):
            values.append(
                (self._income_range[7 + i, 1:-2], [func(w) for w in self._gigs_by_week])
            )

        # MTD values
        values += [
            (
                self._income_range[i_row, -2],
                f"=SUM({self._income_range[i_row, 1:self._num_weeks + 1].in_a1_notation})"
            )
            for i_row in range(3, 14)
        ]

        # VAT
        for i_row in [3, 8, 9]:
            mtd = self._income_range[i_row, -2].in_a1_notation
            vat = self._vat_cell.in_a1_notation
            values.append(
                (self._income_range[i_row, -1], f"=SUM({mtd} * {vat} / (1 + {vat}))")
            )

        # Bottom totals
        for i_week in range(self._num_weeks + 2):  # +2 for MTD + VAT
            ticket_sales_cell = self._income_range[3, i_week + 1].in_a1_notation
            hire_fees_cell = self._income_range[8, i_week + 1].in_a1_notation
            bar_takings_cell = self._income_range[9, i_week + 1].in_a1_notation
            values.append(
                (self._income_range[13, i_week + 1], f"={ticket_sales_cell} + {hire_fees_cell} + {bar_takings_cell}")
            )

        return values

    def update(self):

        format_requests = self.clear_values_and_formats_requests() \
                          + self._workbook_format_requests() \
                          + self._month_headings_format_requests() \
                          + self.ticket_numbers_range.format_requests() \
                          + self._income_format_requests()

        self.workbook.batch_update(format_requests)
        self.workbook.batch_update_values(
            self._month_headings_values() + self.ticket_numbers_range.values() + self._income_values()
        )


if __name__ == '__main__':
    month = AccountingMonth(AccountingYear(2022), 7)
    contracts_and_events = VortexDB().contracts_and_events_for_period(month)
    accounts = MonthlyAccounts(Workbook(TEST_SHEET_ID), month, vat_rate=0.2, gigs_info=contracts_and_events)
    accounts.row_groups()
    accounts.update()
