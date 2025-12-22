from abc import abstractmethod
from decimal import Decimal
from numbers import Number
from typing import List

from airtable_db.gigs_info import GigsInfo
from airtable_db.table_columns import TicketPriceLevel, TicketCategory
from bank_statements.transactions import Transactions
from bank_statements.payee_categories import PayeeCategory
from date_range import DateRange
from date_range.date_range import SplitType
from date_range.month import Month
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_type, checked_list_type


class MonthAnalysisRange(TabRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            period: DateRange,
            gigs_info: GigsInfo,
    ):
        self.period: DateRange = checked_type(period, DateRange)
        self.months: list[Month] = checked_list_type(
            period.split_into(Month, split_type=SplitType.OUTER),
            Month
        )
        self.years = sorted(list({month.y for month in self.months}))
        self.gigs_by_month: dict[Month, GigsInfo] = {
            month: gigs_info.restrict_to_period(month)
            for month in self.months
        }
        super().__init__(top_left_cell, len(self.years) + 2, 14)

        self.month_titles = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        self.num_months: int = len(self.months)
        self.TITLE = 0
        self.MONTHS = 1
        self.TO_DATE = self.num_cols - 1

    @abstractmethod
    def month_value(self, month: Month) -> Number:
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        pass

    def format_requests(self):
        return [

            # Headings
            self.outline_border_request(),
            self[self.TITLE].merge_columns_request(),
            self[self.TITLE:self.MONTHS + 1].center_text_request(),
            self[self.TITLE:self.MONTHS + 1].set_bold_text_request(),
            self[self.MONTHS].border_request(["bottom"]),
            self[1:, 0].border_request(["right"]),
            self[1:, self.TO_DATE].border_request(["left"]),
            self[2:, 1:].set_decimal_format_request("#,##0")
        ]

    def total_values(self):
        values = []
        # To date totals
        for i_row in range(2, self.num_rows):
            month_range = self[i_row, 1:self.TO_DATE]
            values.append(
                (self[i_row, self.TO_DATE], f"=Sum({month_range.in_a1_notation})")
            )
        return values

    @property
    def total_title(self):
        return "Total"

    def values(self):
        values = [
            (self[self.TITLE], [self.title]),
            (self[1, 1:13], self.month_titles),
            (self[self.MONTHS, -1], [self.total_title])
        ]

        for i_year, year in enumerate(self.years):
            i_row = i_year + 2
            values.append((self[i_row, 0], [year]))

            month_values = [
                self.month_value(Month(year, i))
                for i in range(1, 13)
            ]
            values.append((self[i_row, 1:13], month_values))
        values += self.total_values()
        return values


class GigNumbersRange(MonthAnalysisRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            period: DateRange,
            gigs_info: GigsInfo,
    ):
        super().__init__(top_left_cell, period, gigs_info)

    def month_value(self, month: Month) -> Number:
        if month not in self.gigs_by_month:
            return 0
        return self.gigs_by_month[month].number_of_gigs

    @property
    def title(self) -> str:
        return "Number of Gigs"


class AirtableTicketSalesRange(MonthAnalysisRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            period: DateRange,
            gigs_info: GigsInfo,
    ):
        super().__init__(top_left_cell, period, gigs_info)

    @property
    def title(self) -> str:
        return "Ticket Sales (Airtable)"

    def month_value(self, month: Month) -> Number:
        if month not in self.gigs_by_month:
            return 0
        return self.gigs_by_month[month].total_ticket_sales

class AirtableNumTicketsSoldRange(MonthAnalysisRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            period: DateRange,
            gigs_info: GigsInfo,
    ):
        super().__init__(top_left_cell, period, gigs_info)

    @property
    def title(self) -> str:
        return "Number of Tickets Sold (Airtable)"

    def month_value(self, month: Month) -> Number:
        if month not in self.gigs_by_month:
            return 0
        return self.gigs_by_month[month].total_tickets

