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

class MonthlyGigReport:
    month = "month"
    week = "week"

    audience_number = "audience number"
    advance_ticket_sales = "advance ticket sales"
    credit_card_sales = "credit card ticket sales"
    cash_ticket_sales = "cash ticket sales"
    total_ticket_sales = "total ticket sales"
    evening_hire_fee = "evening hire fee"
    day_hire = "day hire"
    bar_takings = "bar takings"
    total_income = "total income"
    deal_fee = "deal fee"
    cash_paid_to_musicians = "j cash paid to musicians"
    musician_internet = "musician internet"
    musician_fees = "musician fees"
    accommodation = "accommodation"
    travel = "travel"
    catering = "catering"
    equipment_hire = "equipment hire"
    work_permits = "work permits"
    sound_engineering = "sound engineering"
    hire_fees = "hire fees"
    musician_costs = "musician costs"
    prs = "prs"
    volunteer_costs = "volunteer costs"
    bar_cash_purchases = "bar cash purchases"
    drinks_cash_purchases = "drinks cash purchases"
    drinks_bank = "drinks bank"
    drinks_card = "drinks card"
    bar_expenditure = "bar expenditure"
    security = "security"
    marketing = "marketing"

    TERMS = [
        audience_number,
        advance_ticket_sales,
        credit_card_sales,
        cash_ticket_sales,
        total_ticket_sales,
        evening_hire_fee,
        day_hire,
        bar_takings,
        total_income,
        deal_fee,
        cash_paid_to_musicians,
        musician_internet,
        musician_fees,
        accommodation,
        travel,
        catering,
        equipment_hire,
        work_permits,
        sound_engineering,
        hire_fees,
        musician_costs,
        prs,
        volunteer_costs,
        bar_cash_purchases,
        drinks_cash_purchases,
        drinks_bank,
        drinks_card,
        bar_expenditure,
        security,
        marketing,
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
    def from_spreadsheet(path: Path, month: AccountingMonth) -> 'MonthlyGigReport':
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
        mtd_column = sheet_as_dict[MonthlyGigReport.week].index("MTD")
        vat_column = sheet_as_dict[MonthlyGigReport.week].index("VAT estimate")
        weeks = [
            Week(month.year, int(w))
            for w in sheet_as_dict[MonthlyGigReport.week][:-2]
            if int(w) <= month.year.num_weeks  # Blank extra week in Aug 21 report
        ]
        breakdowns = []
        for term in MonthlyGigReport.TERMS:
            if term == MonthlyGigReport.week:
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
    name = month.corresponding_calendar_month.first_day.date.strftime("%b %Y")
    path = reports_path / f"{month.year.y}" / f"Gig Report Month {month.m}  - {name}.xlsx"
    return path


if __name__ == '__main__':
    month = AccountingMonth(AccountingYear(2019), 3)
    path = path_for_accounting_month(month)
    gig_report = MonthlyGigReport.from_spreadsheet(path, month)

    # reports_path = Path(
    #     "/Users/alex/Dropbox (Personal)/vortex/Tim stuff/memory stick/Gig reports monthly/"
    # )
    # for y in [AccountingYear(y) for y in range(2019, 2024)]:
    #     for i, m in enumerate(y.accounting_months):
    #         name = m.corresponding_calendar_month.first_day.date.strftime("%b %Y")
    #         path = reports_path / f"{y.y}" / f"Gig Report Month {i + 1}  - {name}.xlsx"
    #         gig_report = MonthlyGigReport.from_spreadsheet(path, m)
