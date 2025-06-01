from abc import abstractmethod
from typing import List, Optional, Tuple, Dict

from airtable_db.gigs_info import GigsInfo
from bank_statements import BankActivity, Transaction
from bank_statements.categorized_transaction import CategorizedTransaction
from bank_statements.payee_categories import PayeeCategory
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from google_sheets import Tab, Workbook
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_list_type, checked_type, checked_optional_type
from utils.collection_utils import group_into_dict


class RangesAndValues:
    def __init__(self, ranges_and_values: List[Tuple[TabRange, List[List[any]]]]):
        self.ranges_and_values: List[Tuple[TabRange, List[List[any]]]] = ranges_and_values
        for r, v in ranges_and_values:
            assert isinstance(r, TabRange)
            assert isinstance(v, list)
            for row in v:
                assert isinstance(row, list)
                if len(row) > r.num_cols:
                    raise ValueError(f"Row {row} has more columns than range {r}")

    def __add__(self, rhs: 'RangesAndValues'):
        return RangesAndValues(self.ranges_and_values + rhs.ranges_and_values)


class PaymentsRangeForCategory(TabRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            transactions: List[CategorizedTransaction],
            category: PayeeCategory,
            num_cols: int
    ):
        self.category: PayeeCategory = checked_type(category, PayeeCategory)
        self.transactions = [t for t in transactions if t.category == category]
        self.by_month: Dict[AccountingMonth, List[CategorizedTransaction]] = group_into_dict(
            self.transactions,
            lambda t: AccountingMonth.containing(t.payment_date)
        )
        self.accounting_months = sorted(self.by_month.keys())
        super().__init__(top_left_cell, num_rows=1 + len(self.transactions) + len(self.accounting_months),
                         num_cols=num_cols)

        self.month_total_rows = [self[1, :]]
        for m in self.accounting_months[:-1]:
            last_total_row = self.month_total_rows[-1]
            self.month_total_rows.append(last_total_row.offset(rows=len(self.by_month[m]) + 1))

    @property
    def format_requests(self):
        requests = [
            self[0, 0].set_bold_text_request(),
            self[:, 0].right_align_text_request(),
            self[:, 1:].set_currency_format_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        for i_month, m in enumerate(self.accounting_months):
            month_total_row = self.month_total_rows[i_month]
            num_in_month = len(self.by_month[m])
            requests.append(
                self.tab.group_rows_request(
                    month_total_row.i_first_row + 1,
                    month_total_row.i_first_row + num_in_month
                )
            )
            rows_offset = month_total_row.i_first_row - self.i_first_row + 1
            requests.append(
                self[rows_offset:rows_offset + num_in_month, 0].date_format_request("d Mmm yy")
            )
        return requests


class PaymentsRangeForCategorySansVAT(PaymentsRangeForCategory):

    def __init__(
            self,
            top_left_cell: TabCell,
            transactions: List[CategorizedTransaction],
            category: PayeeCategory,
    ):
        super().__init__(
            top_left_cell,
            transactions,
            category,
            num_cols=7
        )

    @property
    def values(self) -> RangesAndValues:
        summing_cols = range(1, 3)
        category_total_formulae = [
            "=" + "+".join(month_total_row[0, i_col].in_a1_notation for month_total_row in self.month_total_rows)
            for i_col in summing_cols
        ]
        values = [
            [self.category] + category_total_formulae
        ]
        i_row = 1
        for m in self.accounting_months:
            trans_for_month = sorted(self.by_month[m], key=lambda t: (t.payment_date, t.payee))
            month_total_formulae = [
                f"=SUM({self[i_row + 1:i_row + 1 + len(trans_for_month), i_col].in_a1_notation})"
                for i_col in summing_cols
            ]
            row = [m.month_name] + month_total_formulae
            values.append(row)
            for i_trans, t in enumerate(self.by_month[m]):
                amount_cells = [0.00, t.amount] if t.amount < 0 else [t.amount, 0.00]
                row = [t.payment_date] + amount_cells + ["", "", "", t.transaction.payee]
                values.append(row)
            i_row += 1 + len(trans_for_month)
        return RangesAndValues([(self, values)])


class PaymentsRangeForCategoryWithVAT(PaymentsRangeForCategory):

    def __init__(
            self,
            top_left_cell: TabCell,
            transactions: List[CategorizedTransaction],
            service_charge_cell: TabCell,
            category: PayeeCategory,
            reclaimable_vat_fraction_cell: TabCell,
    ):
        super().__init__(
            top_left_cell,
            transactions,
            category,
            num_cols=7
        )
        self.service_charge_cell: TabCell = checked_type(service_charge_cell, TabCell)
        self.reclaimable_vat_fraction_cell: TabCell = checked_type(reclaimable_vat_fraction_cell,
                                                                   TabCell)
        self.include_vat_columns = True

    @property
    def values(self) -> RangesAndValues:
        num_vat_columns = 3
        num_cash_flow_columns = 2
        summing_cols = range(1, 1 + num_cash_flow_columns + num_vat_columns)
        category_total_formulae = [
            "=" + "+".join(month_total_row[0, i_col].in_a1_notation for month_total_row in self.month_total_rows)
            for i_col in summing_cols
        ]
        values = [
            [self.category] + category_total_formulae
        ]
        i_row = 1
        for m in self.accounting_months:
            trans_for_month = sorted(self.by_month[m], key=lambda t: (t.payment_date, t.payee))
            month_total_formulae = [
                f"=SUM({self[i_row + 1:i_row + 1 + len(trans_for_month), i_col].in_a1_notation})"
                for i_col in summing_cols
            ]
            row = [m.month_name] + month_total_formulae
            values.append(row)
            for i_trans, t in enumerate(self.by_month[m]):
                amount_cell = self[i_row + 1 + i_trans, 1]
                row = [t.payment_date]
                if PayeeCategory.is_credit(self.category):
                    row += [t.amount, ""]
                else:
                    row += ["", t.amount]
                    amount_cell = self[i_row + 1 + i_trans, 2]

                if self.include_vat_columns:
                    if self.category == PayeeCategory.RENT:
                        vat_formula = f"=({amount_cell.in_a1_notation} - {self.service_charge_cell.in_a1_notation}) / 6.0"
                    else:
                        vat_formula = f"={amount_cell.in_a1_notation} / 6.0"
                    is_credit = PayeeCategory.is_credit(self.category)
                    if is_credit:
                        row += [vat_formula, "", ""]
                    else:
                        full_vat_cell = self[i_row + 1 + i_trans, len(row) + 1]
                        if self.category in [PayeeCategory.BAR_STOCK, PayeeCategory.BAR_SNACKS]:
                            reclaimable_vat_formula = f"={full_vat_cell.in_a1_notation}"
                        else:
                            reclaimable_vat_formula = f"={full_vat_cell.in_a1_notation} * {self.reclaimable_vat_fraction_cell.cell_coordinates.text}"
                        row += ["", vat_formula, reclaimable_vat_formula]

                row.append(t.transaction.payee)
                values.append(row)
            i_row += 1 + len(trans_for_month)
        return RangesAndValues([(self, values)])


class WalkInSalesRange(TabRange):

    def __init__(
            self,
            top_left_cell: TabCell,
            gigs_info: GigsInfo,
            right_align_title: bool,
    ):
        self.right_align_title: bool = checked_type(right_align_title, bool)
        self.gigs_info: GigsInfo = gigs_info.restrict_to_gigs()
        self.accounting_months = sorted(
            set(AccountingMonth.containing(ce.performance_date) for ce in self.gigs_info.contracts_and_events))
        self.by_month = {m: self.gigs_info.restrict_to_period(m) for m in self.accounting_months}
        super().__init__(top_left_cell, num_rows=1 + self.gigs_info.number_of_gigs + len(self.accounting_months),
                         num_cols=3)

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
        if self.right_align_title:
            requests.append(self[0, 0].right_align_text_request(), )
        for i_month, m in enumerate(self.accounting_months):
            month_total_cell = self.month_total_cells[i_month]
            requests += [
                self.tab.group_rows_request(
                    month_total_cell.i_first_row + 1,
                    month_total_cell.i_first_row + len(self.by_month[m].contracts_and_events)
                ),
                self[
                month_total_cell.i_first_row - self.i_first_row + 1:month_total_cell.i_first_row - self.i_first_row + 1 + len(
                    self.by_month[m].contracts_and_events), 0].date_format_request("d Mmm yy")
            ]
        return requests

    @property
    def values(self) -> RangesAndValues:
        total_formula = "=" + "+".join(c.in_a1_notation for c in self.month_total_cells)
        values = [
            ["Walk in sales", total_formula]
        ]
        i_row = 1
        for m in self.accounting_months:
            gigs_for_month = sorted(self.by_month[m].contracts_and_events,
                                    key=lambda t: (t.performance_date, t.event_titles))
            month_total_formula = f"=SUM({self[i_row + 1:i_row + 1 + len(gigs_for_month), 1].in_a1_notation})"
            row = [m.month_name, month_total_formula]
            values.append(row)
            contracts_and_events = sorted(self.by_month[m].contracts_and_events,
                                          key=lambda t: (t.performance_date, t.event_titles))
            for t in contracts_and_events:
                row = [t.performance_date, t.total_walk_in_sales, t.event_titles]
                values.append(row)
            i_row += 1 + len(gigs_for_month)
        return RangesAndValues([(self, values)])


class TotalBarSalesRange(TabRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction],
                 gigs_info: GigsInfo, num_cols: int):
        self.zettle_credit_range = PaymentsRangeForCategorySansVAT(
            top_left_cell.offset(1),
            categorised_transactions,
            category=PayeeCategory.CARD_SALES,
        )
        self.walk_in_sales_range = WalkInSalesRange(
            self.zettle_credit_range.bottom_left_cell.offset(num_rows=1),
            gigs_info,
            right_align_title=True,
        )
        super().__init__(
            top_left_cell,
            1 + self.zettle_credit_range.num_rows + self.walk_in_sales_range.num_rows,
            num_cols
        )

    @property
    def format_requests(self):
        requests = [
            self[0, 0].set_bold_text_request(),
            self[0, 1:].set_currency_format_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        requests += self.zettle_credit_range.format_requests
        requests += self.walk_in_sales_range.format_requests
        return requests


class TotalBarSalesWithVATRange(TotalBarSalesRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction],
                 gigs_info: GigsInfo):
        super().__init__(top_left_cell, categorised_transactions, gigs_info, num_cols=6)

    @property
    def values(self) -> RangesAndValues:
        zettle_cell, walk_in_cell = [r.top_left_cell.offset(0, 1).cell_coordinates.text for r in
                                     [self.zettle_credit_range, self.walk_in_sales_range]]
        bar_sales_cell = self.top_left_cell.offset(0, 1).cell_coordinates.text
        top_row = ["Total Bar Sales", f"={zettle_cell} - {walk_in_cell}", "", f"={bar_sales_cell} / 6"]
        return (RangesAndValues([(self[0, :], [top_row])]) +
                self.zettle_credit_range.values + self.walk_in_sales_range.values)


