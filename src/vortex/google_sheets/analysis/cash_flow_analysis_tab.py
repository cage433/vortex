from decimal import Decimal
from typing import List

from vortex.airtable_db.gigs_info import GigsInfo
from vortex.banking import BankActivity
from vortex.banking.category.payee_categories import PayeeCategory
from vortex.banking.transaction.transactions import Transactions
from vortex.date_range.month import Month
from vortex.google_sheets import Tab, Workbook
from vortex.google_sheets.tab_range import TabRange, TabCell
from vortex.google_sheets.vat.vat_returns_tab import RangesAndValues
from vortex.utils import checked_list_type, checked_type


class RegularCostsRange(TabRange):
    HEADINGS = ["Regular Costs", "Salaries", "Rent", "Rates", "BB Loan", "Cleaning", "Insurance", "Web Host", "Utilities", "Other"]

    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 months: List[Month]
                 ):
        super().__init__(
            top_left_cell,
            num_rows=len(months) + 1,
            num_cols=len(self.HEADINGS),
        )
        self.transactions: Transactions = checked_type(transactions, Transactions)
        self.months: List[Month] = checked_list_type(months, Month)

    @property
    def values(self) -> RangesAndValues:
        def row_for_month(i_month: int, m: Month):
            month_trans = self.transactions.restrict_to_period(m)
            salaries = month_trans.restrict_to_category(PayeeCategory.SALARIES).total_amount
            rent = month_trans.restrict_to_category(PayeeCategory.RENT).total_amount
            rates = month_trans.restrict_to_category(PayeeCategory.RATES).total_amount
            bb_loan = month_trans.restrict_to_category(PayeeCategory.BB_LOAN).total_amount
            cleaning = month_trans.restrict_to_category(PayeeCategory.CLEANING).total_amount
            insurance = month_trans.restrict_to_category(PayeeCategory.INSURANCE).total_amount
            web_host = month_trans.restrict_to_category(PayeeCategory.WEB_HOST).total_amount
            utilities = month_trans.restrict_to_categories(
                [
                    PayeeCategory.ELECTRICITY,
                    PayeeCategory.TELEPHONE,
                    PayeeCategory.THAMES_WATER,
                    PayeeCategory.UTILITIES,
                ]
            ).total_amount
            other = month_trans.restrict_to_categories(
                [
                    PayeeCategory.CREDIT_CARD_FEES,
                    PayeeCategory.FIRE_ALARM,
                    PayeeCategory.MAILCHIMP,
                    PayeeCategory.MARKETING,
                    PayeeCategory.SLACK,
                    PayeeCategory.SUBSCRIPTIONS,
                ]
            ).total_amount

            total_formula = f"=SUM({self[i_month + 1, 1:len(self.HEADINGS)].in_a1_notation})"
            return [total_formula, salaries, rent, rates, bb_loan, cleaning, insurance, web_host, utilities, other]

        return RangesAndValues.single_range(
            self,
            [self.HEADINGS] + [
                row_for_month(i, m) for i, m in enumerate(self.months)
            ]
        )

    @property
    def format_requests(self):
        requests = [
            self[0, :].set_bold_text_request(),
            self[0, :].border_request(["bottom"]),
            self[0, :].right_align_text_request(),
            self[1:, :].set_rounded_currency_format_request(),
            self.tab.group_columns_request(self.i_first_col + 1, self.i_first_col + self.num_cols - 1),
        ]
        return requests

