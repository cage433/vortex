from typing import List, Optional, Tuple

from airtable_db.gigs_info import GigsInfo
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

    def __add__(self, rhs: 'RangesAndValues'):
        return RangesAndValues(self.ranges_and_values + rhs.ranges_and_values)


class PaymentsRange(TabRange):

    def __init__(self, top_left_cell: TabCell, transactions: List[CategorizedTransaction],
                 category: Optional[PayeeCategory]):
        self.category: Optional[PayeeCategory] = checked_optional_type(category, PayeeCategory)
        self.transactions = [t for t in transactions if t.category == category]
        self.by_month = group_into_dict(
            self.transactions,
            lambda t: AccountingMonth.containing(t.payment_date)
        )
        self.accounting_months = sorted(self.by_month.keys())
        super().__init__(top_left_cell, num_rows=1 + len(self.transactions) + len(self.accounting_months), num_cols=3)

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
            num_in_month = len(self.by_month[m])
            requests.append(
                self.tab.group_rows_request(
                    month_total_cell.i_first_row + 1,
                    month_total_cell.i_first_row + num_in_month
                )
            )
            rows_offset = month_total_cell.i_first_row - self.i_first_row + 1
            requests.append(
                self[rows_offset:rows_offset + num_in_month, 0].date_format_request("d Mmm yy")
            )
        return requests

    @property
    def values(self) -> RangesAndValues:
        category_total_formula = "=" + "+".join(c.in_a1_notation for c in self.month_total_cells)
        values = [
            [self.category or "Uncategorized", category_total_formula, ""]
        ]
        i_row = 1
        for m in self.accounting_months:
            trans_for_month = sorted(self.by_month[m], key=lambda t: (t.payment_date, t.payee))
            month_total_formula = f"=SUM({self[i_row + 1:i_row + 1 + len(trans_for_month), 1].in_a1_notation})"
            values.append([m.month_name, month_total_formula, ""])
            for t in self.by_month[m]:
                values.append([t.payment_date, t.amount, t.transaction.payee])
            i_row += 1 + len(trans_for_month)
        return RangesAndValues([(self, values)])


