from typing import List, Tuple, Optional, Dict

from airtable_db.gigs_info import GigsInfo
from bank_statements.categorized_transaction import CategorizedTransaction
from bank_statements.payee_categories import PayeeCategory
from date_range import Day
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from google_sheets import Tab, Workbook
from google_sheets.summary.vortex_summary_range import TicketSalesRange
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_list_type, checked_type, checked_optional_type
from utils.collection_utils import group_into_dict


def _category_text(t: CategorizedTransaction) -> str:
    if t.category is None:
        return "Uncategorized"
    return t.category


class TransactionsByMonthAndCategory:
    def __init__(self, transactions: List[CategorizedTransaction]):
        self.transactions = checked_list_type(transactions, CategorizedTransaction)
        self.by_month_and_category: Dict[
            Tuple[AccountingMonth, Optional[PayeeCategory]], List[CategorizedTransaction]] = group_into_dict(
            self.transactions,
            lambda t: (AccountingMonth.containing(t.payment_date), t.category)
        )

    def total_for_month_and_category(self, month: AccountingMonth, category: Optional[PayeeCategory]) -> float:
        return sum(t.transaction.amount for t in self.by_month_and_category.get((month, category), []))


class CategorisedTransactionsRange(TabRange):

    def __init__(
            self,
            top_left_cell: TabCell,
            accounting_months: List[AccountingMonth],
            categorised_transactions: List[CategorizedTransaction]):
        self.categories = [c for c in PayeeCategory] + [None]
        super().__init__(top_left_cell, num_rows=2 + len(self.categories), num_cols=6)
        self.accounting_months: List[AccountingMonth] = checked_list_type(accounting_months, AccountingMonth)
        self.categorised_transactions: List[CategorizedTransaction] = checked_list_type(categorised_transactions,
                                                                                        CategorizedTransaction)
        self.transactions_by_month_and_category: TransactionsByMonthAndCategory = TransactionsByMonthAndCategory(
            categorised_transactions)

    @property
    def format_requests(self):
        return [
            self[0, :].merge_columns_request(),
            self[0, :].center_text_request(),
            self.outline_border_request(style="SOLID"),
            self[2:, 1:6].set_currency_format_request(),
            self[0:2, :].set_bold_text_request(),
            self[:, 0].set_bold_text_request(),
        ]

    def acc_month(self, d: Day) -> AccountingMonth:
        for m in self.accounting_months:
            if m.contains(d):
                return m
        raise ValueError(f"No accounting month found for {d}")

    @property
    def values(self):
        # by_accounting_month = group_into_dict(self.categorised_transactions, lambda t: self.acc_month(t.payment_date))
        # by_category = {
        #     m: group_into_dict(by_accounting_month[m], _category_text)
        #     for m in self.accounting_months
        # }
        #
        # def total_for_category(m: AccountingMonth, category: str) -> float:
        #     return sum(t.transaction.amount for t in by_category[m].get(category, []))

        categories_values = [
            ["Categorised Transactions"],
            [""] + [m.month_name for m in self.accounting_months] + ["Total", "VAT"]
        ]
        for i_cat, c in enumerate(self.categories):
            total_formula = f"=SUM({self[i_cat + 2, 1:4].in_a1_notation})"
            is_liable_to_vat = PayeeCategory.is_subject_to_vat(c)
            if is_liable_to_vat:
                vat_formula = f"={self[i_cat + 2, 4].in_a1_notation} / 6.0"
            else:
                vat_formula = ""
            row = [c or "Uncategorized"] + [self.transactions_by_month_and_category.total_for_month_and_category(m, c)
                                            for m in self.accounting_months] + [total_formula, vat_formula]

            categories_values.append(row)
        return categories_values

    def zettle_credits_cell(self, i_col):
        i = self.categories.index(PayeeCategory.ZETTLE_CREDITS)
        return self[i + 2, i_col].in_a1_notation

    def ticketweb_credits_cell(self, i_col):
        i = self.categories.index(PayeeCategory.TICKETWEB_CREDITS)
        return self[i + 2, i_col].in_a1_notation

    def space_hire_cell(self, i_col):
        i = self.categories.index(PayeeCategory.SPACE_HIRE)
        return self[i + 2, i_col].in_a1_notation