class DrinksRange(TabRange):
    HEADINGS = ["Drinks", "Stock", "Snacks", "Sales", "VAT"]

    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 gigs_info: GigsInfo,
                 months: List[Month]
                 ):
        super().__init__(
            top_left_cell,
            num_rows=len(months) + 1,
            num_cols=len(self.HEADINGS),
        )
        self.transactions: Transactions = checked_type(transactions, Transactions)
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.months: List[Month] = checked_list_type(months, Month)

    @property
    def values(self) -> RangesAndValues:
        def row_for_month(i_month: int, m: Month):
            month_trans = self.transactions.restrict_to_period(m)
            stock = month_trans.restrict_to_category(PayeeCategory.BAR_STOCK).total_amount
            snacks = month_trans.restrict_to_category(PayeeCategory.BAR_SNACKS).total_amount
            card_sales = month_trans.restrict_to_category(PayeeCategory.CARD_SALES).total_amount
            vat = month_trans.restrict_to_category(PayeeCategory.VAT).total_amount
            month_gigs = self.gigs_info.restrict_to_period(m)
            walk_in_sales = month_gigs.total_walk_in_sales
            sales = card_sales - Decimal(walk_in_sales)

            total_formula = f"=SUM({self[i_month + 1, 1:len(self.HEADINGS)].in_a1_notation})"
            return [total_formula, stock, snacks, sales, vat]

        return RangesAndValues(
            [(self,
              [self.HEADINGS] + [
                  row_for_month(i, m) for i, m in enumerate(self.months)
              ]
              )]
        )

    @property
    def format_requests(self):
        requests = [
            self[0, :].set_bold_text_request(),
            self[0, :].border_request(["bottom"]),
            self[0, :].right_align_text_request(),
            self[1:, :].set_rounded_currency_format_request(),
            self.tab.group_columns_request(self.i_first_col + 1, self.i_first_col + self.num_cols - 1),
        ]
        return requests


class MusicRange(TabRange):
    HEADINGS = ["Music", "Fees", "Expenses", "Work Permits", "PRS", "Tuner", "Sound", "Equipment", "MVT"]

    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 months: List[Month]
                 ):
        super().__init__(
            top_left_cell,
            num_rows=len(months) + 1,
            num_cols=len(self.HEADINGS),
        )
        self.transactions: Transactions = checked_type(transactions, Transactions)
        self.months: List[Month] = checked_list_type(months, Month)

    @property
    def values(self) -> RangesAndValues:
        def row_for_month(i_month: int, m: Month):
            month_trans = self.transactions.restrict_to_period(m)
            payments = month_trans.restrict_to_category(PayeeCategory.MUSICIAN_PAYMENTS).total_amount
            expenses = month_trans.restrict_to_category(PayeeCategory.MUSICIAN_COSTS).total_amount
            permits = month_trans.restrict_to_category(PayeeCategory.WORK_PERMITS).total_amount
            prs = month_trans.restrict_to_category(PayeeCategory.PRS).total_amount
            tuner = month_trans.restrict_to_category(PayeeCategory.PIANO_TUNER).total_amount
            sound = month_trans.restrict_to_category(PayeeCategory.SOUND_ENGINEER).total_amount
            equipment = month_trans.restrict_to_categories(
                [PayeeCategory.EQUIPMENT_PURCHASE, PayeeCategory.EQUIPMENT_HIRE, PayeeCategory.EQUIPMENT_MAINTENANCE]
            ).total_amount
            mvt = month_trans.restrict_to_category(PayeeCategory.MUSIC_VENUE_TRUST).total_amount
            total_formula = f"=SUM({self[i_month + 1, 1:len(self.HEADINGS)].in_a1_notation})"
            return [total_formula, payments, expenses, permits, prs, tuner, sound, equipment, mvt]

        return RangesAndValues(
            [(self,
              [self.HEADINGS] + [
                  row_for_month(i, m) for i, m in enumerate(self.months)
              ]
              )]
        )

    @property
    def format_requests(self):
        requests = [
            self[0, :].set_bold_text_request(),
            self[0, :].border_request(["bottom"]),
            self[0, :].right_align_text_request(),
            self[1:, :].set_rounded_currency_format_request(),
            self.tab.group_columns_request(self.i_first_col + 1, self.i_first_col + self.num_cols - 1),
        ]
        return requests


