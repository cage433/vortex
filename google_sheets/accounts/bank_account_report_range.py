from typing import List

from accounting.accounting_activity import AccountingActivity
from airtable_db.gigs_info import GigsInfo
from bank_statements import BankActivity
from bank_statements.bank_account import CHARITABLE_ACCOUNT, CURRENT_ACCOUNT, SAVINGS_ACCOUNT, BBL_ACCOUNT
from bank_statements.categorized_transaction import CategorizedTransactions
from date_range import DateRange
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type, checked_list_type


class BankAccountReportRange(TabRange):
    HEADINGS_BLANKS = ["", "", ""]
    NET_TITLE = ["Net"]
    ACCOUNT_TITLES = ["Current", "Savings", "BBL", "Charitable"]
    ROW_HEADINGS = (HEADINGS_BLANKS + NET_TITLE + ACCOUNT_TITLES)

    (TITLE_ROW, PERIOD_START_ROW, PERIOD_ROW,
     NET_ROW,
     CURRENT_ROW, SAVINGS_ROW, BBL_ROW, CHARITABLE_ROW
     ) = range(len(ROW_HEADINGS))

    (ROW_TITLE, INITIAL_BALANCE, TERMINAL_BALANCE, PERIOD_1) = range(4)

    NUM_ROWS = len(ROW_HEADINGS)

    def __init__(
            self,
            top_left_cell: TabCell,
            title: str,
            periods: List[DateRange],
            period_titles: List[str],
            accounting_activity: AccountingActivity,
            categorized_transactions: CategorizedTransactions,
    ):
        super().__init__(top_left_cell, self.NUM_ROWS, len(periods) + 4)
        self.title = checked_type(title, str)
        self.periods: List[DateRange] = checked_list_type(periods, DateRange)
        self.period_titles: List[str] = checked_list_type(period_titles, str)
        self.num_periods: int = len(self.periods)
        self.bank_activity_by_sub_period: list[BankActivity] = [
            accounting_activity.bank_activity.restrict_to_period(period)
            for period in self.periods
        ]
        self.gigs_by_sub_period: list[GigsInfo] = [
            accounting_activity.gigs_info.restrict_to_period(period)
            for period in self.periods
        ]
        self.categorized_transactions_by_sub_period: list[CategorizedTransactions] = [
            categorized_transactions.restrict_to_period(period)
            for period in self.periods
        ]
        self.vat_rate: float = 0.0  # checked_type(vat_rate, Number)
        self.LAST_PERIOD = self.PERIOD_1 + self.num_periods - 1
        self.TO_DATE = self.PERIOD_1 + self.num_periods
        self.NUM_ROWS = len(self.ROW_HEADINGS)

    def format_requests(self):
        return [

            # Headings
            self.outline_border_request(),
            self[self.TITLE_ROW].merge_columns_request(),
            self[self.TITLE_ROW].center_text_request(),
            self[self.PERIOD_START_ROW].date_format_request("d Mmm"),
            self[self.PERIOD_ROW, self.PERIOD_1:].right_align_text_request(),
            self[self.PERIOD_ROW].border_request(["bottom"]),
            self[self.TITLE_ROW:self.PERIOD_ROW + 1].set_bold_text_request(),
            self[:, self.ROW_TITLE].set_bold_text_request(),
            self[1:, self.TERMINAL_BALANCE].border_request(["right"]),
            self[1:, self.TO_DATE].border_request(["left"]),

            # P&L
            self[self.NET_ROW:, self.PERIOD_1:].set_decimal_format_request("#,##0"),

            # last row
            self[-1].offset(rows=1).border_request(["top"], style="SOLID_MEDIUM"),
        ]

    def period_range(self, i_row):
        return self[i_row, self.PERIOD_1:self.LAST_PERIOD + 1]

    def raw_values(self):
        # Dates we want to display as strings
        return [
            (
                self.period_range(self.PERIOD_ROW),
                [w for w in self.period_titles]
            ),
            (
                self[self.PERIOD_ROW, self.TO_DATE], ["To Date"]
            ),
        ]

    def _heading_values(self):
        values = []

        values.append((self[2:, self.ROW_TITLE], self.ROW_HEADINGS[2:]))
        values.append((
            self.period_range(self.PERIOD_START_ROW),
            [w.first_day.date for w in self.periods]
        ))
        values.append((self[self.TITLE_ROW], [f"Bank Statements {self.title}"]))

        # To date totals
        for i_row in range(self.NET_ROW, self.NUM_ROWS):
            period_range = self.period_range(i_row)
            values.append(
                (self[i_row, self.TO_DATE], f"=Sum({period_range.in_a1_notation})")
            )
        return values

    def _sum_rows_text(self, rows: List[int], i_col: int):
        return f"={'+'.join([self[i_row, i_col].in_a1_notation for i_row in rows])}"

    def _sum_range(self, first_row: int, last_row: int, i_col: int):
        return f"=SUM({self[first_row:last_row + 1, i_col].in_a1_notation})"

    def _category_values(self):
        values = []

    def sum_formula(self, first_row: int, last_row: int, i_col: int):
        return f"SUM({self[first_row:last_row + 1, i_col].in_a1_notation})"

    def _p_and_l_values(self):
        values = [
            (
                self.period_range(self.NET_ROW),
                [
                    self._sum_rows_text(
                        [self.CURRENT_ROW, self.SAVINGS_ROW, self.BBL_ROW, self.CHARITABLE_ROW],
                        i_col
                    )
                    for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
                ]
            ),
        ]

        for (i_row, account) in zip(
                [self.CURRENT_ROW, self.SAVINGS_ROW, self.BBL_ROW, self.CHARITABLE_ROW],
                [CURRENT_ACCOUNT, SAVINGS_ACCOUNT, BBL_ACCOUNT, CHARITABLE_ACCOUNT]
        ):
            values.append(
                (self.period_range(i_row),
                 [
                     bacc.balance_at_eod(period.last_day) - bacc.balance_at_sod(period.first_day)
                     for ba, period in zip(self.bank_activity_by_sub_period, self.periods)
                     for bacc in [ba.restrict_to_account(account)]
                 ]
                 )
            )
            values.append(
                (
                    self[i_row, self.INITIAL_BALANCE],
                    [
                        self.bank_activity_by_sub_period[0].restrict_to_account(account).balance_at_sod(self.periods[0].first_day)
                    ]
                )
            )
            values.append(
                (
                    self[i_row, self.TERMINAL_BALANCE],
                    [
                        self.bank_activity_by_sub_period[-1].restrict_to_account(account).balance_at_sod(self.periods[-1].last_day)
                    ]
                )
            )

        return values

    def values(self):
        values = self._heading_values() \
                 + self._p_and_l_values()

        return values
