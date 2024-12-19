from typing import List

from accounting.accounting_activity import AccountingActivity
from airtable_db.gigs_info import GigsInfo
from bank_statements import BankActivity
from bank_statements.bank_account import CHARITABLE_ACCOUNT, CURRENT_ACCOUNT, SAVINGS_ACCOUNT, BBL_ACCOUNT
from bank_statements.categorized_transaction import CategorizedTransactions
from bank_statements.payee_categories import PayeeCategory
from date_range import DateRange
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type, checked_list_type


class AccountsByCategoryRange(TabRange):
    CATEGORY_TITLES = [c for c in PayeeCategory]
    UNCATEGORIZED_TITLE = ["Uncategorized"]
    PNL_TITLE = ["P&L"]
    GIGS_PNL_TITLE = ["Gigs P&L"]
    TICKET_SALES_TITLE = ["Ticket Sales"]
    ONLINE_AND_WALK_IN_TITLES = ["Online Sales", "Walk In Sales"]
    GIG_COSTS_TITLE = ["Gig Costs"]

    CURRENT_ACCOUNT_TITLE = ["Current Account"]
    CURRENT_ACC_CHECK_TITLE = ["Current Account Check"]
    HEADINGS_BLANKS = ["", "", ""]
    OTHER_ACCOUNTS = ["Savings Account", "BBL", "Charitable Account"]
    ROW_HEADINGS = (HEADINGS_BLANKS +
                    PNL_TITLE + GIGS_PNL_TITLE +
                    [""] * len(TICKET_SALES_TITLE + ONLINE_AND_WALK_IN_TITLES + GIG_COSTS_TITLE) +
                    CURRENT_ACCOUNT_TITLE +
                    [""] * len(CURRENT_ACC_CHECK_TITLE + CATEGORY_TITLES + UNCATEGORIZED_TITLE) +
                    OTHER_ACCOUNTS)
    CAT_1_HEADINGS = (HEADINGS_BLANKS +
                      [""] * len(PNL_TITLE + GIGS_PNL_TITLE) +
                      TICKET_SALES_TITLE +
                      [""] * len(ONLINE_AND_WALK_IN_TITLES) +
                      GIG_COSTS_TITLE +
                      [""] * len(CURRENT_ACCOUNT_TITLE) +
                      CURRENT_ACC_CHECK_TITLE +
                      [""] * len(CATEGORY_TITLES + UNCATEGORIZED_TITLE + OTHER_ACCOUNTS))

    CAT_2_HEADINGS = (HEADINGS_BLANKS +
                      [""] * len(PNL_TITLE + GIGS_PNL_TITLE) +
                      [""] * len(TICKET_SALES_TITLE) +
                      ONLINE_AND_WALK_IN_TITLES +
                      [""] * len(GIG_COSTS_TITLE) +
                      [""] * len(CURRENT_ACCOUNT_TITLE + CURRENT_ACC_CHECK_TITLE) +
                      CATEGORY_TITLES + UNCATEGORIZED_TITLE +
                      [""] * len(OTHER_ACCOUNTS))

    (TITLE_ROW, PERIOD_START_ROW, PERIOD_ROW,

     # P&L
     P_AND_L_ROW,
     GIGS_PNL_ROW,
     TOTAL_TICKET_SALES_ROW,
     ONLINE_TICKET_SALES_ROW,
     WALK_IN_TICKET_SALES_ROW,
     GIG_COSTS_ROW,
     CURRENT_ACCOUNT_ROW,
     CURRENT_ACCOUNT_CHECK_ROW,
     ) = range(11)

    CATEGORY_ROWS = range(CURRENT_ACCOUNT_CHECK_ROW + 1, CURRENT_ACCOUNT_CHECK_ROW + 1 + len(CATEGORY_TITLES))
    (
        ADMINISTRATION_CAT_ROW, AIRTABLE_CAT_ROW, BANK_FEES_CAT_ROW, BANK_INTEREST_CAT_ROW, BAR_STOCK_CAT_ROW,
        BAR_SNACKS_CAT_ROW,
        BB_LOAN_CAT_ROW, BT_CAT_ROW, BUILDING_MAINTENANCE_CAT_ROW, BUILDING_SECURITY_CAT_ROW, CLEANING_CAT_ROW,
        CREDIT_CARD_FEES_CAT_ROW,
        DONATION_CAT_ROW, ELECTRICITY_CAT_ROW, EQUIPMENT_HIRE_CAT_ROW, EQUIPMENT_MAINTENANCE_CAT_ROW,
        EQUIPMENT_PURCHASE_CAT_ROW,
        FIRE_ALARM_CAT_ROW, FLOOD_CAT_ROW, INSURANCE_CAT_ROW, INTERNAL_TRANSFER_CAT_ROW, KASHFLOW_CAT_ROW,
        MAILCHIMP_CAT_ROW, LICENSING_DIRECT_CAT_ROW,
        LICENSING_INDIRECT_CAT_ROW, MARKETING_DIRECT_CAT_ROW, MARKETING_INDIRECT_CAT_ROW, MEMBERSHIPS_CAT_ROW,
        MUSICIAN_COSTS_CAT_ROW,
        MUSICIAN_PAYMENTS_CAT_ROW, MUSIC_VENUE_TRUST_CAT_ROW, OPERATIONAL_COSTS_CAT_ROW, PETTY_CASH_CAT_ROW,
        PIANO_TUNER_CAT_ROW,
        PRS_CAT_ROW, RATES_CAT_ROW, RENT_CAT_ROW, SALARIES_CAT_ROW, SECURITY_CAT_ROW, SERVICES_CAT_ROW, SLACK_CAT_ROW,
        SOUND_ENGINEER_CAT_ROW, SPACE_HIRE_CAT_ROW,
        SUBSCRIPTIONS_CAT_ROW, TELEPHONE_CAT_ROW, THAMES_WATER_CAT_ROW, TICKETWEB_CREDITS_CAT_ROW, TICKET_SALES_CAT_ROW,
        UTILITIES_CAT_ROW,
        VAT_CAT_ROW, WEB_HOST_CAT_ROW, WORK_PERMITS_CAT_ROW, ZETTLE_CREDITS_CAT_ROW,
    ) = CATEGORY_ROWS
    UNCATEGORIZED_ROW = CATEGORY_ROWS[-1] + 1
    (SAVINGS_ROW, BBL_ROW, CHARITABLE_ROW) = range(
        UNCATEGORIZED_ROW + 1,
        UNCATEGORIZED_ROW + 4,
    )

    (ROW_TITLE, CAT_1, CAT_2, PERIOD_1) = range(4)

    NUM_ROWS = CHARITABLE_ROW + 1

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
            self[1:, self.CAT_2].border_request(["right"]),
            self[1:, self.TO_DATE].border_request(["left"]),

            # P&L
            self[self.P_AND_L_ROW:, self.PERIOD_1:].set_decimal_format_request("#,##0"),
            # self.tab.group_rows_request(self.i_first_row + self.WALK_IN_SALES_ROW,
            #                             self.i_first_row + self.SAVINGS_ROW - 1),

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
        values.append((self[2:, self.CAT_1], self.CAT_1_HEADINGS[2:]))
        values.append((self[2:, self.CAT_2], self.CAT_2_HEADINGS[2:]))
        values.append((self[self.TITLE_ROW], [f"Accounts {self.title}"]))

        # To date totals
        for i_row in range(self.P_AND_L_ROW, self.NUM_ROWS):
            period_range = self.period_range(i_row)
            values.append(
                (self[i_row, self.TO_DATE], f"=Sum({period_range.in_a1_notation})")
            )
        return values

    def _sum_rows_text(self, rows: List[int], i_col: int):
        return f"={'+'.join([self[i_row, i_col].in_a1_notation for i_row in rows])}"

    def _category_values(self):
        values = []
        for i_row, category in zip(self.CATEGORY_ROWS, PayeeCategory):
            values.append(
                (self.period_range(i_row),
                 [ct.total_for(category) for ct in self.categorized_transactions_by_sub_period])
            )
        values += [
            (
                self.period_range(self.UNCATEGORIZED_ROW),
                [ct.total_for(None) for ct in self.categorized_transactions_by_sub_period]
            ),
            (
                self.period_range(self.WALK_IN_TICKET_SALES_ROW),
                [gi.total_walk_in_sales for gi in self.gigs_by_sub_period]
            ),
        ]
        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values += [
                (
                    self[self.TOTAL_TICKET_SALES_ROW, i_col],
                    self._sum_rows_text(
                        [self.ONLINE_TICKET_SALES_ROW, self.WALK_IN_TICKET_SALES_ROW],
                        i_col
                    )
                ),
                (
                    self[self.ONLINE_TICKET_SALES_ROW, i_col],
                    self._sum_rows_text(
                        [self.TICKETWEB_CREDITS_CAT_ROW, self.TICKET_SALES_CAT_ROW],
                        i_col
                    )
                ),
            ]
        return values

    def sum_formula(self, first_row: int, last_row: int, i_col: int):
        return f"SUM({self[first_row:last_row + 1, i_col].in_a1_notation})"

    def _p_and_l_values(self):
        values = [
            (
                self.period_range(self.P_AND_L_ROW),
                [
                    f"={self[self.CURRENT_ACCOUNT_ROW, i_col].in_a1_notation} + SUM({self[self.SAVINGS_ROW:self.CHARITABLE_ROW + 1, i_col].in_a1_notation})"
                    for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
                ]
            ),
        ]

        for (i_row, account) in zip(
                [self.CURRENT_ACCOUNT_ROW, self.SAVINGS_ROW, self.BBL_ROW, self.CHARITABLE_ROW],
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
            (self.period_range(self.CURRENT_ACCOUNT_CHECK_ROW),
             [
                 f"={self.sum_formula(self.CATEGORY_ROWS[0], self.UNCATEGORIZED_ROW, i_col)}"
                 for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
             ]
             )
        )

        return values

    def values(self):
        values = self._heading_values() \
                 + self._p_and_l_values() \
                 + self._category_values()

        return values
