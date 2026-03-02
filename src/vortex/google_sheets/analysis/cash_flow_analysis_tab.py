from abc import abstractmethod, ABC
from decimal import Decimal
from typing import List

from vortex.airtable_db.gigs_info import GigsInfo
from vortex.banking import BankActivity
from vortex.banking.category.payee_categories import PayeeCategory
from vortex.banking.transaction.transactions import Transactions
from vortex.date_range import DateRange, ContiguousDateRange
from vortex.date_range.date_range import SplitType
from vortex.date_range.month import Month
from vortex.google_sheets import Tab, Workbook
from vortex.google_sheets.tab_range import TabRange, TabCell
from vortex.google_sheets.vat.vat_returns_tab import RangesAndValues, BankCheckRange
from vortex.utils import checked_list_type, checked_type
from vortex.utils.collection_utils import group_into_dict


class AnalysisColumn:
    def __init__(self, name: str, categories: list[PayeeCategory]):
        self.name: str = checked_type(name, str)
        self.categories: list[PayeeCategory] = checked_list_type(categories, PayeeCategory)

    def value(self, transactions: Transactions) -> Decimal:
        return transactions.restrict_to_categories(self.categories).total_amount

    def __eq__(self, other):
        return isinstance(other, AnalysisColumn) and self.name == other.name and self.categories == other.categories

    @staticmethod
    def from_category(category: PayeeCategory) -> 'AnalysisColumn':
        return AnalysisColumn(category.name, [category])


class CashFlowAnalysisRange(TabRange, ABC):
    def __init__(self,
                 top_left_cell: TabCell,
                 transactions: Transactions,
                 periods: list[DateRange]
                 ):
        self.transactions: Transactions = checked_type(transactions, Transactions)
        self.periods: List[DateRange] = checked_list_type(periods, DateRange)
        super().__init__(
            top_left_cell,
            num_rows=len(periods) + 1,
            num_cols=len(self.headings),
        )

    @property
    def headings(self) -> list[str]:
        return [self.name] + [c.name.capitalize().replace("_", " ") for c in self.columns]

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError("name")

    @property
    @abstractmethod
    def columns(self) -> list[AnalysisColumn]:
        raise NotImplementedError("columns")

    @property
    def categories(self) -> list[PayeeCategory]:
        categories = []
        for c in self.columns:
            categories += c.categories
        d = group_into_dict(categories, lambda c: c)
        for k, v in d.items():
            if len(v) > 1:
                raise ValueError(f"duplicated category {k} in {self.name}")
        return categories

    def value_for_period(self, period: DateRange, period_transactions: Transactions, column: AnalysisColumn) -> Decimal:
        return column.value(period_transactions)

    @property
    def values(self) -> RangesAndValues:
        def row_for_period(i_period: int, period: DateRange):
            period_transactions = self.transactions.restrict_to_period(period)
            values = [self.value_for_period(period, period_transactions, col) for col in self.columns]
            total_formula = f"=SUM({self[i_period + 1, 1:len(self.headings)].in_a1_notation})"
            return [total_formula] + values

        return RangesAndValues.single_range(
            self,
            [self.headings] + [
                row_for_period(i, p) for i, p in enumerate(self.periods)
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


class IrregularCostsRange(CashFlowAnalysisRange):

    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 periods: List[DateRange]
                 ):
        super().__init__(
            top_left_cell,
            transactions,
            periods
        )

    @property
    def name(self) -> str:
        return "Irregular costs"

    @property
    def columns(self) -> list[AnalysisColumn]:
        return [
            AnalysisColumn.from_category(PayeeCategory.BUILDING_WORKS),
            AnalysisColumn.from_category(PayeeCategory.DIRECTORS_LOAN),
            AnalysisColumn.from_category(PayeeCategory.DONATION),
            AnalysisColumn.from_category(PayeeCategory.FLOOD),
            AnalysisColumn.from_category(PayeeCategory.GRANT),
            AnalysisColumn.from_category(PayeeCategory.INSURANCE_PAYOUT),
            AnalysisColumn.from_category(PayeeCategory.LEGAL_ADVICE),
        ]


class RegularCostsRange(CashFlowAnalysisRange):
    # HEADINGS = ["Regular Costs", "Salaries", "Rent", "Rates", "BB Loan", "Cleaning", "Insurance", "Web Host",
    #             "Utilities", "Maintenance", "Operational", "Petty Cash", "Other"]

    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 periods: List[DateRange]
                 ):
        super().__init__(
            top_left_cell,
            transactions,
            periods
        )

    @property
    def name(self) -> str:
        return "Regular costs"

    @property
    def columns(self) -> list[AnalysisColumn]:
        return [
            AnalysisColumn.from_category(PayeeCategory.SALARIES),
            AnalysisColumn.from_category(PayeeCategory.RENT),
            AnalysisColumn.from_category(PayeeCategory.RATES),
            AnalysisColumn.from_category(PayeeCategory.BB_LOAN),
            AnalysisColumn.from_category(PayeeCategory.CLEANING),
            AnalysisColumn.from_category(PayeeCategory.INSURANCE),
            AnalysisColumn.from_category(PayeeCategory.WEB_HOST),
            AnalysisColumn.from_category(PayeeCategory.INTERNAL_TRANSFER),
            AnalysisColumn.from_category(PayeeCategory.UNCATEGORISED),
            AnalysisColumn(
                "Utilities",
                [
                    PayeeCategory.BT,
                    PayeeCategory.ELECTRICITY,
                    PayeeCategory.TELEPHONE,
                    PayeeCategory.THAMES_WATER,
                    PayeeCategory.UTILITIES,
                ]
            ),
            AnalysisColumn.from_category(PayeeCategory.BUILDING_MAINTENANCE),
            AnalysisColumn.from_category(PayeeCategory.OPERATIONAL_COSTS),
            AnalysisColumn.from_category(PayeeCategory.PETTY_CASH),
            AnalysisColumn(
                "Other",
                [
                    PayeeCategory.ACCOUNTANT,
                    PayeeCategory.ADVERTISING,
                    PayeeCategory.AIRTABLE,
                    PayeeCategory.BANK_FEES,
                    PayeeCategory.BANK_INTEREST,
                    PayeeCategory.BUILDING_SECURITY,
                    PayeeCategory.CREDIT_CARD_FEES,
                    PayeeCategory.FIRE_ALARM,
                    PayeeCategory.KASHFLOW,
                    PayeeCategory.LICENSING,
                    PayeeCategory.MAILCHIMP,
                    PayeeCategory.MARKETING,
                    PayeeCategory.SLACK,
                    PayeeCategory.SUBSCRIPTIONS,
                ]
            )
        ]


