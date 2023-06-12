from numbers import Number
from typing import Callable

from airtable_db import VortexDB
from airtable_db.contracts_and_events import GigsInfo
from airtable_db.table_columns import TicketPriceLevel, TicketCategory
from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
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
        self._gigs_info = checked_type(gigs_info, GigsInfo)
        self._gigs_by_week = [self._gigs_info.restrict_to_period(w) for w in self.month.weeks]
        self._month_heading_range = TabRange.from_range_name(self, "B2:C4")
        self._ticket_numbers_range = TabRange(self.cell("B6"), num_rows=12, num_cols=month.num_weeks + 2)
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _ticket_numbers_array(self):
        def tickets_row(name: str, ticket_func: Callable[[GigsInfo], int]) -> list[any]:
            return [name] + [ticket_func(gigs) for gigs in self._gigs_by_week] + [ticket_func(self._gigs_info)]

        values = [
            ["Audience"],
            [],
            ["Week"] + [w.week_no for w in self.month.weeks] + ["MTD"],
            tickets_row("Total", lambda gigs: gigs.total_tickets),
        ]
        for text, level in [
            ["Full Price", TicketPriceLevel.FULL],
            ["Members", TicketPriceLevel.MEMBER],
            ["Concessions", TicketPriceLevel.CONCESSION],
            ["Other", TicketPriceLevel.OTHER],
        ]:
            values.append(
                tickets_row(text, lambda gigs: gigs.num_paid_tickets(price_level=level))
            )

        values += [
            tickets_row("Guest", lambda gigs: gigs.num_free_tickets()),
            [],
            tickets_row("Online", lambda gigs: gigs.num_paid_tickets(category=TicketCategory.ONLINE)),
            tickets_row("Walk-in", lambda gigs: gigs.num_paid_tickets(category=TicketCategory.WALK_IN)),
        ]
        return values

    def _ticket_numbers_formats(self):
        return [
            self._ticket_numbers_range.outline_border_request(),
            self._ticket_numbers_range[0:4, :].set_bold_text_request(),
            self._ticket_numbers_range[0].merge_columns_request(),
            self._ticket_numbers_range[0].center_text_request(),
            self._ticket_numbers_range[2, -1].right_align_text_request(),
            self._ticket_numbers_range[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
            self._ticket_numbers_range[2].border_request(["bottom"]),
            self._ticket_numbers_range[2:, 1].border_request(["left"]),
            self._ticket_numbers_range[2:, -1].border_request(["left"]),
            self.group_rows_request(self._ticket_numbers_range.i_first_row + 4,
                                    self._ticket_numbers_range.i_last_row)
        ]

    def _month_headings_formats(self):
        return [
            self._month_heading_range.outline_border_request(),
            self._month_heading_range[0, 1].date_format_request("mmm-yy"),
            self._month_heading_range[1, 1].date_format_request("d mmm yy"),
            self._month_heading_range[2, 1].percentage_format_request(),
            self._month_heading_range[:, 0].set_bold_text_request(),
        ]

    def _month_headings_values(self) -> list[list[any]]:
        return [
            ["Month", self.month.corresponding_calendar_month.first_day],
            ["Start Date", self.month.first_day],
            ["VAT Rate", self.vat_rate]
        ]

    def _workbook_requests(self):
        return self.delete_all_row_groups_requests() + [
            self.set_column_width_request(i_col=0, width=20)
        ]

    def update(self):

        format_requests = self.clear_values_and_formats_requests() \
                          + self._workbook_requests() \
                          + self._month_headings_formats() \
                          + self._ticket_numbers_formats()
        self.workbook.batch_update(format_requests)

        self.workbook.batch_update_values(
            {
                self._month_heading_range: self._month_headings_values(),
                self._ticket_numbers_range: self._ticket_numbers_array()
            }
        )


if __name__ == '__main__':
    month = AccountingMonth(AccountingYear(2022), 5)
    contracts_and_events = VortexDB().contracts_and_events_for_period(month)
    accounts = MonthlyAccounts(Workbook(TEST_SHEET_ID), month, vat_rate=0.2, gigs_info=contracts_and_events)
    accounts.row_groups()
    accounts.update()
