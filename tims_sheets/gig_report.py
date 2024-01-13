import decimal
from numbers import Number
from pathlib import Path
from typing import Dict, TypeVar, Generic, List

import numpy as np
import pandas as pd

from date_range.accounting_month import AccountingMonth
from date_range.accounting_year import AccountingYear
from date_range.week import Week
from myopt.nothing import Nothing
from myopt.opt import Opt
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
    MONTH = "month"
    WEEK = "week"

    AUDIENCE_NUMBER = "audience number"
    ADVANCE_TICKET_SALES = "advance ticket sales"
    CREDIT_CARD_SALES = "credit card ticket sales"
    CASH_TICKET_SALES = "cash ticket sales"
    TOTAL_TICKET_SALES = "total ticket sales"
    EVENING_HIRE_FEE = "evening hire fee"
    DAY_HIRE = "day hire"
    BAR_TAKINGS = "bar takings"
    TOTAL_INCOME = "total income"
    DEAL_FEE = "deal fee"
    CASH_PAID_TO_MUSICIANS = "j cash paid to musicians"
    MUSICIAN_INTERNET = "musician internet"
    MUSICIAN_FEES = "musician fees"
    ACCOMMODATION = "accommodation"
    TRAVEL = "travel"
    CATERING = "catering"
    EQUIPMENT_HIRE = "equipment hire"
    WORK_PERMITS = "work permits"
    SOUND_ENGINEERING = "sound engineering"
    HIRE_FEES = "hire fees"
    MUSICIAN_COSTS = "musician costs"
    PRS = "prs"
    VOLUNTEER_COSTS = "volunteer costs"
    BAR_CASH_PURCHASES = "bar cash purchases"
    DRINKS_CASH_PURCHASES = "drinks cash purchases"
    DRINKS_BANK = "drinks bank"
    DRINKS_CARD = "drinks card"
    BAR_EXPENDITURE = "bar expenditure"
    SECURITY = "security"
    MARKETING = "marketing"

    TERMS = [
        AUDIENCE_NUMBER,
        ADVANCE_TICKET_SALES,
        CREDIT_CARD_SALES,
        CASH_TICKET_SALES,
        TOTAL_TICKET_SALES,
        EVENING_HIRE_FEE,
        DAY_HIRE,
        BAR_TAKINGS,
        TOTAL_INCOME,
        DEAL_FEE,
        CASH_PAID_TO_MUSICIANS,
        MUSICIAN_INTERNET,
        MUSICIAN_FEES,
        ACCOMMODATION,
        TRAVEL,
        CATERING,
        EQUIPMENT_HIRE,
        WORK_PERMITS,
        SOUND_ENGINEERING,
        HIRE_FEES,
        MUSICIAN_COSTS,
        PRS,
        VOLUNTEER_COSTS,
        BAR_CASH_PURCHASES,
        DRINKS_CASH_PURCHASES,
        DRINKS_BANK,
        DRINKS_CARD,
        BAR_EXPENDITURE,
        SECURITY,
        MARKETING,
    ]

    def __init__(
            self,
            month: AccountingMonth,
            audience_number: WeeklyBreakdown[int],
            breakdowns: List[WeeklyBreakdown[decimal]],
    ):
        self.month: AccountingMonth = checked_type(month, AccountingMonth)
        self.audience_number = checked_type(audience_number, WeeklyBreakdown)
        self.breakdowns: List[WeeklyBreakdown[decimal]] = checked_list_type(breakdowns, WeeklyBreakdown)
        self.breakdowns_by_term: Dict[str, WeeklyBreakdown[decimal]] = {b.term: b for b in breakdowns}

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
        mtd_column = sheet_as_dict[MonthlyGigReportSheet.WEEK].index("MTD")
        vat_column = sheet_as_dict[MonthlyGigReportSheet.WEEK].index("VAT estimate")
        weeks = [
            Week(month.year, int(w))
            for w in sheet_as_dict[MonthlyGigReportSheet.WEEK][:-2]
            if int(w) <= month.year.num_weeks  # Blank extra week in Aug 21 report
        ]
        breakdowns = []
        for term in MonthlyGigReportSheet.TERMS:
            if term == MonthlyGigReportSheet.WEEK:
                continue
            terms = sheet_as_dict[term]
            week_values = terms[:len(weeks)]
            vat = Nothing()
            mtd_value = terms[mtd_column]
            if terms[vat_column] is not np.nan:
                vat = Opt.of(terms[vat_column])
            breakdown = WeeklyBreakdown(term, weeks, week_values, mtd_value, vat)
            breakdowns.append(breakdown)


def path_for_accounting_month(month: AccountingMonth) -> Path:
    reports_path = Path(
        "/Users/alex/Dropbox (Personal)/vortex/Tim stuff/memory stick/Gig reports monthly/"
    )
    month_name = month.corresponding_calendar_month.first_day.date.strftime("%b %Y")
    return reports_path / f"{month.year.y}" / f"Gig Report Month {month.m}  - {month_name}.xlsx"


if __name__ == '__main__':
    month = AccountingMonth(AccountingYear(2019), 3)
    path = path_for_accounting_month(month)
    gig_report = MonthlyGigReportSheet.from_spreadsheet(path, month)

    # reports_path = Path(
    #     "/Users/alex/Dropbox (Personal)/vortex/Tim stuff/memory stick/Gig reports monthly/"
    # )
    # for y in [AccountingYear(y) for y in range(2019, 2024)]:
    #     for i, m in enumerate(y.accounting_months):
    #         name = m.corresponding_calendar_month.first_day.date.strftime("%b %Y")
    #         path = reports_path / f"{y.y}" / f"Gig Report Month {i + 1}  - {name}.xlsx"
    #         gig_report = MonthlyGigReport.from_spreadsheet(path, m)