class DrinksRange(CashFlowAnalysisRange):
    HEADINGS = ["Drinks", "Stock", "Snacks", "Sales", "VAT"]

    DRINKS_SALES = "Drinks Sales"

    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 gigs_info: GigsInfo,
                 periods: List[DateRange]
                 ):
        super().__init__(
            top_left_cell,
            transactions,
            periods
        )
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)

    @property
    def name(self) -> str:
        return "Drinks"

    @property
    def columns(self) -> list[AnalysisColumn]:
        return [
            AnalysisColumn.from_category(PayeeCategory.BAR_STOCK),
            AnalysisColumn.from_category(PayeeCategory.BAR_SNACKS),
            AnalysisColumn(
                self.DRINKS_SALES,
                [PayeeCategory.CARD_SALES, PayeeCategory.CASH_SALES]
            ),
            AnalysisColumn.from_category(PayeeCategory.VAT),
        ]

    def value_for_period(self, period: DateRange, period_transactions: Transactions, column: AnalysisColumn) -> Decimal:
        if column.name == self.DRINKS_SALES:
            period_gigs = self.gigs_info.restrict_to_period(period)
            walk_in_sales = period_gigs.total_walk_in_sales
            sales = column.value(period_transactions) - Decimal(walk_in_sales)
            return sales
        return column.value(period_transactions)


