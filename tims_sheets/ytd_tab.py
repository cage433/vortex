from decimal import Decimal
from numbers import Number
from pathlib import Path
from typing import Generic, List, Dict, TypeVar

import numpy as np
import pandas as pd

from date_range import Day
from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from tims_sheets.path_utils import tims_gig_report_sheet_path
from utils import checked_type, checked_list_type
from tims_sheets.ytd_tab_fields import YTD_TabFields as YTDF

T = TypeVar("T", bound=Number)


class MonthlyBreakdown(Generic[T]):
    def __init__(self, term: str, months: List[AccountingMonth], values: List[T]):
        self.term = checked_type(term, str)
        self.months = checked_list_type(months, AccountingMonth)
        for v in values:
            if not isinstance(v, Number):
                raise ValueError(f"Expected a number, got {v}")
        self.values: List[T] = checked_list_type(values, Number)

    @property
    def total_value(self) -> T:
        return sum(self.values)


class YTD_Tab:
    def __init__(
            self,
            month: AccountingMonth,
            audience_number: MonthlyBreakdown[int],
            breakdowns: List[MonthlyBreakdown[Decimal]],
    ):
        self.month: AccountingMonth = checked_type(month, AccountingMonth)
        self.audience_number = checked_type(audience_number, MonthlyBreakdown)
        self.breakdowns: List[MonthlyBreakdown[Decimal]] = checked_list_type(breakdowns, MonthlyBreakdown)
        self.breakdowns_by_term: Dict[str, MonthlyBreakdown[Decimal]] = {b.term: b for b in breakdowns}

    def total_for_term(self, term: str) -> Decimal:
        return self.breakdowns_by_term[term].total_value

    def value_for_term(self, term: str) -> Decimal:
        i = self.month.months_since(self.month.year.first_accounting_month)
        return self.breakdowns_by_term[term].values[i]

    @staticmethod
    def from_spreadsheet(path: Path, month: AccountingMonth) -> 'YTD_Tab':
        def exclude_row(row):
            if row[0] is np.nan:
                return True
            if pd.isna(row[0]):
                return True
            return False

        xls = pd.ExcelFile(path)
        sheet = pd.read_excel(xls, 'YTD', header=None)
        rows = [
            list(row[1])[1:] for row in
            list(sheet.iterrows())
        ]
        months = [
            AccountingMonth.from_calendar_month(Day.from_datetime(d).month) for d in rows[6][1:13]
        ]
        months = [m for m in months if m <= month]
        rows = [row for row in rows if not exclude_row(row)]
        row_headings = [row[0] for row in rows[3:]]

        def check_rows_consistent_with_terms(i, headings, terms):
            if len(terms) == 0 and len(terms) == 0:
                return
            if len(terms) == 0:
                raise ValueError(f"Still have rows {headings}")
            if len(headings) == 0:
                raise ValueError(f"Still have terms {terms}")
            l = terms[0].lower().strip()
            r = headings[0].lower().strip()
            if l == r:
                check_rows_consistent_with_terms(i + 1, headings[1:], terms[1:])
            else:
                raise ValueError(f"{i}. l: {l}, r: {r}")

        check_rows_consistent_with_terms(0, row_headings, YTDF.TERMS)

        breakdowns = []
        audience_numbers = None
        for term, row in zip(YTDF.TERMS, rows[3:]):
            assert term.lower().strip() == row[0].lower().strip(), f"{term} != {row[1]}"
            if row[2] == "Wages":
                # Bug in (at least) Aug 23 sheet
                row = [0 for _ in range(12)]
            breakdown = MonthlyBreakdown(
                term,
                months,
                row[1:len(months) + 1]
            )
            if term == YTDF.AUDIENCE_NUMBER:
                audience_numbers = breakdown
            else:
                breakdowns.append(breakdown)
        return YTD_Tab(month, audience_numbers, breakdowns)



if __name__ == '__main__':
    month = AccountingMonth(AccountingYear(2023), 12)
    path = tims_gig_report_sheet_path(month)
    gig_report_sheet = YTD_Tab.from_spreadsheet(path, month)
    print(gig_report_sheet.month)
    # accounting_activity = AccountingActivity.activity_for_months([month], force=False)
    #
    # compare_sheets_for_month(gig_report_sheet, accounting_activity)