class WalkInSalesRange(TabRange):
    def __init__(self, top_left_cell: TabCell, accounting_months: List[AccountingMonth], gigs_infos: List[GigsInfo]):
        super().__init__(top_left_cell, num_rows=4, num_cols=6)
        self.accounting_months: List[AccountingMonth] = checked_list_type(accounting_months, AccountingMonth)
        self.gigs_infos: List[GigsInfo] = checked_list_type(gigs_infos, GigsInfo)

    @property
    def format_requests(self):
        return [
            self[0, :].merge_columns_request(),
            self[0, :].center_text_request(),
            self.outline_border_request(style="SOLID"),
            self[2:, 1:6].set_currency_format_request(),
            self[0:2, :].set_bold_text_request(),
            self[:, 0].set_bold_text_request(),
        ]

    @property
    def values(self):
        return [
            ["Walk In Ticket Sales"],
            [""] + [m.month_name for m in self.accounting_months] + ["Total", ""],
            ["Walk In Sales"] + [gi.total_walk_in_sales for gi in self.gigs_infos] + ["", ""],
        ]

    def walk_in_sales_cell(self, i_col: int):
        return self[2, i_col].in_a1_notation


class OutputsRange(TabRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions_range: CategorisedTransactionsRange,
                 walk_in_sales_range: WalkInSalesRange):
        super().__init__(top_left_cell, num_rows=7, num_cols=6)
        self.categorised_transactions_range: CategorisedTransactionsRange = checked_type(categorised_transactions_range,
                                                                                         CategorisedTransactionsRange)
        self.walk_in_sales_range: WalkInSalesRange = checked_type(walk_in_sales_range, WalkInSalesRange)

    @property
    def accounting_months(self):
        return self.categorised_transactions_range.accounting_months

    @property
    def format_requests(self):
        return [
            self[0, :].merge_columns_request(),
            self[0:2, :].set_bold_text_request(),
            self[0:2, :].center_text_request(),
            self.outline_border_request(style="SOLID"),
            self[1:, 1:].set_currency_format_request(),
        ]

    @property
    def values(self):
        def bar_takings_formula(i_month: int):
            zettle_cell = self.categorised_transactions_range.zettle_credits_cell(i_month + 1) or ""
            walk_ins_cell = self.walk_in_sales_range.walk_in_sales_cell(i_month + 1)
            return f"={zettle_cell} - {walk_ins_cell}"

        def ticket_sales_formula(i_month: int):
            ticket_web_cell = self.categorised_transactions_range.ticketweb_credits_cell(i_month + 1) or ""
            walk_ins_cell = self.walk_in_sales_range.walk_in_sales_cell(i_month + 1)
            return f"={ticket_web_cell} + {walk_ins_cell}"

        def hire_fees_formula(i_month: int):
            space_hire_cell = self.categorised_transactions_range.space_hire_cell(i_month + 1)
            if space_hire_cell is None:
                return ""
            return f"={space_hire_cell}"

        return [
            ["Outputs"],
            [""] + [m.month_name for m in self.accounting_months] + ["Total", "VAT"],
            ["Total Ticket Sales"] + [ticket_sales_formula(i) for i in range(3)] + ["", ""],
            ["Hire Fees"] + [hire_fees_formula(i) for i in range(3)] + ["", ""],
            ["Bar Takings"] + [bar_takings_formula(i) for i in range(3)] + ["", ""],
            ["Total", "", "", "", "", ""],
        ]