class PaymentsRangeWithVAT(TabRange):

    def __init__(self, top_left_cell: TabCell, transactions: List[CategorizedTransaction],
                 category: Optional[PayeeCategory],
                 reclaimable_vat_fraction_cell: Optional[TabCell]
                 ):
        self.category: Optional[PayeeCategory] = checked_optional_type(category, PayeeCategory)
        self.transactions = [t for t in transactions if t.category == category]
        self.by_month = group_into_dict(
            self.transactions,
            lambda t: AccountingMonth.containing(t.payment_date)
        )
        self.accounting_months = sorted(self.by_month.keys())
        self.reclaimable_vat_fraction_cell = checked_optional_type(reclaimable_vat_fraction_cell, TabCell)
        self.num_value_cols = 2 if self.reclaimable_vat_fraction_cell is None else 3
        super().__init__(top_left_cell, num_rows=1 + len(self.transactions) + len(self.accounting_months),
                         num_cols=2 + self.num_value_cols)

        self.month_total_rows = [self[1, :]]
        for m in self.accounting_months[:-1]:
            last_total_row = self.month_total_rows[-1]
            self.month_total_rows.append(last_total_row.offset(rows=len(self.by_month[m]) + 1))

    @property
    def format_requests(self):
        requests = [
            self[0, 0].set_bold_text_request(),
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

    @property
    def values(self) -> RangesAndValues:
        category_total_formulae = [
            "=" + "+".join(month_total_row[0, i_col].in_a1_notation for month_total_row in self.month_total_rows)
            for i_col in range(1, 1 + self.num_value_cols)
        ]
        values = [
            [self.category or "Uncategorized"] + category_total_formulae + [""]
        ]
        i_row = 1
        for m in self.accounting_months:
            trans_for_month = sorted(self.by_month[m], key=lambda t: (t.payment_date, t.payee))
            month_total_formulae = [
                f"=SUM({self[i_row + 1:i_row + 1 + len(trans_for_month), i_col].in_a1_notation})"
                for i_col in range(1, 1 + self.num_value_cols)
            ]
            values.append([m.month_name] + month_total_formulae + [""])
            for i_trans, t in enumerate(self.by_month[m]):
                amount_cell = self[i_row + 1 + i_trans, 1]
                vat_formula = f"={amount_cell.in_a1_notation} / 6.0"
                if self.reclaimable_vat_fraction_cell is None:
                    reclaimable_vat_formula = []
                else:
                    reclaimable_vat_formula = [
                        f"={amount_cell.in_a1_notation} / 6.0 * {self.reclaimable_vat_fraction_cell.cell_coordinates.text}"]
                values.append([t.payment_date, t.amount, vat_formula] + reclaimable_vat_formula + [t.transaction.payee])
            i_row += 1 + len(trans_for_month)
        return RangesAndValues([(self, values)])


class PaymentsRangeForCategory(TabRange):

    def __init__(self, top_left_cell: TabCell, transactions: List[CategorizedTransaction],
                 category: Optional[PayeeCategory],
                 reclaimable_vat_fraction_cell: Optional[TabCell],
                 show_vat_if_applicable: bool,
                 show_reclaimable_vat_if_applicable: bool,
                 show_payee: bool
                 ):
        self.category: Optional[PayeeCategory] = checked_optional_type(category, PayeeCategory)
        self.transactions = [t for t in transactions if t.category == category]
        self.by_month = group_into_dict(
            self.transactions,
            lambda t: AccountingMonth.containing(t.payment_date)
        )
        self.accounting_months = sorted(self.by_month.keys())
        self.reclaimable_vat_fraction_cell = checked_optional_type(reclaimable_vat_fraction_cell, TabCell)
        self.show_vat = (
                show_vat_if_applicable
                and self.category is not None
                and PayeeCategory.is_subject_to_vat(self.category)
        )
        self.show_reclaimable_vat = (show_reclaimable_vat_if_applicable
                                     and self.category is not None
                                     and self.show_vat
                                     and PayeeCategory.is_debit(self.category))
        self.show_payee = checked_type(show_payee, bool)
        if (not self.show_vat and not self.show_reclaimable_vat and not self.show_payee):
            num_cols = 2
        else:
            num_cols = 5
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

    @property
    def values(self) -> RangesAndValues:
        if self.show_reclaimable_vat:
            summing_cols = range(1, 4)
        elif self.show_vat:
            summing_cols = range(1, 3)
        else:
            summing_cols = [1]
        category_total_formulae = [
            "=" + "+".join(month_total_row[0, i_col].in_a1_notation for month_total_row in self.month_total_rows)
            for i_col in summing_cols
        ]
        values = [
            [self.category or "Uncategorized"] + category_total_formulae + [""]
        ]
        i_row = 1
        for m in self.accounting_months:
            trans_for_month = sorted(self.by_month[m], key=lambda t: (t.payment_date, t.payee))
            month_total_formulae = [
                f"=SUM({self[i_row + 1:i_row + 1 + len(trans_for_month), i_col].in_a1_notation})"
                for i_col in summing_cols
            ]
            values.append([m.month_name] + month_total_formulae + [""])
            for i_trans, t in enumerate(self.by_month[m]):
                amount_cell = self[i_row + 1 + i_trans, 1]
                row = [t.payment_date, t.amount]
                if self.show_vat:
                    row.append(f"={amount_cell.in_a1_notation} / 6.0")
                if self.show_reclaimable_vat:
                    if self.category in [PayeeCategory.BAR_STOCK, PayeeCategory.BAR_SNACKS]:
                        reclaimable_vat_formula = f"={amount_cell.in_a1_notation} / 6.0"
                    else:
                        reclaimable_vat_formula = f"={amount_cell.in_a1_notation} / 6.0 * {self.reclaimable_vat_fraction_cell.cell_coordinates.text}"
                    row.append(reclaimable_vat_formula)
                if self.show_payee:
                    padding = [""] * (4 - len(row))
                    row += padding
                    row.append(t.transaction.payee)
                values.append(row)
            i_row += 1 + len(trans_for_month)
        return RangesAndValues([(self, values)])


class WalkInSalesRange(TabRange):

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
            self[0, 0].right_align_text_request(),
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
    def values(self) -> RangesAndValues:
        total_formula = "=" + "+".join(c.in_a1_notation for c in self.month_total_cells)
        values = [
            ["Walk in sales", total_formula, "", ""]
        ]
        i_row = 1
        for m in self.accounting_months:
            gigs_for_month = sorted(self.by_month[m].contracts_and_events,
                                    key=lambda t: (t.performance_date, t.event_titles))
            month_total_formula = f"=SUM({self[i_row + 1:i_row + 1 + len(gigs_for_month), 1].in_a1_notation})"
            values.append([m.month_name, month_total_formula, "", ""])
            contracts_and_events = sorted(self.by_month[m].contracts_and_events,
                                          key=lambda t: (t.performance_date, t.event_titles))
            for t in contracts_and_events:
                values.append([t.performance_date, t.total_walk_in_sales, "", t.event_titles])
            i_row += 1 + len(gigs_for_month)
        return RangesAndValues([(self, values)])


class FunctionOfTwoRangesRange(TabRange):
    def __init__(self, total_tile: str, range1: TabRange, range2: TabRange, operand: str, include_vat: bool):
        self.total_title: str = checked_type(total_tile, str)
        self.range1: TabRange = checked_type(range1, TabRange)
        self.range2: TabRange = checked_type(range2, TabRange)
        self.operand: str = checked_type(operand, str)
        self.include_vat: bool = checked_type(include_vat, bool)
        self.num_cols = 3 if self.include_vat else 2
        super().__init__(range1.top_left_cell.offset(-1, 0), num_rows=1, num_cols=self.num_cols)

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
    def values(self) -> RangesAndValues:
        cell_1, cell_2 = [r.top_left_cell.offset(0, 1).cell_coordinates.text for r in [self.range1, self.range2]]
        operand_cell_text = f"={cell_1} {self.operand} {cell_2}"
        vat_cell = [
            f"={self.top_left_cell.offset(0, 1).cell_coordinates.text} / 6.0"
        ] if self.include_vat else []

        vs = [
            [self.total_title] + [operand_cell_text] + vat_cell
        ]
        return RangesAndValues([(self, vs)])


class TotalBarSalesRange(FunctionOfTwoRangesRange):
    def __init__(self, zettle_credits_range: TabRange, walk_in_sales_range: TabRange, include_vat: bool):
        super().__init__("Total Bar Sales", zettle_credits_range, walk_in_sales_range, "-", include_vat)


class TotalTicketSalesRange(FunctionOfTwoRangesRange):
    def __init__(self, ticket_web_credits_range: TabRange, walk_in_sales_range: TabRange):
        super().__init__("Total Ticket Sales", ticket_web_credits_range, walk_in_sales_range, "+", include_vat=False)


class TotalBarSalesRange2(TabRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction],
                 gigs_info: GigsInfo, show_vat_if_applicable: bool, show_payee: bool):
        self.zettle_credit_range = PaymentsRangeForCategory(top_left_cell.offset(1),
                                                            categorised_transactions,
                                                            PayeeCategory.ZETTLE_CREDITS,
                                                            reclaimable_vat_fraction_cell=None,
                                                            show_vat_if_applicable=show_vat_if_applicable,
                                                            show_reclaimable_vat_if_applicable=False,
                                                            show_payee=show_payee
                                                            )
        self.walk_in_sales_range = WalkInSalesRange(self.zettle_credit_range.bottom_left_cell.offset(num_rows=1),
                                                    gigs_info)
        super().__init__(top_left_cell,
                         1 + self.zettle_credit_range.num_rows + self.walk_in_sales_range.num_rows,
                         5)

    @property
    def format_requests(self):
        requests = [
            self.outline_border_request(style="SOLID"),
            self[0].offset(self.num_rows).border_request(["top"], style="SOLID"),
            self[0, 0].set_bold_text_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        requests += self.zettle_credit_range.format_requests
        requests += self.walk_in_sales_range.format_requests
        return requests

    @property
    def values(self) -> RangesAndValues:
        zettle_cell, walk_in_cell = [r.top_left_cell.offset(0, 1).cell_coordinates.text for r in
                                     [self.zettle_credit_range, self.walk_in_sales_range]]
        bar_sales_cell = self.top_left_cell.offset(0, 1).cell_coordinates.text
        return RangesAndValues([
            (self[0, :], [["Total Bar Sales", f"={zettle_cell} - {walk_in_cell}", f"={bar_sales_cell} / 6", ""]])
        ]) + self.zettle_credit_range.values + self.walk_in_sales_range.values


class VATReclaimFractionRange(TabRange):
    def __init__(self, top_left_cell: TabCell, total_bar_sales_range: TotalBarSalesRange,
                 total_ticket_sales_range: TotalTicketSalesRange,
                 space_hire_range: PaymentsRange):
        super().__init__(top_left_cell, num_rows=1, num_cols=2)
        self.total_bar_sales_range: TotalBarSalesRange = checked_type(total_bar_sales_range, TotalBarSalesRange)
        self.total_ticket_sales_range: TotalTicketSalesRange = checked_type(total_ticket_sales_range,
                                                                            TotalTicketSalesRange)
        self.space_hire_range: PaymentsRange = checked_type(space_hire_range, PaymentsRange)

    @property
    def format_requests(self):
        return [
            self[0, 0].set_bold_text_request(),
            self[0, 1].percentage_format_request(),
        ]

    @property
    def values(self) -> RangesAndValues:
        bar_sales, ticket_sales, space_hire = [
            range.top_left_cell.offset(0, 1).cell_coordinates.text
            for range in [self.total_bar_sales_range, self.total_ticket_sales_range, self.space_hire_range]
        ]
        vs = [
            ["VAT Reclaim Fraction",
             f"=({bar_sales} + {space_hire}) / ({bar_sales} + {space_hire} + {ticket_sales} * 1.2) "]
        ]
        return RangesAndValues([(self, vs)])


class VatablePaymentsRange(TabRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction],
                 reclaimable_vat_cell: TabCell):
        self.trans_categories = set(t.category for t in categorised_transactions)
        debit_vat_categories = sorted(
            [c for c in PayeeCategory if
             c in self.trans_categories and (not PayeeCategory.is_credit(c)) and PayeeCategory.is_subject_to_vat(c)
             ])
        if None in self.trans_categories:
            debit_vat_categories.append(None)
        self.debit_categories_ranges = [
            PaymentsRangeForCategory(top_left_cell.offset(num_rows=3),
                                     categorised_transactions,
                                     debit_vat_categories[0], reclaimable_vat_cell,
                                     show_vat_if_applicable=True,
                                     show_reclaimable_vat_if_applicable=True,
                                     show_payee=True
                                     )
        ]
        for i in range(1, len(debit_vat_categories)):
            last_range = self.debit_categories_ranges[-1]
            self.debit_categories_ranges.append(
                PaymentsRangeForCategory(last_range.bottom_left_cell.offset(num_rows=1),
                                         categorised_transactions,
                                         debit_vat_categories[i],
                                         reclaimable_vat_cell,
                                         show_vat_if_applicable=True,
                                         show_reclaimable_vat_if_applicable=True,
                                         show_payee=True
                                         )
            )
        super().__init__(
            top_left_cell,
            3 + sum(r.num_rows for r in self.debit_categories_ranges),
            5
        )

    @property
    def format_requests(self):
        formats = [
            self.outline_border_request(),
            self[0].merge_columns_request(),
            self[0].center_text_request(),
            self[1].right_align_text_request(),
            self[0:2].set_bold_text_request(),
            self[-1].offset(1).border_request(["top"], style="SOLID_MEDIUM"),
            self.tab.group_rows_request(self.i_first_row + 3, self.i_first_row + self.num_rows - 1),
        ]
        for r in self.debit_categories_ranges:
            formats += r.format_requests
        return formats

    @property
    def values(self) -> RangesAndValues:
        def sum_cell(i_col):
            cells = [r[0, i_col].in_a1_notation for r in self.debit_categories_ranges]
            return f"={' + '.join(cells)}"

        headings = [
            ["Payments including VAT"],
            ["Category", "Payments", "VAT", "Reclaimable VAT", "Payee"],
            ["", sum_cell(1), sum_cell(2), sum_cell(3), ""]
        ]
        vs = RangesAndValues([(self[0:3], headings)])
        for r in self.debit_categories_ranges:
            vs += r.values
        return vs


