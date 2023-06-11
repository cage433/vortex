from numbers import Number

from airtable_db.contracts_and_events import MultipleContractAndEvents
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from env import TEST_SHEET_ID
from google_sheets import Workbook, Tab
from google_sheets.sheet_range import TabRange
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
        format_requests = [
            month_heading_range.set_border_request(["bottom", "top", "left", "right"]),
            month_heading_range[0, 1].set_date_format_request("mmm-yy"),
            month_heading_range[1, 1].set_date_format_request("d mmm yy"),
            month_heading_range[2, 1].set_percentage_format_request(),
            month_heading_range[:, 0].set_bold_text_request()
        ]
        self.workbook.batch_update(format_requests)
        month_heading_range.write_values(
            [
                ["Month", self.month.corresponding_calendar_month.first_day],
                ["Start Date", self.month.first_day],
                ["VAT Rate", self.vat_rate]
            ]
        )
        # set_date_format_request( @ sheet_range[START_DATE_ROW, 1], "d Mmm yy"),
        # month_heading_range.write_values([[contracts_and_events.month.title]])


if __name__ == '__main__':
    accounts = MonthlyAccounts(Workbook(TEST_SHEET_ID), AccountingMonth(2023, 1), vat_rate=0.2)
    accounts.update(None)
