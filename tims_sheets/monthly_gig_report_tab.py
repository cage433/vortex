from decimal import Decimal
from numbers import Number
from pathlib import Path
from typing import Dict, TypeVar, Generic, List

import numpy as np
import pandas as pd

from date_range.accounting_month import AccountingMonth
from date_range.week import Week
from myopt.nothing import Nothing
from myopt.opt import Opt
from tims_sheets.monthly_git_report_tab_fields import MonthlyGigReportTabFields as MGRF
from utils.type_checks import checked_opt_type, checked_type, checked_list_type

T = TypeVar("T", bound=Number)


class WeeklyBreakdown(Generic[T]):
    def __init__(self, term: str, weeks: List[Week], values: List[T], mtd_value, vat_estimate: Opt[T]):
        self.term = checked_type(term, str)
        self.weeks = checked_list_type(weeks, Week)
        self.weekly_values: List[T] = checked_list_type(values, Number)
        self.mtd_value: T = checked_type(mtd_value, Number)
        self.vat_estimate: Opt[T] = checked_opt_type(vat_estimate, Number)

    @property
    def has_inconsistent_mtd_value(self):
        return abs(self.mtd_value - sum(self.weekly_values)) > 0.01


class MonthlyGigReportSheet:

    def __init__(
            self,
            month: AccountingMonth,
            audience_number: WeeklyBreakdown[int],
            breakdowns: List[WeeklyBreakdown[Decimal]],
    ):
        self.month: AccountingMonth = checked_type(month, AccountingMonth)
        self.audience_number = checked_type(audience_number, WeeklyBreakdown)
        self.breakdowns: List[WeeklyBreakdown[Decimal]] = checked_list_type(breakdowns, WeeklyBreakdown)
        self.breakdowns_by_term: Dict[str, WeeklyBreakdown[Decimal]] = {b.term: b for b in breakdowns}

    def total_for_term(self, term: str) -> Decimal:
        return self.breakdowns_by_term[term].mtd_value

    @staticmethod
    def from_spreadsheet(path: Path, month: AccountingMonth) -> 'MonthlyGigReportSheet':
        def exclude_row(row):
            if row[0] is np.nan:
                return True
            if pd.isna(row[0]):
                return True
            return False

        xls = pd.ExcelFile(path)
        sheet = pd.read_excel(xls, 'Monthly Gig Report', header=None)
        rows = [
            list(row[1])[1:] for row in
            list(sheet.iterrows())
        ]
        rows = [row for row in rows if not exclude_row(row)]
        sheet_as_dict = {row[0].lower(): row[1:] for row in rows}
        mtd_column = sheet_as_dict[MGRF.WEEK].index("MTD")
        vat_column = sheet_as_dict[MGRF.WEEK].index("VAT estimate")
        weeks = [
            Week(month.year, int(w))
            for w in sheet_as_dict[MGRF.WEEK][:-2]
            if int(w) <= month.year.num_weeks  # Blank extra week in Aug 21 report
        ]
        breakdowns = []
        audience_breakdown = None
        for term in MGRF.TERMS:
            if term == MGRF.WEEK:
                continue
            terms = sheet_as_dict[term]
            week_values = terms[:len(weeks)]
            vat = Nothing()
            mtd_value = terms[mtd_column]
            if terms[vat_column] is not np.nan:
                vat = Opt.of(terms[vat_column])
            breakdown = WeeklyBreakdown(term, weeks, week_values, mtd_value, vat)
            if term == MGRF.AUDIENCE_NUMBER:
                audience_breakdown = breakdown
            else:
                breakdowns.append(breakdown)

        return MonthlyGigReportSheet(month, audience_breakdown, breakdowns)
