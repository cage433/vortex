from numbers import Number
from typing import List

from airtable_db.contracts_and_events import GigsInfo
from airtable_db.table_columns import TicketPriceLevel
from bank_statements import BankActivity
from bank_statements.payee_categories import PayeeCategory
from date_range import DateRange
from google_sheets import Tab, Workbook
from google_sheets.tab_range import TabRange, TabCell
from google_sheets.tim_replication.audience_report_range import AudienceReportRange
from google_sheets.tim_replication.constants import VAT_RATE, QUARTERLY_RENT, QUARTERLY_RENTOKILL, \
    QUARTERLY_WASTE_COLLECTION, QUARTERLY_BIN_HIRE_EX_VAT, YEARLY_DOOR_SECURITY, MONTHLY_FOWLERS_ALARM
from kashflow.nominal_ledger import NominalLedger, NominalLedgerItemType
from utils import checked_type, checked_list_type


class AccountingReportRange(TabRange):
    ROW_HEADINGS = [
        # Headings
        "", "", "",
        # P&L
        "P&L",
        "Gigs",
        # Ticket sales (money)
        "Ticket Sales", "", "", "", "",

        # gig costs
        "Gig costs", "", "", "", "", "", "", "", "", "", "", "",
        # Hire fees
        "Hire Fees", "", "",
        # Bar
        "Bar", "", "", "", "", "",
        # CAP EX
        "Cap Ex", "", "", "",
        # Costs
        "Costs", "", "", "", "", "", "", "", "", "", "",
        "", "", "", "", "", "", "", "", "", "",
    ]
    CAT_1_HEADINGS = [
        "", "", "Breakdown 1",
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
        "Piano Tuning",
        "Other Costs",
        "",
        "",
        "",
        # Hire fees
        "", "Evening", "Day",
        # Bar
        "", "Sales", "Purchases", "", "", "Zettle Fees",
        # CAP EX
        "", "Building works", "Downstairs works", "Equipment",
        # Costs
        "",
        "Salaries",
        "Rent",
        "Rates",
        "Cleaning",
        "Operational Costs",
        "BB Loan Payment",
        "Electricity",
        "Insurance",
        "Building Maintenance",
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
    ]
    CAT_2_HEADINGS = [
        "", "", "Breakdown 2",
        # P&L
        "",
        "",
        # Ticket sales (money)
        "", "", "", "", "",
        # gig costs
        "", "", "", "", "", "", "", "",
        "", "Accommodation", "Travel", "Catering",
        # Hire fees
        "", "", "",
        # Bar
        "", "", "", "Evening", "Delivered", "",
        # CAP EX
        "", "", "", "",
        # Costs
        "", "", "", "", "", "", "", "", "", "", "",
        "", "", "", "", "", "", "", "", "",
    ]
    (TITLE, _, PERIOD,
     P_AND_L,
     GIG_P_AND_L,
     TICKET_SALES_TOTAL, FULL_PRICE_SALES, MEMBER_SALES, CONC_SALES, OTHER_TICKET_SALES,
     GIG_COSTS, MUSICIAN_FEES,
     WORK_PERMITS,
     SECURITY,
     SOUND_ENGINEERING, PRS, MARKETING,
     PIANO_TUNING,
     OTHER_COSTS, ACCOMMODATION, TRAVEL, CATERING,

     HIRE_FEES, EVENING_HIRE_FEES, DAY_HIRE_FEES,

     BAR_P_AND_L, BAR_SALES, BAR_PURCHASES, BAR_EVENING, BAR_DELIVERED, ZETTLE_FEES,

     CAP_EX, BUILDING_WORKS, DOWNSTAIRS_WORKS, EQUIPMENT_PURCHASE,

     COSTS_TOTAL,
     SALARIES,
     RENT,
     RATES,
     DAILY_CLEANING,
     OPERATIONAL_COSTS,
     BB_LOAN,
     ELECTRICITY,
     INSURANCE,
     BUILDING_MAINTENANCE,
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

            # P&L
            self[self.P_AND_L].border_request(["top", "bottom"]),
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
                                        self.i_first_row + self.ZETTLE_FEES),
            self.tab.group_rows_request(self.i_first_row + self.BAR_EVENING,
                                        self.i_first_row + self.BAR_DELIVERED),
            # CAP EX
            self[self.CAP_EX].border_request(["top"]),
            self.tab.group_rows_request(self.i_first_row + self.BUILDING_WORKS,
                                        self.i_first_row + self.EQUIPMENT_PURCHASE),
            # Costs
            self[self.COSTS_TOTAL].border_request(["top"]),
            self.tab.group_rows_request(self.i_first_row + self.SALARIES,
                                        self.i_first_row + self.KASHFLOW),

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
        for i_row in range(self.P_AND_L, self.NUM_ROWS):
            week_range = self.period_range(i_row)
            values.append(
                (self[i_row, self.TO_DATE], f"=Sum({week_range.in_a1_notation})")
            )
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
            (self.PIANO_TUNING, lambda ledger: ledger.piano_tuning),
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
                    "=" +
                    "+".join(
                        [self[i_row, i_col].in_a1_notation
                         for i_row in [self.BAR_SALES, self.BAR_PURCHASES, self.ZETTLE_FEES]
                         ]
                    )
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
            ),
            (
                self.period_range(self.ZETTLE_FEES),
                [activity.net_amount_for_category(PayeeCategory.CREDIT_CARD_FEES)
                 for activity in self.bank_activity_by_sub_period]
            )
        ]
        return values

    def _cap_ex_values(self):
        values = []
        for (i_row, ledger_item) in [
            (self.BUILDING_WORKS, NominalLedgerItemType.BUILDING_WORKS),
            (self.DOWNSTAIRS_WORKS, NominalLedgerItemType.DOWNSTAIRS_BUILDING_WORKS),
            (self.EQUIPMENT_PURCHASE, NominalLedgerItemType.EQUIPMENT_PURCHASE),
        ]:
            values.append(
                (self.period_range(i_row), [ledger.total_for(ledger_item) for ledger in self.ledger_by_sub_period])
            )
        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values.append(
                (
                    self[self.CAP_EX, i_col],
                    f"={self.sum_formula(self.BUILDING_WORKS, self.EQUIPMENT_PURCHASE, i_col)}"
                )
            )
        return values

    def _costs_values(self):
        values = []
        values += [
            (self.period_range(self.RENT), [-QUARTERLY_RENT / 3.0 for _ in range(self.num_periods)]),
            (self.period_range(self.RENTOKIL), [-QUARTERLY_RENTOKILL / 3.0 for _ in range(self.num_periods)]),
            (self.period_range(self.WASTE_COLLECTION),
             [-QUARTERLY_WASTE_COLLECTION / 3.0 for _ in range(self.num_periods)]),
            (self.period_range(self.BIN_HIRE), [-QUARTERLY_BIN_HIRE_EX_VAT / 3.0 for _ in range(self.num_periods)]),
            (self.period_range(self.CONSOLIDATED_DOOR_SECURITY),
             [-YEARLY_DOOR_SECURITY / 12.0 for _ in range(self.num_periods)]),
            (self.period_range(self.FOWLERS_ALARM), [-MONTHLY_FOWLERS_ALARM for _ in range(self.num_periods)]),
        ]
        for (i_row, ledger_item) in [
            (self.TELEPHONE, NominalLedgerItemType.TELEPHONE),
            (self.SALARIES, NominalLedgerItemType.STAFF_COSTS),
            (self.DAILY_CLEANING, NominalLedgerItemType.CLEANING),
            (self.BUILDING_MAINTENANCE, NominalLedgerItemType.BUILDING_MAINTENANCE),
            (self.EQUIPMENT_PURCHASE, NominalLedgerItemType.EQUIPMENT_PURCHASE),
            (self.EQUIPMENT_MAINTENANCE, NominalLedgerItemType.EQUIPMENT_MAINTENANCE),
            (self.OPERATIONAL_COSTS, NominalLedgerItemType.OPERATIONAL_COSTS),
            (self.LICENSING_INDIRECT, NominalLedgerItemType.LICENSING_INDIRECT),
        ]:
            values.append(
                (self.period_range(i_row), [ledger.total_for(ledger_item) for ledger in self.ledger_by_sub_period])
            )

        for (i_row, category, subtract_vat) in [
            (self.RATES, PayeeCategory.RATES, False),
            (self.ELECTRICITY, PayeeCategory.ELECTRICITY, True),
            (self.INSURANCE, PayeeCategory.INSURANCE, False),
            (self.KASHFLOW, PayeeCategory.KASHFLOW, True),
            (self.BB_LOAN, PayeeCategory.BB_LOAN, False),
            (self.BANK_FEES, PayeeCategory.BANK_FEES, False),
            (self.BANK_INTEREST, PayeeCategory.BANK_INTEREST, False),
        ]:
            vat_adjustment = 1.2 if subtract_vat else 1.0
            values.append(
                (self.period_range(i_row),
                 [activity.net_amount_for_category(category) / vat_adjustment
                  for activity in self.bank_activity_by_sub_period])
            )

        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values.append(
                (
                    self[self.COSTS_TOTAL, i_col],
                    f"={self.sum_formula(self.SALARIES, self.KASHFLOW, i_col)}"
                )
            )
        return values

    def _p_and_l_values(self):
        values = []
        for i_col in range(self.PERIOD_1, self.LAST_PERIOD + 1):
            values.append(
                (
                    self[self.P_AND_L, i_col],
                    "=" +
                    "+".join(
                        [self[i_row, i_col].in_a1_notation
                         for i_row in
                         [self.GIG_P_AND_L, self.HIRE_FEES, self.BAR_P_AND_L, self.CAP_EX, self.COSTS_TOTAL]
                         ]
                    )
                ),
            )
        return values

    def values(self):
        values = self._heading_values() \
                 + self._ticket_sales_values() \
                 + self._gig_costs_values() \
                 + self._hire_fee_values() \
                 + self._bar_values() \
                 + self._costs_values() \
                 + self._cap_ex_values() \
                 + self._p_and_l_values()

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
        self.audience_numbers_range = AudienceReportRange(
            self.report_range.bottom_left_cell.offset(num_rows=2),
            title,
            periods,
            period_titles,
            gigs_info,
        )
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    def _workbook_format_requests(self):
        return self.delete_all_row_groups_requests() + [
            # Workbook
            self.set_columns_width_request(i_first_col=2, i_last_col=4, width=150),
            self.set_columns_width_request(i_first_col=5, i_last_col=14, width=75),
        ] + self.report_range.format_requests() + self.audience_numbers_range.format_requests()

    def update(self):
        self.workbook.batch_update(
            self.clear_values_and_formats_requests() +
            self._workbook_format_requests()
        )

        self.workbook.batch_update_values(
            self.report_range.raw_values() + self.audience_numbers_range.raw_values(),
            value_input_option="RAW"  # Prevent creation of dates
        )
        self.workbook.batch_update_values(
            self.report_range.values() + self.audience_numbers_range.values()
        )

