from typing import List

from airtable_db.gigs_info import GigsInfo
from bank_statements.categorized_transaction import CategorizedTransaction
from date_range import Day
from date_range.accounting_month import AccountingMonth
from date_range.month import Month
from date_range.quarter import Quarter
from google_sheets import Tab, Workbook
from google_sheets.tab_range import TabRange
from utils import checked_type, checked_list_type
from utils.collection_utils import group_into_dict


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
        self.outputs_range = TabRange(self.cell("B2"), num_rows=7, num_cols=6)
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
                self.set_column_width_request(self.outputs_range.i_first_col + col, width=width)
            )
        return format_requests

    @staticmethod
    def _category_text(t: CategorizedTransaction) -> str:
        if t.category is None:
            return "Uncategorized"
        return t.category

    def _output_formats_and_values(self):
        format_requests = [
            self.outputs_range[0, :].merge_columns_request(),
            self.outputs_range[0:2, :].set_bold_text_request(),
            self.outputs_range[0:2, :].center_text_request(),
            self.outputs_range.outline_border_request(style="SOLID"),
            self.outputs_range[1:, 1:].set_currency_format_request(),
        ]

        output_values = [
            ["Outputs"],
            [""] + [m.month_name for m in self.months] + ["Total", "VAT"],
            ["Total Ticket Sales", "", "", "", "", ""],
            ["Hire Fees", "", "", "", "", ""],
            ["Bar Takings", "", "", "", "", ""],
            ["Total", "", "", "", "", ""],
        ]
        return format_requests, output_values

    def acc_month(self, d: Day) -> AccountingMonth:
        for m in self.accounting_months:
            if m.contains(d):
                return m
        raise ValueError(f"No accounting month found for {d}")

    def _categories_formats_and_values(self, categorised_transactions: List[CategorizedTransaction]):
        categories = sorted(set(self._category_text(t) for t in categorised_transactions))
        categories_range = TabRange(self.cell("B15"), num_rows=2 + len(categories), num_cols=6)
        format_requests = [

            categories_range[0, :].merge_columns_request(),
            categories_range[0, :].center_text_request(),
            categories_range.outline_border_request(style="SOLID"),
            categories_range[2:, 1:6].set_currency_format_request(),
            categories_range[0:2, :].set_bold_text_request(),
            categories_range[:, 0].set_bold_text_request(),
        ]

        by_accounting_month = group_into_dict(categorised_transactions, lambda t: self.acc_month(t.payment_date))
        by_category = {
            m: group_into_dict(by_accounting_month[m], self._category_text)
            for m in self.accounting_months
        }

        def total_for_category(m: AccountingMonth, category: str) -> float:
            return sum(t.transaction.amount for t in by_category[m].get(category, []))

        categories_values = [
            ["Categorised Transactions"],
            [""] + [m.month_name for m in self.months] + ["Total", "VAT"]
        ]
        for c in categories:
            row = [c] + [total_for_category(m, c) for m in self.accounting_months] + [""] * 2
            categories_values.append(row)

        return categories_range, format_requests, categories_values

    def _zettle_breakdown(self, category_range: TabRange, gigs_infos: List[GigsInfo]):
        zettle_range = TabRange(
            category_range.bottom_left_cell.offset(2, 0),
            num_rows=4,
            num_cols=6
        )
        format_requests = [
            zettle_range[0, :].merge_columns_request(),
            zettle_range[0, :].center_text_request(),
            zettle_range.outline_border_request(style="SOLID"),
            zettle_range[2:, 1:6].set_currency_format_request(),
            zettle_range[0:2, :].set_bold_text_request(),
            zettle_range[:, 0].set_bold_text_request(),
        ]

        zettle_values = [
            ["Zettle Breakdown"],
            [""] + [m.month_name for m in self.months] + ["Total", ""],
            ["Walk In Sales"] + [gi.total_walk_in_sales for gi in gigs_infos] + ["", ""],
            ["Total Sales"] + [gi.total_ticket_sales for gi in gigs_infos] + ["", ""],
        ]
        return zettle_range, format_requests, zettle_values

    def update(self, categorised_transactions: List[CategorizedTransaction], gigs_infos: List[GigsInfo]):

        output_format_requests, output_values = self._output_formats_and_values()
        categories_range, categories_format_requests, categories_values = self._categories_formats_and_values(
            categorised_transactions)

        zettle_range, zettle_format_requests, zettle_values = self._zettle_breakdown(categories_range, gigs_infos)

        self.workbook.batch_update(
            self._general_format_requests + output_format_requests + categories_format_requests + zettle_format_requests
        )

        self.workbook.batch_update_values([
            (self.outputs_range, output_values),
            (categories_range[:len(categories_values)], categories_values),
            (zettle_range, zettle_values),
        ])