class TicketSalesRange(TabRange):
    HEADINGS = ["Tickets", "Ticket Web", "Walk-in", "Membership"]

    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 gigs_info: GigsInfo,
                 months: List[Month]
                 ):
        super().__init__(
            top_left_cell,
            num_rows=len(months) + 1,
            num_cols=len(self.HEADINGS),
        )
        self.transactions: Transactions = checked_type(transactions, Transactions)
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.months: List[Month] = checked_list_type(months, Month)

    @property
    def values(self) -> RangesAndValues:
        def row_for_month(i_month: int, m: Month):
            month_trans = self.transactions.restrict_to_period(m)
            ticket_web = month_trans.restrict_to_category(PayeeCategory.TICKET_SALES).total_amount
            membership = month_trans.restrict_to_category(PayeeCategory.MEMBERSHIPS).total_amount
            month_gigs = self.gigs_info.restrict_to_period(m)
            walk_in_sales = month_gigs.total_walk_in_sales
            total_formula = f"=SUM({self[i_month + 1, 1:4].in_a1_notation})"
            return [total_formula, ticket_web, walk_in_sales, membership]

        return RangesAndValues(
            [(self,
              [self.HEADINGS] + [
                  row_for_month(i, m) for i, m in enumerate(self.months)
              ]
              )]
        )

    @property
    def format_requests(self):
        requests = [
            self[0, :].set_bold_text_request(),
            self[0, :].border_request(["bottom"]),
            self[0, :].right_align_text_request(),
            self[1:, :].set_rounded_currency_format_request(),
            self.tab.group_columns_request(self.i_first_col + 1, self.i_first_col + self.num_cols - 1),
        ]
        return requests


class MonthHeadingsRange(TabRange):
    def __init__(self, top_left_cell: TabCell,
                 months: List[Month]
                 ):
        super().__init__(
            top_left_cell,
            num_rows=len(months) + 1,
            num_cols=1,
        )
        self.months: List[Month] = checked_list_type(months, Month)

    @property
    def values(self) -> RangesAndValues:
        return RangesAndValues.single_range(
            self,
            [["Month"]] + [[m.month_name] for m in self.months]
        )

    @property
    def format_requests(self):
        requests = [
            self[:, 0].set_bold_text_request(),
            self[:, 0].right_align_text_request(),
            self[:, 0].border_request(["right"]),
            self[0, 0].border_request(["bottom"]),
        ]
        return requests


class CashFlowAnalysisTab(Tab):
    def __init__(self, workbook: Workbook, months: List[Month]):
        super().__init__(workbook, tab_name=months[-1].tab_name)
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)
        self.months: List[Month] = checked_list_type(months, Month)

    def update(self,
               transactions: Transactions,
               gigs_info: GigsInfo,
               bank_activity: BankActivity
               ):
        month_headings_range = MonthHeadingsRange(self.cell("B10"), self.months)
        ticket_range = TicketSalesRange(month_headings_range.top_right_cell.offset(num_cols=1), transactions, gigs_info,
                                        self.months)
        music_range = MusicRange(ticket_range.top_right_cell.offset(num_cols=1), transactions, self.months)
        drinks_range = DrinksRange(music_range.top_right_cell.offset(num_cols=1), transactions, gigs_info, self.months)
        regular_costs_range = RegularCostsRange(drinks_range.top_right_cell.offset(num_cols=1), transactions, self.months)

        format_requests = self.delete_all_groups_requests() + self.clear_values_and_formats_requests() + [
            self.set_column_width_request(0, width=30)
        ]
        format_requests += month_headings_range.format_requests
        format_requests += ticket_range.format_requests
        format_requests += music_range.format_requests
        format_requests += drinks_range.format_requests
        format_requests += regular_costs_range.format_requests
        self.workbook.batch_update(
            format_requests
        )
        values = month_headings_range.values + ticket_range.values + music_range.values + drinks_range.values + regular_costs_range.values
        self.workbook.batch_update_values(values.ranges_and_values)
