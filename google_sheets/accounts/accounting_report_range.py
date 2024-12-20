from decimal import Decimal
from typing import List

from accounting.accounting_activity import AccountingActivity
from airtable_db.gigs_info import GigsInfo
from bank_statements import BankActivity
from bank_statements.bank_account import CHARITABLE_ACCOUNT, CURRENT_ACCOUNT, SAVINGS_ACCOUNT, BBL_ACCOUNT
from bank_statements.categorized_transaction import CategorizedTransactions
from bank_statements.payee_categories import PayeeCategory
from date_range import DateRange
from date_range.accounting_month import AccountingMonth
from date_range.week import Week
from google_sheets.accounts.constants import GRANTS, PRS_PAYMENTS, \
    INSURANCE_PAYMENTS
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type, checked_list_type


class AccountingReportRange(TabRange):
    ROW_HEADINGS = [
        # Headings
        "", "", "",
        # P&L
        "P&L",
        # CAP EX
        "Cap Ex", "", "", "",
        # Grants
        "Grants",
        # Insurance Comp
        "Insurance Comp",
        # PRS Special
        "PRS Special",
        # Flood Clearance
        "Flood Clearance",
        "Bank Balance Change",
        # Bank accounts
        "", "", "", "",
        "Expected Bank Balance Change",
        "", "", "", "", "",
        "Gig P&L",
        # Ticket sales
        "", "", "", "", "",

        # gig costs
        "", "", "", "", "", "", "", "", "", "", "", "",
        # Hire fees
        "Hire Fees", "", "",
        # Bar
        "Bar", "", "", "",
        "Rates",
        "Salaries",
        "Rent",
        "Operational Costs",
        "Building Maintenance",
        "VAT Payments",
        # Costs
        "Regular Costs", "", "", "", "", "",
        "", "", "", "", "", "", "", "", "", "",
        "", "", "", "", "", "", "", "", "", "",
        "", "", "", "", "", "", "",
    ]
    CAT_1_HEADINGS = [
        "", "", "",
        # Calculated P&L
        "",
        # CAP EX
        "", "Building works", "Downstairs works", "Equipment",
        # Grants
        "",
        # Insurance Comp
        "",
        # PRS Special
        "",
        # Flood Clearance
        "",
        # Bank Balance change
        "",
        "Current", "Savings", "BBL", "Charitable",
        # Expected Bank P&L
        "",
        "Bank Ticket Sales",
        "Walk in Sales",
        "Ticket Sales Discrepancy",
        "Uncategorised Transactions",
        "Unexplained Bank Movements",
        # Gig P&L
        "",
        "Ticket Sales",
        "", "", "", "",
        # gig costs
        "Gig costs", "", "", "", "", "", "", "", "", "", "", "",
        # Hire fees
        "", "Evening", "Day",
        # Bar
        "", "Sales", "Purchases", "Zettle Fees",
        # Rates, Salaries, Rent, Operational Costs, Building Maintenance
        "", "", "", "", "",
        # VAT Payments
        "",
        # Costs
        "",
        "Cleaning",
        "BB Loan Payment",
        "Electricity",
        "Insurance",
        "Rentokil",
        "Waste Collection",
        "Telephone",
        "Licensing - Indirect",
        "Bank Fees",
        "Bank Interest",
        "Bin Hire",
        "Consolidated Door Security",
        "Alarm (Fowler's)",
        "Equipment Maintenance",
        "Kashflow",
        "Administration",
        "Airtable",
        "BT",
        "Donation",
        "Equipment Hire",
        "Fire Alarm",
        "Internal Transfer",
        "Mailchimp",
        "Licensing - Direct",
        "Memberships",
        "Music Venue Trust",
        "Petty Cash",
        "Slack",
        "Subscriptions",
        "Thames Water",
        "Utilities",
        "Web Host",
    ]
    CAT_2_HEADINGS = [
        "", "", "",
        # Calculated P&L
        "",
        # CAP EX
        "", "", "", "",
        # Grants
        "",
        # Insurance Comp
        "",
        # PRS Special
        "",
        # Flood Clearance
        "",
        # Bank P&L
        "",
        "", "", "", "",
        # Expected Bank P&L
        "",
        "", "", "", "", "",
        # Gig P&L
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
        "Piano Tuning",
        "Other Costs",
        "Accommodation", "Travel", "Catering",
        # Hire fees
        "", "", "",
        # Bar
        "", "", "", "",
        # Rates, Salaries, Rent, Operational Costs, Building Maintenance
        "", "", "", "", "",
        # VAT Payments
        "",
        # Costs
        "", "", "", "", "", "",
        "", "", "", "", "", "", "", "", "",
        "", "", "", "", "", "", "", "", "", "",
        "", "", "", "", "", "", "",
    ]
    (TITLE, PERIOD_START, PERIOD,

     # P&L
     P_AND_L,

     # CAP EX
     CAP_EX,
     BUILDING_WORKS, DOWNSTAIRS_WORKS, EQUIPMENT_PURCHASE,

     # Other credits
     GRANTS,
     INSURANCE_COMP,
     PRS_SPECIAL,
     FLOOD_CLEARANCE,

     # Bank accounts
     BANK_P_AND_L,
     CURRENT_ACC_P_AND_L, SAVINGS_ACC_P_AND_L, BBL_P_AND_L, CHARITABLE_ACC_P_AND_L,

     EXPECTED_BANK_P_AND_L,
     BANK_TICKET_SALES,
     WALK_IN_SALES,
     TICKET_SALES_DISCREPANCY,
     UNCATEGORISED_TRANSACTIONS,
     UNEXPLAINED_BANK_MOVEMENTS,

     # Gig P&L
     GIG_P_AND_L,
     TICKET_SALES_TOTAL,
     FULL_PRICE_SALES, MEMBER_SALES, CONC_SALES, OTHER_TICKET_SALES,
     GIG_COSTS,
     MUSICIAN_FEES, SECURITY, SOUND_ENGINEERING, PRS, MARKETING, WORK_PERMITS, PIANO_TUNING,
     OTHER_COSTS,
     ACCOMMODATION, TRAVEL, CATERING,

     # Hire fees
     HIRE_FEES,
     EVENING_HIRE_FEES, DAY_HIRE_FEES,

     # Bar
     BAR_P_AND_L,
     BAR_SALES, BAR_PURCHASES, ZETTLE_FEES,

     # Other costs
     RATES,
     SALARIES,
     RENT,
     OPERATIONAL_COSTS,
     BUILDING_MAINTENANCE,
     VAT_PAYMENTS,
     COSTS_TOTAL,
     DAILY_CLEANING,
     BB_LOAN,
     ELECTRICITY,
     INSURANCE,
     RENTOKIL,
     WASTE_COLLECTION,
     TELEPHONE,
     LICENSING_INDIRECT,
     BANK_FEES,
     BANK_INTEREST,
     BIN_HIRE,
     CONSOLIDATED_DOOR_SECURITY,
     FOWLERS_ALARM,
     EQUIPMENT_MAINTENANCE,
     KASHFLOW,
     ADMINISTRATION,
     AIRTABLE,
     BT,
     DONATION,
     EQUIPMENT_HIRE,
     FIRE_ALARM,
     INTERNAL_TRANSFER,
     MAILCHIMP,
     LICENSING_DIRECT,
     MEMBERSHIPS,
     MUSIC_VENUE_TRUST,
     PETTY_CASH,
     SLACK,
     SUBSCRIPTIONS,
     THAMES_WATER,
     UTILITIES,
     WEB_HOST

     ) = range(len(ROW_HEADINGS))

    (ROW_TITLE, CAT_1, CAT_2, PERIOD_1) = range(4)

    def __init__(
            self,
            top_left_cell: TabCell,
            title: str,
            periods: List[DateRange],
            period_titles: List[str],
            accounting_activity: AccountingActivity,
            categorized_transactions: CategorizedTransactions,
            vat_rate: float
    ):
        super().__init__(top_left_cell, len(self.ROW_HEADINGS), len(periods) + 4)
        self.title = checked_type(title, str)
        self.periods: List[DateRange] = checked_list_type(periods, DateRange)
        self.period_titles: List[str] = checked_list_type(period_titles, str)
        self.num_periods: int = len(self.periods)
        self.gigs_by_sub_period: list[GigsInfo] = [
            accounting_activity.gigs_info.restrict_to_period(period)
            for period in self.periods
        ]
        # self.ledger_by_sub_period: list[NominalLedger] = [
        #     accounting_activity.nominal_ledger.restrict_to_period(period)
        #     for period in self.periods
        # ]
        self.bank_activity_by_sub_period: list[BankActivity] = [
            accounting_activity.bank_activity.restrict_to_period(period)
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
            self[self.TITLE].merge_columns_request(),
            self[self.TITLE].center_text_request(),
            self[self.PERIOD_START].date_format_request("d Mmm"),
            self[self.PERIOD, self.PERIOD_1:].right_align_text_request(),
            self[self.PERIOD].border_request(["bottom"]),
            self[self.TITLE:self.PERIOD + 1].set_bold_text_request(),
            self[:, self.ROW_TITLE].set_bold_text_request(),
            self[1:, self.CAT_2].border_request(["right"]),
            self[1:, self.TO_DATE].border_request(["left"]),

            # P&L
            self[self.P_AND_L:, self.PERIOD_1:].set_decimal_format_request("#,##0"),
            self.tab.group_rows_request(self.i_first_row + self.CURRENT_ACC_P_AND_L,
                                        self.i_first_row + self.CHARITABLE_ACC_P_AND_L),

            self[self.FLOOD_CLEARANCE].border_request(["bottom"]),
            self[self.UNEXPLAINED_BANK_MOVEMENTS].border_request(["bottom"]),
            self.tab.group_rows_request(self.i_first_row + self.BANK_TICKET_SALES,
                                        self.i_first_row + self.UNEXPLAINED_BANK_MOVEMENTS),
            # Gig P&L
            self.tab.group_rows_request(self.i_first_row + self.TICKET_SALES_TOTAL,
                                        self.i_first_row + self.CATERING),
            # Ticket sales (money)
            self.tab.group_rows_request(self.i_first_row + self.FULL_PRICE_SALES,
                                        self.i_first_row + self.OTHER_TICKET_SALES),
            self[self.TICKET_SALES_TOTAL, 0].right_align_text_request(),

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

            # Bar
            self.tab.group_rows_request(self.i_first_row + self.BAR_SALES,
                                        self.i_first_row + self.ZETTLE_FEES),
            # CAP EX
            self.tab.group_rows_request(self.i_first_row + self.BUILDING_WORKS,
                                        self.i_first_row + self.EQUIPMENT_PURCHASE),
            # Costs
            self.tab.group_rows_request(self.i_first_row + self.DAILY_CLEANING,
                                        self.i_first_row + self.WEB_HOST),

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
        values.append((
            self.period_range(self.PERIOD_START),
            [w.first_day.date for w in self.periods]
        ))
        values.append((self[2:, self.CAT_1], self.CAT_1_HEADINGS[2:]))
        values.append((self[2:, self.CAT_2], self.CAT_2_HEADINGS[2:]))
        values.append((self[self.TITLE], [f"Accounts {self.title}"]))

        # To date totals
        for i_row in range(self.P_AND_L, self.NUM_ROWS):
            period_range = self.period_range(i_row)
            values.append(
                (self[i_row, self.TO_DATE], f"=Sum({period_range.in_a1_notation})")
            )
        return values

    def _ticket_sales_values(self):
        values = [
            (
                self.period_range(self.TICKET_SALES_TOTAL),
                [
                    ct.total_for(PayeeCategory.TICKET_SALES, PayeeCategory.TICKETWEB_CREDITS)
                    + Decimal(gi.total_walk_in_sales)
                    for ct, gi in zip(self.categorized_transactions_by_sub_period, self.gigs_by_sub_period)
                ]
                # [
                #     f"=SUM({self[self.FULL_PRICE_SALES:self.OTHER_TICKET_SALES + 1, i_col].in_a1_notation})"
                #     for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
                # ]
            )
        ]
        # for i_row, level in [
        #     (self.FULL_PRICE_SALES, TicketPriceLevel.FULL),
        #     (self.MEMBER_SALES, TicketPriceLevel.MEMBER),
        #     (self.CONC_SALES, TicketPriceLevel.CONCESSION)
        # ]:
        #     values.append(
        #         (self.period_range(i_row), [gig.ticket_sales(level) for gig in self.gigs_by_sub_period])
        #     )
        #
        # # Other ticket sales
        # values.append(
        #     (self.period_range(self.OTHER_TICKET_SALES), [gig.other_ticket_sales for gig in self.gigs_by_sub_period])
        # )
        return values

    def sum_formula(self, first_row: int, last_row: int, i_col: int):
        return f"SUM({self[first_row:last_row + 1, i_col].in_a1_notation})"

    def _gig_costs_values(self):
        values = []
        for (i_row, category) in [
            (self.MUSICIAN_FEES, PayeeCategory.MUSICIAN_PAYMENTS),
            (self.ACCOMMODATION, PayeeCategory.MUSICIAN_COSTS),
            # (self.TRAVEL, lambda gig: -gig.band_transport),
            # (self.CATERING, lambda gig: -gig.band_catering / (1 + self.vat_rate)),
            (self.PRS, PayeeCategory.PRS),
        ]:
            values.append(
                (self.period_range(i_row),
                 [ct.total_for(category) for ct in self.categorized_transactions_by_sub_period])
            )
        for (i_row, category, subtract_vat) in [
            (self.SOUND_ENGINEERING, PayeeCategory.SOUND_ENGINEER, False),
            (self.PIANO_TUNING, PayeeCategory.PIANO_TUNER, True),
            (self.WORK_PERMITS, PayeeCategory.WORK_PERMITS, False),
        ]:
            vat_adjustment = Decimal(1.0 + self.vat_rate) if subtract_vat else Decimal(1.0)
            values.append(
                (
                    self.period_range(i_row),
                    [ct.total_for(category) / vat_adjustment for ct in
                     self.categorized_transactions_by_sub_period]
                )
            )

        values.append(
            (
                self.period_range(self.MARKETING),
                [
                    cat_trans.total_for(PayeeCategory.MARKETING_INDIRECT, PayeeCategory.MARKETING_DIRECT)
                    for cat_trans in
                    self.categorized_transactions_by_sub_period
                ]
            )
        )
        values.append(
            (
                self.period_range(self.SECURITY),
                [
                    cat_trans.total_for(PayeeCategory.BUILDING_SECURITY, PayeeCategory.SECURITY)
                    for cat_trans in
                    self.categorized_transactions_by_sub_period
                ]
            )
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
        # values = [
        #     (
        #         self.period_range(self.HIRE_FEES),
        #         [
        #             f"=SUM({self[self.EVENING_HIRE_FEES:self.DAY_HIRE_FEES + 1, i_col].in_a1_notation})"
        #             for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
        #         ]
        #     )
        # ]
        values = [
            (
                self.period_range(self.HIRE_FEES),
                [ct.total_for(PayeeCategory.SPACE_HIRE) / Decimal(1 + self.vat_rate) for ct in
                 self.categorized_transactions_by_sub_period]
            ),
        ]
        return values

    def _grant_and_prs_values(self):
        values = []
        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values += [
                (
                    (
                        self.period_range(self.GRANTS),
                        [GRANTS.total_for_period(period) for period in self.periods]
                    )
                ),
                (
                    (
                        self.period_range(self.INSURANCE_COMP),
                        [INSURANCE_PAYMENTS.total_for_period(period) for period in self.periods]
                    )
                ),
                (
                    (
                        self.period_range(self.PRS_SPECIAL),
                        [PRS_PAYMENTS.total_for_period(period) for period in self.periods]
                    )
                )
            ]
        return values

    def _bar_values(self):
        values = []
        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values += [
                (
                    self[self.BAR_P_AND_L, i_col],
                    "=" +
                    "+".join(
                        [self[i_row, i_col].in_a1_notation
                         for i_row in [self.BAR_SALES, self.BAR_PURCHASES, self.ZETTLE_FEES]
                         ]
                    )
                ),
            ]
        values += [
            (
                self.period_range(self.BAR_SALES),
                [
                    ct.total_for(PayeeCategory.ZETTLE_CREDITS) - Decimal(gi.total_walk_in_sales)
                    for ct, gi in zip(self.categorized_transactions_by_sub_period, self.gigs_by_sub_period)
                ]
                # [gig.bar_takings / (1 + self.vat_rate) for gig in self.gigs_by_sub_period]
            ),
            (
                self.period_range(self.BAR_PURCHASES),
                [
                    ct.total_for(PayeeCategory.BAR_STOCK, PayeeCategory.BAR_SNACKS) / Decimal(1 + self.vat_rate)
                    for ct in self.categorized_transactions_by_sub_period
                ]
            ),
            (
                self.period_range(self.ZETTLE_FEES),
                [
                    cat_trans.total_for(PayeeCategory.CREDIT_CARD_FEES)
                    for cat_trans in self.categorized_transactions_by_sub_period
                ]
            )
        ]
        return values

    def _cap_ex_values(self):
        values = []
        for (i_row, category) in [
            (self.BUILDING_WORKS, PayeeCategory.BUILDING_MAINTENANCE),
            (self.EQUIPMENT_PURCHASE, PayeeCategory.EQUIPMENT_PURCHASE),
        ]:
            values.append(
                (self.period_range(i_row),
                 [ct.total_for(category) / Decimal(1.0 + self.vat_rate) for ct in
                  self.categorized_transactions_by_sub_period])
            )
        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values.append(
                (
                    self[self.CAP_EX, i_col],
                    f"={self.sum_formula(self.BUILDING_WORKS, self.EQUIPMENT_PURCHASE, i_col)}"
                )
            )
        return values

    def _exceptional_values(self):
        values = []
        for (i_row, category) in [
            (self.FLOOD_CLEARANCE, PayeeCategory.FLOOD),
        ]:
            values.append(
                (self.period_range(i_row),
                 [ct.total_for(category) / Decimal(1.0 + self.vat_rate) for ct in
                  self.categorized_transactions_by_sub_period])
            )
        return values

    def _costs_values(self):
        values = []
        if isinstance(self.periods[0], Week):
            is_weekly = True
        elif isinstance(self.periods[0], AccountingMonth):
            is_weekly = False
        else:
            raise ValueError(f"Unexpected period type {type(self.periods[0])}")

        def period_cost(monthly_cost):
            if is_weekly:
                return monthly_cost / self.num_periods
            else:
                return monthly_cost

        values += [
            # (self.period_range(self.RENT), [period_cost(-MONTHLY_RENT) for _ in range(self.num_periods)]),
            # (self.period_range(self.RENTOKIL), [period_cost(-MONTHLY_RENTOKILL) for _ in range(self.num_periods)]),
            # (self.period_range(self.WASTE_COLLECTION),
            #  [period_cost(-MONTHLY_WASTE_COLLECTION) for _ in range(self.num_periods)]),
            # (
            #     self.period_range(self.BIN_HIRE),
            #     [period_cost(-MONTHLY_BIN_HIRE_EX_VAT) for _ in range(self.num_periods)]),
            # (self.period_range(self.CONSOLIDATED_DOOR_SECURITY),
            #  [period_cost(-MONTHLY_DOOR_SECURITY) for _ in range(self.num_periods)]),
            # (self.period_range(self.FOWLERS_ALARM),
            #  [period_cost(-MONTHLY_FOWLERS_ALARM) for _ in range(self.num_periods)]),
        ]
        for (i_row, category, subtract_vat) in [
            # (self.RENTOKIL, PayeeCategory.RENT, False),
            (self.RENT, PayeeCategory.RENT, False),
            (self.TELEPHONE, PayeeCategory.TELEPHONE, True),
            (self.SALARIES, PayeeCategory.SALARIES, False),
            (self.DAILY_CLEANING, PayeeCategory.CLEANING, True),
            (self.EQUIPMENT_HIRE, PayeeCategory.EQUIPMENT_HIRE, True),
            (self.FIRE_ALARM, PayeeCategory.FIRE_ALARM, True),
            (self.INTERNAL_TRANSFER, PayeeCategory.INTERNAL_TRANSFER, False),
            (self.MAILCHIMP, PayeeCategory.MAILCHIMP, False),
            (self.EQUIPMENT_MAINTENANCE, PayeeCategory.EQUIPMENT_MAINTENANCE, True),
            (self.OPERATIONAL_COSTS, PayeeCategory.OPERATIONAL_COSTS, True),
            (self.BUILDING_MAINTENANCE, PayeeCategory.BUILDING_MAINTENANCE, True),
            (self.LICENSING_INDIRECT, PayeeCategory.LICENSING_INDIRECT, True),
            (self.LICENSING_DIRECT, PayeeCategory.LICENSING_DIRECT, True),
            (self.MEMBERSHIPS, PayeeCategory.MEMBERSHIPS, True),
            (self.MUSIC_VENUE_TRUST, PayeeCategory.MUSIC_VENUE_TRUST, True),
            (self.PETTY_CASH, PayeeCategory.PETTY_CASH, True),
            (self.SLACK, PayeeCategory.SLACK, True),
            (self.SUBSCRIPTIONS, PayeeCategory.SUBSCRIPTIONS, True),
            (self.THAMES_WATER, PayeeCategory.THAMES_WATER, True),
            (self.UTILITIES, PayeeCategory.UTILITIES, True),
            (self.WEB_HOST, PayeeCategory.WEB_HOST, True),
            (self.RATES, PayeeCategory.RATES, False),
            (self.ELECTRICITY, PayeeCategory.ELECTRICITY, True),
            (self.INSURANCE, PayeeCategory.INSURANCE, False),
            (self.KASHFLOW, PayeeCategory.KASHFLOW, True),
            (self.ADMINISTRATION, PayeeCategory.ADMINISTRATION, True),
            (self.AIRTABLE, PayeeCategory.AIRTABLE, True),
            (self.BT, PayeeCategory.BT, True),
            (self.DONATION, PayeeCategory.DONATION, False),
            (self.BB_LOAN, PayeeCategory.BB_LOAN, False),
            (self.BANK_FEES, PayeeCategory.BANK_FEES, False),
            (self.BANK_INTEREST, PayeeCategory.BANK_INTEREST, False),
        ]:
            vat_adjustment = Decimal(1.0 + self.vat_rate) if subtract_vat else Decimal(1.0)
            values.append(
                (
                    self.period_range(i_row),
                    [
                        cat_trans.total_for(category) / vat_adjustment
                        for cat_trans in self.categorized_transactions_by_sub_period
                    ]
                )
            )

        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values.append(
                (
                    self[self.COSTS_TOTAL, i_col],
                    f"={self.sum_formula(self.DAILY_CLEANING, self.WEB_HOST, i_col)}"
                )
            )
        return values

    def _p_and_l_values(self):
        values = [
            (
                self.period_range(self.BANK_P_AND_L),
                [
                    f"=SUM({self[self.CURRENT_ACC_P_AND_L:self.CHARITABLE_ACC_P_AND_L + 1, i_col].in_a1_notation})"
                    for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
                ]
            ),
            (
                self.period_range(self.VAT_PAYMENTS),
                [
                    ba.total_for(PayeeCategory.VAT) for ba in self.categorized_transactions_by_sub_period
                ]
            ),

        ]

        for (i_row, account) in zip(
                [self.CURRENT_ACC_P_AND_L, self.SAVINGS_ACC_P_AND_L, self.BBL_P_AND_L, self.CHARITABLE_ACC_P_AND_L],
                [CURRENT_ACCOUNT, SAVINGS_ACCOUNT, BBL_ACCOUNT, CHARITABLE_ACCOUNT]
        ):
            values.append(
                (self.period_range(i_row),
                 [
                     bacc.balance_at_eod(period.last_day) - bacc.balance_at_sod(period.first_day)
                     for ba, period in zip(self.bank_activity_by_sub_period, self.periods)
                     for bacc in [ba.restrict_to_accounts(account)]
                 ]
                 )
            )

        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values.append(
                (
                    self[self.P_AND_L, i_col],
                    "=" +
                    "+".join(
                        [self[i_row, i_col].in_a1_notation
                         for i_row in
                         [self.GIG_P_AND_L, self.HIRE_FEES, self.BAR_P_AND_L,
                          self.RATES,
                          self.SALARIES, self.RENT, self.OPERATIONAL_COSTS, self.BUILDING_MAINTENANCE,
                          self.VAT_PAYMENTS, self.COSTS_TOTAL]
                         ]
                    )
                ),
            )
            values.append(
                (
                    self[self.EXPECTED_BANK_P_AND_L, i_col],
                    "=" +
                    "+".join(
                        [self[i_row, i_col].in_a1_notation
                         for i_row in
                         [
                             self.P_AND_L,
                             self.CAP_EX,
                             self.GRANTS, self.INSURANCE_COMP, self.PRS_SPECIAL,
                             self.FLOOD_CLEARANCE
                         ]]
                    )
                ),
            )
        return values

    def _bank_balance_changes_values(self):
        values = [
            (
                self.period_range(self.BANK_TICKET_SALES),
                [
                    ct.total_for(PayeeCategory.TICKETWEB_CREDITS, PayeeCategory.TICKET_SALES) for ct in
                    self.categorized_transactions_by_sub_period
                ]
            ),
            (
                self.period_range(self.WALK_IN_SALES),
                [
                    gi.total_walk_in_sales for gi in self.gigs_by_sub_period
                ]
            ),
            (
                self.period_range(self.TICKET_SALES_DISCREPANCY),
                [
                    f"={self[self.TICKET_SALES_TOTAL, i_col].in_a1_notation} - ({self[self.BANK_TICKET_SALES, i_col].in_a1_notation} - {self[self.WALK_IN_SALES, i_col].in_a1_notation})"
                    for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1)
                ]
            ),
            (
                self.period_range(self.UNCATEGORISED_TRANSACTIONS),
                [
                    ct.total_for(None) for ct in self.categorized_transactions_by_sub_period
                ]
            ),

        ]
        return values

    def values(self):
        values = self._heading_values() \
                 + self._ticket_sales_values() \
                 + self._gig_costs_values() \
                 + self._hire_fee_values() \
                 + self._grant_and_prs_values() \
                 + self._bar_values() \
                 + self._costs_values() \
                 + self._cap_ex_values() \
                 + self._exceptional_values() \
                 + self._p_and_l_values() \
                 + self._bank_balance_changes_values()

        return values