class BankTicketSalesRange(MonthAnalysisRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            period: DateRange,
            transactions: Transactions,
            gigs_info: GigsInfo,
    ):
        super().__init__(top_left_cell, period, gigs_info)
        self.transactions_by_month: dict[Month, Transactions] = {
            month: transactions.restrict_to_period(month)
            for month in self.months
        }

    @property
    def title(self) -> str:
        return "Ticket Sales (Bank)"

    def month_value(self, month: Month) -> Number:
        if month not in self.gigs_by_month:
            return 0
        walk_ins = self.gigs_by_month[month].total_walk_in_sales
        online = self.transactions_by_month[month].total_for(PayeeCategory.TICKET_SALES)
        return online + Decimal(walk_ins)


class AirtableDrinkSalesRange(MonthAnalysisRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            period: DateRange,
            gigs_info: GigsInfo,
    ):
        super().__init__(top_left_cell, period, gigs_info)

    @property
    def title(self) -> str:
        return "Drink Sales (Airtable)"

    def month_value(self, month: Month) -> Number:
        if month not in self.gigs_by_month:
            return 0
        return self.gigs_by_month[month].bar_takings

class BankDrinkSalesRange(MonthAnalysisRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            period: DateRange,
            transactions: Transactions,
            gigs_info: GigsInfo,
    ):
        super().__init__(top_left_cell, period, gigs_info)
        self.transactions_by_month: dict[Month, Transactions] = {
            month: transactions.restrict_to_period(month)
            for month in self.months
        }

    @property
    def title(self) -> str:
        return "Drink Sales (Bank)"

    def month_value(self, month: Month) -> Number:
        if month not in self.gigs_by_month:
            return 0
        walk_ins = self.gigs_by_month[month].total_walk_in_sales
        zettle = self.transactions_by_month[month].total_for(PayeeCategory.CARD_SALES)
        return zettle - Decimal(walk_ins)

class AirtableDrinkSalesPerCustomerRange(MonthAnalysisRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            period: DateRange,
            gigs_info: GigsInfo,
    ):
        super().__init__(top_left_cell, period, gigs_info)

    def format_requests(self):
        return super().format_requests() + [
            self[2:, 1:].set_decimal_format_request("#,##0.00")
        ]

    @property
    def title(self) -> str:
        return "Drink Sales per Customer (Airtable)"

    def total_values(self):
        values = []
        # To date totals
        for i_row in range(2, self.num_rows):
            month_range = self[i_row, 4:self.TO_DATE]
            values.append(
                (self[i_row, self.TO_DATE], f"=Average({month_range.in_a1_notation})")
            )
        return values

    @property
    def total_title(self):
        return "Average"

    def month_value(self, month: Month) -> Number:
        if month not in self.gigs_by_month:
            return 0
        num_tickets = self.gigs_by_month[month].total_tickets
        sales = self.gigs_by_month[month].bar_takings
        if num_tickets == 0:
            return 0
        return sales / num_tickets

class BankDrinkSalesPerCustomerRange(MonthAnalysisRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            period: DateRange,
            transactions: Transactions,
            gigs_info: GigsInfo,
    ):
        super().__init__(top_left_cell, period, gigs_info)
        self.transactions_by_month: dict[Month, Transactions] = {
            month: transactions.restrict_to_period(month)
            for month in self.months
        }

    def format_requests(self):
        return super().format_requests() + [
            self[2:, 1:].set_decimal_format_request("#,##0.00")
        ]

    @property
    def title(self) -> str:
        return "Drink Sales per Customer (Bank)"

    def total_values(self):
        values = []
        # To date totals
        for i_row in range(2, self.num_rows):
            month_range = self[i_row, 4:self.TO_DATE]
            values.append(
                (self[i_row, self.TO_DATE], f"=Average({month_range.in_a1_notation})")
            )
        return values

    @property
    def total_title(self):
        return "Average"

    def month_value(self, month: Month) -> Number:
        if month not in self.gigs_by_month:
            return 0
        walk_ins = self.gigs_by_month[month].total_walk_in_sales
        zettle = self.transactions_by_month[month].total_for(PayeeCategory.CARD_SALES)
        sales = zettle - Decimal(walk_ins)
        num_tickets = self.gigs_by_month[month].total_tickets
        if num_tickets == 0:
            return 0
        return sales / Decimal(num_tickets)
