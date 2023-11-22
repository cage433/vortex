import shelve
from numbers import Number
from pathlib import Path
from typing import List

from airtable_db import VortexDB
from airtable_db.contracts_and_events import GigsInfo
from airtable_db.table_columns import TicketPriceLevel, TicketCategory
from bank_statements import BankActivity
from bank_statements.payee_categories import PayeeCategory
from date_range import DateRange
from date_range.accounting_year import AccountingYear
from env import YTD_ACCOUNTS_SPREADSHEET_ID
from google_sheets import Tab, Workbook
from google_sheets.tab_range import TabRange, TabCell
from google_sheets.tim_replication.constants import VAT_RATE
from kashflow.nominal_ledger import NominalLedger
from utils import checked_type, checked_list_type


class AccountingReportRange(TabRange):
    ROW_HEADINGS = [
        # Headings
        "", "", "",
        # Ticket sales (numbers)
        "Audience", "", "", "", "", "", "", "",
        # P&L
        "P&L",
        "Gigs",
        # Ticket sales (money)
        "Ticket Sales", "", "", "", "",

        # gig costs
        "Gig costs", "", "", "", "", "", "", "", "", "", "",
        # Hire fees
        "Hire Fees", "", "",
        # Bar
        "Bar", "", "", "", "",
    ]
    CAT_1_HEADINGS = [
        "", "", "Breakdown 1",
        # Ticket sales (numbers)
        "",
        "Full Price", "Member", "Conc", "Other", "Guest", "Online", "Walk in",
        # P&L
        "",
        "",
        # Ticket sales (money)
        "",
        "Full Price",
        "Member",
        "Conc",
        "Other",
        # gig costs
        "",
        "Musicians Fees",
        "Security",
        "Sound Engineer",
        "PRS",
        "Marketing",
        "Work Permits",
        "Other Costs",
        "",
        "",
        "",
        # Hire fees
        "", "Evening", "Day",
        # Bar
        "", "Sales", "Purchases", "", "",
    ]
    CAT_2_HEADINGS = [
        "", "", "Breakdown 2",
        # Ticket sales (numbers)
        "",
        "", "", "", "", "", "", "",
        # P&L
        "",
        "",
        # Ticket sales (money)
        "", "", "", "", "",
        # gig costs
        "", "", "", "", "", "", "",
        "", "Accommodation", "Travel", "Catering",
        # Hire fees
        "", "", "",
        # Bar
        "", "", "", "Evening", "Delivered",
    ]
    (TITLE, _, PERIOD,
     AUDIENCE_TOTAL, FULL_PRICE_TICKETS, MEMBER_TICKETS, CONC_TICKETS, OTHER_TICKETS, GUEST_TICKETS, ONLINE_TICKETS,
     WALK_IN_TICKETS,
     P_AND_L,
     GIG_P_AND_L,
     TICKET_SALES_TOTAL, FULL_PRICE_SALES, MEMBER_SALES, CONC_SALES, OTHER_TICKET_SALES,
     GIG_COSTS, MUSICIAN_FEES,
     WORK_PERMITS,
     SECURITY,
     SOUND_ENGINEERING, PRS, MARKETING,
     OTHER_COSTS, ACCOMMODATION, TRAVEL, CATERING,

     HIRE_FEES, EVENING_HIRE_FEES, DAY_HIRE_FEES,

     BAR_P_AND_L, BAR_SALES, BAR_PURCHASES, BAR_EVENING, BAR_DELIVERED
     ) = range(len(ROW_HEADINGS))

    (ROW_TITLE, CAT_1, CAT_2, PERIOD_1) = range(4)

    def __init__(
            self,
            top_left_cell: TabCell,
            title: str,
            periods: List[DateRange],
            period_titles: List[str],
            gigs_info: GigsInfo,
            nominal_ledger: NominalLedger,
            bank_activity: BankActivity,
            vat_rate: float
    ):
        super().__init__(top_left_cell, len(self.ROW_HEADINGS), len(periods) + 4)
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
        self.vat_rate: float = checked_type(vat_rate, Number)
        self.LAST_PERIOD = self.PERIOD_1 + self.num_periods - 1
        self.TO_DATE = self.PERIOD_1 + self.num_periods
        self.NUM_ROWS = len(self.ROW_HEADINGS)

    def format_requests(self):
        return [

            # Headings
            self.outline_border_request(),
            self[self.TITLE].merge_columns_request(),
            self[self.TITLE].center_text_request(),
            self[self.PERIOD, self.PERIOD_1:].right_align_text_request(),
            self[self.PERIOD].border_request(["bottom"]),
            self[self.TITLE:self.PERIOD + 1].set_bold_text_request(),
            self[:, self.ROW_TITLE].set_bold_text_request(),
            self[2:, self.CAT_2].border_request(["right"]),
            self[2:, self.TO_DATE].border_request(["left"]),

            # Ticket sales (numbers)
            self.tab.group_rows_request(self.i_first_row + self.FULL_PRICE_TICKETS,
                                        self.i_first_row + self.WALK_IN_TICKETS),
            self[self.AUDIENCE_TOTAL:self.WALK_IN_TICKETS + 1, self.PERIOD_1:].set_decimal_format_request("#,##0"),
            self[self.ONLINE_TICKETS].border_request(["top"]),
            self[self.WALK_IN_TICKETS].border_request(["bottom"]),
            # P&L
            self[self.P_AND_L].border_request(["top", "bottom"]),
            self[self.AUDIENCE_TOTAL, 0].right_align_text_request(),
            # Ticket sales (money)
            self.tab.group_rows_request(self.i_first_row + self.FULL_PRICE_SALES,
                                        self.i_first_row + self.OTHER_TICKET_SALES),
            self[self.TICKET_SALES_TOTAL:, self.PERIOD_1:].set_decimal_format_request("#,##0.00"),
            self[self.TICKET_SALES_TOTAL, 0].right_align_text_request(),
            self[self.FULL_PRICE_SALES].border_request(["top"]),
            self[self.OTHER_TICKET_SALES].border_request(["bottom"]),

            # gig costs
            self[self.GIG_COSTS, 0].right_align_text_request(),

            self.tab.group_rows_request(self.i_first_row + self.ACCOMMODATION,
                                        self.i_first_row + self.CATERING),
            self.tab.group_rows_request(self.i_first_row + self.MUSICIAN_FEES,
                                        self.i_first_row + self.CATERING),
            #
            # # Hire fees
            self.tab.group_rows_request(self.i_first_row + self.EVENING_HIRE_FEES,
                                        self.i_first_row + self.DAY_HIRE_FEES),
            self[self.HIRE_FEES].border_request(["top"]),
            self[self.DAY_HIRE_FEES].border_request(["bottom"]),

            # Bar
            self[self.BAR_P_AND_L].border_request(["top"]),
            self.tab.group_rows_request(self.i_first_row + self.BAR_SALES,
                                        self.i_first_row + self.BAR_DELIVERED),
            self.tab.group_rows_request(self.i_first_row + self.BAR_EVENING,
                                        self.i_first_row + self.BAR_DELIVERED),
            # last row
            self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
        ]

    def period_range(self, i_row):
        return self[i_row, self.PERIOD_1:self.LAST_PERIOD + 1]

    def raw_values(self):
        # Dates we want to display as strings
        return [
            (
                self.period_range(self.PERIOD),
                [w for w in self.period_titles]
            ),
            (
                self[self.PERIOD, self.TO_DATE], ["To Date"]
            ),
        ]

    def _heading_values(self):
        values = []

        values.append((self[2:, self.ROW_TITLE], self.ROW_HEADINGS[2:]))
        values.append((self[2:, self.CAT_1], self.CAT_1_HEADINGS[2:]))
        values.append((self[2:, self.CAT_2], self.CAT_2_HEADINGS[2:]))
        values.append((self[self.TITLE], [f"Accounts {self.title}"]))

        # To date totals
        for i_row in range(self.AUDIENCE_TOTAL, self.NUM_ROWS):
            week_range = self.period_range(i_row)
            values.append(
                (self[i_row, self.TO_DATE], f"=Sum({week_range.in_a1_notation})")
            )
        return values

    def _audience_values(self):
        values = []
        for i_row, level in [
            (self.FULL_PRICE_TICKETS, TicketPriceLevel.FULL),
            (self.MEMBER_TICKETS, TicketPriceLevel.MEMBER),
            (self.CONC_TICKETS, TicketPriceLevel.CONCESSION),
            (self.OTHER_TICKETS, TicketPriceLevel.OTHER),
        ]:
            values.append((
                self.period_range(i_row),
                [gigs.num_paid_tickets(price_level=level) for gigs in self.gigs_by_sub_period]
            ))
        values.append(
            (self.period_range(self.GUEST_TICKETS),
             [gigs.num_free_tickets for gigs in self.gigs_by_sub_period])
        )
        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):  # +1 for MTD
            breakdown_values = self[self.FULL_PRICE_TICKETS:self.GUEST_TICKETS + 1, i_col]
            values.append(
                (self[self.AUDIENCE_TOTAL, i_col], f"=Sum({breakdown_values.in_a1_notation})")
            )
        for i_row, category in [
            (self.ONLINE_TICKETS, TicketCategory.ONLINE),
            (self.WALK_IN_TICKETS, TicketCategory.WALK_IN)
        ]:
            values.append((self.period_range(i_row),
                           [gig.num_paid_tickets(category=category) for gig in self.gigs_by_sub_period]))
        return values

    def _ticket_sales_values(self):
        values = [
            (
                self.period_range(self.TICKET_SALES_TOTAL),
                [
                    f"=SUM({self[self.FULL_PRICE_SALES:self.OTHER_TICKET_SALES + 1, i_col].in_a1_notation})"
                    for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
                ]
            )
        ]
        for i_row, level in [
            (self.FULL_PRICE_SALES, TicketPriceLevel.FULL),
            (self.MEMBER_SALES, TicketPriceLevel.MEMBER),
            (self.CONC_SALES, TicketPriceLevel.CONCESSION)
        ]:
            values.append(
                (self.period_range(i_row), [gig.ticket_sales(level) for gig in self.gigs_by_sub_period])
            )

        # Other ticket sales
        values.append(
            (self.period_range(self.OTHER_TICKET_SALES), [gig.other_ticket_sales for gig in self.gigs_by_sub_period])
        )
        return values

    def sum_formula(self, first_row: int, last_row: int, i_col: int):
        return f"SUM({self[first_row:last_row + 1, i_col].in_a1_notation})"

    def _gig_costs_values(self):
        values = []
        for (i_row, func) in [
            (self.MUSICIAN_FEES, lambda gig: -gig.musicians_fees),
            (self.ACCOMMODATION, lambda gig: -gig.band_accommodation),
            (self.TRAVEL, lambda gig: -gig.band_transport),
            (self.CATERING, lambda gig: -gig.band_catering / (1 + self.vat_rate)),
            (self.PRS, lambda gig: -gig.prs_fee_ex_vat),
        ]:
            values.append(
                (self.period_range(i_row), [func(gig) for gig in self.gigs_by_sub_period])
            )
        for (i_row, func) in [
            (self.SOUND_ENGINEERING, lambda ledger: ledger.sound_engineering),
            (self.SECURITY, lambda ledger: ledger.security),
            (self.MARKETING, lambda ledger: ledger.marketing),
        ]:
            values.append(
                (self.period_range(i_row), [func(ledger) for ledger in self.ledger_by_sub_period])
            )
        for (i_row, category) in [
            (self.WORK_PERMITS, PayeeCategory.WORK_PERMITS)
        ]:
            values.append(
                (self.period_range(i_row),
                 [activity.net_amount_for_category(category) for activity in self.bank_activity_by_sub_period])
            )

        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values += [(
                self[self.GIG_COSTS, i_col],
                f"={self.sum_formula(self.MUSICIAN_FEES, self.OTHER_COSTS, i_col)} "
            ), (
                self[self.OTHER_COSTS, i_col],
                f"={self.sum_formula(self.ACCOMMODATION, self.CATERING, i_col)}"
            ),
                (
                    self[self.GIG_P_AND_L, i_col],
                    f"={self[self.TICKET_SALES_TOTAL, i_col].in_a1_notation} + {self[self.GIG_COSTS, i_col].in_a1_notation}"
                )
            ]
        return values

    def _hire_fee_values(self):
        values = [
            (
                self.period_range(self.HIRE_FEES),
                [
                    f"=SUM({self[self.EVENING_HIRE_FEES:self.DAY_HIRE_FEES + 1, i_col].in_a1_notation})"
                    for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
                ]
            )
        ]
        values += [
            (
                self.period_range(self.EVENING_HIRE_FEES),
                [gigs_info.excluding_hires.hire_fees / (1 + self.vat_rate) for gigs_info in self.gigs_by_sub_period]
            ),
            (
                self.period_range(self.DAY_HIRE_FEES),
                [ledger.total_space_hire for ledger in self.ledger_by_sub_period]
            )
        ]
        return values

    def _bar_values(self):
        values = []
        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values += [
                (
                    self[self.BAR_P_AND_L, i_col],
                    f"={self[self.BAR_SALES, i_col].in_a1_notation} + {self[self.BAR_PURCHASES, i_col].in_a1_notation}"
                ),
                (
                    self[self.BAR_PURCHASES, i_col],
                    f"={self[self.BAR_EVENING, i_col].in_a1_notation} + {self[self.BAR_DELIVERED, i_col].in_a1_notation}"
                )
            ]
        values += [
            (
                self.period_range(self.BAR_SALES),
                [gig.bar_takings / (1 + self.vat_rate) for gig in self.gigs_by_sub_period]
            ),
            (
                self.period_range(self.BAR_EVENING),
                [- gig.evening_purchases / (1 + self.vat_rate) for gig in self.gigs_by_sub_period]
            ),
            (
                self.period_range(self.BAR_DELIVERED),
                [ledger.bar_stock for ledger in self.ledger_by_sub_period]
            )
        ]
        return values

    def values(self):
        values = self._heading_values() \
                 + self._audience_values() \
                 + self._ticket_sales_values() \
                 + self._gig_costs_values() \
                 + self._hire_fee_values() \
                 + self._bar_values()

        return values


class AccountingReport(Tab):
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
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _workbook_format_requests(self):
        return self.delete_all_row_groups_requests() + [
            # Workbook
            self.set_column_width_request(i_col=1, width=200),
            self.set_columns_width_request(i_first_col=2, i_last_col=14, width=75),
        ] + self.report_range.format_requests()

    def update(self):
        self.workbook.batch_update(
            self.clear_values_and_formats_requests() +
            self._workbook_format_requests()
        )

        self.workbook.batch_update_values(
            self.report_range.raw_values(),
            value_input_option="RAW"  # Prevent creation of dates
        )
        self.workbook.batch_update_values(
            self.report_range.values()
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
    tab = AccountingReport(workbook, "YTD 2023", str(acc_year.y),
                           acc_months, period_titles, gigs_info, nominal_ledger, bank_activity)
    tab.update()