class GigCostsRange(CashFlowAnalysisRange):

    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 periods: List[DateRange]
                 ):
        super().__init__(
            top_left_cell,
            transactions,
            periods
        )

    @property
    def name(self) -> str:
        return "Gig Costs"

    @property
    def columns(self) -> list[AnalysisColumn]:
        return [
            AnalysisColumn.from_category(PayeeCategory.MUSICIAN_PAYMENTS),
            AnalysisColumn.from_category(PayeeCategory.MUSICIAN_COSTS),
            AnalysisColumn.from_category(PayeeCategory.WORK_PERMITS),
            AnalysisColumn.from_category(PayeeCategory.PRS),
            AnalysisColumn.from_category(PayeeCategory.PIANO_TUNER),
            AnalysisColumn.from_category(PayeeCategory.SOUND_ENGINEER),
            AnalysisColumn(
                "Equipment",
                [PayeeCategory.EQUIPMENT_PURCHASE, PayeeCategory.EQUIPMENT_HIRE, PayeeCategory.EQUIPMENT_MAINTENANCE]
            ),
            AnalysisColumn.from_category(PayeeCategory.GIG_SECURITY),
        ]


class TicketSalesRange(CashFlowAnalysisRange):
    WALK_IN = "Walk-in"

    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 gigs_info: GigsInfo,
                 periods: List[DateRange]
                 ):
        super().__init__(
            top_left_cell,
            transactions,
            periods
        )
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)

    @property
    def name(self) -> str:
        return "Income"

    @property
    def columns(self) -> list[AnalysisColumn]:
        return [
            AnalysisColumn.from_category(PayeeCategory.TICKET_SALES),
            AnalysisColumn(self.WALK_IN, []),
            AnalysisColumn.from_category(PayeeCategory.MUSIC_VENUE_TRUST),
        ]

    def value_for_period(self, period: DateRange, period_transactions: Transactions, column: AnalysisColumn) -> Decimal:
        if column.name == self.WALK_IN:
            month_gigs = self.gigs_info.restrict_to_period(period)
            walk_in_sales = month_gigs.total_walk_in_sales
            return Decimal(walk_in_sales)
        return column.value(period_transactions)


class OtherIncomeRange(CashFlowAnalysisRange):

    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 periods: List[DateRange]
                 ):
        super().__init__(
            top_left_cell,
            transactions,
            periods
        )

    @property
    def name(self) -> str:
        return "Other Income"

    @property
    def columns(self) -> list[AnalysisColumn]:
        return [
            AnalysisColumn.from_category(PayeeCategory.SPACE_HIRE),
            AnalysisColumn.from_category(PayeeCategory.VORTEX_MERCH),
            AnalysisColumn.from_category(PayeeCategory.MEMBERSHIPS),
        ]


class PeriodHeadingsRange(TabRange):
    def __init__(self, top_left_cell: TabCell,
                 periods: List[ContiguousDateRange]
                 ):
        super().__init__(
            top_left_cell,
            num_rows=len(periods) + 1,
            num_cols=1,
        )
        self.periods: List[ContiguousDateRange] = checked_list_type(periods, ContiguousDateRange)

    @property
    def values(self) -> RangesAndValues:
        return RangesAndValues.single_range(
            self,
            [["Period"]] + [[m.excel_format] for m in self.periods]
        )

    @property
    def categories(self) -> list[PayeeCategory]:
        return []

    @property
    def format_requests(self):
        requests = [
            self[:, 0].set_bold_text_request(),
            self[:, 0].right_align_text_request(),
            self[:, 0].border_request(["right"]),
            self[0, 0].border_request(["bottom"]),
        ]
        return requests


class SummaryRange(TabRange):
    def __init__(self, cash_flow_range: TabRange):
        super().__init__(
            cash_flow_range.bottom_left_cell.offset(num_rows=2),
            num_rows=1,
            num_cols=cash_flow_range.num_cols)
        self.cash_flow_range: TabRange = checked_type(cash_flow_range, TabRange)

    @property
    def values(self) -> RangesAndValues:
        return RangesAndValues.single_range(
            self,
            [
                [f"=AVERAGE({self.cash_flow_range[:, i_col].in_a1_notation}) / 3" for i_col in range(self.num_cols)],
            ]
        )

    @property
    def format_requests(self):
        requests = [
            self.set_rounded_currency_format_request(),
        ]
        return requests

    @property
    def categories(self) -> list[PayeeCategory]:
        return []

