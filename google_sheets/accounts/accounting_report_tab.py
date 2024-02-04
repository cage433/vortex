import shelve
from pathlib import Path
from typing import List

from airtable_db import VortexDB
from airtable_db.contracts_and_events import GigsInfo
from bank_statements import BankActivity
from date_range import DateRange
from date_range.accounting_year import AccountingYear
from env import YTD_ACCOUNTS_SPREADSHEET_ID
from google_sheets import Tab, Workbook
from google_sheets.accounts.accounting_report_range import AccountingReportRange
from google_sheets.accounts.audience_report_range import AudienceReportRange
from google_sheets.accounts.bank_activity_range import BankActivityRange
from google_sheets.accounts.constants import VAT_RATE
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type


class AccountingReportTab(Tab):
    def __init__(
            self,
            workbook: Workbook,
            title: str,
            periods: List[DateRange],
            period_titles: List[str],
            gigs_info: GigsInfo,
            nominal_ledger: NominalLedger,
            bank_activity: BankActivity,
            show_transactions: bool
    ):
        super().__init__(workbook, tab_name=title)
        self.report_range = AccountingReportRange(
            self.cell("B2"),
            title,
            periods,
            period_titles,
            gigs_info,
            nominal_ledger,
            bank_activity,
            VAT_RATE
        )
        self.audience_numbers_range = AudienceReportRange(
            self.report_range.bottom_left_cell.offset(num_rows=2),
            title,
            periods,
            period_titles,
            gigs_info,
        )
        self.show_transactions = checked_type(show_transactions, bool)
        if self.show_transactions:
            self.transaction_range = BankActivityRange(
                self.audience_numbers_range.bottom_right_cell.offset(num_rows=2, num_cols=2),
                bank_activity
            )
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _workbook_format_requests(self):
        return self.delete_all_row_groups_requests() + [
            # Workbook
            self.set_columns_width_request(i_first_col=1, i_last_col=3, width=75),
            self.set_columns_width_request(i_first_col=4, i_last_col=14, width=75),
        ] + self.report_range.format_requests() + self.audience_numbers_range.format_requests()

    def update(self):
        self.workbook.batch_update(
            self.clear_values_and_formats_requests() +
            self._workbook_format_requests()
        )
        self.workbook.batch_update(
            self.collapse_all_group_rows_requests()
        )

        self.workbook.batch_update_values(
            self.report_range.raw_values() + self.audience_numbers_range.raw_values(),
            value_input_option="RAW"  # Prevent creation of dates
        )
        self.workbook.batch_update_values(
            self.report_range.values() + self.audience_numbers_range.values()
        )

        if self.show_transactions:
            self.workbook.batch_update(
                self.transaction_range.format_requests()
            )
            self.workbook.batch_update_values(
                self.transaction_range.values()
            )


SHELF = Path(__file__).parent / "_ytd_report.shelf"


def gig_info(period: DateRange, force: bool) -> GigsInfo:
    key = f"gig_info_{period}"
    with shelve.open(str(SHELF)) as shelf:
        if key not in shelf or force:
            info = VortexDB().contracts_and_events_for_period(period)
            shelf[key] = info
        return shelf[key]


def read_nominal_ledger(force: bool) -> NominalLedger:
    key = "nominal_ledger"
    with shelve.open(str(SHELF)) as shelf:
        if key not in shelf or force:
            info = NominalLedger.from_csv_file()
            shelf[key] = info
        return shelf[key]


def read_bank_activity(period: DateRange, force: bool) -> BankActivity:
    key = f"bank_activity_{period}"
    with shelve.open(str(SHELF)) as shelf:
        if key not in shelf or force:
            activity = BankActivity.build(force).restrict_to_period(period)
            shelf[key] = activity
        return shelf[key]


if __name__ == '__main__':
    workbook = Workbook(YTD_ACCOUNTS_SPREADSHEET_ID)
    acc_year = AccountingYear(2023)
    m = acc_year.first_accounting_month
    gigs_info_list = []
    force = False
    acc_months = acc_year.accounting_months
    for month in acc_months:
        month_info = gig_info(month, force)
        gigs_info_list += month_info.contracts_and_events
    gigs_info = GigsInfo(gigs_info_list)
    nominal_ledger = read_nominal_ledger(force).restrict_to_period(acc_year)
    bank_activity = read_bank_activity(acc_year, force=True)
    period_titles = [m.month_name for m in acc_months]
    tab = AccountingReportTab(workbook, "YTD 2023", "YTD 2023",
                              acc_months, period_titles, gigs_info, nominal_ledger, bank_activity)
    tab.update()