class VatReclaimFractionRange2(TabRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction],
                 gigs_info: GigsInfo):
        self.zettle_credit_range = PaymentsRange(top_left_cell.offset(2),
                                                 categorised_transactions,
                                                 PayeeCategory.ZETTLE_CREDITS)
        self.walk_in_sales_range = WalkInSalesRange(self.zettle_credit_range.bottom_left_cell.offset(num_rows=1),
                                                    gigs_info)
        self.total_bar_sales_range = TotalBarSalesRange(self.zettle_credit_range, self.walk_in_sales_range,
                                                        include_vat=False)
        self.ticket_web_credits_range = PaymentsRange(self.walk_in_sales_range.bottom_left_cell.offset(num_rows=2),
                                                      categorised_transactions,
                                                      PayeeCategory.TICKETWEB_CREDITS)
        self.walk_in_sales_range2 = WalkInSalesRange(self.ticket_web_credits_range.bottom_left_cell.offset(num_rows=1),
                                                     gigs_info)
        self.total_ticket_sales_range = TotalTicketSalesRange(self.ticket_web_credits_range, self.walk_in_sales_range2)
        self.total_space_hires_range = PaymentsRange(self.walk_in_sales_range2.bottom_left_cell.offset(num_rows=1),
                                                     categorised_transactions,
                                                     PayeeCategory.SPACE_HIRE)
        self.vat_reclaim_fraction_range = VATReclaimFractionRange(top_left_cell, self.total_bar_sales_range,
                                                                  self.total_ticket_sales_range,
                                                                  self.total_space_hires_range)
        self.reclaim_percentage_cell = self.vat_reclaim_fraction_range.bottom_right_cell

        num_rows = (self.zettle_credit_range.num_rows +
                    self.walk_in_sales_range.num_rows +
                    self.total_bar_sales_range.num_rows +
                    self.ticket_web_credits_range.num_rows +
                    self.walk_in_sales_range2.num_rows +
                    self.total_ticket_sales_range.num_rows +
                    self.total_space_hires_range.num_rows +
                    self.vat_reclaim_fraction_range.num_rows)

        super().__init__(
            top_left_cell,
            num_rows,
            5
        )

    @property
    def format_requests(self):
        formats = [
            self.outline_border_request(),
            self[-1].offset(1).border_request(["top"], style="SOLID_MEDIUM"),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        formats = formats + (self.zettle_credit_range.format_requests +
                             self.walk_in_sales_range.format_requests +
                             self.total_bar_sales_range.format_requests +
                             self.ticket_web_credits_range.format_requests +
                             self.walk_in_sales_range2.format_requests +
                             self.total_ticket_sales_range.format_requests +
                             self.total_space_hires_range.format_requests +
                             self.vat_reclaim_fraction_range.format_requests)
        return formats

    @property
    def values(self) -> RangesAndValues:
        vs = RangesAndValues([])
        for r in [
            self.zettle_credit_range,
            self.walk_in_sales_range,
            self.total_bar_sales_range,
            self.ticket_web_credits_range,
            self.walk_in_sales_range2,
            self.total_ticket_sales_range,
            self.total_space_hires_range,
            self.vat_reclaim_fraction_range,
        ]:
            vs += r.values
        return vs


class VatableReceiptsRange(TabRange):
    def __init__(self, top_left_cell: TabCell, categorised_transactions: List[CategorizedTransaction],
                 gigs_info: GigsInfo):
        self.space_hire_range = PaymentsRangeForCategory(
            top_left_cell.offset(3),
            categorised_transactions,
            PayeeCategory.SPACE_HIRE,
            reclaimable_vat_fraction_cell=None,
            show_vat_if_applicable=True,
            show_reclaimable_vat_if_applicable=False,
            show_payee=True
        )
        # self.zettle_credit_range2 = PaymentsRangeForCategory(
        #     self.space_hire_range.bottom_left_cell.offset(num_rows=2),
        #     categorised_transactions,
        #     PayeeCategory.ZETTLE_CREDITS,
        #     reclaimable_vat_fraction_cell=None,
        #     show_vat_if_applicable=True,
        #     show_reclaimable_vat_if_applicable=False,
        #     show_payee=True
        # )
        # self.walk_in_sales_range3 = WalkInSalesRange(self.zettle_credit_range2.bottom_left_cell.offset(num_rows=1),
        #                                              gigs_info)
        self.total_bar_sales_range2 = TotalBarSalesRange2(
            self.space_hire_range.bottom_left_cell.offset(num_rows=1),
            categorised_transactions, gigs_info,
            show_vat_if_applicable=True,
            show_payee=True
        )
        num_rows = 3 + (self.space_hire_range.num_rows +
                        # self.zettle_credit_range2.num_rows +
                        # self.walk_in_sales_range3.num_rows +
                        self.total_bar_sales_range2.num_rows)

        super().__init__(
            top_left_cell,
            num_rows,
            5
        )

    @property
    def format_requests(self):
        formats = [
            self.outline_border_request(),
            self[0].merge_columns_request(),
            self[0].center_text_request(),
            self[1].right_align_text_request(),
            self[0:2].set_bold_text_request(),
            self[-1].offset(1).border_request(["top"], style="SOLID_MEDIUM"),
            self.tab.group_rows_request(self.i_first_row + 3, self.i_first_row + self.num_rows - 1),
        ]
        for r in [self.space_hire_range,
                  # self.zettle_credit_range2, self.walk_in_sales_range3,
                  self.total_bar_sales_range2]:
            formats += r.format_requests
        return formats

    @property
    def values(self) -> RangesAndValues:
        def sum_cell(i_col):
            cells = [r[0, i_col].in_a1_notation for r in [self.space_hire_range, self.total_bar_sales_range2]]
            return f"={' + '.join(cells)}"

        vs = RangesAndValues([
            (self, [
                ["Receipts including VAT"],
                ["Category", "Payments", "VAT", "", "Payee"],
                ["", sum_cell(1), sum_cell(2), ""]
            ])])
        for r in [
            self.space_hire_range,
            self.total_bar_sales_range2,
            # self.zettle_credit_range2,
            # self.walk_in_sales_range3,
        ]:
            vs += r.values
        return vs


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
            (self.TOTAL, 250),
            (self.VAT, 150),
        ]:
            format_requests.append(
                self.set_column_width_request(1 + col, width=width)
            )
        return format_requests

    def update(self, categorised_transactions: List[CategorizedTransaction], gigs_info: GigsInfo):

        vat_reclaim_fraction_range2 = VatReclaimFractionRange2(self.cell("B2"), categorised_transactions, gigs_info)

        vat_payments_range = VatablePaymentsRange(
            vat_reclaim_fraction_range2.bottom_left_cell.offset(num_rows=2),
            categorised_transactions,
            vat_reclaim_fraction_range2.reclaim_percentage_cell
        )

        vat_receipts_range = VatableReceiptsRange(
            vat_payments_range.bottom_left_cell.offset(num_rows=2),
            categorised_transactions,
            gigs_info
        )

        self.workbook.batch_update(
            self._general_format_requests
        )
        format_requests = (
                vat_reclaim_fraction_range2.format_requests +
                vat_payments_range.format_requests +
                vat_receipts_range.format_requests
        )
        self.workbook.batch_update(
            format_requests
        )
        self.workbook.batch_update(
            self.collapse_all_groups_requests()
        )

        values = vat_reclaim_fraction_range2.values + vat_payments_range.values + vat_receipts_range.values

        self.workbook.batch_update_values(values.ranges_and_values)
