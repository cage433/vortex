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
from google_sheets.tab_range import TabRange
from utils import checked_type


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
        self._ticket_numbers_range: TabRange = TabRange(self.cell("B6"), num_rows=11, num_cols=month.num_weeks + 2)
        self._income_range: TabRange = TabRange(self.cell("B19"), num_rows=11, num_cols=month.num_weeks + 3)
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _workbook_format_requests(self):
        return self.delete_all_row_groups_requests() + [
            self.set_column_width_request(i_col=0, width=20)
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
            (self._month_heading_range[:, 1], [self.month.corresponding_calendar_month.first_day, self.month.first_day, self.vat_rate]),
        ]

    def _ticket_numbers_format_requests(self):
        return [
            self._ticket_numbers_range.outline_border_request(),
            self._ticket_numbers_range[0:4, :].set_bold_text_request(),
            self._ticket_numbers_range[0].merge_columns_request(),
            self._ticket_numbers_range[0].center_text_request(),
            self._ticket_numbers_range[2, -1].right_align_text_request(),
            self._ticket_numbers_range[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),

            self._ticket_numbers_range[2:, 1].border_request(["left"]),
            self._ticket_numbers_range[2:, -1].border_request(["left"]),
            self._ticket_numbers_range[3].border_request(["top", "bottom"]),
            self._ticket_numbers_range[-2:].border_request(["top"]),
            self.group_rows_request(self._ticket_numbers_range.i_first_row + 4,
                                    self._ticket_numbers_range.i_last_row)
        ]

    def _week_gigs_row(self, gig_func: Callable[[GigsInfo], int]) -> list[any]:
        return [gig_func(gigs) for gigs in self._gigs_by_week]

    def _ticket_numbers_values(self):
        values = [
            (self._ticket_numbers_range[:, 0], ["Audience", "", "Week", "Total", "Full Price", "Members", "Concessions", "Other", "Guest", "Online", "Walk-in"])
        ]
        for i_level, level in enumerate([
            TicketPriceLevel.FULL,
            TicketPriceLevel.MEMBER,
            TicketPriceLevel.CONCESSION,
            TicketPriceLevel.OTHER,
        ]):
            func = lambda gigs: gigs.num_paid_tickets(price_level=level)
            week_range = self._ticket_numbers_range[i_level + 4, 1:self._num_weeks + 1]
            values.append((week_range, self._week_gigs_row(func)))

        values.append(
            (self._ticket_numbers_range[8, 1:self._num_weeks + 1], self._week_gigs_row(lambda x: x.num_free_tickets()))
        )
        for i_category, category in enumerate([TicketCategory.ONLINE, TicketCategory.WALK_IN]):
            func = lambda gigs: gigs.num_paid_tickets(category=category)
            week_range = self._ticket_numbers_range[i_category + 9, 1:self._num_weeks + 1]
            values.append((week_range, self._week_gigs_row(func)))

        for i_week in range(self._num_weeks + 1):                          # +1 for MTD
            breakdown_values = self._ticket_numbers_range[4:9, i_week + 1]
            values.append(
                (self._ticket_numbers_range[3, i_week + 1], f"=Sum({breakdown_values.in_a1_notation})")
            )
        for i_row in range(3, 11):
            week_range = self._ticket_numbers_range[i_row, 1:self._num_weeks + 1]
            values.append(
                (week_range.top_right_cell.offset(cols=1), f"=Sum({week_range.in_a1_notation})")
            )

        return values

    def _income_format_requests(self):
        return [
            self._income_range.outline_border_request(),
            self._income_range[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
            self._income_range[2].border_request(["bottom"]),
            self._income_range[2:, 1].border_request(["left"]),
            self._income_range[2:, -2].border_request(["left", "right"]),
            self.group_rows_request(self._income_range.i_first_row + 4,
                                    self._income_range.i_last_row),
            self._income_range[0].merge_columns_request(),
            self._income_range[0].center_text_request(),
            self._income_range[2, -2:].right_align_text_request(),
        ]

    def _income_values(self):
        values = [
            ["Income"],
            [],
            ["Week"] + [w.week_no for w in self.month.weeks] + ["MTD", "VAT Estimate"],
        ]
        return values

    def update(self):

        format_requests = self.clear_values_and_formats_requests() \
                          + self._workbook_format_requests() \
                          + self._month_headings_format_requests() \
                          + self._ticket_numbers_format_requests() \
                          + self._income_format_requests()

        self.workbook.batch_update(format_requests)
        self.workbook.batch_update_values(
            self._month_headings_values() + self._ticket_numbers_values()
        )


if __name__ == '__main__':
    month = AccountingMonth(AccountingYear(2022), 5)
    contracts_and_events = VortexDB().contracts_and_events_for_period(month)
    accounts = MonthlyAccounts(Workbook(TEST_SHEET_ID), month, vat_rate=0.2, gigs_info=contracts_and_events)
    accounts.row_groups()
    accounts.update()
