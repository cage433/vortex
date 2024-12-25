from typing import List

from accounting.accounting_activity import AccountingActivity
from date_range import DateRange
from date_range.accounting_year import AccountingYear
from env import YTD_ACCOUNTS_SPREADSHEET_ID
from google_sheets import Tab, Workbook
from google_sheets.accounts.accounts_by_category import AccountsByCategoryRange
from google_sheets.accounts.bank_activity_range import BankActivityRange


class AccountingReportTab(Tab):
    def __init__(
            self,
            workbook: Workbook,
            title: str,
            periods: List[DateRange],
            period_titles: List[str],
            accounting_activity: AccountingActivity,
    ):
        super().__init__(workbook, tab_name=title)
        self.report_range = AccountsByCategoryRange(
            self.cell("B2"),
            title,
            periods,
            period_titles,
            accounting_activity,
        )
        self.transaction_range = BankActivityRange(
            self.report_range.bottom_left_cell.offset(num_rows=5),
            accounting_activity,
            periods
        )
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _workbook_format_requests(self):
        return (self.delete_all_groups_requests() + [
            # Workbook
            self.set_columns_width_request(i_first_col=1, i_last_col=2, width=75),
            self.set_columns_width_request(i_first_col=3, i_last_col=3, width=110),
            self.set_columns_width_request(i_first_col=4, i_last_col=14, width=75),
        ] + self.report_range.format_requests() +
                self.transaction_range.format_requests()
                )

    def update(self):
        self.workbook.batch_update(
            self.clear_values_and_formats_requests() +
            self._workbook_format_requests()
        )
        self.workbook.batch_update(
            self.collapse_all_groups_requests()
        )

        self.workbook.batch_update_values(
            self.report_range.raw_values(),
            value_input_option="RAW"  # Prevent creation of dates
        )
        self.workbook.batch_update_values(
            self.report_range.values() +
            self.transaction_range.values(),
        )



if __name__ == '__main__':
    workbook = Workbook(YTD_ACCOUNTS_SPREADSHEET_ID)
    acc_year = AccountingYear(2023)
    accounting_activity = AccountingActivity.activity_for_period(acc_year, force=False)

    acc_months = acc_year.accounting_months
    period_titles = [m.month_name for m in acc_months]
    tab = AccountingReportTab(workbook, "YTD 2023",
                              acc_months, period_titles, accounting_activity)

    tab.update()