class SummaryHeadingsRange(TabRange):
    def __init__(self, top_left_cell: TabCell):
        super().__init__(
            top_left_cell,
            num_rows=1,
            num_cols=1,
        )

    @property
    def values(self) -> RangesAndValues:
        return RangesAndValues.single_range(
            self,
            [["Month Average"]]
        )

    @property
    def format_requests(self):
        requests = [
            self[:, 0].set_bold_text_request(),
            self[:, 0].right_align_text_request(),
            self[:, 0].border_request(["right"]),
        ]
        return requests

    @property
    def categories(self) -> list[PayeeCategory]:
        return []

class GigPnLRange(TabRange):
    def __init__(self, top_left_cell: TabCell,
                 transactions: Transactions,
                 gigs_info: GigsInfo,
                 periods: List[DateRange]
                 ):
        self.gig_income_range = TicketSalesRange(top_left_cell.offset(num_cols=1), transactions, gigs_info, periods)
        self.gig_costs_range = GigCostsRange(self.gig_income_range.top_right_cell.offset(num_cols=1), transactions,
                                             periods)
        super().__init__(
            top_left_cell,
            num_cols=1 + self.gig_income_range.num_cols + self.gig_costs_range.num_cols,
            num_rows=self.gig_income_range.num_rows
        )

    @property
    def categories(self) -> list[PayeeCategory]:
        return self.gig_costs_range.categories + self.gig_income_range.categories

    @property
    def values(self) -> RangesAndValues:
        sum_values = RangesAndValues.single_range(
            self,
            [["Gig P&L"]] + [
                [f"={self.gig_income_range[i_row, 0].in_a1_notation} + {self.gig_costs_range[i_row, 0].in_a1_notation}"]
                for i_row in range(1, self.num_rows)
            ]
        )
        return sum_values + self.gig_income_range.values + self.gig_costs_range.values

    @property
    def format_requests(self):
        outer_requests = [
            self[0, :].set_bold_text_request(),
            self[0, :].border_request(["bottom"]),
            self[0, :].right_align_text_request(),
            self[1:, :].set_rounded_currency_format_request(),
            self.tab.group_columns_request(self.i_first_col + 1, self.i_first_col + self.num_cols - 1),
        ]
        return outer_requests + self.gig_income_range.format_requests + self.gig_costs_range.format_requests

class PnLRange(TabRange):
    def __init__(self,
                 top_left_cell: TabCell,
                 ranges: list[TabRange],
                 bank_activity: BankActivity,
                 periods: List[DateRange]
                 ):
        self.bank_activity: BankActivity = checked_type(bank_activity, BankActivity)
        self.periods: List[DateRange] = checked_list_type(periods, DateRange)
        super().__init__(
            top_left_cell,
            num_cols=3,
            num_rows=1 + len(periods)
        )
        self.ranges: list[TabRange] = checked_list_type(ranges, TabRange)

    @property
    def values(self) -> RangesAndValues:
        def row_values(i_row):
            terms = [f"{r[i_row, 0].in_a1_notation}" for r in self.ranges]
            sum_value = "=" + "+".join(terms)
            period = self.periods[i_row - 1]
            activity = self.bank_activity.restrict_to_period(period)
            initial_pnl = activity.initial_balance_across_accounts
            terminal_pnl = activity.terminal_balance_across_accounts
            pnl_change = terminal_pnl - initial_pnl
            return [sum_value, terminal_pnl, pnl_change]

        return RangesAndValues.single_range(
            self,
            [["P&L", "Balance", "Bank P&L"]] + [
                row_values(i_row) for i_row in range(1, self.num_rows)
            ]
        )

    @property
    def format_requests(self):
        outer_requests = [
            self[0, :].set_bold_text_request(),
            self[0, :].border_request(["bottom"]),
            self[:, 0].border_request(["left"]),
            self[0, :].right_align_text_request(),
            self[1:, :].set_rounded_currency_format_request(),
            self.tab.group_columns_request(self.i_first_col + 1, self.i_first_col + self.num_cols - 1),
        ]
        return outer_requests

    @property
    def categories(self) -> list[PayeeCategory]:
        return []

