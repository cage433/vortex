from numbers import Number

from airtable_db import VortexDB
from airtable_db.contracts_and_events import MultipleContractAndEvents
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
        month_heading_range = TabRange.from_range_name(self, "B2:C4")
        audience_range = TabRange(self.cell("B6"), num_rows=12, num_cols=22)
        format_requests = [
            month_heading_range.set_border_request(["bottom", "top", "left", "right"]),
            month_heading_range[0, 1].set_date_format_request("mmm-yy"),
            month_heading_range[1, 1].set_date_format_request("d mmm yy"),
            month_heading_range[2, 1].set_percentage_format_request(),
            month_heading_range[:, 0].set_bold_text_request()
        ]
        self.workbook.batch_update(format_requests)
        month_heading_values = [
            ["Month", self.month.corresponding_calendar_month.first_day],
            ["Start Date", self.month.first_day],
            ["VAT Rate", self.vat_rate]
        ]
        self.workbook.batch_update_values(
            {
                month_heading_range: month_heading_values
            }
        )


if __name__ == '__main__':
    month = AccountingMonth(AccountingYear(2023), 1)
    accounts = MonthlyAccounts(Workbook(TEST_SHEET_ID), month, vat_rate=0.2)
    contracts_and_events = VortexDB().contracts_and_events_for_period(month)
    accounts.update(contracts_and_events)
