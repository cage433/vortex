from numbers import Number

from airtable_db import VortexDB
from airtable_db.contracts_and_events import MultipleContractAndEvents
from airtable_db.table_columns import TicketPriceLevel, TicketCategory
from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from env import TEST_SHEET_ID
from google_sheets import Workbook, Tab
from google_sheets.tab_range import TabRange
from utils import checked_type


class MonthlyAccounts(Tab):
    def __init__(self, workbook: Workbook, month: AccountingMonth, vat_rate: Number):
        super().__init__(workbook, month.tab_name)
        self.month = checked_type(month, AccountingMonth)
        self.vat_rate: float = checked_type(vat_rate, Number)
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def update(self, contracts_and_events: MultipleContractAndEvents):

        weekly_c_and_e = [contracts_and_events.restrict_to_period(w) for w in self.month.weeks]
        month_heading_range = TabRange.from_range_name(self, "B2:C4")
        audience_range = TabRange(self.cell("B6"), num_rows=12, num_cols=month.num_weeks + 2)
        format_requests = self.clear_values_and_formats_requests() + [
            month_heading_range.outline_border_request(),
            month_heading_range[0, 1].date_format_request("mmm-yy"),
            month_heading_range[1, 1].date_format_request("d mmm yy"),
            month_heading_range[2, 1].percentage_format_request(),
            month_heading_range[:, 0].set_bold_text_request(),

            audience_range.outline_border_request(),
            audience_range[0:4, :].set_bold_text_request(),
            audience_range[0].merge_columns_request(),
            audience_range[2, -1].right_align_text_request(),
        ]
        self.workbook.batch_update(format_requests)
        month_heading_values = [
            ["Month", self.month.corresponding_calendar_month.first_day],
            ["Start Date", self.month.first_day],
            ["VAT Rate", self.vat_rate]
        ]
        audience_range_values = [
            ["Audience"],
            [],
            ["Week"] + [w.week_no for w in self.month.weeks] + ["MTD"],
            ["Total"] + [ce.total_tickets for ce in weekly_c_and_e] + [contracts_and_events.total_tickets]
        ]

        for text, level in [
            ["Full Price", TicketPriceLevel.FULL],
            ["Members", TicketPriceLevel.MEMBER],
            ["Concessions", TicketPriceLevel.CONCESSION],
            ["Other", TicketPriceLevel.OTHER],
        ]:
            audience_range_values.append(
                [text] + [ce.num_paid_tickets(price_level=level) for ce in weekly_c_and_e] + [
                    contracts_and_events.num_paid_tickets(price_level=level)
                ]
            )
        audience_range_values += [
            ["Guest"] + [ce.num_free_tickets() for ce in weekly_c_and_e] + [contracts_and_events.num_free_tickets()],
            [],
            ["Online"] + [ce.num_paid_tickets(category=TicketCategory.ONLINE) for ce in weekly_c_and_e] + [contracts_and_events.num_paid_tickets(category=TicketCategory.ONLINE)],
            ["Walk-in"] + [ce.num_paid_tickets(category=TicketCategory.WALK_IN) for ce in weekly_c_and_e] + [
                contracts_and_events.num_paid_tickets(category=TicketCategory.WALK_IN)],
        ]
        self.workbook.batch_update_values(
            {
                month_heading_range: month_heading_values,
                audience_range: audience_range_values
            }
        )


if __name__ == '__main__':
    month = AccountingMonth(AccountingYear(2022), 5)
    accounts = MonthlyAccounts(Workbook(TEST_SHEET_ID), month, vat_rate=0.2)
    contracts_and_events = VortexDB().contracts_and_events_for_period(month)
    accounts.update(contracts_and_events)
