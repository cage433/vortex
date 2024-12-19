from typing import List

from accounting.accounting_activity import AccountingActivity
from bank_statements.categorized_transaction import CategorizedTransactions
from date_range import DateRange
from date_range.accounting_year import AccountingYear
from env import YTD_ACCOUNTS_SPREADSHEET_ID
from google_sheets import Tab, Workbook
from google_sheets.accounts.accounting_report_range import AccountingReportRange
from google_sheets.accounts.accounts_by_category import AccountsByCategoryRange
from google_sheets.accounts.audience_report_range import AudienceReportRange
from google_sheets.accounts.bank_activity_range import BankActivityRange
from google_sheets.accounts.constants import VAT_RATE
from utils import checked_type


class AccountingReportTab(Tab):
    def __init__(
            self,
            workbook: Workbook,
            title: str,
            periods: List[DateRange],
            period_titles: List[str],
            accounting_activity: AccountingActivity,
            categorized_transactions: CategorizedTransactions,
            show_transactions: bool
    ):
        super().__init__(workbook, tab_name=title)
        # self.report_range = AccountingReportRange(
        #     self.cell("B2"),
        #     title,
        #     periods,
        #     period_titles,
        #     accounting_activity,
        #     categorized_transactions,
        #     VAT_RATE
        # )
        self.report_range = AccountsByCategoryRange(
            self.cell("B2"),
            title,
            periods,
            period_titles,
            accounting_activity,
            categorized_transactions,
        )
        self.audience_numbers_range = AudienceReportRange(
            self.report_range.bottom_left_cell.offset(num_rows=2),
            title,
            periods,
            period_titles,
            accounting_activity.gigs_info,
        )
        self.show_transactions = checked_type(show_transactions, bool)
        if self.show_transactions:
            self.transaction_range = BankActivityRange(
                self.audience_numbers_range.bottom_right_cell.offset(num_rows=2, num_cols=2),
                accounting_activity.bank_activity
            )
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _workbook_format_requests(self):
        return self.delete_all_groups_requests() + [
            # Workbook
            self.set_columns_width_request(i_first_col=1, i_last_col=2, width=75),
            self.set_columns_width_request(i_first_col=3, i_last_col=3, width=110),
            self.set_columns_width_request(i_first_col=4, i_last_col=14, width=75),
        ] + self.report_range.format_requests() + self.audience_numbers_range.format_requests()

    def update(self):
        self.workbook.batch_update(
            self.clear_values_and_formats_requests() +
            self._workbook_format_requests()
        )
        self.workbook.batch_update(
            self.collapse_all_groups_requests()
        )

        self.workbook.batch_update_values(
            self.report_range.raw_values() + self.audience_numbers_range.raw_values(),
            value_input_option="RAW"  # Prevent creation of dates
        )
        foo = self.report_range.values()
        bar = self.audience_numbers_range.values()
        self.workbook.batch_update_values(
            foo + bar
            # self.report_range.values() + self.audience_numbers_range.values()
        )

        if self.show_transactions:
            self.workbook.batch_update(
                self.transaction_range.format_requests()
            )
            self.workbook.batch_update_values(
                self.transaction_range.values()
            )


if __name__ == '__main__':
    workbook = Workbook(YTD_ACCOUNTS_SPREADSHEET_ID)
    acc_year = AccountingYear(2023)
    accounting_activity = AccountingActivity.activity_for_period(acc_year, force=False)

    acc_months = acc_year.accounting_months
    period_titles = [m.month_name for m in acc_months]
    tab = AccountingReportTab(workbook, "YTD 2023",
                              acc_months, period_titles, accounting_activity, show_transactions=True)

    tab.update()
