from decimal import Decimal
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
    # CATEGORY_TITLES = [c for c in PayeeCategory]
    PNL_TITLE = ["P&L"]
    CURRENT_ACCOUNT_TITLE = ["Current"]
    CURRENT_ACCOUNT_CHECK_TITLE = ["Check"]
    GIGS_PNL_TITLE = ["Gigs"]
    TICKET_SALES_TITLE = ["Ticket Sales"]
    ONLINE_AND_WALK_IN_TITLES = ["Online Sales", "Walk In Sales"]
    GIG_COSTS_TITLE = ["Gig Costs"]
    GIG_COSTS_BREAKDOWN = [
        "Musician Fees", "Security", "Sound Engineer", "PRS", "Marketing", "Work Permits",
        "Piano Tuner", "Musician Costs",
    ]

    BAR_PNL_TITLE = ["Bar"]
    BAR_BREAKDOWN_TITLES = ["Sales", "Purchases", "Zettle Fees"]

    HIRE_PNL_TITLE = ["Hire"]
    MEMBERSHIPS_TITLE = ["Memberships"]
    BUILDING_COSTS_TITLE = ["Building Costs"]
    BUILDING_COSTS_BREAKDOWN_TITLES = [
        "Building Maintenance",
        "Cleaning",
        "Electricity",
        "Rates",
        "Rent",
        "Thames Water",
        "Utilities",
    ]

    MAJOR_COSTS_TITLES = [
        "Accountant",
        "BB Loan",
        "Internal Transfer",
        "Operational Costs",
        "Petty Cash",
        "Salaries",
        "VAT",
    ]

    OTHER_COSTS_TITLE = ["Other Costs"]
    OTHER_COSTS_BREAKDOWN_TITLES = [
        "Airtable", "Bank Fees",
        "Equipment",
        "Fire Alarm",
        "Flood", "Insurance", "Kashflow",
        "Mailchimp", "Licensing",
        "Music Venue Trust",
        "Services", "Slack", "Subscriptions",
        "Telephone",
        "Web Host",
    ]
    UNCATEGORIZED_TITLE = ["Uncategorized"]
    OTHER_ACCOUNT_TITLES = ["Savings", "BBL", "Charitable"]

    HEADINGS_BLANKS = ["", "", ""]
    ROW_HEADINGS = (
            HEADINGS_BLANKS +
            PNL_TITLE +
            [""] * len(CURRENT_ACCOUNT_TITLE + CURRENT_ACCOUNT_CHECK_TITLE) +
            [""] * len(GIGS_PNL_TITLE) +
            [""] * len(TICKET_SALES_TITLE + ONLINE_AND_WALK_IN_TITLES + GIG_COSTS_TITLE) +
            [""] * len(GIG_COSTS_BREAKDOWN) +
            [""] * len(BAR_PNL_TITLE) +
            [""] * len(BAR_BREAKDOWN_TITLES) +
            [""] * len(HIRE_PNL_TITLE + MEMBERSHIPS_TITLE + BUILDING_COSTS_TITLE) +
            [""] * len(BUILDING_COSTS_BREAKDOWN_TITLES) +
            [""] * len(MAJOR_COSTS_TITLES) +
            [""] * len(OTHER_COSTS_TITLE) +
            [""] * len(OTHER_COSTS_BREAKDOWN_TITLES) +
            [""] * len(UNCATEGORIZED_TITLE) +
            [""] * len(OTHER_ACCOUNT_TITLES))
    CAT_1_HEADINGS = (HEADINGS_BLANKS +
                      [""] * len(PNL_TITLE) +
                      CURRENT_ACCOUNT_TITLE +
                      CURRENT_ACCOUNT_CHECK_TITLE +
                      GIGS_PNL_TITLE +
                      [""] * len(TICKET_SALES_TITLE) +
                      [""] * len(ONLINE_AND_WALK_IN_TITLES) +
                      [""] * len(GIG_COSTS_TITLE) +
                      [""] * len(GIG_COSTS_BREAKDOWN) +
                      BAR_PNL_TITLE +
                      [""] * len(BAR_BREAKDOWN_TITLES) +
                      HIRE_PNL_TITLE +
                      MEMBERSHIPS_TITLE +
                      BUILDING_COSTS_TITLE +
                      [""] * len(BUILDING_COSTS_BREAKDOWN_TITLES) +
                      MAJOR_COSTS_TITLES +
                      OTHER_COSTS_TITLE +
                      [""] * len(OTHER_COSTS_BREAKDOWN_TITLES) +
                      UNCATEGORIZED_TITLE +
                      OTHER_ACCOUNT_TITLES
                      )

    CAT_2_HEADINGS = (HEADINGS_BLANKS +
                      [""] * len(PNL_TITLE + CURRENT_ACCOUNT_TITLE + CURRENT_ACCOUNT_CHECK_TITLE + GIGS_PNL_TITLE) +
                      TICKET_SALES_TITLE +
                      [""] * len(ONLINE_AND_WALK_IN_TITLES) +
                      GIG_COSTS_TITLE +
                      [""] * len(GIG_COSTS_BREAKDOWN) +
                      [""] * len(BAR_PNL_TITLE) +
                      BAR_BREAKDOWN_TITLES +
                      [""] * len(HIRE_PNL_TITLE + MEMBERSHIPS_TITLE) +
                      [""] * len(BUILDING_COSTS_TITLE) +
                      BUILDING_COSTS_BREAKDOWN_TITLES +
                      [""] * len(MAJOR_COSTS_TITLES) +
                      [""] * len(OTHER_COSTS_TITLE) +
                      OTHER_COSTS_BREAKDOWN_TITLES +
                      [""] * len(UNCATEGORIZED_TITLE) +
                      [""] * len(OTHER_ACCOUNT_TITLES)
                      )

    CAT_3_HEADINGS = (HEADINGS_BLANKS +
                      [""] * len(PNL_TITLE + CURRENT_ACCOUNT_TITLE + CURRENT_ACCOUNT_CHECK_TITLE + GIGS_PNL_TITLE) +
                      [""] * len(TICKET_SALES_TITLE) +
                      [""] * len(ONLINE_AND_WALK_IN_TITLES) +
                      [""] * len(GIG_COSTS_TITLE) +
                      GIG_COSTS_BREAKDOWN +
                      [""] * len(BAR_PNL_TITLE) +
                      [""] * len(BAR_BREAKDOWN_TITLES) +
                      [""] * len(HIRE_PNL_TITLE + MEMBERSHIPS_TITLE) +
                      [""] * len(BUILDING_COSTS_TITLE) +
                      [""] * len(BUILDING_COSTS_BREAKDOWN_TITLES) +
                      [""] * len(MAJOR_COSTS_TITLES) +
                      [""] * len(OTHER_COSTS_TITLE) +
                      [""] * len(OTHER_COSTS_BREAKDOWN_TITLES) +
                      [""] * len(UNCATEGORIZED_TITLE) +
                      [""] * len(OTHER_ACCOUNT_TITLES)
                      )
    (TITLE_ROW, PERIOD_START_ROW, PERIOD_ROW,

     P_AND_L_ROW,
     CURRENT_ACCOUNT_ROW,
     CURRENT_ACCOUNT_CHECK_ROW,
     GIGS_PNL_ROW,
     TOTAL_TICKET_SALES_ROW,
     ONLINE_TICKET_SALES_ROW,
     WALK_IN_TICKET_SALES_ROW,
     GIG_COSTS_ROW,
     ) = range(11)

    GIG_COSTS_BREAKDOWN_ROWS = range(GIG_COSTS_ROW + 1, GIG_COSTS_ROW + 1 + len(GIG_COSTS_BREAKDOWN))

    (MUSICIAN_FEES_ROW, SECURITY_ROW, SOUND_ENGINEER_ROW, PRS_ROW, MARKETING_ROW, WORK_PERMITS_ROW,
     PIANO_TUNER_ROW, MUSICIAN_COSTS_ROW,) = GIG_COSTS_BREAKDOWN_ROWS

    BAR_PNL_ROW = GIG_COSTS_BREAKDOWN_ROWS[-1] + 1
    BAR_BREAKDOWN_ROWS = list(range(BAR_PNL_ROW + 1, BAR_PNL_ROW + 1 + len(BAR_BREAKDOWN_TITLES)))
    BAR_SALES_ROW, BAR_PURCHASES_ROW, BAR_ZETTLE_FEES_ROW = BAR_BREAKDOWN_ROWS

    HIRE_PNL_ROW = BAR_BREAKDOWN_ROWS[-1] + 1
    MEMBERSHIPS_ROW = HIRE_PNL_ROW + 1
    BUILDING_COSTS_ROW = MEMBERSHIPS_ROW + 1
    BUILDING_COSTS_BREAKDOWN_ROWS = list(
        range(BUILDING_COSTS_ROW + 1, BUILDING_COSTS_ROW + 1 + len(BUILDING_COSTS_BREAKDOWN_TITLES)))
    (
        BUILDING_MAINTENANCE_ROW,
        CLEANING_ROW,
        ELECTRICITY_ROW,
        RATES_ROW,
        RENT_ROW,
        THAMES_WATER_ROW,
        UTILITIES_ROW,
    ) = BUILDING_COSTS_BREAKDOWN_ROWS
    MAJOR_COSTS_BREAKDOWN_ROWS = list(
        range(BUILDING_COSTS_BREAKDOWN_ROWS[-1] + 1, BUILDING_COSTS_BREAKDOWN_ROWS[-1] + 1 + len(MAJOR_COSTS_TITLES)))
    (
        ADMINISTRATION_ROW,
        BB_LOAN_ROW,
        INTERNAL_TRANSFER_ROW,
        OPERATIONAL_COSTS_ROW,
        PETTY_CASH_ROW,
        SALARIES_ROW,
        VAT_ROW,
    ) = MAJOR_COSTS_BREAKDOWN_ROWS

    MINOR_COSTS_ROW = MAJOR_COSTS_BREAKDOWN_ROWS[-1] + 1
    MINOR_COSTS_BREAKDOWN_ROWS = list(
        range(MINOR_COSTS_ROW + 1, MINOR_COSTS_ROW + 1 + len(OTHER_COSTS_BREAKDOWN_TITLES)))

    (AIRTABLE_ROW, BANK_FEES_ROW,
     EQUIPMENT_ROW,
     FIRE_ALARM_ROW, FLOOD_ROW, INSURANCE_ROW, KASHFLOW_ROW,
     MAILCHIMP_ROW, LICENSING_ROW,
     MUSIC_VENUE_TRUST_ROW,
     SERVICES_ROW, SLACK_ROW, SUBSCRIPTIONS_ROW, TELEPHONE_ROW,
     WEB_HOST_ROW) = MINOR_COSTS_BREAKDOWN_ROWS
    UNCATEGORIZED_ROW = MINOR_COSTS_BREAKDOWN_ROWS[-1] + 1
    SAVINGS_ACCOUNT_ROW, BBL_ACCOUNT_ROW, CHARITABLE_ACCOUNT_ROW = range(UNCATEGORIZED_ROW + 1, UNCATEGORIZED_ROW + 4)

    # CURRENT_ACCOUNT_ROW = MINOR_COSTS_BREAKDOWN_ROWS[-1] + 2
    # CURRENT_ACCOUNT_CHECK_ROW = CURRENT_ACCOUNT_ROW + 1

    # CATEGORY_ROWS = range(CURRENT_ACCOUNT_CHECK_ROW + 2, CURRENT_ACCOUNT_CHECK_ROW + 2 + len(CATEGORY_TITLES))
    # (
    #     ADMINISTRATION_CAT_ROW, AIRTABLE_CAT_ROW, BANK_FEES_CAT_ROW, BANK_INTEREST_CAT_ROW, BAR_STOCK_CAT_ROW,
    #     BAR_SNACKS_CAT_ROW,
    #     BB_LOAN_CAT_ROW, BT_CAT_ROW, BUILDING_MAINTENANCE_CAT_ROW, BUILDING_SECURITY_CAT_ROW, CLEANING_CAT_ROW,
    #     CREDIT_CARD_FEES_CAT_ROW,
    #     DONATION_CAT_ROW, ELECTRICITY_CAT_ROW, EQUIPMENT_HIRE_CAT_ROW, EQUIPMENT_MAINTENANCE_CAT_ROW,
    #     EQUIPMENT_PURCHASE_CAT_ROW,
    #     FIRE_ALARM_CAT_ROW, FLOOD_CAT_ROW, INSURANCE_CAT_ROW, INTERNAL_TRANSFER_CAT_ROW, KASHFLOW_CAT_ROW,
    #     MAILCHIMP_CAT_ROW, LICENSING_DIRECT_CAT_ROW,
    #     LICENSING_INDIRECT_CAT_ROW, MARKETING_DIRECT_CAT_ROW, MARKETING_INDIRECT_CAT_ROW, MEMBERSHIPS_CAT_ROW,
    #     MUSICIAN_COSTS_CAT_ROW,
    #     MUSICIAN_PAYMENTS_CAT_ROW, MUSIC_VENUE_TRUST_CAT_ROW, OPERATIONAL_COSTS_CAT_ROW, PETTY_CASH_CAT_ROW,
    #     PIANO_TUNER_CAT_ROW,
    #     PRS_CAT_ROW, RATES_CAT_ROW, RENT_CAT_ROW, SALARIES_CAT_ROW, SECURITY_CAT_ROW, SERVICES_CAT_ROW, SLACK_CAT_ROW,
    #     SOUND_ENGINEER_CAT_ROW, SPACE_HIRE_CAT_ROW,
    #     SUBSCRIPTIONS_CAT_ROW, TELEPHONE_CAT_ROW, THAMES_WATER_CAT_ROW, TICKETWEB_CREDITS_CAT_ROW, TICKET_SALES_CAT_ROW,
    #     UTILITIES_CAT_ROW,
    #     VAT_CAT_ROW, WEB_HOST_CAT_ROW, WORK_PERMITS_CAT_ROW, ZETTLE_CREDITS_CAT_ROW,
    # ) = CATEGORY_ROWS
    # (SAVINGS_ROW, BBL_ROW, CHARITABLE_ROW) = range(
    #     UNCATEGORIZED_ROW + 1,
    #     UNCATEGORIZED_ROW + 4,
    # )

    (ROW_TITLE, CAT_1, INITIAL_BALANCE, TERMINAL_BALANCE, PERIOD_1) = range(5)

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
        super().__init__(top_left_cell, self.NUM_ROWS, len(periods) + 5)
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
            self[self.PERIOD_ROW, self.INITIAL_BALANCE:].right_align_text_request(),
            self[self.PERIOD_ROW].border_request(["bottom"]),
            self[self.TITLE_ROW:self.PERIOD_ROW + 1].set_bold_text_request(),
            self[:, self.ROW_TITLE].set_bold_text_request(),
            self[1:, self.TERMINAL_BALANCE].border_request(["right"]),
            self[1:, self.TO_DATE].border_request(["left"]),

            # P&L
            self[self.P_AND_L_ROW:, self.INITIAL_BALANCE:].set_decimal_format_request("#,##0"),
            # self.tab.group_rows_request(self.i_first_row + self.CURRENT_ACCOUNT_ROW,
            #                             self.i_first_row + self.CHARITABLE_ACCOUNT_ROW),
            self.tab.group_rows_request(self.i_first_row + self.CURRENT_ACCOUNT_CHECK_ROW,
                                        self.i_first_row + self.UNCATEGORIZED_ROW),
            self.tab.group_rows_request(self.i_first_row + self.TOTAL_TICKET_SALES_ROW,
                                        self.i_first_row + self.GIG_COSTS_BREAKDOWN_ROWS[-1]),
            self.tab.group_rows_request(self.i_first_row + self.ONLINE_TICKET_SALES_ROW,
                                        self.i_first_row + self.WALK_IN_TICKET_SALES_ROW),
            self.tab.group_rows_request(self.i_first_row + self.GIG_COSTS_BREAKDOWN_ROWS[0],
                                        self.i_first_row + self.GIG_COSTS_BREAKDOWN_ROWS[-1]),
            self.tab.group_rows_request(self.i_first_row + self.BAR_BREAKDOWN_ROWS[0],
                                        self.i_first_row + self.BAR_BREAKDOWN_ROWS[-1]),
            self.tab.group_rows_request(self.i_first_row + self.MINOR_COSTS_BREAKDOWN_ROWS[0],
                                        self.i_first_row + self.MINOR_COSTS_BREAKDOWN_ROWS[-1]),
            self.tab.group_rows_request(self.i_first_row + self.BUILDING_COSTS_BREAKDOWN_ROWS[0],
                                        self.i_first_row + self.BUILDING_COSTS_BREAKDOWN_ROWS[-1]),

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
        values.append((self[2:, self.INITIAL_BALANCE], self.CAT_2_HEADINGS[2:]))
        values.append((self[2:, self.TERMINAL_BALANCE], self.CAT_3_HEADINGS[2:]))
        values.append((self[2, self.INITIAL_BALANCE], ["Initial"]))
        values.append((self[2, self.TERMINAL_BALANCE], ["Terminal"]))
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

    def _sum_range(self, first_row: int, last_row: int, i_col: int):
        return f"=SUM({self[first_row:last_row + 1, i_col].in_a1_notation})"

    def _category_values(self):
        values = []
        # for i_row, category in zip(self.CATEGORY_ROWS, PayeeCategory):
        #     values.append(
        #         (self.period_range(i_row),
        #          [ct.total_for(category) for ct in self.categorized_transactions_by_sub_period])
        #     )
        values += [
            (
                self.period_range(self.BAR_SALES_ROW),
                [
                    ct.total_for(PayeeCategory.ZETTLE_CREDITS) - Decimal(gi.total_walk_in_sales)
                    for ct, gi in zip(
                    self.categorized_transactions_by_sub_period,
                    self.gigs_by_sub_period
                )
                ]
            ),
            (
                self.period_range(self.WALK_IN_TICKET_SALES_ROW),
                [gi.total_walk_in_sales for gi in self.gigs_by_sub_period]
            ),
        ]
        for (i_row, account) in zip(
                [self.CURRENT_ACCOUNT_ROW, self.SAVINGS_ACCOUNT_ROW, self.BBL_ACCOUNT_ROW, self.CHARITABLE_ACCOUNT_ROW],
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
                        self.bank_activity_by_sub_period[0].restrict_to_account(account).balance_at_sod(
                            self.periods[0].first_day)
                    ]
                )
            )
            values.append(
                (
                    self[i_row, self.TERMINAL_BALANCE],
                    [
                        self.bank_activity_by_sub_period[-1].restrict_to_account(account).balance_at_eod(
                            self.periods[-1].last_day)
                    ]
                )
            )
        for i_col in range(self.INITIAL_BALANCE, self.LAST_PERIOD + 1):
            values += [
                (
                    self[self.P_AND_L_ROW, i_col],
                    self._sum_rows_text(
                        [
                            self.CURRENT_ACCOUNT_ROW, self.SAVINGS_ACCOUNT_ROW, self.BBL_ACCOUNT_ROW,
                            self.CHARITABLE_ACCOUNT_ROW
                        ],
                        i_col
                    )
                ),
            ]
        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values += [
                # (
                #     self[self.CURRENT_ACCOUNT_ROW, i_col],
                #     self._sum_rows_text(
                #         [
                #             self.GIGS_PNL_ROW, self.BAR_PNL_ROW, self.HIRE_PNL_ROW, self.MEMBERSHIPS_ROW,
                #             self.BUILDING_COSTS_ROW, self.ADMINISTRATION_ROW, self.BB_LOAN_ROW, self.SALARIES_ROW,
                #             self.OPERATIONAL_COSTS_ROW, self.PETTY_CASH_ROW, self.VAT_ROW, self.MINOR_COSTS_ROW,
                #         ],
                #         i_col
                #     )
                # ),
                (
                    self[self.CURRENT_ACCOUNT_CHECK_ROW, i_col],
                    self._sum_rows_text(
                        [
                            self.GIGS_PNL_ROW, self.BAR_PNL_ROW, self.HIRE_PNL_ROW, self.MEMBERSHIPS_ROW,
                            self.BUILDING_COSTS_ROW, self.ADMINISTRATION_ROW, self.BB_LOAN_ROW, self.SALARIES_ROW,
                            self.OPERATIONAL_COSTS_ROW, self.PETTY_CASH_ROW, self.VAT_ROW, self.MINOR_COSTS_ROW,
                        ],
                        i_col
                    )
                ),
                (
                    self[self.GIGS_PNL_ROW, i_col],
                    self._sum_rows_text(
                        [self.TOTAL_TICKET_SALES_ROW, self.GIG_COSTS_ROW],
                        i_col
                    )
                ),
                (
                    self[self.TOTAL_TICKET_SALES_ROW, i_col],
                    self._sum_rows_text(
                        [self.ONLINE_TICKET_SALES_ROW, self.WALK_IN_TICKET_SALES_ROW],
                        i_col
                    )
                ),
                (
                    self.period_range(self.ONLINE_TICKET_SALES_ROW),
                    [ct.total_for(PayeeCategory.TICKET_SALES, PayeeCategory.TICKETWEB_CREDITS) for ct in
                     self.categorized_transactions_by_sub_period]
                ),
                (
                    self[self.GIG_COSTS_ROW, i_col],
                    self._sum_range(
                        self.GIG_COSTS_BREAKDOWN_ROWS[0],
                        self.GIG_COSTS_BREAKDOWN_ROWS[-1],
                        i_col
                    )
                ),
                (
                    self[self.BAR_PNL_ROW, i_col],
                    self._sum_rows_text(
                        self.BAR_BREAKDOWN_ROWS,
                        i_col
                    )
                ),
                (
                    self[self.BUILDING_COSTS_ROW, i_col],
                    self._sum_range(
                        self.BUILDING_COSTS_BREAKDOWN_ROWS[0],
                        self.BUILDING_COSTS_BREAKDOWN_ROWS[-1],
                        i_col
                    )
                ),
                (
                    self[self.MINOR_COSTS_ROW, i_col],
                    self._sum_range(
                        self.MINOR_COSTS_BREAKDOWN_ROWS[0],
                        self.MINOR_COSTS_BREAKDOWN_ROWS[-1],
                        i_col
                    )
                ),
            ]
        for row, categories in [
            (self.MUSICIAN_FEES_ROW, [PayeeCategory.MUSICIAN_PAYMENTS]),
            (self.SECURITY_ROW, [PayeeCategory.BUILDING_SECURITY, PayeeCategory.SECURITY]),
            (self.SOUND_ENGINEER_ROW, [PayeeCategory.SOUND_ENGINEER]),
            (self.MARKETING_ROW, [PayeeCategory.MARKETING_DIRECT, PayeeCategory.MARKETING_INDIRECT]),
            (self.WORK_PERMITS_ROW, [PayeeCategory.WORK_PERMITS]),
            (self.PIANO_TUNER_ROW, [PayeeCategory.PIANO_TUNER]),
            (self.MUSICIAN_COSTS_ROW, [PayeeCategory.MUSICIAN_COSTS]),
            (self.BAR_PURCHASES_ROW, [PayeeCategory.BAR_STOCK, PayeeCategory.BAR_SNACKS]),
            (self.BAR_ZETTLE_FEES_ROW, [PayeeCategory.CREDIT_CARD_FEES]),
            (self.HIRE_PNL_ROW, [PayeeCategory.SPACE_HIRE]),
            (self.RATES_ROW, [PayeeCategory.RATES]),
            (self.RENT_ROW, [PayeeCategory.RENT]),
            (self.SALARIES_ROW, [PayeeCategory.SALARIES]),
            (self.VAT_ROW, [PayeeCategory.VAT]),
            (self.CLEANING_ROW, [PayeeCategory.CLEANING]),
            (self.ELECTRICITY_ROW, [PayeeCategory.ELECTRICITY]),
            (self.BB_LOAN_ROW, [PayeeCategory.BB_LOAN]),
            (self.OPERATIONAL_COSTS_ROW, [PayeeCategory.OPERATIONAL_COSTS]),
            (self.PETTY_CASH_ROW, [PayeeCategory.PETTY_CASH]),
            (self.ADMINISTRATION_ROW, [PayeeCategory.ADMINISTRATION]),
            (self.AIRTABLE_ROW, [PayeeCategory.AIRTABLE]),
            (self.BANK_FEES_ROW, [PayeeCategory.BANK_FEES, PayeeCategory.BANK_INTEREST]),
            (self.BUILDING_MAINTENANCE_ROW, [PayeeCategory.BUILDING_MAINTENANCE]),
            (self.EQUIPMENT_ROW,
             [PayeeCategory.EQUIPMENT_HIRE, PayeeCategory.EQUIPMENT_PURCHASE, PayeeCategory.EQUIPMENT_MAINTENANCE]),
            (self.FIRE_ALARM_ROW, [PayeeCategory.FIRE_ALARM]),
            (self.FLOOD_ROW, [PayeeCategory.FLOOD]),
            (self.INSURANCE_ROW, [PayeeCategory.INSURANCE]),
            (self.INTERNAL_TRANSFER_ROW, [PayeeCategory.INTERNAL_TRANSFER]),
            (self.KASHFLOW_ROW, [PayeeCategory.KASHFLOW]),
            (self.MAILCHIMP_ROW, [PayeeCategory.MAILCHIMP]),
            (self.LICENSING_ROW, [PayeeCategory.LICENSING_DIRECT, PayeeCategory.LICENSING_INDIRECT]),
            (self.MEMBERSHIPS_ROW, [PayeeCategory.MEMBERSHIPS]),
            (self.MUSIC_VENUE_TRUST_ROW, [PayeeCategory.MUSIC_VENUE_TRUST]),
            (self.SERVICES_ROW, [PayeeCategory.SERVICES]),
            (self.SLACK_ROW, [PayeeCategory.SLACK]),
            (self.SUBSCRIPTIONS_ROW, [PayeeCategory.SUBSCRIPTIONS]),
            (self.TELEPHONE_ROW, [PayeeCategory.TELEPHONE, PayeeCategory.BT]),
            (self.THAMES_WATER_ROW, [PayeeCategory.THAMES_WATER]),
            (self.UTILITIES_ROW, [PayeeCategory.UTILITIES]),
            (self.WEB_HOST_ROW, [PayeeCategory.WEB_HOST]),
            (self.ONLINE_TICKET_SALES_ROW, [PayeeCategory.TICKET_SALES, PayeeCategory.TICKETWEB_CREDITS]),
            (self.UNCATEGORIZED_ROW, [None]),
        ]:
            values.append(
                (
                    self.period_range(row),
                    [
                        ct.total_for(*categories)
                        for ct in self.categorized_transactions_by_sub_period
                    ]
                )
            )
        return values

    def sum_formula(self, first_row: int, last_row: int, i_col: int):
        return f"SUM({self[first_row:last_row + 1, i_col].in_a1_notation})"

    def _p_and_l_values(self):
        values = []
        # values = [
        #     (
        #         self.period_range(self.P_AND_L_ROW),
        #         [
        #             f"={self[self.CURRENT_ACCOUNT_ROW, i_col].in_a1_notation} + SUM({self[self.SAVINGS_ROW:self.CHARITABLE_ROW + 1, i_col].in_a1_notation})"
        #             for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
        #         ]
        #     ),
        # ]

        # for (i_row, account) in zip(
        #         [self.CURRENT_ACCOUNT_ROW, self.SAVINGS_ROW, self.BBL_ROW, self.CHARITABLE_ROW],
        #         [CURRENT_ACCOUNT, SAVINGS_ACCOUNT, BBL_ACCOUNT, CHARITABLE_ACCOUNT]
        # ):
        #     values.append(
        #         (self.period_range(i_row),
        #          [
        #              bacc.balance_at_eod(period.last_day) - bacc.balance_at_sod(period.first_day)
        #              for ba, period in zip(self.bank_activity_by_sub_period, self.periods)
        #              for bacc in [ba.restrict_to_account(account)]
        #          ]
        #          )
        #     )
        # values.append(
        #     (self.period_range(self.CURRENT_ACCOUNT_CHECK_ROW),
        #      [
        #          f"={self.sum_formula(self.CATEGORY_ROWS[0], self.UNCATEGORIZED_ROW, i_col)}"
        #          for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
        #      ]
        #      )
        # )

        return values

    def values(self):
        values = self._heading_values() \
                 + self._p_and_l_values() \
                 + self._category_values()

        return values
