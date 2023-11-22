import shelve
from pathlib import Path
from typing import List

from airtable_db import VortexDB
from airtable_db.contracts_and_events import GigsInfo
from airtable_db.table_columns import TicketPriceLevel
from bank_statements import BankActivity
from date_range import DateRange
from date_range.accounting_year import AccountingYear
from env import YTD_ACCOUNTS_SPREADSHEET_ID
from google_sheets import Tab, Workbook
from google_sheets.tab_range import TabRange
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type, checked_list_type


class AccountingReport(Tab):
    NUM_ROWS = 18
    ROW_HEADINGS = [
        # Headings
        "", "", "Period",
        # Ticket sales (numbers)
        "Audience", "Full Price", "Member", "Conc", "Other", "Guest",
        "Online",
        "Walk in",
        # P&L
        "P&L",
        "Income",
        # Ticket sales (money)
        "Ticket Sales Total", "Full Price", "Member", "Conc", "Other",
    ]
    (TITLE, _, SUB_PERIOD,
     AUDIENCE_TOTAL, FULL_PRICE_TICKETS, MEMBER_TICKETS, CONC_TICKETS, OTHER_TICKETS, GUEST_TICKETS, ONLINE_TICKETS,
     WALK_IN_TICKETS,
     P_AND_L,
     INCOME,
     TICKET_SALES_TOTAL, FULL_PRICE_SALES, MEMBER_SALES, CONC_SALES, OTHER_TICKET_SALES
     ) = range(len(ROW_HEADINGS))

    def __init__(
            self,
            workbook: Workbook,
            title: str,
            tab_name: str,
            periods: List[DateRange],
            period_titles: List[str],
            gigs_info: GigsInfo,
            nominal_ledger: NominalLedger,
            bank_activity: BankActivity,
    ):
        super().__init__(workbook, tab_name=tab_name)
        self.title = checked_type(title, str)
        self.periods: List[DateRange] = checked_list_type(periods, DateRange)
        self.period_titles: List[str] = checked_list_type(period_titles, str)
        self.num_periods: int = len(self.periods)
        self.gigs_by_sub_period: list[GigsInfo] = [
            gigs_info.restrict_to_period(period)
            for period in self.periods
        ]
        self.ledger_by_sub_period: list[NominalLedger] = [
            nominal_ledger.restrict_to_period(period)
            for period in self.periods
        ]
        self.bank_activity_by_sub_period: list[BankActivity] = [
            bank_activity.restrict_to_period(period)
            for period in self.periods
        ]
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)
        self.report_range = TabRange(self.cell("B1"), num_rows=self.NUM_ROWS,
                                     num_cols=self.num_periods + 2)

    def _workbook_format_requests(self):
        return self.delete_all_row_groups_requests() + [
            # Workbook
            self.set_column_width_request(i_col=1, width=200),
            self.set_columns_width_request(i_first_col=2, i_last_col=14, width=75),

            # Headings
            self.report_range[self.TITLE].merge_columns_request(),
            self.report_range[self.TITLE].center_text_request(),
            self.report_range[self.SUB_PERIOD:self.AUDIENCE_TOTAL + 1].set_bold_text_request(),
            self.group_rows_request(self.report_range.i_first_row + self.FULL_PRICE_TICKETS,
                                        self.report_range.i_first_row + self.WALK_IN_TICKETS),
        ]

    def _values(self):

        values = [
            (
                self.report_range[self.SUB_PERIOD, 1:-1],
                [w for w in self.period_titles]
            ),
            (
                self.report_range[self.SUB_PERIOD, -1:], ["To Date"]
            ),
        ]
        values.append((self.report_range[2:, 0], self.ROW_HEADINGS[2:]))
        values.append((self.report_range[self.TITLE], [f"Accounts {self.title}"]))
        for i_row, level in [
            (self.FULL_PRICE_TICKETS, TicketPriceLevel.FULL),
            (self.MEMBER_TICKETS, TicketPriceLevel.MEMBER),
            (self.CONC_TICKETS, TicketPriceLevel.CONCESSION),
            (self.OTHER_TICKETS, TicketPriceLevel.OTHER),
        ]:
            values.append((
                    self.report_range[i_row, 1:-1],
                    [gigs.num_paid_tickets(price_level=level) for gigs in self.gigs_by_sub_period]
                ))
        values.append(
            (self.report_range[self.GUEST_TICKETS, 1:self.num_periods + 1],
             [gigs.num_free_tickets for gigs in self.gigs_by_sub_period])
        )
        for i_period in range(self.num_periods + 1):  # +1 for MTD
            breakdown_values = self.report_range[self.FULL_PRICE_TICKETS:self.GUEST_TICKETS + 1, i_period + 1]
            values.append(
                (self.report_range[self.AUDIENCE_TOTAL, i_period + 1], f"=Sum({breakdown_values.in_a1_notation})")
            )
        return values

    def update(self):
        self.workbook.batch_update(
            self.clear_values_and_formats_requests() +
            self._workbook_format_requests()
        )

        self.workbook.batch_update_values(
            self._values()
        )


SHELF = Path(__file__).parent / "_ytd_report.shelf"


def gig_info(period: DateRange, force: bool = False) -> GigsInfo:
    key = f"gig_info_{period}"
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


def read_bank_activity(period: DateRange, force: bool = False) -> BankActivity:
    key = f"bank_activity_{period}"
    with shelve.open(str(SHELF)) as shelf:
        if key not in shelf or force:
            activity = BankActivity.build().restrict_to_period(period)
            shelf[key] = activity
        return shelf[key]


if __name__ == '__main__':
    workbook = Workbook(YTD_ACCOUNTS_SPREADSHEET_ID)
    acc_year = AccountingYear(2023)
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
    tab = AccountingReport(workbook, "YTD 2023", str(acc_year.y),
                           acc_months, period_titles, gigs_info, nominal_ledger, bank_activity)
    tab.update()