class TotalBarSalesSansVATRange(TotalBarSalesRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction],
                 gigs_info: GigsInfo):
        super().__init__(top_left_cell, categorised_transactions, gigs_info, num_cols=3)

    @property
    def values(self) -> RangesAndValues:
        zettle_cell, walk_in_cell = [r.top_left_cell.offset(0, 1).cell_coordinates.text for r in
                                     [self.zettle_credit_range, self.walk_in_sales_range]]
        top_row = ["Total Bar Sales", f"={zettle_cell} - {walk_in_cell}"]
        return (RangesAndValues([(self[0, :], [top_row])]) +
                self.zettle_credit_range.values + self.walk_in_sales_range.values)


class TotalBareSalesExVATRange(TabRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction],
                 gigs_info: GigsInfo):
        self.bar_sales_range = TotalBarSalesSansVATRange(top_left_cell.offset(1), categorised_transactions, gigs_info)
        super().__init__(
            top_left_cell,
            1 + self.bar_sales_range.num_rows,
            num_cols=3
        )

    @property
    def format_requests(self):
        requests = [
            self[0, 0].set_bold_text_request(),
            self[0, 1:].set_currency_format_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        requests += self.bar_sales_range.format_requests
        return requests

    @property
    def values(self) -> RangesAndValues:
        top_row = ["Total Bar Sales (ex VAT)", f"={self.bar_sales_range[0, 1].in_a1_notation} * 5 / 6"]
        return (
                RangesAndValues([(self[0, :], [top_row])]) +
                self.bar_sales_range.values
        )


class SpaceHireExVATRange(TabRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction]):
        self.space_hires_range = PaymentsRangeForCategorySansVAT(
            top_left_cell.offset(num_rows=1),
            categorised_transactions,
            category=PayeeCategory.SPACE_HIRE,
        )
        super().__init__(
            top_left_cell,
            1 + self.space_hires_range.num_rows,
            num_cols=3
        )

    @property
    def format_requests(self):
        requests = [
            self[0, 0].set_bold_text_request(),
            self[0, 1:].set_currency_format_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        requests += self.space_hires_range.format_requests
        return requests

    @property
    def values(self) -> RangesAndValues:
        top_row = ["Space Hire (ex VAT)", f"={self.space_hires_range[0, 1].in_a1_notation} * 5 / 6"]
        return (
                RangesAndValues([(self[0, :], [top_row])]) +
                self.space_hires_range.values
        )


class TotalTicketSalesRange(TabRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction],
                 gigs_info: GigsInfo):
        self.ticket_web_credits_range = PaymentsRangeForCategorySansVAT(
            top_left_cell.offset(1),
            categorised_transactions,
            category=PayeeCategory.TICKETWEB_CREDITS,
        )
        self.walk_in_sales_range = WalkInSalesRange(
            self.ticket_web_credits_range.bottom_left_cell.offset(num_rows=1),
            gigs_info,
            right_align_title=True,
        )
        super().__init__(top_left_cell,
                         1 + self.ticket_web_credits_range.num_rows + self.walk_in_sales_range.num_rows,
                         6)

    @property
    def format_requests(self):
        requests = [
            self[0, 0].set_bold_text_request(),
            self[0, 1:].set_currency_format_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        requests += self.ticket_web_credits_range.format_requests
        requests += self.walk_in_sales_range.format_requests
        return requests

    @property
    def values(self) -> RangesAndValues:
        ticket_web_cell, walk_in_cell = [r.top_left_cell.offset(0, 1).cell_coordinates.text for r in
                                         [self.ticket_web_credits_range, self.walk_in_sales_range]]
        top_row = ["Total Ticket Sales", f"={ticket_web_cell} + {walk_in_cell}"]
        return (RangesAndValues([(self[0, :], [top_row])]) +
                self.ticket_web_credits_range.values + self.walk_in_sales_range.values)


class PaymentsRangeForCategories(TabRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            name: str,
            categories: List[PayeeCategory],
            categorised_transactions: List[CategorizedTransaction],
    ):
        self.name = checked_type(name, str)
        self.categories = checked_type(categories, list)
        self.categorised_transactions: List[CategorizedTransaction] = checked_list_type(categorised_transactions,
                                                                                        CategorizedTransaction)
        self.trans_categories = set(t.category for t in categorised_transactions)
        self.categories_to_display = [c for c in self.categories if c in self.trans_categories]

        self.category_ranges = [
            self.payments_range(top_left_cell.offset(1), self.categories_to_display[0])
        ]
        for i in range(1, len(self.categories_to_display)):
            last_range = self.category_ranges[-1]
            self.category_ranges.append(
                self.payments_range(last_range.bottom_left_cell.offset(num_rows=1), self.categories_to_display[i], )
            )
        super().__init__(
            top_left_cell,
            num_rows=1 + sum(r.num_rows for r in self.category_ranges),
            num_cols=6
        )

    @abstractmethod
    def payments_range(self, top_left: TabCell, category: PayeeCategory):
        raise ValueError("Abstract method")

    @property
    @abstractmethod
    def cols_to_sum(self):
        raise ValueError("Abstract method")

    @property
    def format_requests(self):
        formats = [
            self[0, 0].set_bold_text_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        for r in self.category_ranges:
            formats += r.format_requests
        return formats

    @property
    def values(self) -> RangesAndValues:
        def sum_cell(i_col):
            cells = [r[0, i_col].in_a1_notation for r in self.category_ranges]
            return f"={' + '.join(cells)}"

        headings = [
            [self.name] + [sum_cell(i_col) for i_col in self.cols_to_sum]
        ]
        vs = RangesAndValues([(self[0], headings)])
        for r in self.category_ranges:
            vs += r.values
        return vs


class PaymentsRangeForCategoriesWithVAT(PaymentsRangeForCategories):
    def __init__(
            self,
            top_left_cell: TabCell,
            name: str,
            service_charge_cell: TabCell,
            categories: List[PayeeCategory],
            categorised_transactions: List[CategorizedTransaction],
            reclaimable_vat_cell: TabCell
    ):
        self.service_charge_cell: TabCell = checked_type(service_charge_cell, TabCell)
        self.reclaimable_vat_cell: TabCell = checked_type(reclaimable_vat_cell, TabCell)
        super().__init__(
            top_left_cell,
            name,
            categories,
            categorised_transactions,
        )

    @property
    @abstractmethod
    def cols_to_sum(self):
        return range(1, 6)

    def payments_range(self, top_left: TabCell, category: PayeeCategory):
        return PaymentsRangeForCategoryWithVAT(
            top_left,
            self.categorised_transactions,
            self.service_charge_cell,
            category,
            self.reclaimable_vat_cell
        )


class PaymentsRangeForCategoriesSansVat(PaymentsRangeForCategories):
    def __init__(
            self,
            top_left_cell: TabCell,
            name: str,
            categories: List[PayeeCategory],
            categorised_transactions: List[CategorizedTransaction],
    ):
        super().__init__(
            top_left_cell,
            name,
            categories,
            categorised_transactions,
        )

    def payments_range(self, top_left: TabCell, category: PayeeCategory):
        return PaymentsRangeForCategorySansVAT(
            top_left,
            self.categorised_transactions,
            category,
        )

    @property
    @abstractmethod
    def cols_to_sum(self):
        return range(1, 3)


class ServiceChargeRange(TabRange):
    SERVICE_CHARGE = 594.72
    def __init__(self, top_left_cell: TabCell):
        super().__init__(
            top_left_cell,
            num_rows=1,
            num_cols=2
        )

    @property
    def format_requests(self):
        formats = [
            self.outline_border_request(),
            self[0, 0].set_bold_text_request(),
            self[0, 1].set_currency_format_request(),
        ]
        return formats

    @property
    def values(self) -> RangesAndValues:
        return RangesAndValues(
            [(self[0], [["Service Charge", self.SERVICE_CHARGE]])]
        )

    @property
    def service_charge_cell(self) -> TabCell:
        return self.top_left_cell.offset(0, 1)


class CashFlowsRange(TabRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            service_charge_cell: TabCell,
            categorised_transactions: List[CategorizedTransaction],
            gigs_info: GigsInfo,
            reclaimable_vat_cell: TabCell):
        self.service_charge_cell: TabCell = checked_type(service_charge_cell, TabCell)
        self.trans_categories = set(t.category for t in categorised_transactions)

        debit_vat_categories = sorted(
            [c for c in PayeeCategory if
             c in self.trans_categories and PayeeCategory.is_debit(c) and PayeeCategory.is_subject_to_vat(c)
             ])
        if None in self.trans_categories:
            debit_vat_categories.append(None)
        credit_vat_categories = sorted(
            [c for c in PayeeCategory if
             c in self.trans_categories and PayeeCategory.is_credit(c) and PayeeCategory.is_subject_to_vat(c)
             and c is not PayeeCategory.CARD_SALES
             ])
        non_vat_categories = sorted(
            [c for c in self.trans_categories if
             c not in debit_vat_categories and c not in credit_vat_categories and c is not PayeeCategory.CARD_SALES]
        )
        self.bar_sales_range = TotalBarSalesWithVATRange(top_left_cell.offset(4), categorised_transactions, gigs_info)
        self.walk_in_sales_range = WalkInSalesRange(
            self.bar_sales_range.bottom_left_cell.offset(num_rows=1),
            gigs_info,
            right_align_title=False
        )
        self.other_vatable_receipts_range = PaymentsRangeForCategoriesWithVAT(
            self.walk_in_sales_range.bottom_left_cell.offset(num_rows=1),
            "Other Receipts",
            self.service_charge_cell,
            credit_vat_categories,
            categorised_transactions,
            reclaimable_vat_cell
        )

        self.vatable_payments_range = PaymentsRangeForCategoriesWithVAT(
            self.other_vatable_receipts_range.bottom_left_cell.offset(num_rows=1),
            "VATable Payments",
            self.service_charge_cell,
            debit_vat_categories,
            categorised_transactions,
            reclaimable_vat_cell
        )
        self.non_vatable_range = PaymentsRangeForCategoriesSansVat(
            self.vatable_payments_range.bottom_left_cell.offset(num_rows=1),
            "Not VATable",
            non_vat_categories,
            categorised_transactions,
        )
        self.child_ranges = [
            self.bar_sales_range,
            self.walk_in_sales_range,
            self.other_vatable_receipts_range,
            self.vatable_payments_range,
            self.non_vatable_range,
        ]
        super().__init__(
            top_left_cell,
            4 + sum(r.num_rows for r in self.child_ranges),
            7
        )
        self.net_receipts_cell: TabCell = self.top_left_cell.offset(3, 1)
        self.net_payments_cell: TabCell = self.top_left_cell.offset(3, 2)
        self.net_receipts_vat_cell: TabCell = self.top_left_cell.offset(3, 3)
        self.net_payments_vat_cell: TabCell = self.top_left_cell.offset(3, 4)
        self.net_reclaimable_vat_cell: TabCell = self.top_left_cell.offset(3, 5)

    @property
    def format_requests(self):
        formats = [
            self.outline_border_request(),
            self[0].merge_columns_request(),
            self[1, 3:6].merge_columns_request(),
            self[0:2].center_text_request(),
            self[2].right_align_text_request(),
            self[0:3].set_bold_text_request(),
            self.tab.group_rows_request(self.i_first_row + 4, self.i_first_row + self.num_rows - 1),
            self[0].offset(self.num_rows).border_request(["top"], style="SOLID_MEDIUM"),
        ]
        for r in self.child_ranges:
            formats += r.format_requests
        return formats

    @property
    def values(self) -> RangesAndValues:
        def sum_cell(i_col):
            cells = [r[0, i_col].in_a1_notation for r in self.child_ranges]
            return f"={' + '.join(cells)}"

        headings = [
            ["Cash Flows"],
            ["", "", "", "VAT"],
            ["", "Receipts", "Payments", "Credit", "Debit", "Reclaimable", ""],
            [""] + [sum_cell(i_col) for i_col in range(1, 6)],
        ]
        vs = RangesAndValues([(self[0:4], headings)])
        for r in self.child_ranges:
            vs += r.values
        return vs


class VatReclaimFractionRange(TabRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction],
                 gigs_info: GigsInfo):
        self.total_ticket_sales_range = TotalTicketSalesRange(top_left_cell.offset(1), categorised_transactions,
                                                              gigs_info)
        self.total_bar_sales_range = TotalBareSalesExVATRange(
            self.total_ticket_sales_range.bottom_left_cell.offset(1),
            categorised_transactions,
            gigs_info)
        self.space_hires_range = SpaceHireExVATRange(
            self.total_bar_sales_range.bottom_left_cell.offset(num_rows=1),
            categorised_transactions,
        )

        self.child_ranges = [
            self.total_ticket_sales_range,
            self.total_bar_sales_range,
            self.space_hires_range]
        super().__init__(top_left_cell, num_rows=1 + sum(r.num_rows for r in self.child_ranges), num_cols=3)
        self.reclaim_percentage_cell = self.top_left_cell.offset(0, 1)

    @property
    def format_requests(self):
        formats = [
            self.outline_border_request(),
            self[0, 1:3].merge_columns_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
            self[0, 1].right_align_text_request(),
            self[0, 1].percentage_format_request(),
            self[0, 0].set_bold_text_request(),
            self[0].offset(self.num_rows).border_request(["top"], style="SOLID_MEDIUM"),
        ]
        for child_range in self.child_ranges:
            formats += child_range.format_requests
        return formats

    @property
    def values(self) -> RangesAndValues:
        ticket, bar, space = [r.top_left_cell.offset(0, 1).in_a1_notation for r in self.child_ranges]
        vs = RangesAndValues(
            [
                (
                    self[0],
                    [["VAT Reclaim Fraction", f"=({bar} + {space}) / ({ticket} + {bar} + {space})"]]
                ),
            ]
        )

        for r in self.child_ranges:
            vs += r.values
        return vs


class BankCheckRange(TabRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            bank_activity: BankActivity,
            net_receipts_cell: TabCell,
            net_payments_cell: TabCell,
    ):
        super().__init__(top_left_cell, num_rows=5, num_cols=2)
        self.bank_activity: BankActivity = checked_type(bank_activity, BankActivity)
        self.net_cash_flow_cell: TabCell = checked_type(net_receipts_cell, TabCell)
        self.net_payments_cell: TabCell = checked_type(net_payments_cell, TabCell)

    @property
    def format_requests(self):
        return [
            self[0].merge_columns_request(),
            self[0].center_text_request(),
            self[0].set_bold_text_request(),
            self[:, 0].set_bold_text_request(),
            self[:, 1].set_currency_format_request(),
            self.outline_border_request(),
        ]

    @property
    def values(self) -> RangesAndValues:
        initial_balance_cell = self[1, 1].in_a1_notation
        terminal_balance_cell = self[2, 1].in_a1_notation
        pnl_balance_cell = self[3, 1].in_a1_notation
        return RangesAndValues([(self, [
            ["Bank Check"],
            ["Initial Balance", float(self.bank_activity.initial_balance_across_accounts)],
            ["Terminal Balance", float(self.bank_activity.terminal_balance_across_accounts)],
            ["P/L", f"={terminal_balance_cell} - {initial_balance_cell}"],
            ["Difference",
             f"={pnl_balance_cell} - {self.net_cash_flow_cell.cell_coordinates.text} - {self.net_payments_cell.cell_coordinates.text}"],
        ])])


class VATSubmissionRange(TabRange):
    def __init__(
            self,
            top_left_cell: TabCell,
            cash_flows_range: CashFlowsRange,
    ):
        super().__init__(top_left_cell, num_rows=11, num_cols=2)
        self.cash_flows_range: CashFlowsRange = checked_type(cash_flows_range, CashFlowsRange)

    @property
    def format_requests(self):
        return [
            self.outline_border_request(),
            self[2:, 1].set_currency_format_request(),
            self[1:, 1].right_align_text_request(),
            self[:, 0].set_bold_text_request(),
            self[0:2].set_bold_text_request(),
            self[0].merge_columns_request(),
            self[0].center_text_request(),
        ]

    @property
    def values(self) -> RangesAndValues:
        receipts, payments, receipts_vat, payments_vat, reclaimable_vat = [
            c.cell_coordinates.text for c in [self.cash_flows_range.net_receipts_cell,
                                              self.cash_flows_range.net_payments_cell,
                                              self.cash_flows_range.net_receipts_vat_cell,
                                              self.cash_flows_range.net_payments_vat_cell,
                                              self.cash_flows_range.net_reclaimable_vat_cell,
                                              ]]
        return RangesAndValues([(self, [
            ["VAT Submission"],
            ["Description", "Value"],
            ["VAT due on Sales", f"={receipts_vat}"],
            ["VAT due from EU", 0],
            ["Total VAT due", "Calculated"],
            ["VAT reclaimable", f"={reclaimable_vat} * -1"],
            ["VAT to pay/claim", "Calculated"],
            ["Total Sales (exc)", f"={receipts} - {receipts_vat}"],
            ["Total Purchases (exc)", f"={payments} - {payments_vat}"],
            ["Goods to EU (exc)", 0],
            ["Goods from EU (exc)", 0],
        ])])


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
            (self.VAT + 1, 250),
        ]:
            format_requests.append(
                self.set_column_width_request(1 + col, width=width)
            )
        return format_requests

    def update(
            self,
            categorised_transactions: List[CategorizedTransaction],
            gigs_info: GigsInfo,
            bank_activity: BankActivity
    ):

        vat_reclaim_fraction_range = VatReclaimFractionRange(
            self.cell("B2"),
            categorised_transactions, gigs_info)

        service_charge_range = ServiceChargeRange(
            vat_reclaim_fraction_range.bottom_left_cell.offset(3),
        )
        cash_flows_range = CashFlowsRange(
            service_charge_range.bottom_left_cell.offset(3),
            service_charge_range.service_charge_cell,
            categorised_transactions,
            gigs_info,
            vat_reclaim_fraction_range.reclaim_percentage_cell
        )

        bank_check_range = BankCheckRange(
            cash_flows_range.bottom_left_cell.offset(3),
            bank_activity,
            cash_flows_range.net_receipts_cell,
            cash_flows_range.net_payments_cell,
        )

        vat_submission_range = VATSubmissionRange(
            bank_check_range.bottom_left_cell.offset(3),
            cash_flows_range,
        )
        self.workbook.batch_update(
            self._general_format_requests
        )
        format_requests = (
                vat_reclaim_fraction_range.format_requests +
                service_charge_range.format_requests +
                cash_flows_range.format_requests +
                bank_check_range.format_requests +
                vat_submission_range.format_requests
        )
        self.workbook.batch_update(
            format_requests
        )
        self.workbook.batch_update(
            self.collapse_all_groups_requests()
        )

        values = (vat_reclaim_fraction_range.values
                  + service_charge_range.values
                  + cash_flows_range.values
                  + bank_check_range.values
                  + vat_submission_range.values)

        self.workbook.batch_update_values(values.ranges_and_values)