class PaymentsRange(TabRange):
    COLUMNS = ["Payments", "Date", "Payee"]

    def __init__(self, top_left_cell: TabCell, transactions: List[CategorizedTransaction],
                 category: Optional[PayeeCategory]):
        self.category: Optional[PayeeCategory] = checked_optional_type(category, PayeeCategory)
        self.transactions = [t for t in transactions if t.category == category]
        self.by_month = group_into_dict(
            self.transactions,
            lambda t: AccountingMonth.containing(t.payment_date)
        )
        self.categories = sorted(set(t.category for t in self.transactions if t.category is not None)) + ([None] if any(
            t.category is None for t in self.transactions) else [])
        self.accounting_months = sorted(self.by_month.keys())
        super().__init__(top_left_cell, num_rows=1 + len(self.transactions) + len(self.accounting_months), num_cols=4)

        self.month_total_cells = [self[1, 1]]
        for m in self.accounting_months[:-1]:
            last_total_cell = self.month_total_cells[-1]
            self.month_total_cells.append(last_total_cell.offset(rows=len(self.by_month[m]) + 1))

    @property
    def format_requests(self):
        requests = [
            self[0, 0].set_bold_text_request(),
            self[:, 1].set_currency_format_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        for i_month, m in enumerate(self.accounting_months):
            month_total_cell = self.month_total_cells[i_month]
            requests.append(
                self.tab.group_rows_request(
                    month_total_cell.i_first_row + 1,
                    month_total_cell.i_first_row + len(self.by_month[m])
                )
            )
        return requests

    @property
    def values(self):
        category_total_formula = "=" + "+".join(c.in_a1_notation for c in self.month_total_cells)
        values = [
            [self.category or "Uncategorized", category_total_formula, "", ""]
        ]
        i_row = 1
        for m in self.accounting_months:
            trans_for_month = sorted(self.by_month[m], key=lambda t: (t.payment_date, t.payee))
            month_total_formula = f"=SUM({self[i_row + 1:i_row + 1 + len(trans_for_month), 1].in_a1_notation})"
            values.append(["", month_total_formula, m.month_name, ""])
            for t in self.by_month[m]:
                values.append(["", t.amount, t.payment_date, t.transaction.payee])
            i_row += 1 + len(trans_for_month)
        return values


class WalkInSalesRange2(TabRange):

    def __init__(self, top_left_cell: TabCell, gigsInfo: GigsInfo):
        self.gigsInfo: GigsInfo = gigsInfo.restrict_to_gigs()
        self.accounting_months = sorted(
            set(AccountingMonth.containing(ce.performance_date) for ce in self.gigsInfo.contracts_and_events))
        self.by_month = {m: self.gigsInfo.restrict_to_period(m) for m in self.accounting_months}
        super().__init__(top_left_cell, num_rows=1 + self.gigsInfo.number_of_gigs + len(self.accounting_months),
                         num_cols=4)

        self.month_total_cells = [self[1, 1]]
        for m in self.accounting_months[:-1]:
            last_total_cell = self.month_total_cells[-1]
            self.month_total_cells.append(last_total_cell.offset(rows=len(self.by_month[m].contracts_and_events) + 1))

    @property
    def format_requests(self):
        requests = [
            self[0, 0].set_bold_text_request(),
            self[:, 1].set_currency_format_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        for i_month, m in enumerate(self.accounting_months):
            month_total_cell = self.month_total_cells[i_month]
            requests.append(
                self.tab.group_rows_request(
                    month_total_cell.i_first_row + 1,
                    month_total_cell.i_first_row + len(self.by_month[m].contracts_and_events)
                )
            )
        return requests

    @property
    def values(self):
        total_formula = "=" + "+".join(c.in_a1_notation for c in self.month_total_cells)
        values = [
            ["Walk in sales", total_formula, "", ""]
        ]
        i_row = 1
        for m in self.accounting_months:
            gigs_for_month = sorted(self.by_month[m].contracts_and_events,
                                    key=lambda t: (t.performance_date, t.event_titles))
            month_total_formula = f"=SUM({self[i_row + 1:i_row + 1 + len(gigs_for_month), 1].in_a1_notation})"
            values.append(["", month_total_formula, m.month_name, ""])
            contracts_and_events = sorted(self.by_month[m].contracts_and_events,
                                          key=lambda t: (t.performance_date, t.event_titles))
            for t in contracts_and_events:
                values.append(["", t.total_walk_in_sales, t.performance_date, t.event_titles])
            i_row += 1 + len(gigs_for_month)
        return values


class FunctionOfTwoRangesRange(TabRange):
    def __init__(self, total_tile: str, range1: TabRange, range2: TabRange, operand: str):
        super().__init__(range1.top_left_cell.offset(-1, 0), num_rows=1, num_cols=2)
        self.total_title: str = checked_type(total_tile, str)
        self.range1: TabRange = checked_type(range1, TabRange)
        self.range2: TabRange = checked_type(range2, TabRange)
        self.operand: str = checked_type(operand, str)

    @property
    def format_requests(self):
        return [
            self[0, 0].set_bold_text_request(),
            self[0, 1].set_currency_format_request(),
            self.tab.group_rows_request(
                self.i_first_row + 1,
                self.i_first_row + self.range1.num_rows + self.range2.num_rows
            ),
        ]

    @property
    def values(self):
        range1_total_cell = self.range1.top_left_cell.offset(0, 1)
        range2_total_cell = self.range2.top_left_cell.offset(0, 1)
        return [
            [self.total_title,
             f"={range1_total_cell.cell_coordinates.text} {self.operand} {range2_total_cell.cell_coordinates.text}"]
        ]


class TotalBarSalesRange(FunctionOfTwoRangesRange):
    def __init__(self, zettle_credits_range: TabRange, walk_in_sales_range: TabRange):
        super().__init__("Total Bar Sales", zettle_credits_range, walk_in_sales_range, "-")

class TotalTicketSalesRange(FunctionOfTwoRangesRange):
    def __init__(self, ticket_web_credits_range: TabRange, walk_in_sales_range: TabRange):
        super().__init__("Total Ticket Sales", ticket_web_credits_range, walk_in_sales_range, "+")

class VATReturnsTab(Tab):
    COLUMNS = ["Outputs", "Month 1", "Month 2", "Month 3", "Total For Quarter", "VAT"]
    (OUTPUTS, MONTH_1, MONTH_2, MONTH_3, TOTAL, VAT) = range(len(COLUMNS))

    def __init__(
            self,
            workbook: Workbook,
            months: List[Month],
    ):
        super().__init__(workbook, tab_name=months[-1].tab_name)
        self.months: List[Month] = checked_list_type(months, Month)
        self.accounting_months = [AccountingMonth.from_calendar_month(m) for m in self.months]
        if not self.workbook.has_tab(self.tab_name):
            self.workbook.add_tab(self.tab_name)

    @property
    def _general_format_requests(self):
        format_requests = self.delete_all_groups_requests() + self.clear_values_and_formats_requests() + [
            self.set_column_width_request(0, width=30)
        ]
        for col, width in [
            (self.OUTPUTS, 200),
            (self.MONTH_1, 150),
            (self.MONTH_2, 150),
            (self.MONTH_3, 150),
            (self.TOTAL, 150),
            (self.VAT, 150),
        ]:
            format_requests.append(
                self.set_column_width_request(1 + col, width=width)
            )
        return format_requests

    def update(self, categorised_transactions: List[CategorizedTransaction], gigs_info: GigsInfo):

        categories_range = CategorisedTransactionsRange(self.cell("B2"),
                                                        self.accounting_months,
                                                        categorised_transactions)

        # outputs_range = OutputsRange(categories_range.bottom_left_cell.offset(2, 0), categories_range,
        #                              ticket_sales_range)

        zettle_credit_range = PaymentsRange(categories_range.bottom_left_cell.offset(num_rows=4),
                                            categorised_transactions,
                                            PayeeCategory.ZETTLE_CREDITS)
        walk_in_sales_range = WalkInSalesRange2(zettle_credit_range.bottom_left_cell.offset(num_rows=1),
                                                gigs_info)
        total_bar_sales_range = TotalBarSalesRange(zettle_credit_range, walk_in_sales_range)
        ticket_web_credits_range = PaymentsRange(walk_in_sales_range.bottom_left_cell.offset(num_rows=2),
                                                 categorised_transactions,
                                                 PayeeCategory.TICKETWEB_CREDITS)
        walk_in_sales_range2 = WalkInSalesRange2(ticket_web_credits_range.bottom_left_cell.offset(num_rows=1),
                                                 gigs_info)
        total_ticket_sales_range = TotalTicketSalesRange(ticket_web_credits_range, walk_in_sales_range2)
        total_space_hires_range = PaymentsRange(walk_in_sales_range2.bottom_left_cell.offset(num_rows=1),
                                                 categorised_transactions,
                                                 PayeeCategory.SPACE_HIRE)

        self.workbook.batch_update(
            self._general_format_requests
        )
        self.workbook.batch_update(
            total_bar_sales_range.format_requests +
            categories_range.format_requests +
            zettle_credit_range.format_requests +
            walk_in_sales_range.format_requests +
            ticket_web_credits_range.format_requests +
            walk_in_sales_range2.format_requests +
            total_ticket_sales_range.format_requests +
            total_space_hires_range.format_requests
        )
        self.workbook.batch_update(
            self.collapse_all_groups_requests()
        )

        self.workbook.batch_update_values([
            # (ticket_sales_range, ticket_sales_range.values),
            (categories_range, categories_range.values),
            (zettle_credit_range, zettle_credit_range.values),
            (walk_in_sales_range, walk_in_sales_range.values),
            (total_bar_sales_range, total_bar_sales_range.values),
            (ticket_web_credits_range, ticket_web_credits_range.values),
            (walk_in_sales_range2, walk_in_sales_range2.values),
            (total_ticket_sales_range, total_ticket_sales_range.values),
            (total_space_hires_range, total_space_hires_range.values),
        ])