class TicketAnalysisRange(TabRange):
    def __init__(self, top_left_cell: TabCell,
                 gigs_info: GigsInfo,
                 periods: List[DateRange]
                 ):
        super().__init__(
            top_left_cell,
            num_cols=3,
            num_rows=1 + len(periods)
        )
        self.gigs_info: GigsInfo = checked_type(gigs_info, GigsInfo)
        self.periods: list[DateRange] = checked_list_type(periods, DateRange)

    @property
    def categories(self) -> list[PayeeCategory]:
        return []

    @property
    def values(self) -> RangesAndValues:
        def row_for_period(period: DateRange):
            months = period.split_into(Month, SplitType.EXACT)
            gigs_by_month = [self.gigs_info.restrict_to_period(m) for m in months]
            num_tickets = sum([g.total_tickets for g in gigs_by_month])
            ticket_sales = sum([g.total_ticket_sales for g in gigs_by_month])
            ave_price = ticket_sales / num_tickets
            return [num_tickets, ticket_sales, ave_price]

        sum_values = RangesAndValues.single_range(
            self,
            [["Num Tickets", "Sales", "Average Price"]] + [
                row_for_period(period) for period in self.periods
            ]
        )
        return sum_values

    @property
    def format_requests(self):
        return [
            self[0, :].set_bold_text_request(),
            self[0, :].border_request(["bottom"]),
            self[0, :].right_align_text_request(),
            self[1:, 1].set_rounded_currency_format_request(),
            self[1:, 2].set_currency_format_request(),
        ]

class CashFlowAnalysisTab(Tab):
    def __init__(self, workbook: Workbook, tab_name, periods: List[ContiguousDateRange]):
        super().__init__(workbook, tab_name=tab_name)
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)
        self.periods: List[ContiguousDateRange] = checked_list_type(periods, ContiguousDateRange)

    def update(self,
               transactions: Transactions,
               gigs_info: GigsInfo,
               bank_activity: BankActivity
               ):
        month_headings_range = PeriodHeadingsRange(self.cell("B3"), self.periods)
        summary_headings_range = SummaryHeadingsRange(month_headings_range.bottom_left_cell.offset(num_rows=2))
        gig_pnl_range = GigPnLRange(month_headings_range.top_right_cell.offset(num_cols=1), transactions, gigs_info, self.periods)
        other_income_range = OtherIncomeRange(gig_pnl_range.top_right_cell.offset(num_cols=1), transactions,
                                              self.periods)
        drinks_range = DrinksRange(other_income_range.top_right_cell.offset(num_cols=1), transactions, gigs_info,
                                   self.periods)
        regular_costs_range = RegularCostsRange(drinks_range.top_right_cell.offset(num_cols=1), transactions,
                                                self.periods)
        irregular_costs_range = IrregularCostsRange(regular_costs_range.top_right_cell.offset(num_cols=1),
                                                    transactions,
                                                    self.periods)
        value_ranges = [gig_pnl_range, other_income_range, drinks_range,
                        regular_costs_range,
                        irregular_costs_range,
                        ]
        total_range = PnLRange(irregular_costs_range.top_right_cell.offset(num_cols=1), value_ranges, bank_activity, self.periods)

        ticket_analysis_range = TicketAnalysisRange(total_range.top_right_cell.offset(num_cols=2), gigs_info, self.periods)
        ranges = [month_headings_range, summary_headings_range] + value_ranges + [total_range, ticket_analysis_range]

        summary_ranges = [SummaryRange(v) for v in value_ranges + [total_range]]
        all_categories = []
        format_requests = self.delete_all_groups_requests() + self.clear_values_and_formats_requests() + [
            self.set_column_width_request(0, width=30)
        ]
        values = RangesAndValues([])
        for range in ranges + summary_ranges:
            format_requests += range.format_requests
            values += range.values
            all_categories += range.categories

        assert len(set(all_categories)) == len(all_categories), "Duplicate categories"
        for v in PayeeCategory:
            if v not in all_categories:
                raise ValueError(f"Missing category {v}")

        self.workbook.batch_update(format_requests)
        self.workbook.batch_update_values(values.ranges_and_values)
