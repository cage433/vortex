import shelve
from pathlib import Path

from airtable_db import VortexDB
from airtable_db.contracts_and_events import GigsInfo
from date_range import DateRange
from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from env import YTD_ACCOUNTS_SPREADSHEET_ID
from google_sheets import Tab, Workbook
from google_sheets.tab_range import TabRange, TabCell
from google_sheets.tim_replication.audience_numbers_range import AudienceNumbersRange
from google_sheets.tim_replication.bar_takings import BarTakingsRange
from google_sheets.tim_replication.gig_costs import GigCostsRange
from google_sheets.tim_replication.hire_fees_range import HireFeesRange
from google_sheets.tim_replication.ticket_sales_range import TicketSalesRange
from google_sheets.tim_replication.vat_rate import VAT_RATE
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type


class HeadingsRange(TabRange):
    NUM_ROWS = 4
    NUM_COLS = 14

    def __init__(self, top_left_cell: TabCell, month: AccountingMonth):
        super().__init__(top_left_cell, num_rows=self.NUM_ROWS, num_cols=self.NUM_COLS)
        self.month = checked_type(month, AccountingMonth)

    def format_requests(self):
        return [
            self[0, 1:].merge_columns_request(),
            self[0, 1:].center_text_request(),
            self.set_bold_text_request()
        ]

    def values(self) -> list[type[TabRange, list[list[any]]]]:
        month_name = self.month.month_name
        return [
            (self[0, 1], f"Gig Report Month 12 - {month_name}"),
            (self[1, 0], ["Vortex Jazz Club"]),
            (self[2, 0:2], ["Income and Expenditure", f"Year end {month_name}"]),
            (self[3, 0:2], ["Month", month_name]),
        ]


class YTD_Report(Tab):
    def __init__(
            self,
            workbook: Workbook,
            month: AccountingMonth,
            gigs_info: GigsInfo,
            nominal_ledger: NominalLedger,
    ):
        super().__init__(workbook, tab_name=month.month_name)
        self.month: AccountingMonth = checked_type(month, AccountingMonth)
        self.headings_range = HeadingsRange(self.cell("B1"), self.month)
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

        months = [
            m for m in month.year.months
            if m <= month
        ]
        self.audience_numbers_range = AudienceNumbersRange(
            self.cell("B8"),
            months,
            [m.month_name for m in months],
            gigs_info
        )
        self.ticket_sales_range = TicketSalesRange(
            self.cell("B20"),
            months,
            [m.month_name for m in months],
            gigs_info
        )

        self.hire_fees_range = HireFeesRange(
            self.cell("B29"),
            months,
            [m.month_name for m in months],
            gigs_info,
            nominal_ledger,
            VAT_RATE
        )
        self.bar_takings_range = BarTakingsRange(
            self.cell("B36"),
            months,
            [m.month_name for m in months],
            gigs_info,
            nominal_ledger,
            VAT_RATE
        )

        self.gig_costs_range = GigCostsRange(
            self.cell("B45"),
            months,
            [m.month_name for m in months],
            gigs_info,
            nominal_ledger,
            VAT_RATE
        )

    def _workbook_format_requests(self):
        return self.delete_all_row_groups_requests() + [
            self.set_column_width_request(i_col=1, width=200),
            self.set_columns_width_request(i_first_col=2, i_last_col=14, width=75),
        ]

    def update(self):
        self.workbook.batch_update(
            self.clear_values_and_formats_requests() +
            self._workbook_format_requests() +
            self.headings_range.format_requests() +
            self.audience_numbers_range.format_requests() +
            self.ticket_sales_range.format_requests() +
            self.hire_fees_range.format_requests() +
            self.bar_takings_range.format_requests() +
            self.gig_costs_range.format_requests()
        )

        self.workbook.batch_update_values(
            self.headings_range.values(),
            value_input_option="RAW"  # Prevent creation of dates
        )
        self.workbook.batch_update_values(
            self.audience_numbers_range.values() +
            self.ticket_sales_range.values() +
            self.hire_fees_range.values() +
            self.bar_takings_range.values() +
            self.gig_costs_range.values()
        )


SHELF = Path(__file__).parent / "_gig_info.shelf"


def gig_info(period: DateRange, force: bool = False) -> GigsInfo:
    key = str(period)
    with shelve.open(str(SHELF)) as shelf:
        if key not in shelf or force:
            info = VortexDB().contracts_and_events_for_period(period)
            shelf[key] = info
        return shelf[key]


def read_nominal_ledger(force: bool = False) -> NominalLedger:
    key = "nominal_ledger"
    with shelve.open(str(SHELF)) as shelf:
        if key not in shelf or force:
            info = NominalLedger.from_csv_file()
            shelf[key] = info
        return shelf[key]


if __name__ == '__main__':
    workbook = Workbook(YTD_ACCOUNTS_SPREADSHEET_ID)
    acc_year = AccountingYear(2023)
    acc_month = AccountingMonth(acc_year, 9)
    # acc_month = AccountingMonth(AccountingYear(2023), 7)
    # print(acc_month.first_day)
    # print(acc_month.last_day)
    gigs_info_list = []
    force = False
    for month in acc_year.months:
        month_info = gig_info(month, force)
        gigs_info_list += month_info.contracts_and_events
    gigs_info = GigsInfo(gigs_info_list)
    nominal_ledger = read_nominal_ledger(force).restrict_to_period(acc_year)
    tab = YTD_Report(workbook, AccountingMonth(acc_year, 8), gigs_info, nominal_ledger)
    tab.update()
