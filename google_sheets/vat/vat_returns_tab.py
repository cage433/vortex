from typing import List

from airtable_db.gigs_info import GigsInfo
from bank_statements.categorized_transaction import CategorizedTransaction
from bank_statements.payee_categories import PayeeCategory
from date_range import Day
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from google_sheets import Tab, Workbook
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_list_type, checked_type
from utils.collection_utils import group_into_dict


def _category_text(t: CategorizedTransaction) -> str:
    if t.category is None:
        return "Uncategorized"
    return t.category


def _is_vatable(category: str) -> bool:
    if category in [
        PayeeCategory.AIRTABLE, PayeeCategory.BANK_FEES, PayeeCategory.BAR_SNACKS,
        PayeeCategory.BAR_STOCK, PayeeCategory.BUILDING_MAINTENANCE, PayeeCategory.BUILDING_SECURITY,
        PayeeCategory.CLEANING, PayeeCategory.ELECTRICITY, PayeeCategory.INSURANCE, PayeeCategory.KASHFLOW,
        PayeeCategory.MAILCHIMP, PayeeCategory.MARKETING_DIRECT, PayeeCategory.MARKETING_INDIRECT,
        PayeeCategory.MEMBERSHIPS, PayeeCategory.MUSICIAN_COSTS, PayeeCategory.OPERATIONAL_COSTS,
        PayeeCategory.PRS, PayeeCategory.PIANO_TUNER, PayeeCategory.RENT, PayeeCategory.SECURITY,
        PayeeCategory.SERVICES, PayeeCategory.SLACK, PayeeCategory.SPACE_HIRE, PayeeCategory.SUBSCRIPTIONS,
        PayeeCategory.TELEPHONE, PayeeCategory.TICKETWEB_CREDITS, PayeeCategory.WEB_HOST,
    ]:
        return True
    if category in [
        PayeeCategory.BB_LOAN, PayeeCategory.CREDIT_CARD_FEES, PayeeCategory.INTERNAL_TRANSFER,
        PayeeCategory.MUSIC_VENUE_TRUST, PayeeCategory.MUSICIAN_PAYMENTS, PayeeCategory.PETTY_CASH,
        PayeeCategory.RATES, PayeeCategory.SALARIES, PayeeCategory.SOUND_ENGINEER, PayeeCategory.UNCATEGORIZED,
        PayeeCategory.VAT, PayeeCategory.WORK_PERMITS, PayeeCategory.ZETTLE_CREDITS
    ]:
        return False
    raise ValueError(f"Unknown category {category}")


class CategorisedTransactionsRange(TabRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            accounting_months: List[AccountingMonth],
            categorised_transactions: List[CategorizedTransaction]):
        self.categories = sorted(set(_category_text(t) for t in categorised_transactions))
        super().__init__(top_left_cell, num_rows=2 + len(self.categories), num_cols=6)
        self.accounting_months: List[AccountingMonth] = checked_list_type(accounting_months, AccountingMonth)
        self.categorised_transactions: List[CategorizedTransaction] = checked_list_type(categorised_transactions,
                                                                                        CategorizedTransaction)

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
        by_accounting_month = group_into_dict(self.categorised_transactions, lambda t: self.acc_month(t.payment_date))
        by_category = {
            m: group_into_dict(by_accounting_month[m], _category_text)
            for m in self.accounting_months
        }

        def total_for_category(m: AccountingMonth, category: str) -> float:
            return sum(t.transaction.amount for t in by_category[m].get(category, []))

        categories_values = [
            ["Categorised Transactions"],
            [""] + [m.month_name for m in self.accounting_months] + ["Total", "VAT"]
        ]
        for i_cat, c in enumerate(self.categories):
            total_formula = f"=SUM({self[i_cat + 2, 1:4].in_a1_notation})"
            is_liable_to_vat = _is_vatable(c)
            if is_liable_to_vat:
                vat_formula = f"={self[i_cat + 2, 4].in_a1_notation} / 6.0"
            else:
                vat_formula = ""
            row = [c] + [total_for_category(m, c) for m in self.accounting_months] + [total_formula, vat_formula]

            categories_values.append(row)
        return categories_values

    def zettle_credits_cell(self, i_col):
        if PayeeCategory.ZETTLE_CREDITS not in self.categories:
            return None
        i = self.categories.index(PayeeCategory.ZETTLE_CREDITS)
        return self[i + 2, i_col].in_a1_notation

    def ticketweb_credits_cell(self, i_col):
        if PayeeCategory.TICKETWEB_CREDITS not in self.categories:
            return None
        i = self.categories.index(PayeeCategory.TICKETWEB_CREDITS)
        return self[i + 2, i_col].in_a1_notation

    def space_hire_cell(self, i_col):
        if PayeeCategory.SPACE_HIRE not in self.categories:
            return None
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
        format_requests = self.clear_values_and_formats_requests() + [
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

    def update(self, categorised_transactions: List[CategorizedTransaction], gigs_infos: List[GigsInfo]):

        ticket_sales_range = WalkInSalesRange(self.cell("B2"), self.accounting_months, gigs_infos)

        categories_range = CategorisedTransactionsRange(ticket_sales_range.bottom_left_cell.offset(2, 0),
                                                        self.accounting_months,
                                                        categorised_transactions)

        outputs_range = OutputsRange(categories_range.bottom_left_cell.offset(2, 0), categories_range,
                                     ticket_sales_range)

        self.workbook.batch_update(
            self._general_format_requests + outputs_range.format_requests + categories_range.format_requests + ticket_sales_range.format_requests
        )

        self.workbook.batch_update_values([
            (categories_range, categories_range.values),
            (ticket_sales_range, ticket_sales_range.values),
            (outputs_range, outputs_range.values),
        ])
