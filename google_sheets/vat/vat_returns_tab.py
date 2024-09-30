from typing import List, Optional

from airtable_db.gigs_info import GigsInfo
from bank_statements.categorized_transaction import CategorizedTransaction
from bank_statements.payee_categories import PayeeCategory
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from google_sheets import Tab, Workbook
from google_sheets.tab_range import TabRange, TabCell
from utils import checked_list_type, checked_type, checked_optional_type
from utils.collection_utils import group_into_dict


class PaymentsRange(TabRange):

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
    def values(self):
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
        return values

class PaymentsRangeWithVAT(TabRange):
    COLUMNS = ["Payments", "Date", "Payee", "VAT", "Reclaimable"]

    def __init__(self, top_left_cell: TabCell, transactions: List[CategorizedTransaction],
                 category: Optional[PayeeCategory], vat_reclaim_fraction_cell: Optional[TabCell]):
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

        self.month_total_rows = [self[1, 1]]
        for m in self.accounting_months[:-1]:
            last_total_cell = self.month_total_rows[-1]
            self.month_total_rows.append(last_total_cell.offset(rows=len(self.by_month[m]) + 1))

    @property
    def format_requests(self):
        requests = [
            self[0, 0].set_bold_text_request(),
            self[:, 1].set_currency_format_request(),
            self.tab.group_rows_request(self.i_first_row + 1, self.i_first_row + self.num_rows - 1),
        ]
        for i_month, m in enumerate(self.accounting_months):
            month_total_row = self.month_total_rows[i_month]
            requests.append(
                self.tab.group_rows_request(
                    month_total_row.i_first_row + 1,
                    month_total_row.i_first_row + len(self.by_month[m])
                )
            )
        return requests

    def _category_total_formula(self, i_col):
        return "=" + "+".join(row[0, i_col].in_a1_notation for row in self.month_total_rows)

    def _month_total_formula(self, i_row: int, i_col, n_rows: int):
        return f"=SUM({self[i_row + 1:i_row + 1 + len(n_rows), i_col].in_a1_notation})"

    @property
    def values(self):
        category_total_formula = "=" + "+".join(c.in_a1_notation for c in self.month_total_rows)
        values = [
            [self.category or "Uncategorized"] + [self._category_total_formula(i_col) for i_col in range(2, 5)] + ["", ""]
        ]
        i_row = 1
        for m in self.accounting_months:
            trans_for_month = sorted(self.by_month[m], key=lambda t: (t.payment_date, t.payee))
            month_total_formula = f"=SUM({self[i_row + 1:i_row + 1 + len(trans_for_month), 1].in_a1_notation})"
            values.append([m.month_name] + [self._month_total_formula(i_row, i_col, len(trans_for_month)) for i_col in range(1, 4)] + ["", ""])
            for t in self.by_month[m]:
                values.append(["", t.amount, t.payment_date, t.transaction.payee])
            i_row += 1 + len(trans_for_month)
        return values


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


class VATReclaimFractionRange(TabRange):
    def __init__(self, total_bar_sales_range: TotalBarSalesRange, total_ticket_sales_range: TotalTicketSalesRange,
                 space_hire_range: PaymentsRange):
        super().__init__(space_hire_range.bottom_left_cell.offset(1, 0), num_rows=1, num_cols=2)
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
    def values(self):
        bar_sales, ticket_sales, space_hire = [
            range.top_left_cell.offset(0, 1).cell_coordinates.text
            for range in [self.total_bar_sales_range, self.total_ticket_sales_range, self.space_hire_range]
        ]
        return [
            ["VAT Reclaim Fraction",
             f"=({bar_sales} + {space_hire}) / ({bar_sales} + {space_hire} + {ticket_sales}) "]
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

        zettle_credit_range = PaymentsRange(self.cell("B4"),
                                            categorised_transactions,
                                            PayeeCategory.ZETTLE_CREDITS)
        walk_in_sales_range = WalkInSalesRange(zettle_credit_range.bottom_left_cell.offset(num_rows=1),
                                               gigs_info)
        total_bar_sales_range = TotalBarSalesRange(zettle_credit_range, walk_in_sales_range)
        ticket_web_credits_range = PaymentsRange(walk_in_sales_range.bottom_left_cell.offset(num_rows=2),
                                                 categorised_transactions,
                                                 PayeeCategory.TICKETWEB_CREDITS)
        walk_in_sales_range2 = WalkInSalesRange(ticket_web_credits_range.bottom_left_cell.offset(num_rows=1),
                                                gigs_info)
        total_ticket_sales_range = TotalTicketSalesRange(ticket_web_credits_range, walk_in_sales_range2)
        total_space_hires_range = PaymentsRange(walk_in_sales_range2.bottom_left_cell.offset(num_rows=1),
                                                categorised_transactions,
                                                PayeeCategory.SPACE_HIRE)
        vat_reclaim_fraction_range = VATReclaimFractionRange(total_bar_sales_range, total_ticket_sales_range,
                                                             total_space_hires_range)

        trans_categories = set(t.category for t in categorised_transactions)
        debit_vat_categories = sorted([c for c in PayeeCategory if c in trans_categories if
                                       not PayeeCategory.are_credits(c) and PayeeCategory.is_subject_to_vat(c)])
        if None in trans_categories:
            debit_vat_categories.append(None)
        categories_ranges = [
            PaymentsRange(vat_reclaim_fraction_range.bottom_left_cell.offset(num_rows=2), categorised_transactions,
                          debit_vat_categories[0])
        ]
        for i in range(1, len(debit_vat_categories)):
            last_range = categories_ranges[-1]
            categories_ranges.append(
                PaymentsRange(last_range.bottom_left_cell.offset(num_rows=1), categorised_transactions,
                              debit_vat_categories[i])
            )
        self.workbook.batch_update(
            self._general_format_requests
        )
        format_requests = (total_bar_sales_range.format_requests +
                           zettle_credit_range.format_requests +
                           walk_in_sales_range.format_requests +
                           ticket_web_credits_range.format_requests +
                           walk_in_sales_range2.format_requests +
                           total_ticket_sales_range.format_requests +
                           total_space_hires_range.format_requests +
                           vat_reclaim_fraction_range.format_requests)
        for category_range in categories_ranges:
            format_requests += category_range.format_requests
        self.workbook.batch_update(
            format_requests
            # total_bar_sales_range.format_requests +
            # zettle_credit_range.format_requests +
            # walk_in_sales_range.format_requests +
            # ticket_web_credits_range.format_requests +
            # walk_in_sales_range2.format_requests +
            # total_ticket_sales_range.format_requests +
            # total_space_hires_range.format_requests +
            # vat_reclaim_fraction_range.format_requests
        )
        self.workbook.batch_update(
            self.collapse_all_groups_requests()
        )

        self.workbook.batch_update_values([
            # (ticket_sales_range, ticket_sales_range.values),
            # (categories_range, categories_range.values),
            (zettle_credit_range, zettle_credit_range.values),
            (walk_in_sales_range, walk_in_sales_range.values),
            (total_bar_sales_range, total_bar_sales_range.values),
            (ticket_web_credits_range, ticket_web_credits_range.values),
            (walk_in_sales_range2, walk_in_sales_range2.values),
            (total_ticket_sales_range, total_ticket_sales_range.values),
            (total_space_hires_range, total_space_hires_range.values),
            (vat_reclaim_fraction_range, vat_reclaim_fraction_range.values),
        ])
        self.workbook.batch_update_values([
            (category_range, category_range.values) for category_range in categories_ranges
        ])
